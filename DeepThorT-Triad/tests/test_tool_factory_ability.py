import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from deepthort_local import tool_factory as f
S={'name':'normalise','fields':[{'source':'label','target':'name','operation':'trim'},{'source':'count','target':'total','operation':'copy'}],'fixtures':[{'input':{'label':' A ','count':3},'expected':{'name':'A','total':3}}]}
class FactoryTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);self.root=Path(td.name)
        (self.root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
    def test_actual_generated_tool(self):
        plan,_=f.review(self.root,'spec.json','tool.py')
        r=f.execute(self.root,plan);self.assertFalse(r['executed']);self.assertFalse(r['registered'])
        for raw in (b'{"label":" B ","count":9}',b'{"label":"C","count":false}'):
            out=subprocess.run([sys.executable,'-I',str(self.root/'tool.py')],input=raw,capture_output=True,timeout=10)
            self.assertEqual(out.returncode,0);self.assertEqual(json.loads(out.stdout),f.reference(S['fields'],json.loads(raw)))
        for raw in (b'{"label":"a","label":"b","count":1}',b'{"label":"a","count":NaN}',b'{"label":2,"count":1}',b'{}'):
            out=subprocess.run([sys.executable,'-I',str(self.root/'tool.py')],input=raw,capture_output=True,timeout=10)
            self.assertEqual(out.returncode,2);self.assertEqual(out.stdout,b'')
    def test_refuse_bad_contract_and_fixtures(self):
        for changes in ({'name':'bad;command'},{'fixtures':[{'input':{'label':' A ','count':3},'expected':{'name':'wrong','total':3}}]}, {'fields':[dict(S['fields'][0],operation='exec')]}):
            with self.assertRaises(ValueError):f.checked(dict(S,**changes))
    def test_stale_review_and_no_overwrite(self):
        plan,_=f.review(self.root,'spec.json','tool.py')
        (self.root/'spec.json').write_text(json.dumps(dict(S,name='changed')),encoding='utf-8')
        with self.assertRaises(ValueError):f.execute(self.root,plan)
        self.assertFalse((self.root/'tool.py').exists())
        plan,_=f.review(self.root,'spec.json','tool.py')
        (self.root/'tool.py').write_text('existing',encoding='utf-8')
        with self.assertRaises(ValueError):f.execute(self.root,plan)
        self.assertEqual((self.root/'tool.py').read_text(),'existing')
