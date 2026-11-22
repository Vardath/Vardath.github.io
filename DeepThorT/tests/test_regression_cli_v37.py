"""v37 regression harness must not hang when a test spawns a child."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from regression_cli import run_isolated


class IsolationTests(unittest.TestCase):
    def test_normal_subprocess_exits_and_reports(self):
        code,out,timed_out=run_isolated([sys.executable,'-c','print("done")'],
                                        cwd=Path.cwd(),env=os.environ.copy(),timeout=4)
        self.assertFalse(timed_out)
        self.assertEqual(code,0)
        self.assertIn('done',out)

    @unittest.skipIf(os.name=='nt','Linux process-group behavior; Windows uses taskkill')
    def test_timeout_kills_child_processes_holding_output_pipe(self):
        # Child inherits output, which previously kept communicate() blocked even
        # after the xvfb-run wrapper was killed by subprocess.run.
        program='import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time; time.sleep(45)"]); time.sleep(45)'
        code,out,timed_out=run_isolated([sys.executable,'-c',program],
                                        cwd=Path.cwd(),env=os.environ.copy(),timeout=.4)
        self.assertTrue(timed_out)
        self.assertNotEqual(code,0)
