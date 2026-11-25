import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.asset_import_probe import AssetProbes,plan,import_templates,auto_authority
from deepthort_local.roadmap_runs import RoadmapRuns
from deepthort_local.mixed_roadmap import MixedRoadmaps
from deepthort_local.project_authority import set_policy
from tests.test_tool_workflows_v61 import Recipes
from tests.test_artifact_acceptance_v61 import png

class AutoImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        state=Path(self.tmp.name);self.root=state/'project';self.root.mkdir()
        self.j=JanusStore(state/'janus.sqlite3');self.w=ToolWorkflows(self.j)
        r=Recipes(self.root);original=r._recipe_row
        r._recipe_row=lambda ident,root:{**original(ident,root),'artifact':'image.png'}
        self.acq=Mock();self.acq.tool.return_value={'executable':str(r.exe)}
        task={'after':0,'goal':'Create image usable in Blender','output':'image.png','imports':['Blender']}
        self.binding={'request_id':1,'project':str(self.root),'chat_id':'chat','spec_sha256':'spec'}
        m=freeze(r,self.root,[{'recipe_id':1,'input':''}],continuation=True)
        m['mixed_task']=task;m['specification']=self.binding
        m['roadmap']={'request_id':1,'manifest_sha256':'code','after':0,'project':str(self.root)}
        m['auto_imports']=import_templates(self.acq,m)
        self.assertFalse((self.root/'image.png').exists())
        self.ident=self.w.approve(m,user_approved=True)
        self.roadmaps=RoadmapRuns(state/'roadmap-runs.sqlite3')
        self.mixed_store=MixedRoadmaps(state/'mixed-roadmaps.sqlite3')
        mixed={'request_id':1,'code_sha':'code','tasks':[task]}
        mixed_sha=self.mixed_store.save(mixed)
        self.mixed=self.mixed_store.get(1,'code')
        self.roadmaps.approve({'request_id':1,'project':str(self.root),'chat_id':'chat','manifest_sha256':'code','mixed_sha':mixed_sha})
        self.roadmap=self.roadmaps.get(1)
        # Source binding checked independently by its existing real DB tests.
        # Here isolate claim/gate behavior from the conversation UI fixture.
        p=patch('deepthort_local.workflow_design.current_source',return_value=True);p.start();self.addCleanup(p.stop)
        p=patch('deepthort_local.workflow_design.current_source_file',return_value=True);p.start();self.addCleanup(p.stop)
        (state/'conversations.sqlite3').touch()
        self.w.tick(conversations=Mock(),roadmap_ready=lambda link:True)
        a=self.j.claim_next_action();self.assertIsNotNone(a)
        (self.root/'image.png').write_bytes(png(4,8))
        log=self.root/'producer.log';log.write_text('ok')
        self.j.update_action(a['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
        self.w.tick(conversations=Mock(),roadmap_ready=lambda link:True)
        self.w.tick(conversations=Mock(),roadmap_ready=lambda link:True)
        self.store=AssetProbes(self.w)
        self.p=plan(self.w,self.acq,self.ident,1,'Blender')
    def queue(self):
        return self.store.queue_required(self.p,self.acq,self.roadmap,self.mixed,enabled=True)
    def test_exact_approved_template_dispatch_once(self):
        ident=self.queue();self.assertIsNotNone(ident)
        self.assertEqual(self.j.claim_next_action()['id'],ident)
        self.j.update_action(ident,'failed',detail='failed',returncode=19)
        self.assertIsNone(self.queue())
    def test_no_authority_or_disabled_policy(self):
        with self.assertRaises(PermissionError):self.store.queue_required(self.p,self.acq,self.roadmap,self.mixed)
        changed={**self.p,'argv':self.p['argv']+['extra']}
        with self.assertRaises(ValueError):auto_authority(self.w,changed,self.roadmap,self.mixed)
        set_policy(self.j.path.parent/'project-work-policy.json',False)
        with self.assertRaises(ValueError):self.queue()
    def test_pause_after_queue_defers_claim(self):
        ident=self.queue()
        set_policy(self.j.path.parent/'project-work-policy.json',False)
        self.assertIsNone(self.j.claim_next_action())
        self.assertEqual(self.j.action(ident)['status'],'approved')
        set_policy(self.j.path.parent/'project-work-policy.json',True)
        self.assertEqual(self.j.claim_next_action()['id'],ident)
if __name__=='__main__':unittest.main()
