"""v54: paused JANUS must be distinguished from a hung ONNX/cognitive worker."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from deepthort_local.janus_engine import JanusStore
from deepthort_local.watchdog import JanusSentinel
from deepthort_local.flight_recorder import _db_summary
from deepthort_local.latest_acceptance import load_test, ALLOWED, run_checks


class JanusCoreVisibilityTests(unittest.TestCase):
    def test_paused_flag_is_exported_in_privacy_bounded_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'janus.sqlite3'
            store=JanusStore(db)
            store.set_paused(True)
            status=_db_summary(db,'janus')['janus_status'][0]
            self.assertEqual(status['paused'],1)
            self.assertIn('cycle',status)
            self.assertNotIn('cores_json',status)

    def test_sentinel_does_not_report_paused_janus_as_hung(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            store=JanusStore(root/'janus.sqlite3')
            store.set_paused(True)
            sentinel=JanusSentinel(sentinel_db=root/'sentinel.sqlite3',
                janus_db=root/'janus.sqlite3',jobs_db=root/'jobs.sqlite3',
                games_file=root/'games.txt',gui_heartbeat=root/'heartbeat.json',
                worker_command=[sys.executable,'-c','import time;time.sleep(30)'],
                stall_after=.001)
            try:
                sentinel.step()
                sentinel.last_healthy_monotonic=time.monotonic()-100
                outcome=sentinel.step()
                self.assertEqual(outcome['state'],'paused')
                self.assertIn('resume',outcome['detail'].lower())
                self.assertFalse(any('cycle unchanged' in e['description'] for e in sentinel.store.events()))
            finally:
                sentinel.shutdown()

    def test_v54_manifest_includes_core_read_only_probe(self):
        base=Path(__file__).resolve().parents[1]
        definition=load_test(base/'LATEST_TEST.json')
        self.assertIn(definition['id'],('v54-dual-onnx-janus-core','v55-janus-instruction-handoff'))
        self.assertEqual(len(definition['checks']),7)
        self.assertIn('janus_core',definition['checks'])
        self.assertIn('janus_core',ALLOWED)
        report=run_checks({'schema':definition['schema'], 'id':'v54-mock',
                           'title':'JANUS pause test','checks':['janus_core']},
            {'janus_core':lambda:{'status':'blocked',
                'detail':'JANUS paused: Resume JANUS to continue',
                'evidence':{'janus_cycle':1473,'janus_paused':True}}})
        self.assertEqual(report['outcome'],'blocked')
        self.assertEqual(report['results'][0]['evidence']['janus_paused'],True)

@unittest.skipUnless(__import__('os').name=='nt' or __import__('os').environ.get('DISPLAY'),'Tk display required')
class JanusCoreGuiAcceptanceTests(unittest.TestCase):
    def test_latest_test_ui_reports_paused_coordinator_without_running_a_model(self):
        import desktop_app as app
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'LATEST_TEST.json').write_text(json.dumps({
                'schema':'deepthort-latest-test-v1','id':'v54-gui-paused',
                'title':'JANUS coordinator probe','checks':['janus_core']}))
            with patch.object(app,'ROOT',root),patch.object(app,'STATE',root/'state'),\
                 patch.object(app.DeepThorTDesktop,'_refresh_inventory',lambda self:None):
                gui=app.DeepThorTDesktop()
                try:
                    gui.janus.set_paused(True)
                    gui._run_latest_test()
                    deadline=time.monotonic()+20
                    while time.monotonic()<deadline and not gui._latest_test_last:
                        gui.update();time.sleep(.05)
                    self.assertIsNotNone(gui._latest_test_last)
                    self.assertEqual(gui._latest_test_last['outcome'],'blocked')
                    self.assertIn('PAUSED',gui._latest_test_last['results'][0]['detail'])
                    self.assertEqual(gui._latest_test_last['results'][0]['evidence']['janus_paused'],True)
                    self.assertTrue(list((root/'diagnostics').glob('*.zip')))
                finally:gui._quit()

if __name__=='__main__':unittest.main()
