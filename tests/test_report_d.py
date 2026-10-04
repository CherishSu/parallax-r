"""Report-only regressions; no changes to A/B/C logic or network calls."""
import unittest
from parallax.report import build_report, summary_tables


class ReportTests(unittest.TestCase):
    def test_six_step_navigation_is_preserved(self):
        page = build_report({})
        for step in ('1. What happened', '2. Check records', '3. Make versions',
                     '4. Ask reviewer', '5. Compare', '6. Decide'):
            self.assertIn(step, page)
        self.assertNotIn('<script src=', page)

    def test_summary_tables_use_saved_counts_and_denominators(self):
        text = summary_tables({
            'classes': {'harmful': {'planned': 10, 'eligible': 7, 'excluded_by_checks': 2, 'incomplete_primary': 1}},
            'harmful_directions': {'more_forgiving': {'count': 3, 'rate': 3/7}, 'stricter': {'count': 1, 'rate': 1/7}},
            'call_abstention_causes': {'TRANSPORT_FAILURE': 4}, 'scheduled_judgments_denominator': 144,
            'escalation_by_class': {'harmful': {'escalated': 6, 'cases': 8}}})
        self.assertIn('<td>harmful</td><td>10</td><td>7</td><td>2</td><td>1</td><td>3</td>', text)
        self.assertIn('<td>TRANSPORT_FAILURE</td><td>4</td><td>144</td>', text)
        self.assertIn('<td>harmful</td><td>6</td><td>8</td>', text)

    def test_exclusion_html_is_escaped(self):
        page = build_report({'summary': {'excluded_cases': [{'case_id': '<img src=x onerror=alert(1)>',
                                                            'reason': '</script><script>alert(1)</script>'}]}})
        self.assertNotIn('<img src=x', page)
        self.assertNotIn('</script><script>alert(1)', page)
        self.assertIn('&lt;img', page)
        self.assertIn('\\u003c/script', page)

    def test_missing_values_are_not_reported_as_zero(self):
        text = summary_tables({})
        self.assertIn('Unavailable', text)
        self.assertNotIn('<td>0</td>', text)

    def test_compare_and_empty_state_fields(self):
        page = build_report({})
        for value in ('m.direction', 'm.expected_verdict', 'm.view_results',
                      'Not applicable', 'No cases reached review', 'UNSUPPORTED_CLAIM'):
            self.assertIn(value, page)


if __name__ == '__main__':
    unittest.main()
