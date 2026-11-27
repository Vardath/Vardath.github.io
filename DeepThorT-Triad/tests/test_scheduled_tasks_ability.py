import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.scheduled_tasks import ScheduledTasks

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'conversations.sqlite3'
        self.c=ConversationStore(self.path);self.s=ScheduledTasks(self.c)
    def create(self,project='p',chat='c',prompt='Review the report.',due=110):
        return self.s.create(project,chat,prompt,due,now=100,user_approved=True)
    def test_due_admission_actual_conversation(self):
        n=self.create()
        self.assertIsNone(self.s.release_due('p',['c'],now=109,enabled=True))
        self.assertIsNone(self.s.release_due('p',['c'],now=110,enabled=False))
        r=self.s.release_due('p',['c'],now=110,enabled=True)
        self.assertEqual(r['schedule_id'],n)
        req=self.c.get(r['request_id'])
        self.assertEqual((req['prompt'],req['mode'],req['state'],req['attachments']),('Review the report.','chat','pending','[]'))
        self.assertEqual(self.s.rows('p','c')[0]['state'],'released')
    def test_restart_and_concurrent_exactly_once(self):
        self.create()
        recovered=ScheduledTasks(ConversationStore(self.path))
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts=list(pool.map(lambda _:recovered.release_due('p',['c'],now=111,enabled=True),range(4)))
        self.assertEqual(sum(x is not None for x in receipts),1)
        self.assertEqual(len(self.c.thread('c')),1)
    def test_scope_and_cancellation(self):
        n=self.create();other=self.create(chat='other');self.create(project='q')
        self.assertIsNone(self.s.release_due('p',['closed'],now=200,enabled=True))
        self.assertFalse(self.s.cancel(n,'q','c',now=105))
        self.assertTrue(self.s.cancel(n,'p','c',now=105))
        self.assertEqual(self.s.cancel_chat('p','other',now=105),1)
        self.assertIsNone(self.s.release_due('p',['c','other'],now=200,enabled=True))
        self.assertIsNotNone(self.s.release_due('q',['c'],now=200,enabled=True))
    def test_validation_and_authority(self):
        for due in (99,100,100+366*86400,True):
            with self.assertRaises(ValueError):self.create(due=due)
        with self.assertRaises(ValueError):self.s.create('p','c','run',110,now=100)
        with self.assertRaises(ValueError):self.create(prompt=' ')
        self.assertEqual(self.s.rows('p','c'),[])
