"""Acceptance: verified ZIP receipts and actionable secondary-model waiting states."""
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from deepthort_local.flight_recorder import (
    export_diagnostics,verify_diagnostics_archive,retain_diagnostic_copy)
from deepthort_local.dual_onnx import council_wait_reason,council_port_occupied

G=1024**3


class ExportAcceptance(unittest.TestCase):
    def test_verified_copy_and_receipt_survive_restart(self):
        with tempfile.TemporaryDirectory() as home:
            root=Path(home);state=root/'state';state.mkdir()
            dest=root/'elsewhere'/'support.zip'
            output=export_diagnostics(state,dest,app_root=root,app_state={'model_ready':False})
            self.assertEqual(output,dest)
            self.assertEqual(verify_diagnostics_archive(dest)['path'],str(dest.resolve()))
            receipt_path=state/'last-diagnostic-export.json'
            mirror=root/'diagnostics'/'DeepThorT-Diagnostics-20261123-000000.zip'
            receipt=retain_diagnostic_copy(dest,mirror,receipt_path)
            self.assertEqual(receipt['chosen_path'],str(dest.resolve()))
            self.assertEqual(receipt['retained_path'],str(mirror.resolve()))
            self.assertEqual(receipt['sha256'],verify_diagnostics_archive(mirror)['sha256'])
            self.assertEqual(json.loads(receipt_path.read_text())['retained_path'],str(mirror.resolve()))
            dest.unlink() # The custom Save As path may be moved/deleted later.
            self.assertEqual(verify_diagnostics_archive(mirror)['sha256'],receipt['sha256'])

    def test_invalid_zip_never_receives_success_receipt(self):
        with tempfile.TemporaryDirectory() as home:
            root=Path(home);broken=root/'broken.zip';broken.write_bytes(b'not a zip')
            receipt=root/'state'/'last.json'
            with self.assertRaises((OSError,ValueError,zipfile.BadZipFile)):
                retain_diagnostic_copy(broken,root/'backup.zip',receipt)
            self.assertFalse(receipt.exists())
            self.assertFalse((root/'backup.zip').exists())

    def test_zip_creation_error_does_not_overwrite_existing_export(self):
        with tempfile.TemporaryDirectory() as home:
            root=Path(home);state=root/'state';state.mkdir()
            good=export_diagnostics(state,root/'original.zip')
            before=good.read_bytes()
            with patch('deepthort_local.flight_recorder.verify_diagnostics_archive',side_effect=ValueError('bad new ZIP')):
                with self.assertRaises(ValueError):export_diagnostics(state,good)
            self.assertEqual(good.read_bytes(),before)
            self.assertEqual(sorted(x.name for x in root.glob('.deepthort-export-*')),[])

    def test_default_root_copy_when_chosen_same(self):
        with tempfile.TemporaryDirectory() as home:
            root=Path(home);state=root/'state';state.mkdir()
            dest=export_diagnostics(state,root/'support.zip')
            receipt=retain_diagnostic_copy(dest,dest,state/'receipt.json')
            self.assertEqual(receipt['chosen_path'],receipt['retained_path'])


class CouncilWaitAcceptance(unittest.TestCase):
    def setUp(self):
        self.ready=dict(primary_ready=True,primary_loading=False,memory=(40*G,18*G),capped=True)

    def test_precise_reasons(self):
        self.assertIn('primary ONNX',council_wait_reason(primary_ready=False,primary_loading=True))
        self.assertIn('Start AI',council_wait_reason(primary_ready=False,primary_loading=False))
        self.assertIn('Job Object',council_wait_reason(**{**self.ready,'capped':False}))
        self.assertIn('RAM',council_wait_reason(**{**self.ready,'memory':(40*G,3*G)}))
        self.assertIn('three worker exits',council_wait_reason(**{**self.ready,'restarts':3}))
        self.assertIn('loading',council_wait_reason(**self.ready,council_running=True,
                                                    health={'stage':'Loading weights','loading_seconds':12}))
        self.assertIn('ready',council_wait_reason(**self.ready,council_ready=True))
        self.assertIn('interpreting',council_wait_reason(**self.ready,council_busy=True))
        self.assertIn('queued',council_wait_reason(**self.ready))

    def test_untrusted_port_listener_is_detected(self):
        self.assertTrue(council_port_occupied(connector=lambda:True))
        self.assertFalse(council_port_occupied(connector=lambda:False))

    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk GUI display')
    def test_gui_export_and_inbox_no_primary_worker(self):
        import desktop_app as appmod
        with tempfile.TemporaryDirectory() as home:
            root=Path(home);state=root/'state';project=root/'project';project.mkdir()
            with patch.object(appmod,'STATE',state),\
                 patch.object(appmod,'ROOT',root),\
                 patch.object(appmod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                 patch.object(appmod.filedialog,'asksaveasfilename',return_value=str(root/'manual'/'report.zip')),\
                 patch.object(appmod.messagebox,'askyesno',return_value=False),\
                 patch.object(appmod.messagebox,'showerror') as errors:
                gui=appmod.DeepThorTDesktop()
                try:
                    gui._set_project(project)
                    gui._export_diagnostics()
                    self.assertFalse(errors.called)
                    receipt=json.loads((state/'last-diagnostic-export.json').read_text())
                    self.assertTrue(Path(receipt['chosen_path']).is_file())
                    self.assertTrue(Path(receipt['retained_path']).is_file())
                    gui.input.insert('1.0','Test this milestone after build')
                    gui._queue_janus_instruction()
                    self.assertIn('primary ONNX',gui._council_status())
                    pending=gui.instruction_inbox.list(str(project))
                    self.assertEqual(pending[0]['state'],'pending')
                finally:gui._quit()

if __name__=='__main__':unittest.main()
