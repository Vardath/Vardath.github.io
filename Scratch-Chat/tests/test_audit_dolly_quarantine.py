import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from capability.audit_dolly_quarantine import audit

class QuarantineAuditTests(unittest.TestCase):
    def make_source(self, root):
        root = Path(root)
        raw = b'{"instruction":"example"}\n'
        record = {"id":"dolly:1","license":"PENDING-REVIEW","messages":[
            {"role":"user","content":"Write to example@example.com"},
            {"role":"assistant","content":"Use https://example.org"}]}
        converted = (json.dumps(record) + "\n").encode()
        (root/"upstream.jsonl").write_bytes(raw)
        (root/"quarantined.jsonl").write_bytes(converted)
        manifest = {"status":"QUARANTINED_NOT_APPROVED","training_allowed":False,
                    "upstream_commit":"a"*40,"raw_sha256":hashlib.sha256(raw).hexdigest(),
                    "converted":{"output_sha256":hashlib.sha256(converted).hexdigest(),"records":1}}
        (root/"acquisition.json").write_text(json.dumps(manifest))
        return manifest

    def test_real_content_flagging_is_not_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_source(tmp)
            result = audit(tmp)
            self.assertFalse(result["training_allowed"])
            self.assertEqual(result["counts"]["records"],1)
            self.assertEqual(result["counts"]["flag_email"],1)
            self.assertEqual(result["counts"]["flag_url"],1)
            self.assertEqual(len(result["flagged_records"]),1)
            self.assertNotIn("example@example.com",json.dumps(result))

    def test_tampering_or_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.make_source(tmp)
            (Path(tmp)/"upstream.jsonl").write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                audit(tmp)
            (Path(tmp)/"upstream.jsonl").write_bytes(b'{"instruction":"example"}\n')
            manifest["training_allowed"]=True
            (Path(tmp)/"acquisition.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                audit(tmp)

    def test_invalid_role_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=self.make_source(tmp)
            row=json.loads((Path(tmp)/"quarantined.jsonl").read_text())
            row["messages"][1]["role"]="system"
            data=(json.dumps(row)+"\n").encode()
            (Path(tmp)/"quarantined.jsonl").write_bytes(data)
            manifest["converted"]["output_sha256"]=hashlib.sha256(data).hexdigest()
            (Path(tmp)/"acquisition.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                audit(tmp)

if __name__=="__main__":
    unittest.main()
