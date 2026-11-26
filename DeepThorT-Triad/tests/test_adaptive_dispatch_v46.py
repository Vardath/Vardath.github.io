"""V46 adaptive native admission fixtures and independent queue selection."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from triad_server import Pool
from deepthort_local.adaptive_admission import capacity,optional_ready,mandatory_ready,GIB
from deepthort_local.role_inbox import serial_rank
from deepthort_local.triad_profiles import PROFILES
from deepthort_local.triad_errors import WorkerFailure
from deepthort_local.job_queue import JobStore

def pool(sample):
    p=Pool(resource_sample=sample);p.worker_commit_limit=12*GIB
    p.children={r:(10,'secret',i+10,lambda:True) for i,r in enumerate(PROFILES)}
    p.memory_child=(10,'secret',20,lambda:True)
    p.activate_resident_pool()
    return p

class AdaptiveTests(unittest.TestCase):
    def test_slots_reserve_and_invalid_sample(self):
        for free,expected in [(3,0),(4,1),(5,2),(6,3),(7,4),(20,4)]:
            self.assertEqual(capacity((26*GIB,free*GIB,40*GIB)),expected)
        self.assertEqual(capacity(None),0)
        self.assertEqual(capacity((0,5*GIB,40*GIB)),0)
        self.assertEqual(capacity((26*GIB,41*GIB,40*GIB)),0)
    def test_aging_and_optional_slot_reservation(self):
        earlier=(0,1,'implementation');later=(90,2,'sentinel')
        self.assertTrue(mandatory_ready(set(),[earlier,later],earlier,1,serial_rank,90))
        self.assertFalse(mandatory_ready({'janus'},[earlier],earlier,1,serial_rank,90))
        self.assertFalse(optional_ready(set(),[earlier],4))
        self.assertFalse(optional_ready({'janus'},[],2))
        self.assertTrue(optional_ready({'janus'},[],3))
    def test_capacity_changes_without_evicting_running_role(self):
        free=[4*GIB]
        p=pool(lambda:(26*GIB,free[0],40*GIB))
        entered=threading.Event();release=threading.Event();second=threading.Event()
        errors=[]
        def fake(port,path,key,body,timeout):
            role=body['model']
            if role=='janus':
                entered.set()
                if not release.wait(6):raise RuntimeError('fixture timeout')
            else:second.set()
            return {'model':role,'choices':[{'message':{'content':'ok'}}]}
        def invoke(role):
            try:p.infer(role,[],2)
            except Exception as exc:errors.append(exc)
        a=threading.Thread(target=invoke,args=('janus',));b=threading.Thread(target=invoke,args=('sentinel',))
        with patch('triad_server.request',side_effect=fake):
            a.start()
            try:
                self.assertTrue(entered.wait(2));b.start()
                deadline=time.monotonic()+2
                while p.status(False)['admission_waiting']==0 and time.monotonic()<deadline:time.sleep(.02)
                self.assertEqual(p.status(False)['admission_slots'],1)
                self.assertFalse(second.is_set())
                with self.assertRaises(WorkerFailure):p.infer('memory',[],2)
                free[0]=6*GIB
                with p.admission_lock:
                    p.resource_sample_at=-float('inf');p.admission_lock.notify_all()
                self.assertTrue(second.wait(3))
                self.assertTrue(a.is_alive())
            finally:
                release.set();a.join(6)
                if b.ident:b.join(6)
        self.assertEqual(errors,[])
        self.assertEqual(p.generating,set())
        self.assertEqual(p.status(False)['admission_slots'],3)
    def test_native_pressure_latch_stays_serial_despite_headroom(self):
        p=pool(lambda:(26*GIB,20*GIB,40*GIB))
        answer={'model':'implementation','choices':[{'message':{'content':'ok'}}]}
        with patch('triad_server.request',side_effect=[WorkerFailure('memory_pressure'),answer]):
            self.assertEqual(p.infer('implementation',[],2),'ok')
        self.assertEqual(p.status(False)['admission_slots'],1)
        self.assertTrue(p.serial_memory_mode)
    def test_sample_failure_does_not_admit_optional_inference(self):
        def sample():raise OSError('fixture')
        p=pool(sample)
        self.assertEqual(p.status(False)['admission_slots'],0)
        with patch('triad_server.request') as request:
            with self.assertRaises(WorkerFailure):p.infer('memory',[],2)
            request.assert_not_called()
    def test_reserved_workspace_does_not_block_unrelated_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            jobs=JobStore(root/'jobs.sqlite3')
            first=jobs.submit(str(a),'a','build','Build first project')
            second=jobs.submit(str(b),'b','build','Build independent project')
            self.assertEqual(jobs.next_any_queued()['id'],first)
            self.assertEqual(jobs.next_any_queued(exclude_project=str(a.resolve()))['id'],second)
            self.assertEqual(jobs.get(first)['state'],'queued')
            self.assertIsNone(jobs.next_any_queued(skip_modes=('build',),exclude_project=str(a)))
            self.assertEqual(jobs.next_any_queued()['id'],first)

if __name__=='__main__':unittest.main()
