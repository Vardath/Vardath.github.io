"""JANUS local coordination, approval boundary and bounded Sentinel watchdog."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.janus_engine import JanusStore
from deepthort_local.watchdog import JanusSentinel, SentinelStore
from deepthort_local.job_queue import JobStore
from janus_worker import JanusWorker


class JanusSentinelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.janus_path=self.root/'janus.sqlite3'
        self.sentinel_path=self.root/'sentinel.sqlite3'
        self.jobs_path=self.root/'jobs.sqlite3'
        self.games=self.root/'games.txt'
        self.games.write_text('game.exe\n')
        self.janus=JanusStore(self.janus_path)
        self.jobs=JobStore(self.jobs_path)

    def sentinel(self, **kw):
        return JanusSentinel(sentinel_db=self.sentinel_path,janus_db=self.janus_path,
            jobs_db=self.jobs_path,games_file=self.games,
            gui_heartbeat=self.root/'desktop-heartbeat.json',**kw)

    def test_explicit_approval_required_to_run_command(self):
        with self.assertRaises(PermissionError):
            self.janus.add_approved_action(argv=[sys.executable,'-V'],cwd=self.root,
                kind='tool',label='No approval')
        self.assertEqual(self.janus.actions(),[])

    def test_deterministic_cycles_preserve_prior_front_and_have_eleven_roles(self):
        self.jobs.submit('(general)','thread','chat','Test autonomous observer')
        first=self.janus.tick(self.jobs_path)
        second=self.janus.tick(self.jobs_path)
        self.assertEqual(len(first['cores']),11)
        self.assertEqual(second['cores']['Memory']['previous_front'],first['cores']['Front'])
        self.assertEqual(second['cores']['Interface']['autonomous_install'],False)
        self.assertEqual(self.janus.status()['cycle'],2)

    def test_approved_process_runs_once_and_saves_real_exit_evidence(self):
        output=self.root/'verified.txt'
        ident=self.janus.add_approved_action(argv=[sys.executable,'-c',
                f"from pathlib import Path;Path({str(output)!r}).write_text('verified')"],
                cwd=self.root,kind='verification',label='Safe test',user_approved=True)
        worker=JanusWorker(self.janus_path,self.jobs_path,self.games,game_probe=lambda:False)
        self.assertEqual(worker.execute_next_approved(),ident)
        self.assertTrue(output.exists())
        self.assertEqual(self.janus.action(ident)['status'],'succeeded')
        self.assertIsNone(worker.execute_next_approved())
        self.assertTrue(Path(self.janus.action(ident)['output_file']).exists())

    def test_watchdog_does_not_restart_a_live_but_stale_worker(self):
        sentinel=self.sentinel(worker_command=[sys.executable,'-c','import time;time.sleep(10)'],stall_after=.001)
        try:
            first=sentinel.step()
            self.assertIn(first['state'],('starting','restarting'))
            sentinel.last_healthy_monotonic=time.monotonic()-30
            second=sentinel.step()
            self.assertEqual(second['state'],'needs_attention')
            self.assertIn('NOT killed',second['detail'])
            self.assertEqual(second['janus_pid'],first['janus_pid'])
            self.assertTrue(any('NOT killed' in x['description'] for x in sentinel.store.events()))
        finally:sentinel.shutdown()

    def test_watchdog_limits_crash_restarts_and_escalates(self):
        sentinel=self.sentinel(worker_command=[sys.executable,'-c','raise RuntimeError("broken")'],
                               max_restarts=2,restart_window=600)
        try:
            sentinel.step()
            sentinel.worker.wait(timeout=5)
            sentinel.step()
            sentinel.worker.wait(timeout=5)
            third=sentinel.step()
            self.assertEqual(third['state'],'needs_attention')
            self.assertEqual(third['restart_count'],2)
            self.assertEqual(sum('restart limit' in x['description'] for x in sentinel.store.events()),1)
        finally:sentinel.shutdown()

    def test_watchdog_observes_model_loading_without_false_restart(self):
        (self.root/'desktop-heartbeat.json').write_text(json.dumps({'stamp':'2026-11-21T09:00',
            'model_loading':True,'model_loading_seconds':600}))
        sentinel=self.sentinel(worker_command=[sys.executable,'-c','import time;time.sleep(10)'])
        try:
            sentinel.step()
            state=sentinel.step()
            self.assertEqual(state['state'],'warning')
            self.assertIn('still loading',state['detail'])
            self.assertEqual(state['restart_count'],1)
        finally:sentinel.shutdown()

    def test_loading_warning_does_not_create_new_issue_each_second(self):
        sentinel=self.sentinel(worker_command=[sys.executable,'-c','import time;time.sleep(10)'])
        try:
            sentinel.step()  # start the supervised worker before measuring loading warnings
            first=None
            for elapsed in (250,260,310):
                (self.root/'desktop-heartbeat.json').write_text(json.dumps({
                    'stamp':'2026-11-21T10:00','model_loading':True,
                    'model_loading_seconds':elapsed}))
                snapshot=sentinel.step()
                self.assertIn('still loading',snapshot['detail'])
                if first is None:first=sentinel.store.recommendations()
            self.assertEqual(len(sentinel.store.recommendations()),len(first))
        finally:
            sentinel.shutdown()

    def test_recover_interrupted_actions_never_autoruns(self):
        ident=self.janus.add_approved_action(argv=[sys.executable,'-V'],cwd=self.root,
           kind='tool',label='Interrupted',user_approved=True)
        self.janus.claim_next_action()
        self.assertEqual(self.janus.recover_interrupted_actions(),1)
        self.assertEqual(self.janus.action(ident)['status'],'needs_attention')
        self.assertIsNone(self.janus.claim_next_action())

    def test_user_can_pause_and_stop_approved_action(self):
        self.janus.set_paused(True)
        ident=self.janus.add_approved_action(argv=[sys.executable,'-V'],cwd=self.root,
          kind='tool',label='Paused process',user_approved=True)
        worker=JanusWorker(self.janus_path,self.jobs_path,self.games,game_probe=lambda:False)
        self.assertIsNone(worker.execute_next_approved())
        self.assertTrue(self.janus.cancel_action(ident))
        self.janus.set_paused(False)
        self.assertIsNone(worker.execute_next_approved())
        self.assertEqual(self.janus.action(ident)['status'],'cancelled')

if __name__=='__main__':unittest.main()

# Keep tests above under discovery; standalone tests for stale GUI heartbeat.
class SentinelHeartbeatTests(unittest.TestCase):
    def test_missing_gui_heartbeat_pauses_janus_instead_of_silent_execution(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            j=JanusStore(root/'janus.sqlite3')
            worker=JanusSentinel(sentinel_db=root/'sentinel.sqlite3',
                  janus_db=root/'janus.sqlite3',jobs_db=root/'jobs.sqlite3',
                  games_file=root/'games.txt',gui_heartbeat=root/'not-available.json',
                  worker_command=[sys.executable,'-c','import time;time.sleep(10)'])
            try:
                worker.gui_missing_since=time.monotonic()-60
                worker.step()
                self.assertTrue(j.status()['paused'])
                self.assertTrue(any('heartbeat' in e['description'] for e in worker.store.events()))
            finally:worker.shutdown()

class SentinelInterruptedActionTests(unittest.TestCase):
    def test_worker_crash_does_not_respawn_over_unverified_tool(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            j=JanusStore(root/'janus.sqlite3')
            action=j.add_approved_action(argv=[sys.executable,'-V'],cwd=root,kind='tool',
                                         label='Might still be running',user_approved=True)
            j.claim_next_action()
            sent=JanusSentinel(sentinel_db=root/'sentinel.sqlite3',janus_db=root/'janus.sqlite3',
                  jobs_db=root/'jobs.sqlite3',games_file=root/'games.txt',
                  gui_heartbeat=root/'gui.json',
                  worker_command=[sys.executable,'-c','raise RuntimeError("worker failed")'])
            try:
                sent.step()
                sent.worker.wait(timeout=5)
                result=sent.step()
                self.assertEqual(result['state'],'needs_attention')
                self.assertIn('restart blocked',result['detail'])
                self.assertEqual(result['restart_count'],1)
                self.assertEqual(j.action(action)['status'],'running')
            finally:sent.shutdown()
