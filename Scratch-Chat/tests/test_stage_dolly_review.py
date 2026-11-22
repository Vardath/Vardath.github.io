"""Offline regression tests for quarantined Dolly review staging."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from capability.stage_dolly_review import stage


class ReviewStageTests(unittest.TestCase):
    def test_flags_duplicates_and_preserves_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            rows = []
            for i in range(12):
                rows.append({
                    "id": "dolly:" + str(i),
                    "license": "PENDING-REVIEW",
                    "messages": [
                        {"role": "user", "content": "Question " + str(i)},
                        {"role": "assistant", "content": "Answer " + str(i)},
                    ],
                })
            rows.append(dict(rows[0], id="dolly:duplicate"))
            rows.append({
                "id": "dolly:flag",
                "license": "PENDING-REVIEW",
                "messages": [
                    {"role": "user", "content": "Contact test@example.com"},
                    {"role": "assistant", "content": "Do not publish addresses"},
                ],
            })
            raw = b"upstream-fixture"
            converted = "".join(json.dumps(r) + "\n" for r in rows).encode()
            (source / "upstream.jsonl").write_bytes(raw)
            (source / "quarantined.jsonl").write_bytes(converted)
            (source / "acquisition.json").write_text(json.dumps({
                "training_allowed": False,
                "status": "QUARANTINED_NOT_APPROVED",
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "upstream_commit": "a" * 40,
                "converted": {
                    "output_sha256": hashlib.sha256(converted).hexdigest(),
                    "records": len(rows),
                },
            }))
            output = root / "review"
            result = stage(source, output)
            self.assertEqual(result["source_records"], 14)
            self.assertEqual(result["removed_flagged_records"], 1)
            self.assertEqual(result["removed_exact_duplicate_pairs"], 1)
            self.assertEqual(result["retained_records"], 12)
            self.assertFalse(result["training_allowed"])
            for name in ("train", "validation", "test"):
                data = (output / "review_splits" / (name + ".jsonl")).read_text()
                self.assertTrue(data.strip())
                for line in data.splitlines():
                    self.assertEqual(json.loads(line)["license"], "PENDING-REVIEW")
            with self.assertRaises(FileExistsError):
                stage(source, output)

    def test_rejects_tampered_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.joinpath("acquisition.json").write_text(json.dumps({
                "status": "QUARANTINED_NOT_APPROVED", "training_allowed": False,
                "raw_sha256": "0" * 64,
            }))
            root.joinpath("upstream.jsonl").write_text("tampered")
            root.joinpath("quarantined.jsonl").write_text("")
            with self.assertRaises(ValueError):
                stage(root, root / "output")


if __name__ == "__main__":
    unittest.main()
