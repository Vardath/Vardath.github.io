import os
import sys
import unittest
from tempfile import TemporaryDirectory

from deepthort_local.win_cpu_cap import run_capped


@unittest.skipUnless(os.name == 'nt', 'Windows Job Object')
class WindowsBenchmarkTests(unittest.TestCase):
    def test_observer_sees_single_job_before_and_after_child(self):
        seen = []
        def observe(job, limit, finished):
            self.assertTrue(job)
            self.assertGreater(limit, 0)
            seen.append((job, limit, finished))
        with TemporaryDirectory() as tmp:
            result = run_capped([sys.executable, '-B', '-c', 'pass'], cwd=tmp, observe=observe)
        self.assertEqual(result, 0)
        self.assertFalse(seen[0][2])
        self.assertTrue(seen[-1][2])
        self.assertEqual(seen[0][:2], seen[-1][:2])
