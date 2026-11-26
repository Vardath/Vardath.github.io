"""Read-only foreground advisory checkpoints and reversible exact consolidation."""
import unittest
from unittest.mock import patch
from contextlib import closing
from deepthort_local.memory_duty import reader,observe_memory_duties
from deepthort_local.memory_observer import MemoryObserver
from deepthort_local.memory_governor import retrieve
from deepthort_local.reasoning_council import sha
from deepthort_local.agent_tool_receipts import ToolReceipts
import test_memory_duty_v47 as previous

class MemoryAdviceTests(unittest.TestCase):
    def setUp(self):
        self.f=previous.MemoryDutyTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.args=dict(project=self.f.project,chat_id=self.f.chat,original=self.f.original,
                       job_id=self.f.job,focus='ship ownership loading')
    def observer(self):
        obs=MemoryObserver(path=self.f.jobs.path,select=lambda *a:self.fail('No inference expected'),
                           available=lambda:False)
        obs.start_duty(self.f.duty)
        def close():
            obs.close()
            if obs._thread:obs._thread.join(3)
        self.addCleanup(close)
        return obs
    def test_late_advice_does_not_rebuild_dirty_index_or_wait_for_writer(self):
        packet=self.f.duty.scan()[0]
        self.f.duty.complete(packet,self.f.records(packet))
        note='Unrelated palette observation.'
        self.f.jobs.remember(self.f.old,'verification','palette',sha(self.f.original),sha(note),note)
        obs=self.observer()
        with closing(reader(self.f.jobs.path)) as db:
            before=db.execute("SELECT count(*) FROM memory_term_dirty_v23").fetchone()[0]
        self.assertGreater(before,0)
        with self.f.jobs._conn() as writer:
            writer.execute('BEGIN IMMEDIATE')
            with patch('deepthort_local.memory_index.ensure',side_effect=AssertionError('Foreground schema write')), \
                 patch('deepthort_local.memory_index.refresh',side_effect=AssertionError('Foreground index rebuild')):
                self.assertIn(self.f.note,obs.advice(**self.args,recipient='janus'))
                self.assertIn(self.f.note,obs.advice(**self.args,recipient='sentinel'))
        with closing(reader(self.f.jobs.path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM memory_term_dirty_v23").fetchone()[0],before)
        self.assertFalse(obs.advice(**dict(self.args,focus='music playback')))

    def test_exact_group_retains_original_records_and_invalidates_old_report(self):
        second=self.f.jobs.submit(self.f.project,self.f.chat,'plan',self.f.original)
        self.f.jobs.remember(second,'verification','ship ownership loading',
                             sha(self.f.original),sha('second receipt'),self.f.note)
        foreign=self.f.jobs.submit(self.f.project,'different','plan',self.f.original)
        self.f.jobs.remember(foreign,'verification','ship ownership loading',
                             sha(self.f.original),sha('foreign receipt'),self.f.note)
        packet=self.f.duty.scan()[0]
        records=self.f.records(packet)
        self.assertEqual(len(records),1)
        group=records[0]['evidence']
        self.assertNotEqual(group,sha(self.f.note))
        self.assertNotEqual(group,sha('second receipt'))
        self.f.duty.complete(packet,records)
        self.assertTrue(observe_memory_duties(self.f.jobs.path)['reports'])
        with self.f.jobs._conn() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM task_memory_notes WHERE note=?",
                                        (self.f.note,)).fetchone()[0],3)
            db.execute("DELETE FROM task_memory_notes WHERE job_id=?",(second,))
        self.assertEqual(observe_memory_duties(self.f.jobs.path)['reports'],[])
        self.assertEqual(self.f.records(packet)[0]['evidence'],sha(self.f.note))

    def test_readonly_receipts_use_existing_store_and_preserve_evidence(self):
        ledger=ToolReceipts(self.f.root/'agent-tool-receipts-v61.sqlite3')
        ledger.record(job_id=self.f.job,project=self.f.project,spec_sha=sha(self.f.original),
                      session='fixture',turn=0,request={'tool':'inspect ownership'},
                      result={'items':[{'observed':'fixture'}]})
        expected=retrieve(self.f.jobs.path,**self.args)
        self.assertTrue(any(r['id'].startswith('T') for r in expected))
        with patch.object(ToolReceipts,'__init__',side_effect=AssertionError('Schema write')):
            self.assertEqual(retrieve(self.f.jobs.path,**self.args,read_only=True),expected)

if __name__=='__main__':unittest.main()
