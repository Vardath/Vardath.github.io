"""Real source snapshots and static checks; scripted model replies."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.self_development import observe,run_once,TARGET,CAP_SOURCE

class SelfDevelopmentTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.state=self.root/'state';self.state.mkdir()
        (self.root/'deepthort_local').mkdir()
        self.source="def diagnostic():\n    return 'System resource protection: 35% CPU and 35% committed memory.'\n"
        (self.root/TARGET).write_text(self.source,encoding='utf-8')
        (self.root/CAP_SOURCE).write_text('MAX_CPU_PERCENT = 50\nMAX_RAM_PERCENT = 65\n',encoding='utf-8')
        self.calls=[]
        test=self
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                test.calls.append(role)
                if role=='janus':return json.dumps({'action':'repair','reason':'Stale values','test':'Check actual configured cap constants'})
                if role=='implementation':return json.dumps({'replacement':'System resource protection: 50% CPU maximum and up to 65% RAM-sized commit.'})
                import re
                match=re.search(r'"candidate_sha": "([0-9a-f]{64})"',prompt)
                return json.dumps({'accepted':True,'reason':'Wording matches configured maximum','candidate_sha':match.group(1)})
        self.client=Client()
    def tick(self):
        return run_once(self.root,self.state,self.client,lambda:False)
    def test_versioned_isolated_candidate_and_rollback_baseline(self):
        evidence=observe(self.root)
        self.assertEqual(self.tick()['state'],'planned')
        self.assertEqual(self.tick()['state'],'candidate')
        self.assertEqual(self.tick()['state'],'staged')
        self.assertEqual(self.calls,['janus','implementation','sentinel'])
        folder=self.state/'self-development'/evidence['key']
        manifest=json.loads((folder/'manifest.json').read_text('utf-8'))
        self.assertFalse(manifest['installation_authorized']);self.assertFalse(manifest['runtime_verified'])
        self.assertEqual((folder/'baseline.py.txt').read_bytes(),(self.root/TARGET).read_bytes())
        self.assertIn('up to 65%',(folder/'candidate.py.txt').read_text('utf-8'))
        self.assertEqual((self.root/TARGET).read_text('utf-8'),self.source)
        self.assertIsNone(self.tick())
    def test_stale_observation_and_unavailable_role(self):
        self.assertIsNone(run_once(self.root,self.state,self.client,lambda:False,available=lambda role:False))
        self.assertFalse(self.calls)
        self.tick()
        (self.root/CAP_SOURCE).write_text('MAX_CPU_PERCENT = 49\nMAX_RAM_PERCENT = 64\n',encoding='utf-8')
        self.assertEqual(self.tick()['state'],'planned')
        self.assertEqual(self.calls,['janus','janus'])
        self.assertFalse((self.state/'self-development').exists())
    def test_incorrect_candidate_never_stages(self):
        self.tick()
        from unittest.mock import patch
        with patch.object(self.client,'chat_as',return_value='{"replacement":"System resource protection: 35% CPU and up to 35% commit."}'):
            with self.assertRaises(ValueError):self.tick()
        self.assertFalse((self.state/'self-development').exists())
if __name__=='__main__':unittest.main()
