import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from deepthort_local.flight_recorder import scrub,export_diagnostics
from deepthort_local.secret_redaction import jsonl,tail

class RedactionTests(unittest.TestCase):
    def test_structured_and_text(self):
        values=['fake_password_123','fake_cookie_456','ghp_fixture1234567890','fake_basic_123456','private_fixture_123','url_password_123']
        raw='{"password":"'+values[0]+'"}\nCookie: session='+values[1]+'\n'+values[2]+'\nAuthorization: Basic '+values[3]+'\n-----BEGIN PRIVATE KEY-----\n'+values[4]+'\n-----END PRIVATE KEY-----\nhttps://name:'+values[5]+'@example.test/'
        result=scrub(raw)
        for v in values:self.assertNotIn(v,result)
        self.assertEqual(scrub({'generated_tokens':12,'generated_tokens_per_second':2.5,'token_count':'fake_token_123','authorization':'fake_auth_123'}),{'generated_tokens':12,'generated_tokens_per_second':2.5,'token_count':'[REDACTED]','authorization':'[REDACTED]'})
    def test_legacy_jsonl_and_malformed(self):
        raw=b'{"event":"old","data":{"api_key":"legacy_fixture_123","input_tokens":4}}\ninvalid raw legacy_fixture_456\n'
        rows=[json.loads(x) for x in jsonl(raw).splitlines()]
        self.assertEqual(rows[0]['data']['input_tokens'],4)
        self.assertEqual(rows[1]['event'],'diagnostic_row_omitted')
        self.assertNotIn(b'legacy_fixture',jsonl(raw))
    def test_archive_legacy_and_partial_tail(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);logs=root/'state'/'logs';logs.mkdir(parents=True)
            (logs/'old.jsonl').write_bytes(b'{"event":"old","data":{"private_token":"legacy_fixture_123"}}\nmalformed legacy_fixture_456\n')
            (logs/'triad-fixture.log').write_bytes(b'x'*9000+b'partial_fixture_123\nnormal diagnostic\n')
            self.assertNotIn('partial_fixture',tail(logs/'triad-fixture.log',8192))
            out=export_diagnostics(root/'state',root/'diagnostics.zip')
            with zipfile.ZipFile(out) as z:
                self.assertIn('logs/old.jsonl',z.namelist())
                self.assertIn(b'normal diagnostic',z.read('native-log-tails/triad-fixture.log.txt'))
                for name in z.namelist():
                    data=z.read(name)
                    self.assertNotIn(b'legacy_fixture',data)
                    self.assertNotIn(b'partial_fixture',data)
