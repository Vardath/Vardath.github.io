"""Actual isolated diagnostic behavior and rollback; no native model inference."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from deepthort_local.self_development import observe,run_once,TARGET,CAP_SOURCE
from deepthort_local.self_update_preparation import prepare

class SelfUpdateTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.state=self.root/'state';self.state.mkdir()
        (self.root/'deepthort_local').mkdir()
        source=Path(__file__).resolve().parents[1]/TARGET
        self.baseline=source.read_bytes().replace(
            b'System resource protection: automatic Medium 50% / High 85% CPU hard cap, up to 80% RAM-sized root commit; Medium uses a 65% cooperative admission budget, not forced eviction.',
            b'System resource protection: 35% CPU hard cap and 35% committed-memory job limit are configured by the launcher.')
        self.assertNotEqual(self.baseline,source.read_bytes())
        (self.root/TARGET).write_bytes(self.baseline)
        (self.root/CAP_SOURCE).write_text('MAX_CPU_PERCENT = 50\nMAX_RAM_PERCENT = 65\n',encoding='utf-8')
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                if role=='janus':return json.dumps({'action':'repair','reason':'Stale caps','test':'Compare diagnostic output'})
                if role=='implementation':return json.dumps({'replacement':'System resource protection: 50% CPU maximum and up to 65% RAM-sized commit.'})
                import re
                match=re.search(r'"candidate_sha": "([0-9a-f]{64})"',prompt)
                return json.dumps({'accepted':True,'reason':'Correct configured limits','candidate_sha':match.group(1)})
        self.client=Client()
    def stage(self):
        for _ in range(3):body=run_once(self.root,self.state,self.client,lambda:False)
        self.assertEqual(body['state'],'staged')
        return body
    def test_isolated_probe_package_and_rollback(self):
        body=self.stage()
        result=run_once(self.root,self.state,self.client,lambda:False,update_python=sys.executable)
        self.assertEqual(result['state'],'update_prepared')
        manifest=result['update']['manifest']
        self.assertEqual(manifest['runtime_probe']['cases_passed'],8)
        self.assertTrue(manifest['rollback_bytes_verified'])
        self.assertFalse(manifest['full_application_verified'])
        self.assertFalse(manifest['installation_authorized'])
        folder=self.state/'self-development'/body['key']
        self.assertTrue((folder/result['update']['package']).is_file())
        self.assertEqual((self.root/TARGET).read_bytes(),self.baseline)
        self.assertIsNone(run_once(self.root,self.state,self.client,lambda:False,update_python=sys.executable))
        self.assertEqual(prepare(self.root,self.state,body,lambda:False,python=sys.executable),result['update'])
    def test_tampering_and_cancellation(self):
        body=self.stage()
        self.assertIsNone(prepare(self.root,self.state,body,lambda:True,python=sys.executable))
        folder=self.state/'self-development'/body['key']
        (folder/'candidate.py.txt').write_text('print("tampered")',encoding='utf-8')
        with self.assertRaises(ValueError):prepare(self.root,self.state,body,lambda:False,python=sys.executable)
        self.assertFalse(list(folder.glob('*.zip')))
        self.assertEqual((self.root/TARGET).read_bytes(),self.baseline)
if __name__=='__main__':unittest.main()
