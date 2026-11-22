"""Regression checks for the held-out behavioural scorer."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.independent_chat_eval import evaluate, score_case

class IndependentChatEvalTests(unittest.TestCase):
    def test_exact_and_negative_checks(self):
        case = {"expected": "The answer is 42.", "checks": {"contains": ["answer"], "excludes": ["unknown"]}}
        self.assertTrue(score_case(case, "the answer is 42.")["passed"])
        self.assertFalse(score_case(case, "unknown")["passed"])

    def test_structured_tool_output(self):
        case = {"checks": {"json_object": True, "contains": ['"tool"']}}
        self.assertTrue(score_case(case, '{"tool":"calculator"}')["passed"])
        self.assertFalse(score_case(case, 'calculator')["passed"])

    def test_missing_prediction_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, preds = Path(tmp)/"cases.jsonl", Path(tmp)/"predictions.jsonl"
            cases.write_text(json.dumps({"id":"multi-turn-1","messages":[{"role":"user","content":"Hello"},{"role":"assistant","content":"Hi"},{"role":"user","content":"What did I say?"}],"checks":{"contains":["hello"]}})+"\n",encoding="utf-8")
            preds.write_text("",encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate(cases,preds)
            preds.write_text(json.dumps({"id":"multi-turn-1","response":"You said hello."})+"\n",encoding="utf-8")
            self.assertEqual(evaluate(cases,preds)["passed"],1)

if __name__ == "__main__":
    unittest.main()
