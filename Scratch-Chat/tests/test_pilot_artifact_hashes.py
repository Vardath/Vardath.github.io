"""Regression checks for byte-exact, streaming pilot artifact provenance."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability.run_dialogue_pilot import sha256_file


class ArtifactHashTests(unittest.TestCase):
    def test_hash_matches_standard_sha256_for_binary_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            content = bytes(range(256)) * 9000
            path.write_bytes(content)
            self.assertEqual(sha256_file(path), hashlib.sha256(content).hexdigest())
            path.write_bytes(content + b"modified")
            self.assertNotEqual(sha256_file(path), hashlib.sha256(content).hexdigest())

    def test_missing_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                sha256_file(Path(directory) / "missing.pt")


if __name__ == "__main__":
    unittest.main()
