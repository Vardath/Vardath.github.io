import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from capability.dialogue_source_manifest import validate_manifest, verify_split_files

H = lambda char: char * 64


class SourceManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "source_id": "example", "upstream_url": "https://example.org/data",
            "revision": "immutable-commit", "license_url": "https://example.org/license",
            "license_identifier": "CC0-1.0", "attribution": "none",
            "collection_method": "author supplied", "privacy_review": "reviewed",
            "moderation_procedure": "reviewed", "original_sha256": H("a"),
            "train_sha256": H("b"), "validation_sha256": H("c"),
            "test_sha256": H("d"), "train_records": 10,
            "validation_records": 2, "test_records": 2,
            "reviewer": "named reviewer", "decision": "approved",
        }

    def test_complete_manifest(self):
        self.assertTrue(validate_manifest(self.data))

    def test_pending_rejected(self):
        self.data["decision"] = "pending"
        with self.assertRaises(ValueError):
            validate_manifest(self.data)

    def test_missing_license_rejected(self):
        del self.data["license_url"]
        with self.assertRaises(ValueError):
            validate_manifest(self.data)

    def test_duplicate_split_hash_rejected(self):
        self.data["test_sha256"] = H("b")
        with self.assertRaises(ValueError):
            validate_manifest(self.data)

    def test_invalid_hash_rejected(self):
        self.data["original_sha256"] = "not a hash"
        with self.assertRaises(ValueError):
            validate_manifest(self.data)

    def test_zero_records_rejected(self):
        self.data["train_records"] = 0
        with self.assertRaises(ValueError):
            validate_manifest(self.data)


    def test_verified_files_and_cross_split_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            examples = {
                "train": [{"messages": [{"role": "user", "content": "alpha"}]}],
                "validation": [{"messages": [{"role": "user", "content": "beta"}]}],
                "test": [{"messages": [{"role": "user", "content": "gamma"}]}],
            }
            for split, records in examples.items():
                raw = "".join(json.dumps(record) + "\n" for record in records).encode()
                (root / (split + ".jsonl")).write_bytes(raw)
                self.data[split + "_sha256"] = hashlib.sha256(raw).hexdigest()
                self.data[split + "_records"] = len(records)
            self.assertTrue(verify_split_files(self.data, root))
            self.data["validation_sha256"] = self.data["train_sha256"]
            with self.assertRaises(ValueError):
                verify_split_files(self.data, root)
            self.data["validation_sha256"] = hashlib.sha256((root / "validation.jsonl").read_bytes()).hexdigest()
            raw = (root / "train.jsonl").read_bytes()
            (root / "test.jsonl").write_bytes(raw)
            self.data["test_sha256"] = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):
                verify_split_files(self.data, root)


    def test_metadata_disguised_dialogue_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = {
                "train": [{"id": "a", "messages": [{"role": "user", "content": "Hello   WORLD"}, {"role": "assistant", "content": "Hi"}]}],
                "validation": [{"id": "b", "messages": [{"role": "user", "content": "hello world"}, {"role": "assistant", "content": "Hi"}]}],
                "test": [{"id": "c", "messages": [{"role": "user", "content": "Different"}, {"role": "assistant", "content": "Other"}]}],
            }
            for split, examples in records.items():
                raw = "".join(json.dumps(item) + "\n" for item in examples).encode()
                (root / (split + ".jsonl")).write_bytes(raw)
                self.data[split + "_sha256"] = hashlib.sha256(raw).hexdigest()
                self.data[split + "_records"] = len(examples)
            with self.assertRaisesRegex(ValueError, "Repeated normalized dialogue"):
                verify_split_files(self.data, root)

    def test_missing_messages_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in ("train", "validation", "test"):
                raw = (json.dumps({"id": split}) + "\n").encode()
                (root / (split + ".jsonl")).write_bytes(raw)
                self.data[split + "_sha256"] = hashlib.sha256(raw).hexdigest()
                self.data[split + "_records"] = 1
            with self.assertRaisesRegex(ValueError, "lacks nonempty messages"):
                verify_split_files(self.data, root)


    def test_conversation_family_leakage_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = {
                "train": [{"source_conversation_id": "thread-42", "messages": [{"role": "user", "content": "First question"}]}],
                "validation": [{"source_conversation_id": "thread-42", "messages": [{"role": "user", "content": "Different turn"}]}],
                "test": [{"source_conversation_id": "thread-99", "messages": [{"role": "user", "content": "Independent question"}]}],
            }
            for split, examples in records.items():
                raw = "".join(json.dumps(item) + "\\n" for item in examples).encode()
                (root / (split + ".jsonl")).write_bytes(raw)
                self.data[split + "_sha256"] = hashlib.sha256(raw).hexdigest()
                self.data[split + "_records"] = len(examples)
            with self.assertRaisesRegex(ValueError, "family leakage"):
                verify_split_files(self.data, root)

if __name__ == "__main__":
    unittest.main()
