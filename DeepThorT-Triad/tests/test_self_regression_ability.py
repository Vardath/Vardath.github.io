import json,tempfile,unittest
from pathlib import Path
from deepthort_local import self_investigation as investigation
from deepthort_local import self_regression as m

BASE="def _cross_allowed(row):\n    return row['mode']=='draft_plan' and row['project']!='(general)'\n"
FIX="def _cross_allowed(row):\n    return bool(row.get('project')) and row.get('mode')=='draft_plan' and row.get('project')!='(general)'"

class RegressionTests(unittest.TestCase):
    def test_fixed_oracle_and_unsupported(self):
        self.assertFalse(all(x['passed'] for x in m.outcomes(BASE)))
        self.assertTrue(all(x['passed'] for x in m.outcomes(FIX)))
        for bad in ("def _cross_allowed(row):\n    return __import__('os')","def _cross_allowed(row):\n    return False and row.clear()"):
            with self.assertRaises(ValueError):m.outcomes(bad)
    def test_actual_investigation_advances_without_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();state=root/'state';(state/'logs').mkdir(parents=True)
            target=root/m.TARGET;target.parent.mkdir();target.write_text(BASE,encoding='utf8')
            row={'component':'desktop','event':'memory_conversation_failed','data':{'error_type':'KeyError'}}
            (state/'logs'/'desktop.jsonl').write_text((json.dumps(row)+'\n')*3,encoding='utf8')
            class Client:
                def chat_as(self,role,session,prompt,max_tokens):
                    if role=='janus':return json.dumps({'action':'investigate','function':m.FUNCTION,'reason':'Missing project key','test':'Malformed rows fail closed'})
                    if role=='implementation':return json.dumps({'function_source':FIX})
                    import re
                    key=re.search(r'"candidate_sha": "([0-9a-f]{64})"',prompt).group(1)
                    return json.dumps({'accepted':True,'candidate_sha':key,'reason':'Review exact candidate'})
            client=Client()
            for _ in range(3):body=investigation.run_once(root,state,client,lambda:False)
            self.assertEqual(body['state'],'investigation_staged')
            result=investigation.run_once(root,state,client,lambda:False)
            self.assertEqual(result['state'],'investigation_regression_checked')
            self.assertEqual(result['regression']['status'],'passed')
            self.assertFalse(result['regression']['installation_authorized'])
            self.assertEqual(target.read_text('utf8'),BASE)
            self.assertIsNone(investigation.run_once(root,state,client,lambda:False))
    def test_never_claim_python_runtime(self):
        self.assertFalse(all(x['passed'] for x in m.outcomes("def _cross_allowed(row):\n    return True")))
if __name__=='__main__':unittest.main()
