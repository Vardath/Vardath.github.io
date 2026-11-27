import unittest
from deepthort_local import execution_isolation as tool

class IsolationTests(unittest.TestCase):
    def test_fixed_profile_and_exact_evidence(self):
        self.assertEqual(tool.checked({'probe':'single_process'})['probe'],'single_process')
        for mode in ('spawn_refused','child_terminated'):
            r=tool.assess(tool.CHILD_MARKER,'JANUS_PROCESS_LIMIT '+mode)
            self.assertTrue(r['descendant_execution_blocked_in_probe'])
            self.assertFalse(r['security_sandbox'])
        for bad in ('',tool.CHILD_MARKER,'JANUS_PROCESS_LIMIT spawn_refused\nextra'):
            with self.assertRaises(ValueError):tool.assess(tool.CHILD_MARKER,bad)
        with self.assertRaises(ValueError):tool.assess('', 'JANUS_PROCESS_LIMIT spawn_refused')
        with self.assertRaises(ValueError):tool.checked({'probe':'single_process','command':'other'})

    def test_ci_pressure_retry_requires_real_pass(self):
        calls=[];pauses=[]
        def probe():
            calls.append(1)
            if len(calls)<3:raise tool.HostPressure('busy')
            return {'verified':True}
        self.assertEqual(tool.retry_native_ci(probe,sleep=pauses.append),{'verified':True})
        self.assertEqual(pauses,[5,10])
        def failed():raise ValueError('incorrect isolation evidence')
        with self.assertRaises(ValueError):tool.retry_native_ci(failed,sleep=lambda _:self.fail('not retryable'))
        def pressured():raise tool.HostPressure('busy')
        pauses.clear()
        with self.assertRaises(tool.HostPressure):tool.retry_native_ci(pressured,sleep=pauses.append)
        self.assertEqual(pauses,[5,10,15,20])

if __name__=='__main__':unittest.main()
