"""Durable Memory initiative: real stores, no native inference claims."""
import unittest
from unittest.mock import patch
from deepthort_local.memory_duty import MemoryDuty,observe_memory_duties,reader
from contextlib import closing
import test_memory_duty_v47 as previous

class PendingMemoryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=previous.MemoryDutyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.duty=self.fixture.duty
        self.jobs=self.fixture.jobs

    def count(self):
        with closing(reader(self.duty.path)) as db:
            return db.execute("SELECT COUNT(*) FROM memory_pending_v54").fetchone()[0]

    def test_admitted_work_survives_advancement_and_restart(self):
        first=self.duty.scan()
        self.assertEqual(len(first),2)
        self.assertEqual(self.count(),2)
        step=self.jobs.steps(self.fixture.job)[0]
        self.jobs.set_step(step['id'],'saved','Source produced before recall')
        restarted=MemoryDuty(self.jobs.path,self.fixture.resolve)
        pending=restarted.scan()
        self.assertEqual({p['scope'] for p in pending},{p['scope'] for p in first})
        old=next(p for p in pending if p['scope']==first[0]['scope'])
        restarted.complete(old,self.fixture.records(old))
        self.assertEqual(self.count(),1)
        self.assertTrue(observe_memory_duties(self.jobs.path)['reports'])
        self.assertEqual([p['scope'] for p in restarted.scan()],[first[1]['scope']])

    def test_fair_offers_and_no_eviction_under_pressure(self):
        with patch('deepthort_local.memory_duty.OFFER_DUTIES',1):
            a=self.duty.scan()[0]
            b=self.duty.scan()[0]
            self.assertNotEqual(a['scope'],b['scope'])
            restarted=MemoryDuty(self.jobs.path,self.fixture.resolve)
            self.assertEqual(restarted.scan()[0]['scope'],a['scope'])
            self.assertEqual(self.count(),2)

    def test_pause_retains_cancel_retires(self):
        packets=self.duty.scan()
        self.jobs.change(self.fixture.job,'paused','User paused')
        self.assertEqual(self.duty.scan(),[])
        self.assertEqual(self.count(),2)
        self.assertTrue(packets[0]['cancelled']())
        self.jobs.change(self.fixture.job,'queued','User resumed')
        self.assertEqual({p['scope'] for p in self.duty.scan()},{p['scope'] for p in packets})
        self.jobs.cancel(self.fixture.job)
        self.assertEqual(self.duty.scan(),[])
        self.assertEqual(self.count(),0)

    def test_blocked_approved_job_can_receive_memory_help(self):
        self.jobs.change(self.fixture.job,'needs_input','Dependency needs investigation')
        packets=self.duty.scan()
        self.assertEqual(len(packets),2)
        self.duty.complete(packets[0],self.fixture.records(packets[0]))
        reports=observe_memory_duties(self.jobs.path)['reports']
        self.assertTrue(reports)
        self.assertEqual(reports[0]['recipients'],['janus','sentinel'])
        self.assertFalse(reports[0]['authority'])
        self.assertEqual(self.jobs.get(self.fixture.job)['state'],'needs_input')

    def test_forged_focus_cannot_complete_pending_duty(self):
        packet=self.duty.scan()[0]
        self.duty.complete(dict(packet,focus='Unrelated project'),[])
        self.assertEqual(self.count(),2)
        self.duty.complete(packet,[])
        self.assertEqual(self.count(),1)

if __name__=='__main__':unittest.main()
