import os
import sys
import unittest
from pathlib import Path
from deepthort_local.mcp_stdio import prepare
from deepthort_local.mcp_stdio_probe import exercise

class StdioTests(unittest.TestCase):
    def test_refuse_bad_executable(self):
        with self.assertRaises(ValueError):prepare(Path.cwd(),'not-absolute.exe',[])
    @unittest.skipUnless(os.name=='nt','Windows')
    def test_refuse_credential_args(self):
        with self.assertRaises(ValueError):prepare(Path.cwd(),sys.executable,['--token=bad'])

if __name__=='__main__':unittest.main()
