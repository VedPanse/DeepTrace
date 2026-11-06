"""Scoring edge cases and the included paired dataset; no API calls."""
import copy
import unittest
import reproduce


def paired_rows(target, verdict, restriction='approved_only'):
    return [dict(case_id='example', family=0, variant='example', condition=c,
                 split='test', evidence_tokens=10,
                 expected=dict(effective_restriction=restriction, argument_origin='caller_string',
                               shell_enabled=True, policy_violation=target),
                 response=dict(status='ok', parsed=dict(effective_restriction=restriction,
                               argument_origin='caller_string', shell_enabled=True,
                               policy_violation=verdict, reason='Test answer')))
            for c in reproduce.CONDITIONS]


THRESHOLDS = {c: {'threshold': 1} for c in reproduce.CONDITIONS}


class ReproductionTests(unittest.TestCase):
    def test_null_is_not_safe(self):
        result = reproduce.calculate(paired_rows(False, None), THRESHOLDS)[0]
        self.assertEqual(result['raw_policy_correct'], 0)
        self.assertEqual(result['known_abstentions'], 1)

    def test_correct_unknown_counts(self):
        result = reproduce.calculate(paired_rows(None, None, 'unknown'), THRESHOLDS)[0]
        self.assertEqual(result['raw_policy_correct'], 1)
        self.assertEqual(result['unknown_correct'], 1)
        self.assertEqual(result['safe_n'], 0)

    def test_contradiction_stays_in_raw_counts(self):
        result = reproduce.calculate(paired_rows(False, True), THRESHOLDS)[0]
        self.assertEqual(result['contradictions'], 1)
        self.assertEqual(result['raw_false_accusations'], 1)
        self.assertEqual(result['false_alarms'], 0)

    def test_invalid_unknown_is_not_correct(self):
        rows = paired_rows(None, None, 'unknown')
        for row in rows:
            row['response']['parsed']['shell_enabled'] = 'true'
        result = reproduce.calculate(rows, THRESHOLDS)[0]
        self.assertEqual(result['invalid'], 1)
        self.assertEqual(result['raw_policy_correct'], 0)

    def test_duplicate_and_missing_pairs_fail(self):
        rows = paired_rows(False, False)
        for broken in (rows[:-1], rows + [copy.deepcopy(rows[0])]):
            with self.assertRaises(ValueError):
                reproduce.calculate(broken, THRESHOLDS)

    def test_reference_disagreement_fails(self):
        rows = paired_rows(False, False)
        rows[0]['expected']['policy_violation'] = True
        with self.assertRaises(ValueError):
            reproduce.calculate(rows, THRESHOLDS)

    def test_saved_flags_ignored_and_table_matches(self):
        inputs, _ = reproduce.load_inputs()
        rows = copy.deepcopy(inputs[reproduce.DATA + 'test_analysis.json']['decoded'])
        for row in rows:
            row['policy_correct'] = False
            row['fact_correct'] = False
            row['verdict'] = None
            row['contradictions'] = []
        metrics = reproduce.calculate(rows, THRESHOLDS)
        self.assertEqual([m['raw_policy_correct'] for m in metrics], [20, 26, 24])
        self.assertEqual([m['joint_facts_correct'] for m in metrics], [36, 36, 36])
        self.assertEqual([m['raw_unsafe_identified'] for m in metrics], [6, 4, 6])
        self.assertEqual([m['raw_false_accusations'] for m in metrics], [13, 5, 9])


if __name__ == '__main__':
    unittest.main()
