import unittest
from deepthort_local.residency_wait import wait_residency


class Clock:
    def __init__(self, stop=False):
        self.t = 0
        self.stop = stop
        self.cancelled = False
    def __call__(self):
        return self.t
    def is_set(self):
        return self.cancelled
    def wait(self, seconds):
        self.t += seconds
        self.cancelled = self.stop
        return self.cancelled


class ResidencyWaitTests(unittest.TestCase):
    def run_case(self, samples, *, stop=False, alive=lambda: True, pid=42):
        clock = Clock(stop)
        events = []
        def validate(sample, expected):
            if not sample.get('valid'):
                raise ValueError('Invalid model records')
            return {'janus': {'name': 'fixture', 'pid': 43}}
        def health():
            return samples.pop(0) if len(samples)>1 else samples[0]
        models, result = wait_residency(health, pid, validate, alive=alive,
            cancelled=clock, notify=events.append, timeout=3, clock=clock)
        return models, result, clock.t, events

    def test_startup_then_ready(self):
        models, result, elapsed, events = self.run_case([None,
            {'pid':42,'ready':False}, {'pid':42,'ready':True,'valid':True}])
        self.assertEqual(result['status'],'passed')
        self.assertEqual(elapsed,2)
        self.assertEqual(len(events),1)
        self.assertEqual(models['janus']['pid'],43)

    def test_timeout_is_blocked(self):
        self.assertEqual(self.run_case([None])[1]['status'],'blocked')
        self.assertEqual(self.run_case([None])[2],3)

    def test_cancellation(self):
        self.assertEqual(self.run_case([None],stop=True)[1]['status'],'cancelled')

    def test_wrong_pid_never_accepted(self):
        self.assertEqual(self.run_case([{'pid':99,'ready':True,'valid':True}])[1]['status'],'blocked')

    def test_invalid_ready_records_not_accepted(self):
        self.assertEqual(self.run_case([{'pid':42,'ready':True}])[1]['status'],'blocked')

    def test_exited_and_absent(self):
        self.assertEqual(self.run_case([None],alive=lambda:False)[2],0)
        self.assertEqual(self.run_case([None],pid=None)[1]['status'],'blocked')

    def test_error_is_not_retried(self):
        self.assertEqual(self.run_case([{'pid':42,'error':'startup failed'}])[2],0)


if __name__=='__main__':
    unittest.main()
