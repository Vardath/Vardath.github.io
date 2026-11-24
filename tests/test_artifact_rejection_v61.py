import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.workflow_recovery import recovery_snapshot,verify_recovery
from deepthort_local.artifact_rejection import rejection,preserve
from tests.test_tool_workflows_v61 import Recipes
from tests.test_artifact_acceptance_v61 import png

class RejectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.j=JanusStore(self.root/'janus.sqlite');self.w=ToolWorkflows(self.j)
        recipes=Recipes(self.root);original=recipes._recipe_row
        recipes._recipe_row=lambda ident,root:{**original(ident,root),'artifact':'image.png'}
        m=freeze(recipes,self.root,[{'recipe_id':1,'input':''}],continuation=True)
        m['mixed_task']={'output':'image.png','acceptance':{'width':8}}
        self.ident=self.w.approve(m,user_approved=True)
        self.w.tick();a=self.j.claim_next_action()
        self.source=self.root/'image.png';self.source.write_bytes(png(4,8))
        log=self.root/'run.log';log.write_text('ok')
        self.j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
        self.assertIn('acceptance failed',self.w.tick())
    def test_preserve_and_recovery_remains_valid_after_replacement(self):
        original=self.source.read_bytes()
        plan=rejection(self.w,self.ident)
        with self.assertRaises(ValueError):recovery_snapshot(self.w,self.ident)
        with self.assertRaises(PermissionError):preserve(self.w,plan)
        archive=preserve(self.w,plan,user_approved=True)
        self.assertFalse(self.source.exists())
        self.assertEqual(archive.read_bytes(),original)
        snap=recovery_snapshot(self.w,self.ident)
        self.assertTrue(snap['failure']['rejected_artifact']['archived'])
        self.source.write_bytes(png(8,8))
        self.assertTrue(verify_recovery(self.w,snap,str(self.root)))
        archive.write_bytes(png(3,3))
        with self.assertRaises(ValueError):verify_recovery(self.w,snap,str(self.root))
    def test_changed_or_colliding_file_blocks_preservation(self):
        plan=rejection(self.w,self.ident)
        dest=self.root/plan['archive'];dest.write_bytes(b'existing')
        with self.assertRaises(ValueError):preserve(self.w,plan,user_approved=True)
        self.assertEqual(dest.read_bytes(),b'existing')
        dest.unlink()
        self.source.write_bytes(png(5,8))
        with self.assertRaises(ValueError):preserve(self.w,plan,user_approved=True)
        self.assertTrue(self.source.exists())
    def test_interrupted_link_move_can_resume_only_after_review(self):
        import os
        plan=rejection(self.w,self.ident)
        row=self.w.stages(self.ident)[0];rec=json.loads(row['receipt'])
        rec['archive_intent']=plan['archive']
        with self.j.connect() as db:
            db.execute('UPDATE tool_workflow_stages SET receipt=? WHERE workflow_id=?',(json.dumps(rec),self.ident))
        os.link(self.source,self.root/plan['archive'])
        self.assertEqual(rejection(self.w,self.ident),plan)
        preserve(self.w,plan,user_approved=True)
        self.assertFalse(self.source.exists())
        self.assertTrue(rejection(self.w,self.ident)['archived'])
if __name__=='__main__':unittest.main()
