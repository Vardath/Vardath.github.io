"""DeepThorT v10 canonical recursive societies and supervisory boundary checks."""
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from deepthort_local.janus_cognition import (CORE_NAMES,FACULTIES,FANO_LINES,
    SenseFrame,process_society)
from deepthort_local.janus_engine import JanusStore
from deepthort_local.job_queue import JobStore
from deepthort_local.watchdog import JanusSentinel,SentinelStore
from deepthort_local.janus_counsel import LocalCounsel
from janus_worker import JanusWorker


class RecursiveSocietyContract(unittest.TestCase):
    def test_every_core_contains_seven_fano_faculties(self):
        result=process_society(society='janus',observation={'counts':{'queued':1}},
            frames=[SenseFrame('runtime','unit_test','queued:1')],focus='queued_work',
            decision='monitor',goal='Make a working game')
        self.assertEqual(len(result['cores']),11)
        for name in CORE_NAMES:
            self.assertEqual(set(result['cores'][name]['internal_fano_faculties']),
                             set(str(i) for i in FACULTIES))
            self.assertTrue(result['cores'][name]['recursive_janus'])
        self.assertEqual(result['cores']['Left']['source_roles'],list(CORE_NAMES[:7]))
        self.assertEqual(result['cores']['Right']['source_roles'],list(CORE_NAMES[:7]))
        self.assertEqual(result['cores']['Front']['input_sources'],['Left','Right'])
        self.assertEqual(result['cores']['Interface']['input_sources'],['Front'])
        self.assertFalse(result['cores']['Interface']['may_execute_without_approval'])
        self.assertEqual(len(FANO_LINES),7)
        self.assertTrue(all(a^b==c or a^c==b or b^c==a for a,b,c in FANO_LINES))

    def test_frames_bounded_and_modalities_governed(self):
        with self.assertRaises(ValueError):SenseFrame('internet','test','not allowed')
        frame=SenseFrame('runtime','test','a'*10000,salience=20,uncertainty=-2)
        self.assertEqual(len(frame.content),2500)
        self.assertEqual(frame.salience,1)
        self.assertEqual(frame.uncertainty,0)

    def test_history_changes_only_through_new_sensing(self):
        obs={'counts':{'failed':1},'failed':True}
        old=process_society(society='janus',observation=obs,
             frames=[SenseFrame('runtime','unit','failed')],focus='failure',decision='repair',
             alternatives=['Inspect log'])
        new=process_society(society='janus',observation=obs,
             previous_front=old['cores']['Front'],previous_observation=obs,
             frames=[SenseFrame('runtime','unit','failed')],focus='failure',decision='repair',
             alternatives=['Inspect log'])
        self.assertFalse(new['cores']['Front']['evidence_changed'])
        self.assertEqual(new['cores']['Memory']['previous_front'],old['cores']['Front'])
        self.assertEqual(new['cores']['Interface']['input_sources'],['Front'])


class PersistentCoordinators(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.janus_path=self.root/'janus.sqlite3'
        self.sentinel_path=self.root/'sentinel.sqlite3'
        self.jobs_path=self.root/'jobs.sqlite3'
        self.games=self.root/'games.txt'
        self.games.write_text('game.exe\n')
        self.janus=JanusStore(self.janus_path)
        self.jobs=JobStore(self.jobs_path)

    def sentinel(self,**kwargs):
        return JanusSentinel(sentinel_db=self.sentinel_path,janus_db=self.janus_path,
            jobs_db=self.jobs_path,games_file=self.games,gui_heartbeat=self.root/'gui.json',
            worker_command=[sys.executable,'-c','import time;time.sleep(20)'],**kwargs)

    def test_goal_and_recursive_memory_survive_reopening_database(self):
        self.janus.set_goal('Create Faction Command according to existing specifications')
        first=self.janus.tick(self.jobs_path)
        second=JanusStore(self.janus_path).tick(self.jobs_path)
        self.assertEqual(JanusStore(self.janus_path).goal(),
                         'Create Faction Command according to existing specifications')
        self.assertEqual(second['cores']['Memory']['previous_front'],first['cores']['Front'])
        self.assertEqual(len(second['cores']['Interface']['internal_fano_faculties']),7)

    def test_real_failure_proposes_repair_but_never_reruns(self):
        ident=self.jobs.submit('workspace','chat1','build','Write a game')
        self.jobs.change(ident,'failed','Compilation failed: missing namespace')
        first=self.janus.tick(self.jobs_path)
        self.assertEqual(first['decision'],'diagnose_failure_and_propose_alternatives')
        self.assertEqual(len(self.janus.recommendations()),1)
        self.janus.tick(self.jobs_path)
        self.assertEqual(len(JanusStore(self.janus_path).recommendations()),1)
        self.assertFalse(self.janus.actions())
        self.assertIn('Compilation failed',self.janus.recommendations()[0]['problem'])

    def test_previous_failed_job_does_not_steal_focus_from_new_work(self):
        old=self.jobs.submit('workspace','chat1','build','Old project')
        self.jobs.change(old,'failed','Old failure')
        new=self.jobs.submit('workspace','chat2','build','New project')
        state=self.janus.tick(self.jobs_path)
        self.assertEqual(state['decision'],'wait_for_local_model_and_dispatch')
        self.assertEqual(self.janus.status()['last_focus'],'queued_work')
        self.assertTrue(self.janus.recommendations())
        self.assertEqual(self.jobs.get(new)['state'],'queued')

    def test_sentinel_has_independent_durable_eleven_core_state(self):
        worker=self.sentinel()
        try:
            worker.step()
            before=self.janus.status()['cycle']
            doc=SentinelStore(self.sentinel_path).snapshot()
            cores=json.loads(doc['society_json'])['cores']
            self.assertEqual(len(cores),11)
            self.assertEqual(sum(len(c['internal_fano_faculties']) for c in cores.values()),77)
            self.assertEqual(cores['Interface']['input_sources'],['Front'])
            self.assertEqual(before,self.janus.status()['cycle'])
            self.assertEqual(json.loads(doc['society_json'])['society'],'sentinel')
        finally:worker.shutdown()

    def test_sentinel_detects_main_coordinator_off_task(self):
        self.janus.tick(self.jobs_path)
        self.janus.tick(self.jobs_path)
        self.jobs.submit('workspace','chat1','build','Build game')
        worker=self.sentinel()
        try:
            worker.step()
            self.assertEqual(worker.store.snapshot()['focus'],'task_drift')
            self.assertIn('off-task',worker.store.recommendations()[0]['finding'])
            self.assertEqual(self.jobs.count('workspace')['queued'],1)
            self.assertFalse(self.janus.actions())
        finally:worker.shutdown()

    def test_sentinel_reports_progress_stall_without_stopping_process(self):
        ident=self.jobs.submit('workspace','chat1','build','Write game')
        self.jobs.change(ident,'running','Generating code')
        old=(datetime.now(timezone.utc)-timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        with closing(sqlite3.connect(self.jobs_path)) as db, db:
            db.execute('UPDATE jobs SET updated_at=? WHERE id=?',(old,ident))
        worker=self.sentinel(work_stall_after=120)
        try:
            worker.step()  # Sentinel launches the capped JANUS child first.
            status=worker.step()  # Then can assess running-process stalls.
            self.assertEqual(status['state'],'warning')
            self.assertIn('no recorded progress',status['detail'])
            self.assertIsNone(worker.worker.poll())
            self.assertEqual(self.jobs.get(ident)['state'],'running')
        finally:worker.shutdown()

    def test_stable_warn_does_not_generate_infinite_new_proposals(self):
        self.janus.tick(self.jobs_path)
        self.janus.tick(self.jobs_path)
        self.jobs.submit('workspace','chat1','build','Build something')
        worker=self.sentinel()
        try:
            worker.step();worker.step();worker.step()
            self.assertEqual(len(worker.store.recommendations(50)),1)
            self.assertLessEqual(worker.store.snapshot()['cycle'],2)
        finally:worker.shutdown()

    def test_local_counsel_has_role_exclusive_leases_and_never_claims_remote_models(self):
        adviser=LocalCounsel(self.root/'counsel.sqlite3')
        # The intentionally replaced global singleton must no longer
        # prevent separate resident roles from reasoning concurrently.
        self.assertTrue(adviser._acquire('janus:one'))
        self.assertTrue(adviser._acquire('sentinel:two'))
        self.assertFalse(adviser._acquire('janus:three'))
        self.assertFalse(adviser._acquire('sentinel:three'))
        adviser._release('janus:one')
        self.assertTrue(adviser._acquire('janus:three'))
        self.assertFalse(adviser._acquire('sentinel:three'))
        adviser._release('janus:three')
        adviser._release('sentinel:two')
        with self.assertRaises(ValueError):
            adviser.request(society='cloud',goal='a',problem='x',evidence='x')

    def test_first_local_counsel_runs_after_fresh_boot(self):
        ident=self.jobs.submit('workspace','chat1','build','Make a game')
        self.jobs.change(ident,'failed','Build failed: no Godot')
        # New hosts can have a monotonic clock value below the five-minute
        # cooldown. That must not postpone the very first request.
        with patch('janus_worker.time.monotonic',return_value=15.0):
            worker=JanusWorker(self.janus_path,self.jobs_path,self.games,
                game_probe=lambda:False)
            with patch.object(worker._counsel,'request',return_value='Check Godot setup'):
                worker.observe_once()
                self.assertIsNotNone(worker._counsel_thread)
                worker._counsel_thread.join(timeout=4)
                self.assertFalse(worker._counsel_thread.is_alive())
        self.assertTrue(any(x['origin']=='local_model' for x in self.janus.recommendations()))
        self.assertFalse(self.janus.actions())

    def test_worker_background_counsel_is_only_advice(self):
        ident=self.jobs.submit('workspace','chat1','build','Make a game')
        self.jobs.change(ident,'failed','Build failed: no Godot')
        worker=JanusWorker(self.janus_path,self.jobs_path,self.games,game_probe=lambda:False)
        with patch.object(worker._counsel,'request',return_value='Use installed Godot and run a syntax check'):
            worker.observe_once()
            if worker._counsel_thread:worker._counsel_thread.join(timeout=4)
        items=self.janus.recommendations()
        self.assertTrue(any(x['origin']=='local_model' for x in items))
        self.assertFalse(self.janus.actions())


if __name__=='__main__':unittest.main()
