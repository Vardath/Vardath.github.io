import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.scheduled_tasks import ScheduledTasks

class RecurringTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'conversations.sqlite3'
        self.c=ConversationStore(self.path);self.s=ScheduledTasks(self.c)
    def create(self,occurrences=3,interval=900):
        return self.s.create('p','c','Check the report.',110,now=100,user_approved=True,
                             interval_seconds=interval,occurrences=occurrences)
    def release(self,now):
        return self.s.release_due('p',['c'],now=now,enabled=True)
    def respond(self,r,state='responded'):
        self.c.change(r['request_id'],state,'fixture result','report')
    def test_interval_count_and_durable_history(self):
        n=self.create(2)
        r=self.release(110);self.assertEqual(r['next_due_utc'],1010);self.assertEqual(r['remaining_runs'],1)
        self.respond(r)
        self.assertIsNone(self.release(1009))
        self.s=ScheduledTasks(ConversationStore(self.path))
        r2=self.release(1010);self.assertEqual(r2['remaining_runs'],0);self.assertIsNone(self.release(4000))
        self.assertEqual(self.s.rows('p','c')[0]['state'],'released')
        self.assertEqual(len(self.s.occurrences(n,'p','c')),2)
        self.assertEqual([x['prompt'] for x in self.c.thread('c')],['Check the report.']*2)
    def test_missed_intervals_and_no_overlap(self):
        self.create()
        r=self.release(3000)
        self.assertEqual(r['next_due_utc'],3710)
        self.assertIsNone(self.release(4000))
        self.respond(r)
        r2=self.release(4000)
        self.assertEqual(r2['next_due_utc'],4610)
        self.assertIsNone(self.release(4000))
        self.assertEqual(len(self.c.thread('c')),2)
    def test_failure_and_explicit_cancellation_stop_recurrence(self):
        n=self.create();r=self.release(110);self.respond(r,'failed')
        self.assertIsNone(self.release(1010));self.assertEqual(self.s.rows('p','c')[0]['state'],'cancelled')
        other=self.create();self.assertTrue(self.s.cancel(other,'p','c',now=105))
        self.assertIsNone(self.release(3000))
        self.assertEqual(len(self.s.occurrences(n,'p','c')),1)
    def test_concurrent_admission_and_validation(self):
        n=self.create()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.release(110),range(4)))
        self.assertEqual(sum(x is not None for x in results),1)
        self.assertEqual(len(self.s.occurrences(n,'p','c')),1)
        for occurrences,interval in ((1,900),(1001,900),(2,899),(2,True),(2,None)):
            with self.assertRaises(ValueError):self.create(occurrences,interval)
