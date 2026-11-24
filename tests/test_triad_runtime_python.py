import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess
import download_model as installer

class TriadRuntimePythonTests(unittest.TestCase):
    def test_unsupported_python_315(self):
        with patch.object(installer.subprocess,'run',return_value=Mock(stdout='["C:/Python315/python.exe",[3,15],8,"AMD64"]')):
            self.assertIsNone(installer.probe_python(['python']))
    def test_supported_python_313(self):
        with patch.object(installer.subprocess,'run',return_value=Mock(stdout='["C:/Python313/python.exe",[3,13],8,"AMD64"]')):
            self.assertEqual(installer.probe_python(['python']),Path('C:/Python313/python.exe'))
    def test_wrong_architecture(self):
        with patch.object(installer.subprocess,'run',return_value=Mock(stdout='["python.exe",[3,13],4,"AMD64"]')):
            self.assertIsNone(installer.probe_python(['python']))
    def test_select_supported_launcher(self):
        with patch.object(installer,'probe_python',side_effect=[None,Path('python313.exe')]) as probe, patch.object(installer.shutil,'which',return_value='py.exe'):
            self.assertEqual(installer.choose_runtime_python(),Path('python313.exe'))
            self.assertEqual(probe.call_args.args[0],['py.exe','-3.13'])
    def test_no_supported_interpreter_clear_error(self):
        with patch.object(installer,'probe_python',return_value=None),patch.object(installer.shutil,'which',return_value=None):
            with self.assertRaisesRegex(RuntimeError,'Python 3.15 cannot'):
                installer.choose_runtime_python()
    def test_bad_venv_preserved_before_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=Path(tmp)/'openvino-env'
            exe=env/'Scripts'/'python.exe'
            exe.parent.mkdir(parents=True)
            exe.write_text('old')
            def create(*args,**kwargs):
                exe.parent.mkdir(parents=True)
                exe.write_text('new')
            with patch.object(installer,'probe_python',side_effect=[None,Path('new.exe')]),patch.object(installer,'choose_runtime_python',return_value=Path('python313.exe')),patch.object(installer.subprocess,'run',side_effect=create):
                installer.ensure_runtime_environment(exe)
            self.assertEqual(exe.read_text(),'new')
            backups=list(Path(tmp).glob('openvino-env-incompatible-*'))
            self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/'Scripts/python.exe').read_text(),'old')
    def test_valid_venv_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'Scripts/python.exe'
            exe.parent.mkdir();exe.touch()
            with patch.object(installer,'probe_python',return_value=exe),patch.object(installer,'choose_runtime_python') as choose:
                installer.ensure_runtime_environment(exe)
                choose.assert_not_called()
