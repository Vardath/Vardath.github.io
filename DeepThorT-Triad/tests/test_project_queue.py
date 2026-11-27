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

    def test_remove_restore_persists_and_never_deletes_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);folder=root/'project';folder.mkdir();(folder/'keep.txt').write_text('retain')
            p=str(folder);q=QueuePolicy(root/'priority.sqlite3')
            c=ConversationStore(root/'conversations.sqlite3');j=JobStore(root/'jobs.sqlite3')
            ident=c.submit('x',p,'draft_plan','keep this request',independent=True)
            job=j.submit(p,'x','image','keep this job')
            rows=inventory(c.path,j.path);q.sync((r['project'],r['chat_id']) for r in rows)
            q.sync([('other','y')]);q.remove(p)
            q=QueuePolicy(root/'priority.sqlite3');q.sync([(p,'x'),(p,'new')])
            v=q.snapshot();self.assertIn(p,v.removed);self.assertNotIn(p,grouped(rows,v))
            self.assertFalse(v.allowed({'project':p,'chat_id':'new'}))
            self.assertIsNone(j.next_any_queued(priority=v))
            self.assertEqual(c.get(ident)['state'],'pending');self.assertEqual(j.get(job)['state'],'queued')
            self.assertEqual((folder/'keep.txt').read_text(),'retain')
            with self.assertRaises(ValueError):q.hold(p,held=False)
            q.restore(p);v=q.snapshot()
            self.assertIn(p,grouped(rows,v));self.assertFalse(v.allowed({'project':p,'chat_id':'x'}))
            self.assertGreater(v.scope_key({'project':p}),v.scope_key({'project':'other'}))
            q.hold(p,held=False);self.assertEqual(j.next_any_queued(priority=q.snapshot())['id'],job)

    def test_migrate_existing_queue(self):
        import sqlite3
        from contextlib import closing
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'queue.sqlite3'
            with closing(sqlite3.connect(path)) as db,db:
                db.execute('CREATE TABLE project_priority(project TEXT PRIMARY KEY,position INTEGER NOT NULL,held INTEGER NOT NULL DEFAULT 0)')
                db.execute("INSERT INTO project_priority VALUES('old',1,0)")
            q=QueuePolicy(path);self.assertTrue(q.snapshot().allowed({'project':'old'}))
            q.remove('old');self.assertFalse(q.snapshot().allowed({'project':'old'}))
