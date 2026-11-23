"""Regression: independent evaluation answers must not leak across splits."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.audit_near_duplicates import audit


class AnswerLeakageAuditTests(unittest.TestCase):
    def _write(self, root, answers):
        for split, (question, answer) in zip(("train", "validation", "test"), answers):
            record = {"messages": [{"role": "user", "content": question},
                                   {"role": "assistant", "content": answer}]}
            (root / (split + ".jsonl")).write_text(json.dumps(record) + "\n", encoding="utf-8")

    def test_repeated_answer_with_different_prompts_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, [
                ("How do I inspect a Python stack trace?", "First inspect the exception type and the bottom frame of the traceback."),
                ("What is a debugging traceback?", "First inspect the exception type and the bottom frame of the traceback."),
                ("Explain the purpose of a unit test.", "A unit test verifies one small behavior with a known expectation.")])
            report = audit(root)
            self.assertFalse(report["passed"])
            self.assertEqual(report["records"], 3)
            self.assertTrue(any(item["kind"] == "answer" for item in report["findings"]))

    def test_distinct_answers_and_prompts_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, [
                ("How do I inspect a Python stack trace?", "Inspect the exception and the bottom frame."),
                ("What is photosynthesis?", "Plants convert sunlight into stored chemical energy."),
                ("Why do boats float?", "Buoyancy balances the downward gravitational force.")])
            self.assertTrue(audit(root)["passed"])

    def test_empty_assistant_answer_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, [
                ("Question one", "!!!"),
                ("Question two", "A useful reply."),
                ("Question three", "Another useful reply.")])
            with self.assertRaisesRegex(ValueError, "empty normalized assistant answer"):
                audit(root)


if __name__ == "__main__":
    unittest.main()
