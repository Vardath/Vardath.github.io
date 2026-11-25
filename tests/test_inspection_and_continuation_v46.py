"""v46: user-removed inventory rows must remain on disk; interrupted plans resume."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.inspection_exclusions import InspectionExclusions
from deepthort_local.plan_continuation import PlanContinuation
from deepthort_local.capability_library import CapabilityLibrary
from deepthort_local.agent_plan import PlanError, MAX_PLAN_ATTEMPTS, generate_model_plan


class InspectionExclusionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.project=self.root/'x4mods';self.project.mkdir()
        self.store=InspectionExclusions(self.root/'state'/'inspection.json')

    def test_exclusion_does_not_touch_game_or_output_files(self):
        source=self.project/'content.xml';source.write_text('<content id="safe"/>')
        original=source.read_bytes()
        self.store.exclude(self.project,'content.xml')
        self.assertTrue(source.exists());self.assertEqual(source.read_bytes(),original)
        again=InspectionExclusions(self.store.path)
        self.assertEqual(again.filter(self.project,['content.xml','md/test.xml']),['md/test.xml'])
        again.restore(self.project,'content.xml')
        self.assertEqual(again.filter(self.project,['content.xml']),['content.xml'])
        self.assertEqual(source.read_bytes(),original)

    def test_project_specific_casefolded_paths_and_restore_all(self):
        another=self.root/'other';another.mkdir()
        self.store.exclude(self.project,r'MD\Spawn.XML')
        self.assertEqual(self.store.filter(self.project,['md/spawn.xml','x.xml']),['x.xml'])
        self.assertEqual(self.store.filter(another,['md/spawn.xml']),['md/spawn.xml'])
        self.store.restore(self.project)
        self.assertFalse(self.store.paths(self.project))

    def test_invalid_paths_and_corrupt_store_fail_closed(self):
        for name in ('../game.exe','/absolute.xml','C:\\game\\file.xml','','a//b.xml','a/./b.xml'):
            with self.subTest(name=name),self.assertRaises(ValueError):self.store.exclude(self.project,name)
        self.store.path.parent.mkdir(exist_ok=True)
        self.store.path.write_text('{"schema":"not-ours"}')
        with self.assertRaises(ValueError):self.store.exclude(self.project,'content.xml')
        self.assertEqual(self.store.path.read_text(),'{"schema":"not-ours"}')

    def test_discovery_and_cached_index_exclude_removed_files(self):
        (self.project/'README.md').write_text('This is an X4 readme evidence to index and inspect')
        (self.project/'content.xml').write_text('<content id="mod"/>')
        cap=CapabilityLibrary(self.root/'state'/'cap.sqlite3')
        cap.inspect_project(self.project)
        self.assertIn('README.md',[r['relative_path'] for r in cap.observations(self.project)])
        self.assertTrue(any(r['relative_path']=='README.md' for r in cap.references.current(self.project)))
        self.store.exclude(self.project,'README.md')
        cap.exclude_project_paths(self.project,['README.md'])
        self.assertNotIn('README.md',[r['relative_path'] for r in cap.observations(self.project)])
        self.assertFalse(any(r['relative_path']=='README.md' for r in cap.references.current(self.project)))
        cap.inspect_project(self.project,exclude_paths=self.store.paths(self.project))
        self.assertEqual([r['relative_path'] for r in cap.observations(self.project)],['content.xml'])
        self.assertTrue((self.project/'README.md').is_file())


class PlanContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.project=self.root/'mods';self.project.mkdir()
        self.cache=PlanContinuation(self.root/'state');self.request='Create an X4 Xenon PE extension';self.evidence='verified PE source v1'

    def test_strict_exact_project_request_evidence_identity(self):
        frag=[{'path':'content.xml','description':'Extension metadata for X4'}]
        self.cache.save(self.project,self.request,self.evidence,frag)
        self.assertEqual(self.cache.load(self.project,self.request,self.evidence),frag)
        self.assertFalse(self.cache.load(self.project,self.request+' changed',self.evidence))
        self.assertFalse(self.cache.load(self.project,self.request,self.evidence+' changed'))
        self.assertFalse(self.cache.load(self.project,self.request,self.evidence,context='different document attachments'))
        another=self.root/'other';another.mkdir()
        self.assertFalse(self.cache.load(another,self.request,self.evidence))
        self.assertEqual(list(self.cache.root.glob('*.json')).__len__(),1)

    def test_no_poison_or_workspace_escape(self):
        with self.assertRaises(PlanError):
            self.cache.save(self.project,self.request,self.evidence,
                            [{'path':'../outside.xml','description':'Attempt traversal'}])
        with self.assertRaises(PlanError):
            self.cache.save(self.project,self.request,self.evidence,
                            [{'path':'a.xml','description':'duplicate file'},
                             {'path':'A.xml','description':'duplicate file'}])
        self.assertFalse(self.cache.load(self.project,self.request,self.evidence))

    def test_failed_first_request_recovers_partial_and_succeeds(self):
        first={'files':[{'path':'content.xml','description':'X4 extension metadata using vanilla references'}]}
        request=self.request
        class First:
            def __init__(self):self.calls=0
            def chat(self,*args,**kwargs):self.calls+=1;return json.dumps(first)
        start=First()
        with self.assertRaises(PlanError):
            generate_model_plan(start,'initial',request,self.project,'Initial approved request',
                                x4_evidence=self.evidence,max_rounds=1,continuation=self.cache)
        self.assertEqual(start.calls,1)
        self.assertEqual(len(self.cache.load(self.project,request,self.evidence,context='Initial approved request')),1)
        second={'files':[
            {'path':'md/spawn.xml','description':'Player faction ownership and respawn for Xenon PE ship using vanilla source'},
            {'path':'assets/units/size_m/macros/pe.xml','description':'Vanilla PE ship macro connection mapping, storage cargo and speed handling upgrades'},
            {'path':'index/macros.xml','description':'Macro registration for PE ship variant'},
            {'path':'libraries/equipment.xml','description':'Vanilla forward weapon and turret upgrades with reference compatibility'}]}
        class Second:
            def __init__(self):self.calls=0
            def chat(self,*args,**kwargs):self.calls+=1;return json.dumps(second)
        model=Second()
        answer,steps=generate_model_plan(model,'retry',request,self.project,'Initial approved request',
                            x4_evidence=self.evidence,max_rounds=1,continuation=self.cache)
        self.assertEqual(model.calls,1)
        self.assertEqual(len(steps),5)
        self.assertEqual(json.loads(answer)['files'],steps)
        self.assertEqual(self.cache.load(self.project,request,self.evidence,context='Initial approved request'),[])
        self.assertFalse((self.project/'content.xml').exists())

    def test_recovered_validated_plan_does_not_spend_new_inference(self):
        steps=[
            {'path':'content.xml','description':'X4 metadata inspected from installed vanilla game'},
            {'path':'md/spawn.xml','description':'PE player ownership check and respawn logic for player faction'},
            {'path':'libraries/weapons.xml','description':'PE vanilla forward weapons and turret upgrades with cargo storage and speed handling changes'},
            {'path':'assets/ship.xml','description':'PE vanilla ship macro equipment connection mapping'}]
        self.cache.save(self.project,self.request,self.evidence,steps,context='new prompt')
        class FailModel:
            def chat(self,*args,**kwargs):raise AssertionError('should not call inference')
        answer,restored=generate_model_plan(FailModel(),'fresh',self.request,self.project,'new prompt',
                                            x4_evidence=self.evidence,max_rounds=1,continuation=self.cache)
        self.assertEqual(restored,steps)
        self.assertEqual(self.cache.load(self.project,self.request,self.evidence,context='new prompt'),[])

    def test_default_planning_budget_not_shrunk_to_improve_speed(self):
        self.assertGreaterEqual(MAX_PLAN_ATTEMPTS,40)


class GUIExclusionTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk display')
    def test_gui_exclusion_removes_row_preserves_file_restart_and_restore(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);proj=root/'x4mods';proj.mkdir()
            path=proj/'content.xml';path.write_text('<content id="unchanged"/>')
            with patch.object(mod,'STATE',root/'state'),\
                    patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                    patch.object(mod.messagebox,'showinfo'),patch.object(mod.messagebox,'showerror'):
                app=mod.DeepThorTDesktop()
                try:
                    app._set_project(proj)
                    app.update();app._handle_events()
                    app._exclude_project_file('content.xml')
                    app.update();app._handle_events()
                    self.assertEqual([app.files.item(r,'text') for r in app.files.get_children()],[])
                    self.assertEqual(path.read_text(),'<content id="unchanged"/>')
                    self.assertTrue(app.inspection_exclusions.paths(proj))
                    self.assertIsNotNone(app.files.bind('<Button-3>'))
                finally:
                    app._quit()
                new=InspectionExclusions(root/'state'/'project-inspection-exclusions-v46.json')
                self.assertEqual(new.filter(proj,['content.xml']),[])
                new.restore(proj,'content.xml')
                self.assertEqual(new.filter(proj,['content.xml']),['content.xml'])
                self.assertTrue(path.exists())

if __name__=='__main__':unittest.main()
