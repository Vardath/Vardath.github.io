import unittest
from capability.probe_scoring import score


class ProbeScoringTests(unittest.TestCase):
    def report(self, fact="Four.", instruction="blue", memory="You said violet."):
        ids = ["greeting", "basic_fact", "instruction", "short_explanation",
               "multi_turn_memory", "refusal"]
        replies = dict(basic_fact=fact, instruction=instruction, multi_turn_memory=memory)
        return {"checkpoint_step": 10, "probes": [
            {"id": name, "response": replies.get(name, "")} for name in ids]}

    def test_correct_answers(self):
        result = score(self.report())
        self.assertEqual(result["passed"], 3)
        self.assertFalse(result["ready_for_conversation"])

    def test_repetitive_nonsense_fails(self):
        result = score(self.report("the the the", "blue blue", "violetish"))
        self.assertEqual(result["passed"], 0)

    def test_missing_probe_rejected(self):
        report = self.report()
        report["probes"].pop()
        with self.assertRaises(ValueError):
            score(report)

    def test_duplicate_probe_rejected(self):
        report = self.report()
        report["probes"].append(report["probes"][0])
        with self.assertRaises(ValueError):
            score(report)


if __name__ == "__main__":
    unittest.main()
