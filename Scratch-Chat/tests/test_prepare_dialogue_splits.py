"""Regression tests for deterministic dialogue split preparation."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.prepare_dialogue_splits import prepare


class DialogueSplitTests(unittest.TestCase):
    def test_repeatable_group_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            rows = []
            for i in range(30):
                for turn in range(2):
                    rows.append({"source_conversation_id": f"conversation-{i}",
                                 "messages": [{"role": "user", "content": f"Question {i} turn {turn}"},
                                              {"role": "assistant", "content": f"Answer {i} turn {turn}"}]})
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            first = prepare(source, root / "one")
            second = prepare(source, root / "two")
            self.assertEqual(first, second)
            seen = set()
            for split in ("train", "validation", "test"):
                self.assertGreater(first["splits"][split]["records"], 0)
                records = [json.loads(line) for line in (root / "one" / (split + ".jsonl")).read_text().splitlines()]
                families = {row["source_conversation_id"] for row in records}
                self.assertFalse(families & seen)
                seen |= families
            self.assertEqual(len(seen), 30)

    def test_rejects_insufficient_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text(json.dumps({"messages": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]}) + "\n")
            with self.assertRaises(ValueError):
                prepare(source, root / "splits")


if __name__ == "__main__":
    unittest.main()
