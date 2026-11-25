import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.asset_import_probe import AssetProbes,plan,required_imports
from deepthort_local.mixed_roadmap import parse_tasks,pending_task
from deepthort_local.roadmap_tool_bridge import gate
from tests.test_tool_workflows_v61 import Recipes
from tests.test_artifact_acceptance_v61 import png

class ImportGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.j=JanusStore(self.root/'janus.sqlite')
        self.w=ToolWorkflows(self.j)
        r=Recipes(self.root);original=r._recipe_row
        r._recipe_row=lambda ident,root:{**original(ident,root),'artifact':'image.png'}
        self.task={'after':0,'goal':'Create image usable in Godot and Blender','output':'image.png',
                   'imports':['Blender','Godot']}
        m=freeze(r,self.root,[{'recipe_id':1,'input':''}],continuation=True)
        m['mixed_task']=self.task
        m['roadmap']={'request_id':1,'manifest_sha256':'code','after':0,'project':str(self.root)}
        self.ident=self.w.approve(m,user_approved=True)
        self.w.tick(roadmap_ready=lambda link:True)
        a=self.j.claim_next_action()
        self.image=self.root/'image.png';self.image.write_bytes(png(4,8))
        log=self.root/'producer.log';log.write_text('ok')
        self.j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
        self.w.tick(roadmap_ready=lambda link:True);self.w.tick(roadmap_ready=lambda link:True)
        self.acq=Mock();self.acq.tool.return_value={'executable':str(r.exe)}
        self.store=AssetProbes(self.w)
        self.mixed={'request_id':1,'tasks':[self.task]}
    def finish(self,tool,content='DEEPTHORT_ASSET_PROBE {"kind":"image","width":4,"height":8}',status='succeeded'):
        p=plan(self.w,self.acq,self.ident,1,tool)
        ident=self.store.queue(p,self.acq,user_approved=True)
        self.assertEqual(self.j.claim_next_action()['id'],ident)
        log=self.root/f'probe-{ident}.log';log.write_text(content)
        self.j.update_action(ident,status,detail='fixture',returncode=0 if status=='succeeded' else 19,output_file=str(log))
        return ident
    def pending(self):
        return required_imports(self.w,self.w.get(self.ident))
    def test_both_imports_required_by_both_gates(self):
        self.assertEqual([p['tool'] for p in self.pending()],['Blender','Godot'])
        self.assertEqual(pending_task(self.mixed,self.w,1),self.task)
        self.assertIn('Blender',gate(self.w,1,'code',1))
        self.finish('Blender')
        self.assertEqual([p['tool'] for p in self.pending()],['Godot'])
        self.finish('Godot')
        self.assertEqual(self.pending(),[])
        self.assertIsNone(pending_task(self.mixed,self.w,1))
        self.assertIsNone(gate(self.w,1,'code',1))
    def test_failed_wrong_dimensions_and_stale_probe_do_not_pass(self):
        self.finish('Blender',status='failed')
        self.assertEqual(self.pending()[0]['status'],'failed')
        self.finish('Blender','DEEPTHORT_ASSET_PROBE {"kind":"image","width":8,"height":4}')
        self.assertEqual(self.pending()[0]['status'],'invalid_or_stale')
        self.finish('Blender')
        self.finish('Godot')
        self.image.write_bytes(png(8,4))
        with self.assertRaises(ValueError):pending_task(self.mixed,self.w,1)
    def test_parse_supported_imports_and_reject_invalid(self):
        roadmap={'project':str(self.root),'schedule':[]}
        base={'after':0,'goal':'Make mesh for Blender','output':'new.obj'}
        task=parse_tasks(json.dumps({'artifacts':[{**base,'imports':['Blender']}]}),roadmap,1)[0]
        self.assertEqual(task['imports'],['Blender'])
        for imports in (['Godot'],['Blender','Blender'],['unknown'],[],['Blender',{}]):
            with self.assertRaises(ValueError):
                parse_tasks(json.dumps({'artifacts':[{**base,'imports':imports}]}),roadmap,1)
if __name__=='__main__':unittest.main()
