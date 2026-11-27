import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.interface_learning import analyze,review,execute
from deepthort_local.api_contract import contract
S={'title':'Example','version':'1','endpoints':[{'path':'/items/{id}','method':'post','id':'save_item','summary':'Save item',
    'request':[{'name':'label','type':'string','required':True}],'response':[{'name':'ok','type':'boolean','required':True}],'status':201}]}
def raw():return json.dumps(contract(S)).encode()
class InterfaceTests(unittest.TestCase):
    def test_contract_roundtrip_and_source_pointers(self):
        r=analyze(raw());op=r['operations'][0]
        self.assertEqual(op['pointer'],'/paths/~1items~1{id}/post')
        self.assertEqual(op['parameters'],[{'in':'path','name':'id','required':True}])
        self.assertEqual(op['request']['json']['fields'],[{'name':'label','required':True,'type':'string'}])
        self.assertEqual(op['responses'][0]['status'],'201')
    def test_unresolved_refs_not_followed(self):
        d=contract(S);op=d['paths']['/items/{id}']['post']
        op['parameters'].append({'$ref':'https://example.invalid/param.json'})
        op['responses']['201']={'$ref':'https://example.invalid/response.json'}
        r=analyze(json.dumps(d).encode())['operations'][0]
        self.assertEqual(r['unresolved_parameter_refs'],1)
        self.assertFalse(r['responses'][0]['json']['supported'])
    def test_guarded_learning(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);doc=root/'openapi.json';doc.write_bytes(raw())
            (root/'spec.json').write_text(json.dumps({'document':'openapi.json'}),encoding='utf-8')
            plan,_=review(root,'spec.json','learned.json')
            self.assertFalse(execute(root,plan)['runtime_verified'])
            self.assertEqual(json.loads((root/'learned.json').read_text()),analyze(raw()))
            plan,_=review(root,'spec.json','later.json');doc.write_bytes(raw()+b' ')
            with self.assertRaises(ValueError):execute(root,plan)
