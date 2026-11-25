import io
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from triad_server import Pool
from deepthort_local.triad_job import worker_budget,CONTROL_RESERVE_BYTES
from deepthort_local.triad_profiles import PROFILES
from deepthort_local.triad_errors import WorkerFailure,http_failure,native_error,WORDS
from deepthort_local.triad_acceptance import smoke

def make_pool():
    p=Pool();p.ready=True
    p.children={r:(10,'secret',i+10,lambda:True) for i,r in enumerate(PROFILES)}
    return p

class TriadInferenceRecovery(unittest.TestCase):
    def test_native_classification(self):
        self.assertEqual(native_error(RuntimeError('std::bad_alloc')),'memory_pressure')
        self.assertEqual(native_error(RuntimeError('wrong shape')),'native_error')
    def test_http_error_payload(self):
        e=HTTPError('http://localhost',500,'failure',{},io.BytesIO(b'{"code":"memory_pressure","detail":"bad_alloc"}'))
        f=http_failure(e,include_detail=True)
        self.assertEqual(f.code,'memory_pressure')
        self.assertEqual(f.detail,'bad_alloc')
    def test_memory_retry_exclusive_and_resident(self):
        p=make_pool();answer={'model':'implementation','choices':[{'message':{'content':'ok'}}]}
        with patch('triad_server.request',side_effect=[WorkerFailure('memory_pressure'),answer]) as req:
            self.assertEqual(p.infer('implementation',[],2),'ok')
            self.assertEqual(req.call_count,2)
        self.assertTrue(p.healthy())
        self.assertTrue(p.serial_memory_mode)
        self.assertEqual(p.memory_retries,1)
        self.assertEqual(p.generating,set())
    def test_no_unlimited_retry_or_nonmemory_retry(self):
        for code,n in [('memory_pressure',2),('native_error',1)]:
            p=make_pool()
            with patch('triad_server.request',side_effect=WorkerFailure(code)) as req:
                with self.assertRaises(WorkerFailure):p.infer('janus',[],2)
                self.assertEqual(req.call_count,n)
            self.assertEqual(p.generating,set())
    def test_serial_mode_waits_for_native_generation(self):
        p=make_pool();p.serial_memory_mode=True
        entered=threading.Event();release=threading.Event();second=threading.Event()
        def request(port,path,key,body,timeout):
            role=body['model']
            if role=='janus':
                entered.set()
                if not release.wait(4):raise RuntimeError('test timeout')
            else:second.set()
            return {'model':role,'choices':[{'message':{'content':'ok'}}]}
        with patch('triad_server.request',side_effect=request):
            a=threading.Thread(target=p.infer,args=('janus',[],2));b=threading.Thread(target=p.infer,args=('sentinel',[],2))
            a.start()
            try:
                self.assertTrue(entered.wait(2));b.start()
                self.assertFalse(second.wait(.1))
            finally:
                release.set();a.join(4)
                if b.ident:b.join(4)
            self.assertTrue(second.is_set())
    def test_acceptance_records_individual_and_concurrent_errors(self):
        p=make_pool()
        def ask(role,word):
            if role=='janus':raise WorkerFailure('native_error','fixed synthetic detail')
            return word
        result,overlap=smoke(lambda:p.status(False),ask,p.status(False)['pid'],threading.Event())
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['evidence']['individual_results']['janus']['error']['code'],'native_error')
        self.assertEqual(result['evidence']['concurrent_results']['janus']['error']['detail'],'fixed synthetic detail')
        self.assertFalse(overlap)

    def test_serial_recovery_does_not_certify_concurrency(self):
        p=make_pool();p.serial_memory_mode=True
        result,overlap=smoke(lambda:p.status(False),lambda role,word:word,p.status(False)['pid'],threading.Event())
        self.assertEqual(result['status'],'passed')
        self.assertTrue(result['evidence']['serial_memory_mode'])
        self.assertFalse(overlap)

    def test_protected_by_default(self):
        p=make_pool()
        self.assertTrue(p.serial_memory_mode)
        self.assertEqual(p.status(False)['control_reserve_bytes'],1024**3)
    def test_worker_budget_preserves_control_reserve(self):
        self.assertEqual(worker_budget(14*1024**3),13*1024**3)
        with self.assertRaises(RuntimeError):worker_budget(CONTROL_RESERVE_BYTES)
