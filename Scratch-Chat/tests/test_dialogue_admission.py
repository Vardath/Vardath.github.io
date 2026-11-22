"""Admission gate regression tests: no external datasets downloaded."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from capability.dialogue_admission import audit

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.paths = {}
        digests = {}
        for split in ("train", "validation", "test"):
            path = root / (split + ".jsonl")
            row = {"id": split, "source_id": "authored-fixture", "license": "CC0-1.0",
                   "messages": [{"role": "user", "content": "Question " + split},
                                {"role": "assistant", "content": "Answer " + split}]}
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.paths[split] = path
            digests[split] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest = root / "manifest.json"
        self.metadata = {"source_id": "authored-fixture", "source_url": "https://example.org/fixture",
                         "revision": "fixture-v1", "license": "CC0-1.0",
                         "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                         "approval": "approved", "approved_by": "fixture",
                         "retrieved_utc": "2026-11-21T00:00:00Z", "sha256": digests}
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.metadata), encoding="utf-8")

    def run_audit(self):
        return audit(self.manifest, self.paths["train"], self.paths["validation"], self.paths["test"])

    def test_valid_fixture(self):
        self.assertEqual(self.run_audit()["splits"]["test"]["count"], 1)

    def test_unapproved_source_rejected(self):
        self.metadata["approval"] = "pending"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "not explicitly approved"):
            self.run_audit()

    def test_modified_split_rejected(self):
        with self.paths["test"].open("a") as f:
            f.write("tampering\n")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.run_audit()

    def test_cross_split_duplicate_rejected_even_with_matching_digest(self):
        train = json.loads(self.paths["train"].read_text())
        test = json.loads(self.paths["test"].read_text())
        test["messages"] = train["messages"]
        self.paths["test"].write_text(json.dumps(test) + "\n")
        self.metadata["sha256"]["test"] = hashlib.sha256(self.paths["test"].read_bytes()).hexdigest()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate dialogue"):
            self.run_audit()


    def test_cross_split_lexical_near_duplicate_rejected(self):
        train = json.loads(self.paths["train"].read_text())
        test = json.loads(self.paths["test"].read_text())
        train["messages"] = [
            {"role": "user", "content": "Explain how the station manager allocates food and water supplies to the arriving crews today."},
            {"role": "assistant", "content": "The station manager tracks each crew and assigns food and water according to their requirements."}]
        test["messages"] = [
            {"role": "user", "content": "Explain how the station manager allocates food and water supplies to arriving crews today."},
            {"role": "assistant", "content": "The station manager tracks each crew and assigns food and water according to their requirements."}]
        for split, row in (("train", train), ("test", test)):
            self.paths[split].write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.metadata["sha256"][split] = hashlib.sha256(self.paths[split].read_bytes()).hexdigest()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "near-duplicate dialogue"):
            self.run_audit()

    def test_short_common_phrases_not_falsely_rejected(self):
        train = json.loads(self.paths["train"].read_text())
        test = json.loads(self.paths["test"].read_text())
        train["messages"] = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        test["messages"] = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Goodbye"}]
        for split, row in (("train", train), ("test", test)):
            self.paths[split].write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.metadata["sha256"][split] = hashlib.sha256(self.paths[split].read_bytes()).hexdigest()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "duplicate user prompt"):
            self.run_audit()

    def rewrite_row(self, split, transform):
        row = json.loads(self.paths[split].read_text())
        transform(row)
        self.paths[split].write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.metadata["sha256"][split] = hashlib.sha256(self.paths[split].read_bytes()).hexdigest()
        self.write_manifest()

    def test_same_user_prompt_different_answer_rejected(self):
        self.rewrite_row("test", lambda row: row["messages"].__setitem__(0, {"role": "user", "content": "Question train"}))
        with self.assertRaisesRegex(ValueError, "duplicate user prompt"):
            self.run_audit()

    def test_shared_upstream_family_rejected(self):
        self.rewrite_row("train", lambda row: row.update({"template_family_id": "family-42"}))
        self.rewrite_row("test", lambda row: row.update({"template_family_id": "family-42"}))
        with self.assertRaisesRegex(ValueError, "template_family_id leaks"):
            self.run_audit()

    def test_distinct_families_pass(self):
        self.rewrite_row("train", lambda row: row.update({"source_conversation_id": "a"}))
        self.rewrite_row("test", lambda row: row.update({"source_conversation_id": "b"}))
        self.assertEqual(self.run_audit()["splits"]["test"]["count"], 1)

if __name__ == "__main__":
    unittest.main()
