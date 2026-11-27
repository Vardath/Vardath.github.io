import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.api_contract import contract,review,execute
S={'title':'Project API','version':'1.0','endpoints':[
    {'path':'/items/{item_id}','method':'get','id':'get_item','summary':'Read item','request':[],
     'response':[{'name':'name','type':'string','required':True}],'status':200},
    {'path':'/items','method':'post','id':'create_item','summary':'Create item',
     'request':[{'name':'name','type':'string','required':True}],'response':[],'status':201}]}
class ContractTests(unittest.TestCase):
    def test_routes_parameters_and_schemas(self):
        result=contract(S);self.assertEqual(result['openapi'],'3.1.0')
        get=result['paths']['/items/{item_id}']['get']
        self.assertEqual(get['parameters'][0]['name'],'item_id')
        self.assertEqual(get['responses']['200']['content']['application/json']['schema']['required'],['name'])
        self.assertTrue(result['paths']['/items']['post']['requestBody']['required'])
    def test_ambiguous_routes_and_invalid_body(self):
        s=copy.deepcopy(S);s['endpoints'][1]['path']='/items/{other}'
        with self.assertRaises(ValueError):contract(s)
        s=copy.deepcopy(S);s['endpoints'][0]['status']=204
        with self.assertRaises(ValueError):contract(s)
        s=copy.deepcopy(S);s['endpoints'][0]['request']=S['endpoints'][1]['request']
        with self.assertRaises(ValueError):contract(s)
    def test_approved_export(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
            plan,_=review(root,'spec.json','openapi.json')
            r=execute(root,plan);self.assertFalse(r['server_started'])
            self.assertEqual(json.loads((root/'openapi.json').read_text()),contract(S))
            plan,_=review(root,'spec.json','later.json')
            (root/'spec.json').write_text(json.dumps(dict(S,title='changed')),encoding='utf-8')
            with self.assertRaises(ValueError):execute(root,plan)
