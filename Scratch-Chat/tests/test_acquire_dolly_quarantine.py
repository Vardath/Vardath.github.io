import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability.acquire_dolly_quarantine import acquire, MAX_BYTES

REV = "a" * 40
API_RESPONSE = {"sha": REV, "siblings": [{"rfilename": "databricks-dolly-15k.jsonl"}],
                "cardData": {"license": "cc-by-sa-3.0"}}
RAW = (json.dumps({"instruction": "What is 2+2?", "response": "4"}) + "\n").encode()

class AcquisitionTests(unittest.TestCase):
    def test_pinned_quarantine_and_provenance(self):
        calls = []
        def fake_fetch(url, limit=MAX_BYTES):
            calls.append(url)
            return json.dumps(API_RESPONSE).encode() if "/api/" in url else RAW
        with tempfile.TemporaryDirectory() as directory, patch("capability.acquire_dolly_quarantine.fetch", side_effect=fake_fetch):
            dest = Path(directory) / "candidate"
            report = acquire(dest)
            self.assertFalse(report["training_allowed"])
            self.assertEqual(report["raw_sha256"], hashlib.sha256(RAW).hexdigest())
            self.assertIn(REV, calls[-1])
            self.assertEqual(json.loads((dest / "quarantined.jsonl").read_text())["license"], "PENDING-REVIEW")
            with self.assertRaises(FileExistsError):
                acquire(dest)

    def test_missing_revision_or_ambiguous_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for bad in [{"sha": "main", "siblings": API_RESPONSE["siblings"]},
                        {"sha": REV, "siblings": [{"rfilename": "a.jsonl"}, {"rfilename": "b.jsonl"}]}]:
                with patch("capability.acquire_dolly_quarantine.fetch", return_value=json.dumps(bad).encode()):
                    with self.assertRaises(ValueError):
                        acquire(Path(directory) / "missing")
            self.assertFalse((Path(directory) / "missing").exists())

if __name__ == "__main__":
    unittest.main()
