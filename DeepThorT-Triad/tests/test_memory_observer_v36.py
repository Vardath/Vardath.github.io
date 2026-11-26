import unittest
from unittest.mock import patch
from deepthort_local.memory_observer_probe import exercise
from deepthort_local.memory_observer import MemoryObserver
from deepthort_local.triad_errors import WorkerFailure
from triad_server import Pool

class ObserverTests(unittest.TestCase):
    def test_delayed_recall_and_late_scoped_delivery(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)

    def test_cancelled_request_never_calls_model(self):
        def fail(*a):raise AssertionError('Cancelled observation must not infer')
        observer=MemoryObserver(path='unused',select=fail,available=lambda:False)
        try:
            observer.observe(project='p',chat_id='c',original='spec',focus='step',
                             phase='implementation',cancelled=lambda:True)
            self.assertIsNone(observer._thread)
        finally:observer.close()

    def test_serial_mode_admits_required_memory(self):
        p=Pool()
        p.ready=True
        from deepthort_local.triad_profiles import PROFILES
        p.children={r:(1,'key',42+i,lambda:True) for i,r in enumerate(PROFILES)}
        p.memory_child=(1,'key',50,lambda:True)
        self.assertTrue(p.serial_memory_mode)
        with patch('triad_server.request',return_value={'model':'memory','choices':[{'message':{'content':'recalled'}}]}) as call:
            self.assertEqual(p.infer('memory',[],32),'recalled')
            call.assert_called_once()
        self.assertEqual(p.memory_retries,0)
        self.assertTrue(p.healthy())

    def test_resource_deferral_retries_same_admitted_observation(self):
        import json,tempfile,threading,time
        from pathlib import Path
        from deepthort_local.job_queue import JobStore
        from deepthort_local.reasoning_council import sha
        with tempfile.TemporaryDirectory() as tmp:
            jobs=JobStore(Path(tmp)/'jobs.sqlite3')
            project=str(Path(tmp)/'game');original='Build game and preserve ship ownership.'
            old=jobs.submit(project,'c','plan',original)
            current=jobs.submit(project,'c','plan',original)
            note='Regression: ship ownership changes during load.'
            jobs.remember(old,'verification','ship ownership',sha(original),sha(note),note)
            called=[];published=threading.Event();deferred=threading.Event()
            def select(evidence,prompt,tokens):
                called.append(evidence)
                if len(called)==1:raise WorkerFailure('memory_pressure')
                rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
                return json.dumps({'keep':[r['id'] for r in rows if r['observation']==note],'reason':'Recorded failure'})
            def report(event,**kw):
                if event=='memory_observer_deferred':deferred.set()
                if event=='memory_observer_findings':published.set()
            observer=MemoryObserver(path=jobs.path,select=select,available=lambda:True,report=report)
            params=dict(project=project,chat_id='c',original=original,focus='ship ownership during load',phase='implementation',job_id=current)
            with patch('deepthort_local.memory_observer.DEFER_RETRY',.01):
                try:
                    observer.observe(**params)
                    self.assertTrue(deferred.wait(3))
                    self.assertTrue(published.wait(5))
                    self.assertEqual(len(called),2)
                    self.assertEqual(called[0],called[1])
                finally:
                    observer.close()
                    if observer._thread:observer._thread.join(3)

if __name__=='__main__':
    unittest.main()
