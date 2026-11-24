import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.workflow_design import WorkflowDrafts,source_binding,learn_missing,inventory

class WorkflowScriptLearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.root=root/'project';self.root.mkdir()
        self.store=ToolAcquisition(root/'tools.sqlite')
        self.janus=JanusStore(root/'janus.sqlite')
        exe=root/'blender.exe';exe.write_bytes(b'fixture')
        self.store.discover([{'name':'Blender','location':str(exe),'found':True}])
        a=self.store.authorize_probe('Blender',self.root,self.janus,user_approved=True)
        log=root/'help.log';log.write_text('Blender --background --python script.py -- arguments')
        self.janus.update_action(a,'succeeded',detail='fixture',returncode=0,output_file=str(log))
        self.drafts=WorkflowDrafts(root/'drafts.sqlite')
        self.request=dict(id=1,chat_id='chat',project=str(self.root),mode='draft_plan',prompt='Create a mesh')
        self.drafts.queue(2,source_binding(self.request),'Generate mesh')
        self.proposal={'stages':[],'missing':[{'capability':'Blender','goal':'Export mesh','output':'mesh.glb'}]}
        self.council=Mock()
        self.review=Mock()
        self.obj=dict(title='Generate mesh with script',purpose='Create requested geometry',
                      args=['--background','--python','{{script}}','--','{{output}}'],
                      artifact='mesh.glb',script={'path':'tools/create_mesh.py','source':'import bpy\nimport sys\nbpy.ops.export_scene.gltf(filepath=sys.argv[-1])\n'})
    def learn(self):
        self.council._run.return_value=json.dumps(self.obj)
        return learn_missing(self.drafts,self.store,self.janus,self.council,None,request_id=2,
                             request=self.request,proposal=self.proposal,review=self.review)
    def test_script_candidate_requires_separate_staging_then_becomes_eligible(self):
        rows=self.learn()
        self.assertEqual(rows[0]['state'],'needs_script_review')
        ident=rows[0]['recipe_id']
        self.assertFalse((self.root/'tools/create_mesh.py').exists())
        self.assertEqual(len(self.janus.actions()),1)
        self.assertEqual(inventory(self.store,self.root,'Generate mesh')[0],[])
        self.assertEqual(self.obj['script']['source'],json.loads(self.review.call_args.args[0])['procedure']['script']['source'])
        review=self.store.script_review(ident,self.root)
        self.store.stage_script(ident,self.root,self.root/'backups',user_approved=True,
              expected_proposal_sha=review['proposal_sha'],expected_existing_sha=review['existing_sha'])
        self.assertEqual(self.learn()[0]['state'],'candidate')
        self.assertEqual(self.council._run.call_count,1)
        self.assertEqual(inventory(self.store,self.root,'Generate mesh')[0][0]['recipe_id'],ident)
        self.assertEqual(len(self.janus.actions()),1)
    def test_existing_script_rejected_without_writing(self):
        p=self.root/'tools/create_mesh.py';p.parent.mkdir();p.write_text('original')
        self.assertEqual(self.learn()[0]['state'],'needs_investigation')
        self.assertEqual(p.read_text(),'original')
        self.assertEqual(self.store.recipes(self.root),[])
    def test_exact_output_and_script_syntax(self):
        self.obj['artifact']='wrong.glb'
        self.assertEqual(self.learn()[0]['state'],'needs_investigation')
        self.obj['artifact']='mesh.glb';self.obj['script']['source']='def broken('
        self.assertEqual(self.learn()[0]['state'],'needs_investigation')
        self.assertEqual(self.store.recipes(self.root),[])
    def test_rejected_review_creates_no_recipe_or_file(self):
        self.review.side_effect=ValueError('Sentinel rejected')
        self.assertEqual(self.learn()[0]['state'],'needs_investigation')
        self.assertEqual(self.store.recipes(self.root),[])
        self.assertFalse((self.root/'tools/create_mesh.py').exists())
    def test_command_only_candidate_remains_supported(self):
        del self.obj['script'];self.obj['args']=['--background','{{output}}']
        self.assertEqual(self.learn()[0]['state'],'candidate')
        self.assertEqual(len(self.janus.actions()),1)
if __name__=='__main__':unittest.main()
