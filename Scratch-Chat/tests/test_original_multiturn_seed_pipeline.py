"""Regression checks for the repaired original CC0 dialogue seed.

The test is intentionally checkpoint-independent and never approves external data.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from capability.prepare_dialogue_splits import prepare
from capability.audit_near_duplicates import audit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "original_cc0_multiturn_20261124.jsonl"


class OriginalSeedPipelineTests(unittest.TestCase):
    def test_repaired_seed_is_grouped_and_split_deterministically(self):
        raw = SOURCE.read_bytes()
        records = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        self.assertEqual(len(records), 24)
        self.assertEqual(len({r["id"] for r in records}), 24)
        self.assertEqual(len({r["source_conversation_id"] for r in records}), 24)
        for record in records:
            self.assertEqual(record["license"], "CC0-1.0")
            self.assertEqual([m["role"] for m in record["messages"]],
                             ["user", "assistant", "user", "assistant"])
            self.assertTrue(all(m["content"].strip() for m in record["messages"]))
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            report = prepare(SOURCE, first, seed="original-cc0-20261124")
            prepare(SOURCE, second, seed="original-cc0-20261124")
            self.assertEqual(report["source_sha256"], hashlib.sha256(raw).hexdigest())
            seen = set()
            for split in ("train", "validation", "test"):
                a = (first / (split + ".jsonl")).read_bytes()
                self.assertEqual(a, (second / (split + ".jsonl")).read_bytes())
                self.assertEqual(hashlib.sha256(a).hexdigest(), report["splits"][split]["sha256"])
                rows = [json.loads(line) for line in a.decode().splitlines()]
                self.assertGreater(len(rows), 0)
                for row in rows:
                    self.assertNotIn(row["source_conversation_id"], seen)
                    seen.add(row["source_conversation_id"])
            self.assertEqual(len(seen), 24)
            result = audit(first, threshold=0.8)
            self.assertIn("passed", result)
            # A failed lexical audit must remain visible, never silently approved.
            if not result["passed"]:
                self.assertTrue(result["findings"])


if __name__ == "__main__":
    unittest.main()
