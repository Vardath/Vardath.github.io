"""Offline tests: no external corpus download or implicit license approval."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability.source_snapshot import acquire, validate_url

class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.read_count = 0
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        if self.read_count:
            return b""
        self.read_count += 1
        return self.payload

class FakeOpener:
    def __init__(self, payload):
        self.payload = payload
    def open(self, request, timeout):
        return FakeResponse(self.payload)

class SnapshotTests(unittest.TestCase):
    def test_reject_untrusted_urls(self):
        for url in ("http://example.org/a", "https://user:pass@example.org/a",
                    "https://localhost/a", "https://example.org/a#fragment"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_verified_bytes_and_nonapproval(self):
        payload = b'{"messages":[]}\n'
        expected = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "snapshot.jsonl"
            with patch("capability.source_snapshot.build_opener", return_value=FakeOpener(payload)):
                report = acquire("https://example.org/revision/abc.jsonl", expected, output)
            self.assertEqual(output.read_bytes(), payload)
            self.assertEqual(report["admission"], "NOT_APPROVED")
            with self.assertRaises(FileExistsError):
                acquire("https://example.org/revision/abc.jsonl", expected, output)

    def test_digest_mismatch_deletes_partial(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "snapshot.jsonl"
            with patch("capability.source_snapshot.build_opener", return_value=FakeOpener(b"wrong")):
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    acquire("https://example.org/revision/abc.jsonl", "0" * 64, output)
            self.assertFalse(output.exists())
            self.assertFalse(Path(str(output) + ".partial").exists())

    def test_byte_limit_deletes_partial(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "snapshot.jsonl"
            with patch("capability.source_snapshot.build_opener", return_value=FakeOpener(b"12345")):
                with self.assertRaisesRegex(ValueError, "byte limit"):
                    acquire("https://example.org/revision/abc.jsonl", "0" * 64, output, max_bytes=4)
            self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
