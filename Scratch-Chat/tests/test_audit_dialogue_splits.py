import json
import tempfile
import unittest
from pathlib import Path
from capability.audit_dialogue_splits import audit_splits

class SplitAuditTests(unittest.TestCase):
    def test_detects_cross_split_prompt_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for split, prompt in (("train", "Same prompt"), ("validation", " same   PROMPT "), ("test", "Other prompt")):
                (p / (split + ".jsonl")).write_text(json.dumps({"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": "reply"}]}) + "\n")
            result = audit_splits(p)
            self.assertEqual(result["cross_split_exact_prompt_overlap"], 1)
            self.assertFalse(result["training_allowed"])

    def test_clean_partitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for split in ("train", "validation", "test"):
                (p / (split + ".jsonl")).write_text(json.dumps({"messages": [{"role": "user", "content": split}, {"role": "assistant", "content": "reply"}]}) + "\n")
            self.assertEqual(audit_splits(p)["cross_split_exact_prompt_overlap"], 0)

if __name__ == "__main__":
    unittest.main()
