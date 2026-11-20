"""Regression checks for fail-closed readiness assessment."""
import unittest
from capability.readiness_gate import assess


class ReadinessGateTests(unittest.TestCase):
    def setUp(self):
        self.report = {"checkpoint_step": 1800, "parameters": 139968,
                       "results": {"validation": {"loss": 3.1, "tokens_evaluated": 20000},
                                   "test": {"loss": 3.2, "tokens_evaluated": 20000}}}
        self.scores = {"checkpoint_step": 1800,
                       "checks": {"basic_fact": False, "instruction": False, "multi_turn_memory": False},
                       "passed": 0, "total": 3}

    def test_valid_report_is_not_ready(self):
        self.assertFalse(assess(self.report, probe_scores=self.scores)["ready_for_conversation"])

    def test_mismatched_checkpoint_rejected(self):
        scores = dict(self.scores, checkpoint_step=1500)
        with self.assertRaises(ValueError):
            assess(self.report, probe_scores=scores)

    def test_inconsistent_totals_rejected(self):
        scores = dict(self.scores, passed=3)
        with self.assertRaises(ValueError):
            assess(self.report, probe_scores=scores)

    def test_non_boolean_check_rejected(self):
        scores = dict(self.scores, checks={"instruction": "false"}, total=1)
        with self.assertRaises(ValueError):
            assess(self.report, probe_scores=scores)

    def test_missing_checks_rejected(self):
        with self.assertRaises(ValueError):
            assess(self.report, probe_scores={"checkpoint_step": 1800})


if __name__ == "__main__":
    unittest.main()
