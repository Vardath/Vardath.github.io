import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore, ChatRegistry

class JobPersistenceTests(unittest.TestCase):
    def test_lifecycle_and_stable_order(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'jobs.db'; db=JobStore(p)
            a=db.submit('p','chat1','chat','first')
            b=db.submit('p','chat2','edit','second','src/a.py')
            self.assertEqual(db.next_queued('p')['id'],a)
            self.assertTrue(db.change(a,'running','Model is generating',allowed=('queued',)))
            self.assertEqual(db.next_queued('p')['id'],b)
            self.assertTrue(db.cancel(b))
            self.assertIsNone(db.next_queued('p'))
            self.assertFalse(db.change(b,'complete','Should not complete',allowed=('running',)))
            self.assertEqual(JobStore(p).get(a)['state'],'paused')
            self.assertTrue(db.resume(a))
            self.assertTrue(db.change(a,'running','Started',allowed=('queued',)))
            self.assertTrue(db.change(a,'responded','Answer saved',result='hello',allowed=('running',)))
            self.assertEqual(db.get(a)['result'],'hello')
            self.assertEqual(len(db.events(a)),5)
    def test_intervention(self):
        with tempfile.TemporaryDirectory() as td:
            j=JobStore(Path(td)/'j.db').submit('p','chat','plan','Plan my app')
            store=JobStore(Path(td)/'j.db')
            store.change(j,'needs_input','Which platform?',allowed=('queued',))
            self.assertTrue(store.resume(j))
            self.assertEqual(store.next_queued('p')['id'],j)
    def test_large_request_preserved_not_silently_truncated(self):
        with tempfile.TemporaryDirectory() as td:
            store=JobStore(Path(td)/'j.db')
            ident=store.submit('p','c','chat','x'*9000)
            self.assertEqual(len(store.get(ident)['prompt']),9000)
            larger=store.submit('p','c','chat','x'*250001)
            self.assertEqual(len(store.get(larger)['prompt']),250001)
    def test_threads_isolated(self):
        with tempfile.TemporaryDirectory() as td:
            reg=ChatRegistry(Path(td)/'c.db')
            x=reg.create('p','A'); y=reg.create('p','B'); reg.create('q','Other')
            self.assertEqual([t[0] for t in reg.list('p')],[x,y])
            reg.rename(y,'Renamed');self.assertEqual(reg.list('p')[1][1],'Renamed')
            reg.delete(x,'p');self.assertEqual(len(reg.list('p')),1)

if __name__=='__main__':unittest.main()
