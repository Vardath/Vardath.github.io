import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.self_investigation import observations,run_once,memory_once,EVENTS

class InvestigationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.state=self.root/'state';(self.state/'logs').mkdir(parents=True)
        self.event='technical_preparation_deferred'
        self.target=self.root/EVENTS[self.event];self.target.parent.mkdir()
        self.source='def parse(value):\n    return value["name"]\n'
        self.target.write_text(self.source,encoding='utf-8')
        self.log=self.state/'logs'/'desktop.jsonl'
        self.log.write_text(('{"component":"desktop","event":"technical_preparation_deferred","data":{"error_type":"KeyError","secret":"not used"}}\n')*3,encoding='utf-8')
        self.calls=[]
        owner=self
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                owner.calls.append(role)
                if role=='janus':return json.dumps({'action':'investigate','function':'parse','reason':'Missing name hypothesis','test':'Exercise missing name'})
                if role=='implementation':return json.dumps({'function_source':'def parse(value):\n    return value.get("name")'})
                import re
                match=re.search(r'"candidate_sha": "([0-9a-f]{64})"',prompt)
                return json.dumps({'accepted':True,'candidate_sha':match.group(1),'reason':'Suitable isolated test candidate'})
        self.client=Client()
    def tick(self):return run_once(self.root,self.state,self.client,lambda:False)
    def test_inert_real_evidence_and_restart(self):
        case=observations(self.root,self.state)[0]
        self.assertEqual(case['count'],3);self.assertNotIn('secret',json.dumps(case))
        self.assertEqual(self.tick()['state'],'investigation_planned')
        self.assertEqual(self.tick()['state'],'investigation_candidate')
        body=self.tick();self.assertEqual(body['state'],'investigation_staged')
        folder=self.state/'self-development'/case['key']
        self.assertEqual(self.target.read_text('utf-8'),self.source)
        self.assertIn('value.get',(folder/'candidate.py.txt').read_text('utf-8'))
        manifest=json.loads((folder/'manifest.json').read_text('utf-8'))
        self.assertFalse(manifest['runtime_verified']);self.assertFalse(manifest['installation_authorized'])
        self.assertIsNone(self.tick())
        self.target.write_text(self.source+'\n# next version\n',encoding='utf-8')
        def select(key,prompt,tokens):return json.dumps({'keep':[case['key']],'reason':'Same historical fault'})
        result=memory_once(self.root,self.state,select)
        self.assertEqual(result['selected'][0]['id'],case['key'])
        self.assertEqual(self.tick()['state'],'investigation_planned')
    def test_invalid_function_and_cancel(self):
        self.tick()
        from unittest.mock import patch
        with patch.object(self.client,'chat_as',return_value=json.dumps({'function_source':'def parse(value, extra):\n    return 1'})):
            with self.assertRaises(ValueError):self.tick()
        self.assertIsNone(run_once(self.root,self.state,self.client,lambda:True))
        self.assertFalse((self.state/'self-development').exists())
if __name__=='__main__':unittest.main()
