"""Regression checks for fail-closed training split role sequencing."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from capability.dialogue_source_manifest import verify_split_files


class TrainingRoleGateTests(unittest.TestCase):
    def verify(self, roles):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"source_id": "authored", "upstream_url": "https://example.org/authored",
                    "revision": "fixed", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                    "license_identifier": "CC0-1.0", "attribution": "none",
                    "collection_method": "test fixture", "privacy_review": "no personal data",
                    "moderation_procedure": "manual", "original_sha256": "a" * 64,
                    "reviewer": "test", "decision": "approved"}
            for split in ("train", "validation", "test"):
                selected = roles if split == "train" else ["user", "assistant"]
                messages = [{"role": role, "content": f"{split} {i} {role}"}
                            for i, role in enumerate(selected)]
                raw = (json.dumps({"messages": messages}) + "\n").encode()
                (root / f"{split}.jsonl").write_bytes(raw)
                data[split + "_sha256"] = hashlib.sha256(raw).hexdigest()
                data[split + "_records"] = 1
            return verify_split_files(data, root)

    def test_valid_multi_turn(self):
        self.assertTrue(self.verify(["system", "user", "assistant", "user", "assistant"]))

    def test_valid_tool_reply(self):
        self.assertTrue(self.verify(["user", "assistant", "tool", "assistant"]))

    def test_orphan_tool(self):
        with self.assertRaises(ValueError):
            self.verify(["user","tool","assistant"])

    def test_orphan_assistant(self):
        with self.assertRaises(ValueError):
            self.verify(["assistant","user","assistant"])

    def test_double_user(self):
        with self.assertRaises(ValueError):
            self.verify(["user","user","assistant"])

    def test_late_system(self):
        with self.assertRaises(ValueError):
            self.verify(["user","assistant","system","assistant"])

    def test_unfinished(self):
        with self.assertRaises(ValueError):
            self.verify(["user","assistant","user"])

    def test_double_assistant(self):
        with self.assertRaises(ValueError):
            self.verify(["user","assistant","assistant"])

if __name__ == "__main__":
    unittest.main()
