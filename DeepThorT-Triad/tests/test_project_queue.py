import tempfile,unittest
from pathlib import Path
from deepthort_local.project_queue import QueuePolicy,inventory,grouped
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.job_queue import JobStore

class ProjectQueueTests(unittest.TestCase):
    def test_priority_and_hold_persist(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'q.sqlite3';q=QueuePolicy(path)
            q.sync([('A','x'),('A','y'),('B','z')])
            q.move('B',delta=-1,visible=['A','B']);q.move('A','y',delta=-1,visible=['x','y'])
            q.hold('B',held=True);q.hold('A','y',held=True)
            v=QueuePolicy(path).snapshot()
            self.assertFalse(v.allowed({'project':'B','chat_id':'z'}));self.assertFalse(v.allowed({'project':'A','chat_id':'y'}))
            self.assertLess(v.key({'project':'B','chat_id':'z','id':20}),v.key({'project':'A','chat_id':'x','id':1}))
            q.hold('B',held=False);q.hold('A','y',held=False);v=q.snapshot()
            self.assertLess(v.key({'project':'A','chat_id':'y','id':20}),v.key({'project':'A','chat_id':'x','id':1}))
    def test_real_job_dispatch_and_cooperative_hold(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);j=JobStore(root/'jobs.sqlite3');c=ConversationStore(root/'conversations.sqlite3');q=QueuePolicy(root/'priority.sqlite3')
            a=j.submit('A','x','image','first');b=j.submit('B','z','image','second')
            c.submit('y','A','draft_plan','next project task',independent=True)
            rows=inventory(c.path,j.path);q.sync((r['project'],r['chat_id']) for r in rows)
            q.move('B',delta=-1,visible=['A','B'])
            self.assertEqual(j.next_any_queued(priority=q.snapshot())['id'],b)
            j.change(b,'running','admitted',allowed=('queued',));q.hold('B','z',held=True)
            self.assertEqual(j.get(b)['state'],'running')
            j.change(b,'queued','next safe stage',allowed=('running',))
            self.assertEqual(j.next_any_queued(priority=q.snapshot())['id'],a)
            q.hold('A',held=True);self.assertIsNone(j.next_any_queued(priority=q.snapshot()))
            q.hold('B','z',held=False);self.assertEqual(j.next_any_queued(priority=q.snapshot())['id'],b)
            self.assertIn('y',grouped(rows,q.snapshot())['A'])
    def test_hidden_history_does_not_block_reorder(self):
        with tempfile.TemporaryDirectory() as td:
            q=QueuePolicy(Path(td)/'q.sqlite3');q.sync([('A','old'),('A','x'),('A','y')])
            q.move('A','y',delta=-1,visible=['x','y']);v=q.snapshot()
            self.assertLess(v.key({'project':'A','chat_id':'y'}),v.key({'project':'A','chat_id':'x'}))
            self.assertFalse(q.move('A','y',delta=-1,visible=['x','y']))
