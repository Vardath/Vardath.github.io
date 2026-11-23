"""Regression tests: tiny seed cannot be misrepresented as training-ready."""
import tempfile
import unittest
from pathlib import Path

from capability.prepare_dialogue_splits import prepare
from capability.dialogue_readiness import assess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "original_cc0_multiturn_20261124.jsonl"


class DialogueReadinessTests(unittest.TestCase):
    def test_original_seed_fails_capacity_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "splits"
            prepare(SOURCE, out, seed="capacity-gate-test",
                    train_fraction=0.67, validation_fraction=0.165)
            report = assess(out)
            self.assertEqual(sum(report["counts"].values()), 24)
            self.assertFalse(report["automated_preflight_passed"])
            self.assertFalse(report["ready_for_capacity_training"])
            self.assertTrue(any("minimum" in reason for reason in report["reasons"]))

    def test_rejects_invalid_minimum(self):
        with self.assertRaises(ValueError):
            assess(".", min_train=0)
        with self.assertRaises(ValueError):
            assess(".", min_train=True)


if __name__ == "__main__":
    unittest.main()
