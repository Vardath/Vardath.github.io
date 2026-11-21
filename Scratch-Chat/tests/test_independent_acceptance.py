"""Checkpoint-independent tests for the acceptance runner itself."""
import json
import sys
import unittest

from capability.independent_acceptance import evaluate, grade


class IndependentAcceptanceTests(unittest.TestCase):
    def test_quality_checks_are_not_transport_only(self):
        case = {"kind": "contains", "expected": "violet-orbit-73"}
        self.assertFalse(grade(case, {"ok": True, "response": "I do not know"})[0])
        self.assertTrue(grade(case, {"ok": True, "response": "violet-orbit-73"})[0])
        self.assertFalse(grade({"kind": "equals", "expected": "43"},
                               {"ok": True, "response": "44"})[0])

    def test_real_subprocess_jsonl_roundtrip(self):
        script = ("import json,sys; "
                  "[(lambda q: print(json.dumps({'ok':True,'model':'vardath-scratch-chat'} "
                  "if q['method']=='health' else {'ok':False,'error':'invalid'}),flush=True))"
                  "(json.loads(line)) for line in sys.stdin]")
        cases = [{"id": "health", "kind": "health", "request": {"method": "health"}},
                 {"id": "invalid", "kind": "error", "request": {"method": "invalid"}}]
        result = evaluate([sys.executable, "-c", script], cases=cases, timeout=10)
        self.assertTrue(result["passed"], result)

    def test_fails_closed_on_missing_response(self):
        cases = [{"id": "health", "kind": "health", "request": {"method": "health"}}]
        result = evaluate([sys.executable, "-c", "pass"], cases=cases, timeout=10)
        self.assertFalse(result["passed"])
        self.assertEqual(result["response_lines"], 0)


if __name__ == "__main__":
    unittest.main()
