import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze,artifact
from deepthort_local.action_guards import verify_guards

class Recipes:
    def __init__(self,root):
        self.root=root
        self.exe=root/'app.exe';self.exe.write_bytes(b'tool')
    def _recipe_row(self,ident,project):
        return {'id':ident,'title':str(ident),'name':'fixture','artifact':f'out{ident}.json',
                'args_json':json.dumps(['{{output}}'] if ident==1 else ['{{input}}','{{output}}']),
                'script_path':''}
    def _build_recipe_command(self,row,rel,*,allow_future_input=False):
        return [str(self.exe),*([str(self.root/rel)] if rel else []),str(self.root/row['artifact'])]

class WorkflowTests(unittest.TestCase):
    def test_chain_restart_and_hash_guard(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);j=JanusStore(root/'janus.sqlite');w=ToolWorkflows(j)
            manifest=freeze(Recipes(root),root,[{'recipe_id':1,'input':''},{'recipe_id':2,'input':'out1.json'}])
            ident=w.approve(manifest,user_approved=True)
            self.assertIn('queued',w.tick())
            a=j.claim_next_action()
            verify_guards(json.loads(a['input_guards_json']))
            (root/'out1.json').write_text('{"x":1}')
            log=root/'log.txt';log.write_text('ok')
            j.update_action(a['id'],'succeeded',detail='fixture',returncode=0,output_file=str(log))
            w=ToolWorkflows(j)
            self.assertIn('checked',w.tick())
            self.assertIn('queued',w.tick())
            second=j.claim_next_action()
            verify_guards(json.loads(second['input_guards_json']))
            (root/'out1.json').write_text('{"x":2}')
            with self.assertRaises(ValueError):verify_guards(json.loads(second['input_guards_json']))
            self.assertEqual(len(j.actions()),2)
            w.stop(ident)
            self.assertEqual(w.list()[0]['state'],'cancelled')
    def test_bad_output_and_approval(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);j=JanusStore(root/'janus.sqlite');w=ToolWorkflows(j)
            manifest=freeze(Recipes(root),root,[{'recipe_id':1,'input':''},{'recipe_id':2,'input':'out1.json'}])
            with self.assertRaises(PermissionError):w.approve(manifest)
            w.approve(manifest,user_approved=True);w.tick()
            a=j.claim_next_action()
            (root/'out1.json').write_text('{"x":1,"x":2}')
            log=root/'log.txt';log.write_text('ok')
            j.update_action(a['id'],'succeeded',detail='fixture',returncode=0,output_file=str(log))
            self.assertIn('blocked',w.tick())
            self.assertEqual(len(j.actions()),1)
if __name__=='__main__':unittest.main()
