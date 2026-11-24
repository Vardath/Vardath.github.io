import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.repository_index import RepositoryIndex
from deepthort_local.agent_repository_tools import RepositoryTools,gather
from deepthort_local.agent_tool_receipts import ToolReceipts
from deepthort_local.reasoning_council import sha
from deepthort_local.source_checkpoints import SourceCheckpoints

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);self.root=base/'project';self.root.mkdir()
        self.file=self.root/'main.py';self.file.write_text('def buy(): return 1\n')
        self.index=RepositoryIndex(base/'index.sqlite');self.index.refresh(self.root)
        self.store=ToolReceipts(base/'receipts.sqlite')
        self.cp=SourceCheckpoints(base/'checkpoints')
        self.job={'id':1,'mode':'build','project':str(self.root),'chat_id':'chat','approval_key':'draft:1'}
        self.steps=[{'id':1,'sequence':1,'path':'main.py','description':'Implement purchase'}]
        self.cp.capture(self.job,self.steps,'approval_baseline',baseline=True)
    def test_durable_observed_and_delivered(self):
        council=Mock()
        council._run.side_effect=['{"tool":"search","args":{"query":"buy"}}','{"tool":"done","args":{}}']
        text=gather(RepositoryTools(self.index,self.root),council,None,session='test',
            original='Buy goods',goal='Find buy',budget=1000,receipts=self.store,job_id=1)
        self.assertIn('main.py',text)
        rows=ToolReceipts(self.store.path).recent(1,self.root)
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['delivered'])
        self.assertEqual(rows[0]['spec_sha'],sha('Buy goods'))
        self.assertEqual(self.store.recent(2,self.root),[])
        self.assertIn('Historical',self.store.describe(1,self.root))
    def test_checkpoint_diff_is_read_only_and_current(self):
        self.file.write_text('def buy(): return 2\n');self.index.refresh(self.root)
        tools=RepositoryTools(self.index,self.root,baseline=lambda p:self.cp.comparison_baseline(self.job,self.steps,p))
        req={'tool':'checkpoint_diff','args':{'path':'main.py'}}
        result=tools.execute(req);self.assertIn('-def buy(): return 1',result['items'][0]['preview'])
        self.assertIn('+def buy(): return 2',result['items'][0]['preview'])
        self.assertTrue(tools.valid(result,req))
        self.assertEqual(self.file.read_text(),'def buy(): return 2\n')
        self.file.write_text('def buy(): return 3\n')
        self.assertFalse(tools.valid(result,req))
    def test_diagnostic_changes_invalidate_and_unavailable_tools_rejected(self):
        value=['AssertionError: expected 1']
        tools=RepositoryTools(self.index,self.root,diagnostic=lambda:value[0])
        req={'tool':'diagnostics','args':{}}
        result=tools.execute(req);self.assertTrue(tools.valid(result,req))
        value[0]='AssertionError: expected 2'
        self.assertFalse(tools.valid(result,req))
        with self.assertRaises(ValueError):RepositoryTools(self.index,self.root).execute(req)
    def test_corrupt_receipt_refused(self):
        import sqlite3
        self.store.record(job_id=1,project=self.root,spec_sha=sha('spec'),session='test',turn=0,
            request={'tool':'search','args':{'query':'buy'}},result={'tool':'search','items':[]})
        with sqlite3.connect(self.store.path) as db:db.execute("UPDATE agent_tool_receipts SET payload='{}'")
        with self.assertRaises(ValueError):self.store.recent(1,self.root)
if __name__=='__main__':unittest.main()
