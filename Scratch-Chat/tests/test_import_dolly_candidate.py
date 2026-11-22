import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from capability.import_dolly_candidate import convert


class CandidateImportTests(unittest.TestCase):
    def test_quarantines_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.jsonl"
            row = {"instruction": "Explain gravity", "context": "Briefly", "response": "Attraction between masses."}
            source.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            result = convert(source, root / "candidate.jsonl", revision="abc123", expected_sha256=digest)
            self.assertEqual(result["records"], 1)
            self.assertEqual(result["status"], "QUARANTINED_NOT_APPROVED")
            record = json.loads((root / "candidate.jsonl").read_text())
            self.assertEqual(record["license"], "PENDING-REVIEW")
            self.assertIn("Context:", record["messages"][0]["content"])

    def test_fails_closed_on_revision_hash_and_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.jsonl"
            source.write_text('{"instruction":"Hi","response":"Hello"}\n')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                convert(source, root / "out", revision="main", expected_sha256=digest)
            with self.assertRaises(ValueError):
                convert(source, root / "out", revision="abc123", expected_sha256="0" * 64)
            convert(source, root / "out", revision="abc123", expected_sha256=digest)
            with self.assertRaises(FileExistsError):
                convert(source, root / "out", revision="abc123", expected_sha256=digest)


if __name__ == "__main__":
    unittest.main()
