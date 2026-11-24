import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.asset_import_probe import AssetProbes,plan
from tests.test_tool_workflows_v61 import Recipes
from tests.test_artifact_acceptance_v61 import png

class AssetProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.j=JanusStore(self.root/'janus.sqlite')
        self.w=ToolWorkflows(self.j)
        r=Recipes(self.root);original=r._recipe_row
        r._recipe_row=lambda ident,root:{**original(ident,root),'artifact':'image.png'}
        self.ident=self.w.approve(freeze(r,self.root,[{'recipe_id':1,'input':''}],continuation=True),user_approved=True)
        self.w.tick();a=self.j.claim_next_action()
        self.image=self.root/'image.png';self.image.write_bytes(png(4,8))
        log=self.root/'producer.log';log.write_text('ok')
        self.j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
        self.w.tick();self.w.tick()
        self.acq=Mock();self.acq.tool.return_value={'executable':str(r.exe)}
        self.store=AssetProbes(self.w)
    def queue(self,tool='Blender'):
        p=plan(self.w,self.acq,self.ident,1,tool)
        ident=self.store.queue(p,self.acq,user_approved=True)
        self.assertEqual(self.j.claim_next_action()['id'],ident)
        return ident,p
    def finish(self,ident,content):
        log=self.root/'probe.log';log.write_text(content)
        self.j.update_action(ident,'succeeded',detail='ok',returncode=0,output_file=str(log))
    def test_fixed_blender_command_and_receipt(self):
        ident,p=self.queue()
        self.assertIn('--disable-autoexec',p['argv'])
        self.finish(ident,'DEEPTHORT_ASSET_PROBE {"kind":"image","width":4,"height":8}\n')
        self.assertTrue(self.store.result(ident)['import_verified'])
        self.image.write_bytes(png(8,4))
        with self.assertRaises(ValueError):self.store.result(ident)
    def test_godot_command_and_missing_or_invalid_result(self):
        ident,p=self.queue('Godot')
        self.assertIn('--headless',p['argv'])
        self.assertIn('--script',p['argv'])
        self.finish(ident,'normal exit')
        with self.assertRaises(ValueError):self.store.result(ident)
        self.finish(ident,'SCRIPT ERROR: bad\nDEEPTHORT_ASSET_PROBE {"kind":"image","width":4,"height":8}')
        with self.assertRaises(ValueError):self.store.result(ident)
    def test_no_unapproved_execution_or_changed_input(self):
        p=plan(self.w,self.acq,self.ident,1,'Blender')
        with self.assertRaises(PermissionError):self.store.queue(p,self.acq)
        self.image.write_bytes(png(8,4))
        with self.assertRaises(ValueError):self.store.queue(p,self.acq,user_approved=True)
    def test_unknown_tool_and_tampered_action_cancelled(self):
        with self.assertRaises(ValueError):plan(self.w,self.acq,self.ident,1,'unknown')
        p=plan(self.w,self.acq,self.ident,1,'Godot')
        ident=self.store.queue(p,self.acq,user_approved=True)
        with self.j.connect() as db:
            db.execute('UPDATE janus_actions SET argv_json=? WHERE id=?',(json.dumps(['changed']),ident))
        self.assertIsNone(self.j.claim_next_action())
        self.assertEqual(self.j.action(ident)['status'],'cancelled')
if __name__=='__main__':unittest.main()
