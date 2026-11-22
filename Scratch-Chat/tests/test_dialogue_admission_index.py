"""Regression tests for exact indexed candidate retrieval in admission."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability import dialogue_admission


class IndexedAdmissionTests(unittest.TestCase):
    def test_disjoint_vocabulary_passes_and_cross_split_overlap_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def record(identifier, phrase):
                return {"id": identifier, "source_id": "fixture", "license": "CC0-1.0",
                        "messages": [{"role": "user", "content": phrase},
                                     {"role": "assistant", "content": phrase}]}
            import hashlib
            train = record("a", "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu")
            valid = record("b", "one two three four five six seven eight nine ten eleven twelve")
            test = record("c", "red blue green orange purple yellow silver gold black white gray pink")
            paths = {}
            for split, row in (("train", train), ("validation", valid), ("test", test)):
                p = root / (split + ".jsonl")
                p.write_text(json.dumps(row) + "\n", encoding="utf-8")
                paths[split] = p
            manifest = {"source_id": "fixture", "source_url": "https://example.org/fixture",
                        "revision": "immutable-fixture", "license": "CC0-1.0",
                        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "approval": "approved", "approved_by": "fixture",
                        "retrieved_utc": "2026-11-22T00:00:00Z",
                        "sha256": {k: hashlib.sha256(v.read_bytes()).hexdigest() for k,v in paths.items()}}
            mp = root / "manifest.json"
            mp.write_text(json.dumps(manifest))
            args = (mp, paths["train"], paths["validation"], paths["test"])
            self.assertEqual(dialogue_admission.audit(*args)["splits"]["test"]["count"], 1)
            test["messages"][0]["content"] = train["messages"][0]["content"] + " novel"
            test["messages"][1]["content"] = train["messages"][1]["content"] + " variation"
            paths["test"].write_text(json.dumps(test) + "\n")
            manifest["sha256"]["test"] = hashlib.sha256(paths["test"].read_bytes()).hexdigest()
            mp.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "near-duplicate"):
                dialogue_admission.audit(*args)


if __name__ == "__main__":
    unittest.main()
