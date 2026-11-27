import hashlib
import tempfile
import unittest
from pathlib import Path
from deepthort_local.debug_evidence import candidates
from deepthort_local.agent_repository_tools import RepositoryTools
class DebugTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.source=self.root/'app.py';self.source.write_bytes(b'def run():\n    return 1 / 0\n')
        self.rows={'app.py':(hashlib.sha256(self.source.read_bytes()).hexdigest(),None)}
        self.log='Traceback (most recent call last):\n  File "app.py", line 2, in run\nZeroDivisionError: division by zero'
    def test_exact_current_frame(self):
        r=candidates(self.root,self.log,self.rows)
        self.assertEqual(r[0]['source'],'    return 1 / 0');self.assertEqual(r[0]['line'],2)
        self.assertIn('unverified',r[0]['scope'])
    def test_absolute_and_no_guessing(self):
        log='  File "'+str(self.source)+'", line 2, in run'
        self.assertEqual(candidates(self.root,log,self.rows)[0]['path'],'app.py')
        self.assertEqual(candidates(self.root,'  File "elsewhere/app.py", line 2, in run',self.rows),[])
        self.assertEqual(candidates(self.root,self.log,self.rows,{'app.py'}),[])
    def test_agent_current_evidence_and_invalidation(self):
        rows=self.rows
        class Index:
            def _current_rows(self,*a):return rows
        tools=RepositoryTools(Index(),self.root,diagnostic=lambda:self.log)
        req={'tool':'diagnostics','args':{}}
        r=tools.execute(req)
        self.assertEqual(r['items'][1]['path'],'app.py')
        self.assertTrue(tools.valid(r,req))
        self.source.write_bytes(b'changed\n')
        self.assertFalse(tools.valid(r,req))
        self.assertEqual(len(tools.execute(req)['items']),1)
