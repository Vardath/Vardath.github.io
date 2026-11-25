"""v53 latest test manifest, results, safety and actual desktop entry point."""
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.latest_acceptance import (
    ALLOWED, SCHEMA, LatestTestError, load_test, run_checks,
    save_result, report_summary, check_record)


class LatestTestDefinitionTests(unittest.TestCase):
    def test_current_definition_is_strictly_supported(self):
        base=Path(__file__).resolve().parents[1]
        definition=load_test(base/'LATEST_TEST.json')
        self.assertEqual(definition['schema'],SCHEMA)
        self.assertIn('council_inference',definition['checks'])
        self.assertLess(definition['checks'].index('council_inference'),
                        definition['checks'].index('concurrent_status'))
        self.assertLessEqual(len(definition['checks']),10)

    def test_manifest_update_changes_checks_without_source_change(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'LATEST_TEST.json'
            path.write_text(json.dumps(dict(schema=SCHEMA,id='future-release',
                 title='Future smoke check', checks=['primary_onnx','janus_inbox'])))
            checks=load_test(path)
            result=run_checks(checks,{key:lambda:{'status':'passed','detail':'ready'} for key in ALLOWED})
            self.assertEqual([r['check'] for r in result['results']],['primary_onnx','janus_inbox'])
            self.assertEqual(result['outcome'],'passed')

    def test_arbitrary_command_url_and_unknown_adapters_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'LATEST_TEST.json'
            data=dict(schema=SCHEMA,id='sample',title='Test',checks=['primary_onnx'])
            for malformed in [dict(data,command='powershell -c del C:'),
                              dict(data,checks=['execute_shell']),
                              dict(data,checks=['primary_onnx','primary_onnx']),
                              dict(data,checks=[]),dict(data,checks=['http://example.com'])]:
                with self.subTest(item=malformed):
                    path.write_text(json.dumps(malformed))
                    with self.assertRaises(LatestTestError):load_test(path)

    def test_per_probe_failure_does_not_hide_remaining_probes(self):
        d=dict(schema=SCHEMA,id='retry',title='Retry',checks=['primary_onnx','janus_inbox'])
        def broken():raise RuntimeError('Model disconnected')
        found=run_checks(d,{'primary_onnx':broken,
                             'janus_inbox':lambda:{'status':'passed','detail':'saved'}})
        self.assertEqual(found['outcome'],'failed')
        self.assertEqual([r['status'] for r in found['results']],['failed','passed'])
        self.assertIn('Model disconnected',found['results'][0]['detail'])

    def test_cancel_never_reports_completed_success(self):
        cancel=threading.Event()
        d=dict(schema=SCHEMA,id='cancel',title='Cancel',checks=['primary_onnx','council_onnx'])
        def first():cancel.set();return {'status':'passed','detail':'first'}
        found=run_checks(d,{'primary_onnx':first,'council_onnx':lambda:self.fail('cancel ignored')},
                         cancelled=cancel)
        self.assertEqual(found['outcome'],'cancelled')
        self.assertEqual(found['results'][1]['status'],'cancelled')

    def test_report_atomic_and_no_untrusted_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            result=run_checks(dict(schema=SCHEMA,id='safe',title='Safe',checks=['shared_cap']),
                {'shared_cap':lambda:{'status':'passed','detail':'member',
                                     'evidence':{'pid':100,'secret':'must not persist'}}})
            out=save_result(Path(td)/'state',result)
            data=json.loads(out.read_text())
            self.assertEqual(data['results'][0]['evidence'],{'pid':100})
            self.assertEqual(json.loads((out.parent/'latest.json').read_text()),data)
            self.assertIn('PASSED',report_summary(data))
            self.assertTrue(out.name.startswith('LatestTest-'))

    def test_unavailable_inference_must_not_be_called_by_manifest(self):
        with self.assertRaises(LatestTestError):
            run_checks(dict(schema=SCHEMA,id='future',title='Future',checks=['council_inference']),{})


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Tk display required')
class LatestTestGuiTests(unittest.TestCase):
    def test_single_button_generates_report_and_verified_zip_without_user_dialog(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);state=root/'state';root.joinpath('LATEST_TEST.json').write_text(json.dumps({
              'schema':SCHEMA,'id':'mock-v53','title':'v53 local click acceptance',
              'checks':['shared_cap','janus_inbox']}))
            with patch.object(m,'STATE',state),patch.object(m,'ROOT',root),\
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                 patch.object(m.messagebox,'showerror') as errors,\
                 patch.object(m.filedialog,'asksaveasfilename') as savebox,\
                 patch('deepthort_local.quiet_playtest.is_capped_windows_process',return_value=True):
                gui=m.DeepThorTDesktop()
                try:
                    gui._run_latest_test()
                    self.assertEqual(gui.tabs.tab(gui.tabs.select(),'text'),'Processes')
                    deadline=time.monotonic()+20
                    while time.monotonic()<deadline and (not gui._latest_test_last):
                        gui.update();time.sleep(.05)
                    self.assertIsNotNone(gui._latest_test_last)
                    self.assertEqual(gui._latest_test_last['outcome'],'inconclusive')
                    self.assertIn('no instruction has been submitted',str(gui._latest_test_last['results']))
                    zip_path=next((root/'diagnostics').glob('DeepThorT-LatestTest-*.zip'))
                    self.assertTrue(zip_path.is_file())
                    from deepthort_local.flight_recorder import verify_diagnostics_archive
                    self.assertEqual(verify_diagnostics_archive(zip_path)['path'],str(zip_path.resolve()))
                    receipt=json.loads((state/'last-diagnostic-export.json').read_text())
                    self.assertEqual(receipt['retained_path'],str(zip_path.resolve()))
                    self.assertTrue((state/'latest-tests'/'latest.json').is_file())
                    self.assertFalse(savebox.called)
                    self.assertFalse(errors.called)
                finally:gui._quit()

if __name__=='__main__':unittest.main()
