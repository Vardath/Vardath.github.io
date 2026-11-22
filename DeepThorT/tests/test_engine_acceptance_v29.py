"""v29: read-only engine checks, real test evidence and milestone gates."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from deepthort_local.engine_acceptance import audit_engine_project, main
from deepthort_local.job_queue import JobStore
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.specification_library import SpecificationIndex
from deepthort_local.semantic_reconciliation import capture_verified_sources,verified_sources_current
from deepthort_local.verification_evidence import assess_verification,attach_verification


class X4ExtensionAudit(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'pe_extension'; self.root.mkdir()
        (self.root/'content.xml').write_text('<content id="pe_extension" name="PE"/>')

    def test_valid_macro_index_is_not_ingame_proof(self):
        (self.root/'index').mkdir()
        (self.root/'assets/units/macros').mkdir(parents=True)
        (self.root/'assets/units/macros/pe_macro.xml').write_text('<macros><macro name="pe_macro" class="ship_m"/></macros>')
        (self.root/'index/macros.xml').write_text('<index><entry name="pe_macro" value="extensions/pe_extension/assets/units/macros/pe_macro"/></index>')
        report=audit_engine_project(self.root,[{'path':'content.xml'},
            {'path':'index/macros.xml'}, {'path':'assets/units/macros/pe_macro.xml'}])
        self.assertEqual(report['engine'],'x4_extension')
        self.assertEqual(report['issues'],[])
        self.assertTrue(report['accepted'])
        self.assertFalse(report['acceptance_confirmed'])
        self.assertIn('assets/units/macros/pe_macro.xml',report['source_hashes'])

    def test_missing_locally_registered_macro_is_hard_error(self):
        (self.root/'index').mkdir()
        (self.root/'index/macros.xml').write_text('<index><entry name="missing_macro" value="extensions/pe_extension/assets/units/macros/missing_macro"/></index>')
        found=audit_engine_project(self.root)
        self.assertIn('missing_local_index_target',{x['code'] for x in found['issues']})

    def test_wrong_macro_name_and_duplicate_entry(self):
        (self.root/'index').mkdir()
        (self.root/'assets/macros').mkdir(parents=True)
        (self.root/'assets/macros/test.xml').write_text('<macros><macro name="other"/></macros>')
        (self.root/'index/macros.xml').write_text('<index><entry name="test" value="extensions/pe_extension/assets/macros/test"/></index>')
        found=audit_engine_project(self.root)
        self.assertIn('index_name_not_defined',{x['code'] for x in found['issues']})
        (self.root/'index/macros.xml').write_text('<index><entry name="test" value="assets/macros/test"/><entry name="test" value="assets/macros/test"/></index>')
        found=audit_engine_project(self.root)
        self.assertIn('index_duplicate_name',{x['code'] for x in found['issues']})

    def test_broken_md_or_manifest_rejected_without_running_it(self):
        (self.root/'md').mkdir()
        (self.root/'md/pe.xml').write_text('<script><cue/></script>')
        report=audit_engine_project(self.root,[{'path':'md/pe.xml'}])
        self.assertIn('md_root_invalid',{x['code'] for x in report['issues']})
        (self.root/'md/pe.xml').write_text('<mdscript name="pe"/>')
        (self.root/'content.xml').write_text('<content id="x"><!ENTITY x "boom"></content>')
        self.assertIn('xml_invalid',{x['code'] for x in audit_engine_project(self.root)['issues']})

    def test_reference_to_vanilla_does_not_get_falsely_claimed_local(self):
        (self.root/'index').mkdir()
        (self.root/'index/macros.xml').write_text('<index><entry name="vanilla_macro" value="assets/units/vanilla_macro"/></index>')
        found=audit_engine_project(self.root)
        self.assertEqual(found['issues'],[])
        self.assertTrue(found['observations'])

    def test_pending_planned_files_are_not_accepted(self):
        report=audit_engine_project(self.root,[{'path':'md/pe.xml'}])
        self.assertIn('md/pe.xml',report['pending'])
        self.assertFalse(report['accepted'])

    def test_audit_cli_exits_nonzero_on_broken_xml_and_never_executes(self):
        marker=self.root/'did_not_run'
        (self.root/'md').mkdir();(self.root/'md/x.xml').write_text('<mdscript><bad>')
        capture=io.StringIO()
        with redirect_stdout(capture):
            self.assertEqual(main([str(self.root)]),2) # existing invalid MD is discovered even without a plan
        plan=self.root/'plan.json'; plan.write_text(json.dumps({'files':[{'path':'md/x.xml'}]}))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.root),'--plan',str(plan)]),2)
        self.assertFalse(marker.exists())

    def test_index_symlink_escape_is_blocked(self):
        try:
            (self.root/'bad.xml').symlink_to(Path(self.temp.name)/'outside.xml')
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):
            audit_engine_project(self.root,[{'path':'../outside.xml'}])


class GodotAndAndroidAudit(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_scene_link_checks_and_android_export_preset(self):
        (self.root/'project.godot').write_text('[application]\nrun/main_scene="res://main.tscn"\n')
        missing=audit_engine_project(self.root)
        self.assertIn('missing_main_scene',{i['code'] for i in missing['issues']})
        (self.root/'main.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/main.gd" id="1"]\n')
        missing=audit_engine_project(self.root)
        self.assertIn('missing_resource_reference',{i['code'] for i in missing['issues']})
        (self.root/'scripts').mkdir();(self.root/'scripts/main.gd').write_text('extends Node\n')
        (self.root/'export_presets.cfg').write_text('[preset.0]\nname="Android"\nplatform="Android"\n')
        result=audit_engine_project(self.root)
        self.assertEqual(result['issues'],[])
        self.assertTrue(any(x['code']=='android_export_preset_declared_not_built' for x in result['observations']))
        self.assertFalse(result['acceptance_confirmed'])

    def test_no_untrusted_godot_script_is_executed(self):
        (self.root/'project.godot').write_text('[application]\n')
        (self.root/'test').mkdir();(self.root/'test/test_bad.gd').write_text('extends GutTest\nfunc test_one():\n  OS.shell_open("evil")\n')
        result=audit_engine_project(self.root,[{'path':'test/test_bad.gd'}])
        self.assertEqual(result['static_test_functions'],1)
        self.assertFalse(result['acceptance_confirmed'])

    def test_res_uri_traversal_rejected(self):
        (self.root/'project.godot').write_text('run/main_scene="res://../outside.tscn"\n')
        with self.assertRaises(ValueError):
            audit_engine_project(self.root)

    def test_android_manifest_syntax(self):
        (self.root/'settings.gradle').write_text('include(":app")')
        (self.root/'app/src/main').mkdir(parents=True)
        (self.root/'app/src/main/AndroidManifest.xml').write_text('<manifest package="example.app"/>')
        self.assertTrue(audit_engine_project(self.root)['accepted'])
        (self.root/'app/src/main/AndroidManifest.xml').write_text('<resources/>')
        self.assertIn('android_manifest_invalid',{x['code'] for x in audit_engine_project(self.root)['issues']})


class EngineVerificationEvidenceTests(unittest.TestCase):
    def test_gut_pass_more_than_zero_and_complete_summary(self):
        command=['godot','--headless','--path','.', '-s','addons/gut/gut_cmdln.gd','-gexit']
        good=assess_verification(command,0,['res://test/test_one.gd','3/3 passed.','---- All tests passed! ----'])
        self.assertTrue(good['accepted'])
        self.assertEqual(good['assurance'],'godot_gut_tests_passed')
        self.assertEqual(good['test_count'],3)
        for output in (['0/0 passed.','All tests passed!'],['1/2 passed.','All tests passed!'],
                       ['3/3 passed.','SCRIPT ERROR: parse failed','All tests passed!'],
                       ['3/3 passed.']):
            with self.subTest(output=output):self.assertFalse(assess_verification(command,0,output)['accepted'])

    def test_x4_cli_requires_actual_structural_report(self):
        cmd=[sys.executable,'/app/engine_acceptance_cli.py','/proj']
        fake=assess_verification(cmd,0,['No output'])
        self.assertFalse(fake['accepted'])
        good=assess_verification(cmd,0,[json.dumps({'engine':'x4_extension','issues':[],'pending':[],'accepted':True})])
        self.assertTrue(good['accepted'])
        self.assertEqual(good['assurance'],'x4_static_xml_passed')
        self.assertFalse(assess_verification(cmd,0,[json.dumps({'engine':'x4_extension','issues':[{'code':'bad'}],'accepted':False})])['accepted'])

    def test_modified_unplanned_index_file_invalidates_verified_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'content.xml').write_text('<content id="v"/>')
            (root/'index').mkdir();(root/'index/macros.xml').write_text('<index/>')
            steps=[{'path':'content.xml','description':'mod'}]
            assessment=assess_verification([sys.executable,'/app/engine_acceptance_cli.py',str(root)],0,
                [json.dumps({'engine':'x4_extension','issues':[],'pending':[],'accepted':True})])
            from deepthort_local.engine_acceptance import audit_engine_project
            snap=attach_verification(capture_verified_sources(root,steps),assessment,['python','engine_acceptance_cli.py'],
                                     engine_report=audit_engine_project(root,steps))
            self.assertTrue(verified_sources_current(root,steps,snap))
            (root/'index/macros.xml').write_text('<index><entry name="x" value="extensions/v/nothere"/></index>')
            self.assertFalse(verified_sources_current(root,steps,snap))

    def test_forged_engine_assurance_does_not_pass_fingerprint_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'content.xml').write_text('<content id="x"/>')
            steps=[{'path':'content.xml','description':'meta'}]
            snap=capture_verified_sources(root,steps)
            snap['verification']={'assurance':'x4_static_xml_passed','test_count':None,
                                  'output_sha256':'0'*64,'argv_sha256':'0'*64,
                                  'engine':'x4_extension','engine_sources':{'content.xml':'1'*64}}
            self.assertFalse(verified_sources_current(root,steps,snap))


class DesktopCommandSelection(unittest.TestCase):
    def test_gut_selected_when_real_tests_and_plugin_present(self):
        import desktop_app as app
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'project.godot').write_text('config_version=5')
            (root/'addons/gut').mkdir(parents=True)
            (root/'addons/gut/gut_cmdln.gd').write_text('extends SceneTree\n')
            (root/'tests').mkdir();(root/'tests/test_one.gd').write_text('extends GutTest\nfunc test_thing():\n  pass\n')
            with patch.object(app.shutil,'which',return_value='/tools/godot'):
                cmd=app.DeepThorTDesktop._verification_command(None,root)
            self.assertIn('-gexit',cmd)
            self.assertIn('addons/gut/gut_cmdln.gd',cmd)
            self.assertNotIn('--editor',cmd)

    def test_editor_load_label_without_test_plugin_and_x4_fallback(self):
        import desktop_app as app
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'project.godot').write_text('config_version=5')
            with patch.object(app.shutil,'which',return_value='/tools/godot'):
                self.assertIn('--editor',app.DeepThorTDesktop._verification_command(None,root))
            (root/'project.godot').unlink();(root/'content.xml').write_text('<content id="a"/>')
            self.assertTrue(any('engine_acceptance_cli.py' in arg for arg in
                                app.DeepThorTDesktop._verification_command(None,root)))


class MilestoneEngineIntegration(unittest.TestCase):
    def test_broken_x4_macro_index_blocks_milestone_after_green_process(self):
        with tempfile.TemporaryDirectory() as td:
            parent=Path(td); project=parent/'extension'; project.mkdir()
            original='REQ-1: The extension must create a new player ship.\n'+('x'*2200)
            index=SpecificationIndex(parent/'spec.sqlite3')
            index.index(101,original)
            index.save_response(101,original,0,json.dumps({'files':[
                {'path':'content.xml','description':'Register extension'},
                {'path':'index/macros.xml','description':'Register local ship macro'},
            ]}),project=project)
            plan=HierarchicalPlanStore(parent/'hierarchy.sqlite3')
            plan.prepare(index,101,original,project,chat_id='chat',max_files=12)
            first=plan.milestone(index,101,original,1)
            jobs=JobStore(parent/'jobs.sqlite3')
            job=jobs.submit_approved_milestone_build(first['project'],first['chat_id'],
                first['scope_prompt'],first['steps'],first['approval_key'],
                master_prompt=original,master_steps=first['master_steps'])
            plan.link_job(index,101,original,1,job)
            (project/'index').mkdir()
            (project/'content.xml').write_text('<content id="extension"/>')
            (project/'index/macros.xml').write_text('<index><entry name="ship" value="extensions/extension/assets/ship"/></index>')
            for s in jobs.steps(job):jobs.set_step(s['id'],'saved')
            jobs.change(job,'complete','Verified: test command exited 0 (mock)',
                result=json.dumps(capture_verified_sources(project,first['steps'])),allowed=('queued',))
            result=plan.reconcile_jobs(index,101,original,jobs)
            self.assertEqual(result['milestones_verified'],0)
            self.assertIn('Engine artifact audit',jobs.get(job)['detail'])
            (project/'assets').mkdir()
            (project/'assets/ship.xml').write_text('<macros><macro name="ship"/></macros>')
            self.assertEqual(plan.reconcile_jobs(index,101,original,jobs)['milestones_verified'],0)
            jobs.change(job,'running','User approved fresh check',allowed=('waiting_verification',))
            jobs.change(job,'complete','Verified: test command exited 0 (new approved check)',
                result=json.dumps(capture_verified_sources(project,first['steps'])),allowed=('running',))
            result=plan.reconcile_jobs(index,101,original,jobs)
            self.assertEqual(result['milestones_verified'],1)
            self.assertFalse(result['acceptance_confirmed'])


class EngineContractDiscovery(unittest.TestCase):
    def test_model_declared_godot_test_requires_real_test_function(self):
        from deepthort_local.acceptance_contracts import inspect_model_contracts
        from deepthort_local.requirements_intelligence import requirement_candidates
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'tests').mkdir()
            requirement='REQ-1: Ship movement must respond to input.\n'
            candidates=requirement_candidates(requirement,[(0,0,len(requirement),'','','')])
            steps=[{'path':'tests/test_movement.gd','description':'Test movement; verifies: REQ-1'}]
            (root/'tests/test_movement.gd').write_text('extends GutTest\n')
            self.assertIn('no_test_cases_found',{x['state'] for x in
                inspect_model_contracts(root,steps,requirement,candidates)['issues']})
            (root/'tests/test_movement.gd').write_text('extends GutTest\nfunc test_input():\n    assert_true(true)\n')
            report=inspect_model_contracts(root,steps,requirement,candidates)
            self.assertEqual(report['issues'],[])
            self.assertEqual(report['checks'][0]['state'],'static_test_discovered')
            self.assertFalse(report['acceptance_confirmed'])

    def test_android_test_claim_must_include_test_annotation(self):
        from deepthort_local.acceptance_contracts import inspect_model_contracts
        from deepthort_local.requirements_intelligence import requirement_candidates
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); path=root/'app/src/test/java/game/ShipTest.kt'
            path.parent.mkdir(parents=True)
            requirement='REQ-1: The UI must accept commands.\n'
            candidates=requirement_candidates(requirement,[(0,0,len(requirement),'','','')])
            steps=[{'path':'app/src/test/java/game/ShipTest.kt','description':'Ship tests; verifies: REQ-1'}]
            path.write_text('class ShipTest { }')
            self.assertIn('no_test_cases_found',{x['state'] for x in
                inspect_model_contracts(root,steps,requirement,candidates)['issues']})
            path.write_text('class ShipTest {\n    @Test\n    fun move() = Unit\n}')
            self.assertFalse(inspect_model_contracts(root,steps,requirement,candidates)['issues'])

    def test_bounded_x4_summary_remains_parseable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'content.xml').write_text('<content id="audit"/>')
            lines=io.StringIO()
            with redirect_stdout(lines):
                self.assertEqual(main([str(root),'--summary']),0)
            output=lines.getvalue()
            self.assertLess(len(output),2000)
            self.assertTrue(json.loads(output)['accepted'])


if __name__=='__main__':unittest.main()