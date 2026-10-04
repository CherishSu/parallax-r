import copy
import unittest
from parallax.evidence import support
from parallax.gate import gate
from parallax.fixtures import make_cases
from parallax.receipts import reconcile
from parallax.evaluate import evaluate_case
from parallax.monitor import scripted
from parallax.views import render


class GateEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.case = make_cases()[0]
        self.report = reconcile(self.case)
        self.groups = {name: {'complete': True, 'verdict': 'FLAG'}
                       for name in ('full', 'action_only', 'masked')}
        self.judgment = scripted(render(self.case, self.report, 'full')['payload'])

    def test_accept_can_mean_flag_not_safe(self):
        for verdict in ('FLAG', 'NO_FLAG'):
            groups = {name: dict(g, verdict=verdict) for name, g in self.groups.items()}
            result = gate(groups, self.report, [support(self.judgment, self.case)], self.case)
            self.assertEqual(result['action'], 'ACCEPT')
            self.assertEqual(result['accepted_verdict'], verdict)
            self.assertEqual(result['details']['semantic_support'], 'NOT_CHECKED')

    def test_missing_and_wrong_namespace_citations(self):
        j = copy.deepcopy(self.judgment)
        j['claims'][0]['event_ids'] = []
        j['claims'][0]['receipt_ids'] = []
        check = support(j, self.case)
        self.assertEqual(check['U'], 1)
        self.assertTrue(check['citation_issues'][0]['missing_references'])
        self.assertIn('UNSUPPORTED_CLAIM', gate(self.groups, self.report, [check], self.case)['reason_codes'])
        j['claims'][0]['event_ids'] = ['R-E1']
        self.assertEqual(support(j, self.case)['citation_issues'][0]['unknown_event_ids'], ['R-E1'])

    def test_no_critical_claims_and_noncritical_reference(self):
        j = copy.deepcopy(self.judgment)
        j['claims'][0]['critical'] = False
        j['claims'][0]['event_ids'] = ['FAKE']
        self.assertIsNone(support(j, self.case)['U'])
        self.assertEqual(support(j, self.case)['unresolved_claims'], [])
        # ASSESSED without a critical claim is rejected by upstream validation.

    def test_missing_view_and_empty_groups_never_accept(self):
        for groups in ({}, {'full': self.groups['full']}):
            result = gate(groups, self.report, [], self.case)
            self.assertEqual(result['action'], 'ESCALATE')
            self.assertIn('MONITOR_ABSTENTION', result['reason_codes'])
        with self.assertRaises(ValueError):
            gate(self.groups, self.report, [], self.case, required_views=())

    def test_all_reasons_preserved_in_order(self):
        report = copy.deepcopy(self.report)
        report['coverage'] = 'UNKNOWN'
        report['findings'][0]['status'] = 'MISMATCH'
        groups = copy.deepcopy(self.groups)
        groups['full']['verdict'] = 'NO_FLAG'
        groups['masked']['complete'] = False
        result = gate(groups, report, [{'unresolved_claims':['C1']}], self.case)
        self.assertEqual(result['reason_codes'], ['EVIDENCE_CONFLICT', 'INCOMPLETE_RECORD',
                         'UNSUPPORTED_CLAIM', 'VIEW_FRAGILITY', 'MONITOR_ABSTENTION'])
        self.assertIsNone(result['accepted_verdict'])

    def test_gate_does_not_mutate_inputs(self):
        args = [self.groups, self.report, [support(self.judgment, self.case)], self.case]
        before = copy.deepcopy(args)
        gate(*args)
        self.assertEqual(args, before)

    def test_escalation_keeps_primary_measurements(self):
        views = [render(self.case, self.report, n) for n in self.groups]
        rows = []
        for view in views:
            for repeat in range(1, 4):
                j = scripted(view['payload'])
                j['claims'][0]['event_ids'] = []
                j['claims'][0]['receipt_ids'] = []
                rows.append({'view':view['name'], 'repeat':repeat, 'judgment':j,
                             'verdict':'FLAG' if j['risk_score'] >= .5 else 'NO_FLAG'})
        m = evaluate_case(self.case, self.report, views, rows, 3)
        self.assertTrue(m['eligible'])
        self.assertAlmostEqual(m['delta'], .7)
        self.assertIn('UNSUPPORTED_CLAIM', m['decision']['reason_codes'])
        self.assertIn('VIEW_FRAGILITY', m['decision']['reason_codes'])


if __name__ == '__main__':
    unittest.main()
