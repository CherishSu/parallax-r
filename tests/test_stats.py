import unittest
from pathlib import Path
from parallax.stats import paired_statistics, analyze_run
from parallax.monitor import prompt


class StatisticsTests(unittest.TestCase):
    def test_exact_two_cluster_result(self):
        r = paired_statistics([dict(scenario_id='a', delta=1), dict(scenario_id='b', delta=1)], draws=100)
        self.assertEqual(r['sign_flip_p'], .5)
        self.assertEqual(r['bootstrap_ci'], [1, 1])
        self.assertEqual(r['sign_flip_draws'], 4)

    def test_cluster_members_not_independent(self):
        r = paired_statistics([dict(scenario_id='a', delta=1)] * 3 + [dict(scenario_id='b', delta=1)], draws=100)
        self.assertEqual(r['cases'], 4)
        self.assertEqual(r['scenarios'], 2)
        self.assertEqual(r['sign_flip_p'], .5)

    def test_empty_and_single_cluster_undefined(self):
        for rows in ([], [dict(scenario_id='a', delta=1)] * 3):
            r = paired_statistics(rows, draws=100)
            self.assertIsNone(r['sign_flip_p'])
            self.assertIsNone(r['bootstrap_ci'])

    def test_balanced_and_reproducible(self):
        rows = [dict(scenario_id='a', delta=-1), dict(scenario_id='b', delta=1)]
        r = paired_statistics(rows, draws=100)
        self.assertEqual(r, paired_statistics(rows, draws=100))
        self.assertEqual(r['sign_flip_p'], 1)
        self.assertEqual(r['mean_delta'], 0)

    def test_demo_and_ineligible_exclusion(self):
        run = dict(mode='demo', results=[dict(case=dict(scenario_id='a', ground_truth='harmful'), metrics=dict(eligible=False, delta=None))])
        r = analyze_run(run, draws=100)
        self.assertEqual(r['interpretation'], 'SCRIPTED_DEMO_NOT_RESEARCH')
        self.assertEqual(r['by_class']['harmful']['cases'], 0)

    def test_runtime_prompt_matches_reviewed_file(self):
        saved = Path(__file__).resolve().parents[1] / 'REVIEWER-PROMPT.txt'
        self.assertEqual(prompt().strip(), saved.read_text(encoding='utf-8').strip())


class ReadinessTests(unittest.TestCase):
    def test_current_offline_package_is_consistent(self):
        from preflight import check
        result = check()
        self.assertEqual(result['local_checks'], 'PASS', result['problems'])
        self.assertEqual(result['human_comparison_checks'], 5)
        self.assertEqual(result['model'], 'claude-sonnet-5-5')
        self.assertIsNone(result['cost_estimate']['authorized_budget'])

    def test_invalid_budget_is_rejected_without_network(self):
        from test_bc import quiet
        for value in ('nan', 'inf', '-1', '0'):
            code, _, error = quiet(['--max-spend-usd', value])
            self.assertEqual(code, 2)
            self.assertIn('finite positive', error)
