import unittest
from capability.dialogue_source_manifest import validate_manifest

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


if __name__ == "__main__":
    unittest.main()
