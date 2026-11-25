import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.workflow_recovery import recovery_snapshot,verify_recovery
from deepthort_local.workflow_design import parse_draft
from tests.test_tool_workflows_v61 import Recipes


class RecoveryTests(unittest.TestCase):
    def test_checked_prefix_reused_without_replaying_and_partial_not_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);j=JanusStore(root/'janus.sqlite');w=ToolWorkflows(j);r=Recipes(root)
            parent=w.approve(freeze(r,root,[{'recipe_id':1,'input':''},{'recipe_id':2,'input':'out1.json'}]),user_approved=True)
            w.tick();a=j.claim_next_action()
            (root/'out1.json').write_text('{"x":1}')
            log=root/'first.log';log.write_text('ok')
            j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
            self.assertIn('checked',w.tick());w.tick();b=j.claim_next_action()
            (root/'out2.json').write_text('partial')
            log2=root/'second.log';log2.write_text('failed conversion')
            j.update_action(b['id'],'failed',detail='conversion failed',returncode=1,output_file=str(log2))
            self.assertIn('blocked',w.tick())
            snap=recovery_snapshot(w,parent)
            self.assertEqual(snap['prefix'][0]['output'],'out1.json')
            self.assertTrue(snap['failure']['partial_output_present'])
            self.assertIn('failed conversion',snap['failure']['log_tail'])
            with self.assertRaises(ValueError):
                freeze(r,root,[{'recipe_id':2,'input':'out1.json'}],continuation=True)
            continuation=freeze(r,root,[{'recipe_id':3,'input':'out1.json'}],continuation=True)
            continuation['recovery']=snap
            w.approve(continuation,user_approved=True)
            with self.assertRaises(ValueError):w.approve(continuation,user_approved=True)
            w=ToolWorkflows(j)
            self.assertIn('queued',w.tick())
            c=j.claim_next_action()
            self.assertEqual(json.loads(c['argv_json'])[-1],str(root/'out3.json'))
            self.assertEqual((root/'out2.json').read_text(),'partial')
            self.assertEqual(len(j.actions()),3)
            (root/'out1.json').write_text('{"x":2}')
            with self.assertRaises(ValueError):verify_recovery(w,snap,str(root))

    def test_single_stage_allowed_only_for_continuation(self):
        recipes=[{'recipe_id':1,'input_required':True,'output':'new.json'}]
        answer=json.dumps({'stages':[{'recipe_id':1,'input':'checked.json'}],'missing':[]})
        with self.assertRaises(ValueError):parse_draft(answer,recipes,['checked.json'])
        self.assertEqual(len(parse_draft(answer,recipes,['checked.json'],continuation=True)['stages']),1)

if __name__=='__main__':unittest.main()
