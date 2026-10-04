import copy
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from parallax.fixtures import make_cases, stress_cases
from parallax.receipts import reconcile
from parallax.views import render, check_invariants
from parallax.schema import digest, validate_judgment
from parallax.monitor import judge, scripted
from parallax.evaluate import evaluate_case, summary, support
from parallax.report import build_report


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.case = make_cases()[0]
        self.report = reconcile(self.case)
        self.views = [render(self.case, self.report, n) for n in ('full','action_only','masked','ledger')]

    def test_permissions_survive_every_view(self):
        self.assertTrue(check_invariants(self.case, self.report, self.views))
        for v in self.views:
            self.assertEqual(v['payload']['evidence']['policy']['text'], self.case['policy'])
        changed = copy.deepcopy(self.views)
        changed[1]['payload']['evidence']['policy']['text'] = 'You may email it.'
        changed[1]['hash'] = digest(changed[1]['payload'])
        with self.assertRaises(ValueError):
            check_invariants(self.case, self.report, changed)

    def test_receipt_faults(self):
        expected = {'mismatch':'MISMATCH','dropout':'PHANTOM','hidden':'HIDDEN','chain_break':'CHAIN_BREAK'}
        for c in stress_cases(self.case):
            self.assertIn(expected[c['condition']], [f['status'] for f in reconcile(c)['findings']])
        self.assertEqual(self.report['findings'][0]['status'], 'SUPPORTED')

    def test_invalid_scores_and_status(self):
        j = scripted(self.views[0]['payload'])
        for value in (True, float('nan'), 2, -1):
            bad = copy.deepcopy(j); bad['risk_score'] = value
            with self.assertRaises(ValueError): validate_judgment(bad)
        j['assessment_status'] = 'INSUFFICIENT_EVIDENCE'
        with self.assertRaises(ValueError): validate_judgment(j)
        j['risk_score'] = None
        validate_judgment(j)

    def test_unknown_citation_is_measured(self):
        j = scripted(self.views[0]['payload'])
        j['claims'][0]['event_ids'] = ['INVENTED']
        validate_judgment(j)
        self.assertEqual(support(j,self.case)['U'], 1)

    def run_case(self, case):
        rep = reconcile(case)
        views = [render(case,rep,n) for n in ('full','action_only','masked')]
        with tempfile.TemporaryDirectory() as tmp:
            rows = [judge(v,case['case_id'],i,'demo','test',Path(tmp)) for v in views for i in range(1,4)]
        return {'case':case,'metrics':evaluate_case(case,rep,views,rows,3),'rows':rows}

    def test_disagreement_and_benign_acceptance(self):
        bad = self.run_case(self.case)
        good = self.run_case(make_cases()[1])
        self.assertIn('VIEW_FRAGILITY',bad['metrics']['decision']['reason_codes'])
        self.assertAlmostEqual(bad['metrics']['delta'],.7)
        self.assertEqual(good['metrics']['decision']['action'],'ACCEPT')
        self.assertEqual(good['metrics']['decision']['accepted_verdict'],'NO_FLAG')
        self.assertEqual(summary([bad,good],'demo')['pilot_status'],'NOT_APPLICABLE_SCRIPTED_DEMO')

    def test_abstention_not_zero_risk(self):
        r = self.run_case(self.case)
        r['rows'][0]['verdict']='ABSTAIN'
        r['rows'][0]['judgment']=None
        m=evaluate_case(self.case,self.report,self.views[:3],r['rows'],3)
        self.assertFalse(m['eligible'])
        self.assertIsNone(m['delta'])
        self.assertIn('MONITOR_ABSTENTION',m['decision']['reason_codes'])

    def test_cache_replay_and_repeat_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)
            first=judge(self.views[0],'case',1,'demo','test',cache)
            replay=judge(self.views[0],'case',1,'demo','test',cache,replay=True)
            self.assertFalse(first['cache_hit']);self.assertTrue(replay['cache_hit'])
            with self.assertRaises(ValueError):judge(self.views[0],'case',2,'demo','test',cache,replay=True)
            judge(self.views[0],'case',2,'demo','test',cache)
            self.assertEqual(len(list(cache.glob('*.json'))),2)

    def test_html_escapes_script_injection(self):
        page=build_report({'text':'</script><script>alert(1)</script>'})
        self.assertNotIn('</script><script>alert',page)
        self.assertIn('\\u003c/script',page)

    def test_seven_per_group_pilot_minimum(self):
        # Scripted fixtures exercise decision logic only; not real-model evidence.
        results = [self.run_case(c) for c in make_cases()[:14]]
        self.assertEqual(summary(results, 'anthropic')['pilot_status'], 'CONTINUE')
        for label in ('harmful', 'benign'):
            reduced = copy.deepcopy(results)
            next(r for r in reduced if r['case']['ground_truth'] == label)['metrics']['eligible'] = False
            self.assertEqual(summary(reduced, 'anthropic')['pilot_status'], 'INCONCLUSIVE')
        self.assertEqual(summary(results, 'demo')['pilot_status'], 'NOT_APPLICABLE_SCRIPTED_DEMO')

    def test_identical_views_keep_distinct_cache_records(self):
        hidden=stress_cases(self.case)[2]
        result=self.run_case(hidden)
        self.assertTrue(result['metrics']['groups']['masked']['complete'])
        self.assertIn('EVIDENCE_CONFLICT',result['metrics']['decision']['reason_codes'])

    def test_real_adapter_validation_without_network(self):
        j=scripted(self.views[0]['payload'])
        raw={'content':[{'type':'text','text':json.dumps(j)}],'usage':{'input_tokens':5,'output_tokens':10}}
        with tempfile.TemporaryDirectory() as tmp, patch('parallax.monitor.api_call',return_value=(raw,[])):
            row=judge(self.views[0],'case',1,'anthropic','test-model',Path(tmp))
            self.assertEqual(row['verdict'],'NO_FLAG')
            self.assertIn('usage',row['raw'])
        raw={'content':[{'type':'text','text':'not JSON'}]}
        with tempfile.TemporaryDirectory() as tmp, patch('parallax.monitor.api_call',return_value=(raw,[])):
            row=judge(self.views[0],'case',1,'anthropic','test-model',Path(tmp))
            self.assertEqual(row['verdict'],'ABSTAIN')
            self.assertIsNotNone(row['error'])


if __name__ == '__main__': unittest.main()
