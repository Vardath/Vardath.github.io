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

if __name__=='__main__':
    unittest.main()
