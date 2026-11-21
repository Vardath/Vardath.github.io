"""Regression tests for original dialogue corpus integrity."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.dialogue_corpus import FAMILIES, build, validate

class DialogueCorpusTests(unittest.TestCase):
    def test_original_corpus_passes(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            build(out)
            self.assertEqual(validate(out)["examples"], sum(len(v) for v in FAMILIES.values()))

    def test_mutated_split_fails_digest(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            build(out)
            p = out / "test.jsonl"
            p.write_text(p.read_text() + " ", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(out)

    def test_duplicate_across_splits_rejected_even_with_updated_manifest(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            build(out)
            row = json.loads((out / "train.jsonl").read_text().splitlines()[0])
            p = out / "test.jsonl"
            rows = [json.loads(line) for line in p.read_text().splitlines()]
            rows[0] = row
            payload = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows)
            p.write_text(payload, encoding="utf-8")
            manifest_path = out / "source.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["sha256"]["test"] = hashlib.sha256(payload.encode()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                validate(out)

if __name__ == "__main__":
    unittest.main()
