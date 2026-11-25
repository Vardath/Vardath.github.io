"""v30 read-only toolchain discovery and new X4 macro registration guard."""
from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.engine_acceptance import audit_engine_project
from deepthort_local.engine_environment import (
    godot_executable, inspect_engine_environment, main,
)


class EnvironmentProbes(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)

    def test_godot_discovery_uses_only_real_files_no_process(self):
        exe=self.root/'godot.exe';exe.write_bytes(b'placeholder')
        fake=self.root/'missing'/'godot.exe'
        with patch('subprocess.run',side_effect=AssertionError('Unexpected process execution')):
            self.assertEqual(godot_executable(environ={'GODOT_EXECUTABLE':str(exe)},which=lambda _:None),str(exe))
            self.assertEqual(godot_executable(environ={'GODOT_EXECUTABLE':str(fake)},which=lambda _:None),'')
            self.assertEqual(godot_executable(tools={'tools':[{'name':'Godot','location':str(exe)}]},
                                             environ={},which=lambda _:None),str(exe))
            self.assertEqual(godot_executable(tools={'tools':[{'name':'Godot','location':str(self.root)}]},
                                             environ={},which=lambda _:None),'')

    def test_windows_version_named_godot_binary_supported(self):
        binary=self.root/'Godot_v4.5.1-stable_win64.exe';binary.touch()
        self.assertEqual(godot_executable(environ={'GODOT_EXECUTABLE':str(binary)},which=lambda _:None),str(binary))
        self.assertFalse(godot_executable(environ={'GODOT_EXECUTABLE':str(self.root/'strange.exe')},
                                          which=lambda _:None))

    def test_godot_project_ready_only_when_executable_is_real(self):
        (self.root/'project.godot').write_text('[application]\n')
        report=inspect_engine_environment(self.root,environ={},which=lambda _:None)
        self.assertFalse(report['can_perform_engine_check'])
        self.assertTrue(report['missing_prerequisites'])
        exe=self.root/'godot';exe.touch()
        report=inspect_engine_environment(self.root,environ={'GODOT_EXECUTABLE':str(exe)},which=lambda _:None)
        self.assertTrue(report['can_perform_engine_check'])
        self.assertEqual(report['tools']['godot'],str(exe))
        self.assertIn('No executable run',report['assurance'])

    def test_android_offline_prerequisite_discovery_without_install(self):
        (self.root/'settings.gradle').write_text('include(\":app\")')
        sdk=self.root/'Sdk';(sdk/'build-tools').mkdir(parents=True);(sdk/'platforms').mkdir()
        jdk=self.root/'jdk';(jdk/'bin').mkdir(parents=True);(jdk/'bin/java.exe').touch()
        gradle=self.root/'gradle';(gradle/'bin').mkdir(parents=True);(gradle/'bin/gradle.bat').touch()
        with patch('subprocess.run',side_effect=AssertionError('Unexpected process execution')):
            report=inspect_engine_environment(self.root,environ={
                'ANDROID_SDK_ROOT':str(sdk),'JAVA_HOME':str(jdk),'GRADLE_HOME':str(gradle)},
                which=lambda _:None)
        self.assertEqual(report['engine'],'android_gradle')
        self.assertFalse(report['missing_prerequisites'])
        self.assertTrue(report['tools']['java'].endswith('java.exe'))
        self.assertFalse(report['can_perform_engine_check'])

    def test_android_does_not_claim_sdk_from_empty_folder(self):
        (self.root/'settings.gradle').write_text('include(\":app\")')
        sdk=self.root/'emptySdk';sdk.mkdir()
        report=inspect_engine_environment(self.root,environ={'ANDROID_SDK_ROOT':str(sdk)},which=lambda _:None)
        self.assertFalse(report['tools']['android_sdk'])
        self.assertGreater(len(report['missing_prerequisites']),0)

    def test_x4_preflight_does_not_confuse_extension_and_game_dir(self):
        (self.root/'content.xml').write_text('<content id="one"/>')
        report=inspect_engine_environment(self.root,environ={},which=lambda _:None)
        self.assertEqual(report['engine'],'x4_extension')
        self.assertFalse(report['tools']['game'])
        self.assertFalse(report['tools']['extracted_reference'])
        game=self.root/'game';game.mkdir();(game/'X4.exe').write_bytes(b'fixture')
        refs=self.root/'refs';(refs/'index').mkdir(parents=True)
        (refs/'index/macros.xml').write_text('<index><entry name="m" value="assets/m"/></index>')
        (refs/'index/components.xml').write_text('<index><entry name="c" value="assets/c"/></index>')
        report=inspect_engine_environment(self.root,x4_game_dir=game,x4_reference_dir=refs)
        self.assertFalse(report['missing_prerequisites'])
        self.assertEqual(report['static_issues'],0)

    def test_cli_reports_inference_not_execution(self):
        (self.root/'content.xml').write_text('<content id="x"/>')
        from contextlib import redirect_stdout
        from io import StringIO
        output=StringIO()
        with redirect_stdout(output):
            self.assertEqual(main([str(self.root)]),0)
        report=json.loads(output.getvalue())
        self.assertEqual(report['engine'],'x4_extension')
        self.assertIn('Read-only',report['assurance'])


class X4RegistrationEvidence(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)/'extension';self.root.mkdir()
        (self.root/'content.xml').write_text('<content id="extension"/>')
        (self.root/'assets/units/size_m/macros').mkdir(parents=True)
        self.macro=self.root/'assets/units/size_m/macros/custom_ship.xml'
        self.macro.write_text('<macros><macro name="custom_ship" class="ship_m"/></macros>')

    def test_new_ship_macro_without_index_is_blocked(self):
        report=audit_engine_project(self.root)
        self.assertIn('local_macro_not_indexed',{r['code'] for r in report['issues']})
        self.assertFalse(report['accepted'])

    def test_declared_ship_macro_is_accepted_statically_only(self):
        (self.root/'index').mkdir()
        (self.root/'index/macros.xml').write_text('<index><entry name="custom_ship" value="extensions/extension/assets/units/size_m/macros/custom_ship"/></index>')
        report=audit_engine_project(self.root)
        self.assertEqual(report['issues'],[])
        self.assertTrue(report['accepted'])
        self.assertFalse(report['acceptance_confirmed'])

    def test_diff_patch_does_not_require_local_registration(self):
        self.macro.write_text('<diff><replace sel="/macros/macro/properties"/></diff>')
        report=audit_engine_project(self.root)
        self.assertNotIn('local_macro_not_indexed',{r['code'] for r in report['issues']})

    def test_empty_index_does_not_satisfy_registration(self):
        (self.root/'index').mkdir()
        (self.root/'index/macros.xml').write_text('<index/>')
        report=audit_engine_project(self.root)
        self.assertIn('local_macro_not_indexed',{r['code'] for r in report['issues']})

    def test_no_programs_executed_by_auditing(self):
        with patch('subprocess.run',side_effect=AssertionError('Audit executed code')):
            report=audit_engine_project(self.root)
        self.assertFalse(report['accepted'])


if __name__=='__main__':
    unittest.main()

class X4SelectedVanillaIndexes(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'custom';self.root.mkdir()
        (self.root/'content.xml').write_text('<content id="custom"/>')
        (self.root/'assets/units/size_m/macros').mkdir(parents=True)
        (self.root/'index').mkdir()
        (self.root/'index/macros.xml').write_text('<index><entry name="local_ship" value="extensions/custom/assets/units/size_m/macros/local_ship"/></index>')
        self.source=self.root/'assets/units/size_m/macros/local_ship.xml'
        self.refs=Path(self.temp.name)/'reference';(self.refs/'index').mkdir(parents=True)
        (self.refs/'index/macros.xml').write_text('<index><entry name="known_weapon" value="assets/props/WeaponSystems/weapon"/></index>')
        (self.refs/'index/components.xml').write_text('<index><entry name="known_component" value="assets/units/size_m/ship"/></index>')

    def test_verified_and_unknown_references_distinguished(self):
        from deepthort_local.x4_reference_links import inspect_x4_reference_links
        self.source.write_text('''<macros><macro name="local_ship" class="ship_m">
           <component ref="known_component"/><loadout><macro ref="known_weapon"/>
           <macro ref="dlc_weapon"/><macro ref="local_ship"/></loadout>
           </macro></macros>''')
        report=inspect_x4_reference_links(self.root,self.refs)
        self.assertEqual(report['resolved_vanilla_count'],2)
        self.assertEqual(report['resolved_local_count'],1)
        self.assertEqual(report['unresolved_count'],1)
        self.assertEqual(report['unresolved_samples'][0]['name'],'dlc_weapon')
        self.assertFalse(report['gameplay_verified'])
        self.assertTrue(report['vanilla_index_sha256']['index/macros.xml'])
        ready=inspect_engine_environment(self.root,x4_game_dir=self.refs,x4_reference_dir=self.refs)
        self.assertEqual(ready['x4_reference_links']['unresolved_count'],1)

    def test_missing_reference_indexes_do_not_count_as_bad_game_data(self):
        from deepthort_local.x4_reference_links import inspect_x4_reference_links
        self.source.write_text('<macros><macro name="local_ship"><component ref="a"/></macro></macros>')
        (self.refs/'index/components.xml').unlink()
        report=inspect_x4_reference_links(self.root,self.refs)
        self.assertFalse(report['vanilla_index_available']['component'])
        self.assertEqual(report['unresolved_count'],1)
        self.assertIn('extracted_index_unavailable',{x['code'] for x in report['observations']})

    def test_reference_indexes_do_not_execute_xml_entities(self):
        from deepthort_local.x4_reference_links import inspect_x4_reference_links
        self.source.write_text('<macros><macro name="local_ship"/></macros>')
        (self.refs/'index/macros.xml').write_text('<!DOCTYPE index [<!ENTITY xx "boom">]><index/>')
        report=inspect_x4_reference_links(self.root,self.refs)
        self.assertFalse(report['vanilla_index_available']['macro'])
        self.assertIn('extracted_index_unavailable',{x['code'] for x in report['observations']})

    def test_no_reference_data_claims_engine_success(self):
        self.source.write_text('<macros><macro name="local_ship"/></macros>')
        report=inspect_engine_environment(self.root,x4_reference_dir=self.refs)
        self.assertNotIn('gameplay_verified',report)  # Only scoped source audit has that field
        self.assertFalse(report['x4_reference_links']['gameplay_verified'])
        self.assertGreater(len(report['missing_prerequisites']),0)


class X4InstallationRecognition(unittest.TestCase):
    def test_empty_selected_folder_not_claimed_as_game(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'content.xml').write_text('<content id="x"/>')
            empty=root/'empty_game';empty.mkdir()
            found=inspect_engine_environment(root,x4_game_dir=empty)
            self.assertFalse(found['tools']['game_executable_present'])
            self.assertTrue(any('no X4 executable' in s for s in found['missing_prerequisites']))
