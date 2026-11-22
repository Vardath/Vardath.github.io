"""Regression coverage for malformed dialogue role order in source admission."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from capability.dialogue_admission import audit


class RoleOrderAdmissionTests(unittest.TestCase):
    def test_rejects_invalid_turn_sequences(self):
        bad = [
            ["assistant", "user"],
            ["user", "user", "assistant"],
            ["user", "assistant", "assistant"],
            ["user", "tool", "assistant"],
            ["user", "assistant", "system", "assistant"],
            ["user", "assistant", "tool"],
        ]
        for roles in bad:
            with self.subTest(roles=roles), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                digests = {}
                for split in ("train", "validation", "test"):
                    record = {
                        "id": split, "source_id": "local-test", "license": "CC0-1.0",
                        "messages": [{"role": role, "content": f"{split} {role} {i}"}
                                     for i, role in enumerate(roles if split == "train" else ["user", "assistant"])],
                    }
                    raw = (json.dumps(record) + "\n").encode()
                    (root / f"{split}.jsonl").write_bytes(raw)
                    digests[split] = hashlib.sha256(raw).hexdigest()
                manifest = {
                    "source_id": "local-test", "source_url": "https://example.org/test",
                    "revision": "test-revision", "license": "CC0-1.0",
                    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                    "approval": "approved", "approved_by": "test",
                    "retrieved_utc": "2026-11-23T00:00:00Z", "sha256": digests,
                }
                (root / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    audit(root / "manifest.json", *(root / f"{s}.jsonl" for s in ("train", "validation", "test")))


if __name__ == "__main__":
    unittest.main()
