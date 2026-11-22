import json
import tempfile
import unittest
from pathlib import Path

from capability.audit_near_duplicates import audit


class NearDuplicateAuditTests(unittest.TestCase):
    def write(self, directory, split, prompts):
        with (directory / (split + ".jsonl")).open("w", encoding="utf-8") as f:
            for prompt in prompts:
                f.write(json.dumps({"messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "Acknowledged."}
                ]}) + "\n")

    def test_normalized_near_duplicate_across_splits_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(root, "train", ["Please explain how to repair the old engine carefully today"])
            self.write(root, "validation", ["PLEASE explain how to repair the old engine carefully tomorrow"])
            self.write(root, "test", ["What is the capital city of France?"])
            result = audit(root, threshold=0.6)
            self.assertFalse(result["passed"])
            self.assertEqual(result["findings"][0]["a"], "train:1")

    def test_unrelated_prompts_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(root, "train", ["Describe the engine oil pressure sensor"])
            self.write(root, "validation", ["How do bees pollinate flowers?"])
            self.write(root, "test", ["Calculate seven plus eleven"])
            self.assertTrue(audit(root)["passed"])

    def test_index_matches_exhaustive_reference(self):
        from capability.audit_near_duplicates import normalize, shingles
        prompts = ["the old engine requires regular maintenance today",
                   "the old engine requires regular maintenance tomorrow",
                   "how do bees pollinate the flowers",
                   "how do bees pollinate the flowers",
                   "calculate seven plus eleven",
                   "describe cargo ships and stations"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for split, values in zip(("train", "validation", "test"),
                                     (prompts[:2], prompts[2:4], prompts[4:])):
                self.write(root, split, values)
            result = audit(root, threshold=0.6)
            self.assertEqual(result["candidate_pairs"], 2)
            self.assertTrue(result["passed"])
            self.assertEqual(len(result["findings"]), 0)

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(ValueError):
            audit(".", threshold=0)


if __name__ == "__main__":
    unittest.main()
