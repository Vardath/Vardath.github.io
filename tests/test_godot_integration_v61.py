import tempfile
import unittest
from pathlib import Path
from deepthort_local.godot_integration import command,inputs,current,MARKER
from deepthort_local.project_authority import recognized_test_command
from deepthort_local.verification_evidence import assess_verification

class SceneIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project';self.root.mkdir()
        self.exe=self.root.parent/'godot.exe';self.exe.write_bytes(b'fixture')
        (self.root/'project.godot').write_text('[application]\nrun/main_scene="res://main.tscn"\n')
        (self.root/'main.tscn').write_text('[gd_scene format=3]\n[node name="Main" type="Node"]\n')
        self.argv=command(self.root,self.exe)
    def test_fixed_profile_and_source_changes(self):
        self.assertTrue(recognized_test_command(self.argv,self.root))
        self.assertFalse(recognized_test_command(self.argv+['extra'],self.root))
        baseline=inputs(self.root,self.argv)
        self.assertTrue(current(self.root,baseline))
        (self.root/'new.gd').write_text('extends Node')
        self.assertFalse(current(self.root,baseline))
    def test_real_marker_required_and_errors_override_exit(self):
        marker=MARKER+'{"scene":"res://main.tscn","nodes":2,"frames":12}'
        self.assertEqual(assess_verification(self.argv,0,[marker])['assurance'],'godot_scene_instantiated')
        for lines in ([],[marker,marker],[marker,'SCRIPT ERROR: invalid call'],[marker.replace('12','1')]):
            self.assertFalse(assess_verification(self.argv,0,lines)['accepted'])
        self.assertFalse(assess_verification(self.argv,19,[marker])['accepted'])
    def test_editor_errors_not_success(self):
        argv=[str(self.exe),'--headless','--path',str(self.root),'--editor','--quit']
        self.assertFalse(assess_verification(argv,0,['ERROR: Failed loading resource'])['accepted'])
        self.assertEqual(assess_verification(argv,0,['Godot editor'])['assurance'],'editor_load_only')
    def test_missing_or_uid_scene_not_runtime_profile(self):
        for scene in ('res://missing.tscn','uid://abc'):
            (self.root/'project.godot').write_text('[application]\nrun/main_scene="'+scene+'"\n')
            with self.assertRaises(ValueError):command(self.root,self.exe)
if __name__=='__main__':unittest.main()
