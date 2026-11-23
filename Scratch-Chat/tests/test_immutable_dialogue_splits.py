"""Regression tests for immutable reviewed split outputs."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.prepare_dialogue_splits import prepare


class ImmutableSplitTests(unittest.TestCase):
    def test_refuses_existing_artifacts_without_modification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "reviewed.jsonl"
            rows = [
                {"conversation_id": f"family-{i}", "messages": [
                    {"role": "user", "content": f"Question {i}"},
                    {"role": "assistant", "content": f"Answer {i}"}
                ]} for i in range(6)
            ]
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            output = root / "splits"
            first = prepare(source, output)
            original = {p.name: p.read_bytes() for p in output.iterdir()}
            with self.assertRaisesRegex(FileExistsError, "overwrite"):
                prepare(source, output, seed="different-seed")
            self.assertEqual(original, {p.name: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(first["source_sha256"], __import__("hashlib").sha256(source.read_bytes()).hexdigest())

    def test_refuses_unrelated_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "splits"
            output.mkdir()
            (output / "do-not-delete.txt").write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prepare(root / "missing.jsonl", output)
            self.assertEqual((output / "do-not-delete.txt").read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
