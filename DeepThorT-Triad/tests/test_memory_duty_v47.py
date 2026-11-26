"""V47: self-initiated memory duties use real local stores, scripted model only."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.specification_guard import master_for_job
from deepthort_local.specification_amendments import root_request_for_job
from deepthort_local.memory_duty import MemoryDuty,observe_memory_duties
from deepthort_local.memory_observer import MemoryObserver
from deepthort_local.memory_governor import retrieve
from deepthort_local.reasoning_council import sha

class MemoryDutyTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=str(self.root/'game');Path(self.project).mkdir()
        self.original='Create a Python program preserving ship ownership during loading.'
        self.chat='fixture'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.old=self.jobs.submit(self.project,self.chat,'plan',self.original)
        self.note='Regression: loading resets player ship ownership.'
        self.jobs.remember(self.old,'verification','ship ownership loading',sha(self.original),sha(self.note),self.note)
        steps=[{'path':'ship.py','description':'Preserve ship ownership during loading'},
               {'path':'test_ship.py','description':'Test ship ownership during loading'}]
        self.request=self.chats.submit(self.chat,self.project,'draft_plan',self.original)
        draft=self.chats.save_draft(self.request,steps)
        self.chats.change(self.request,'responded','Draft ready',response='Plan ready')
        self.job=self.jobs.submit_approved_build(self.project,self.chat,self.original,steps,'draft:'+str(draft))
        self.assertTrue(self.chats.approve(draft,self.job))
        self.duty=MemoryDuty(self.jobs.path,self.resolve)
    def resolve(self,job):
        return root_request_for_job(job,self.chats),master_for_job(job,self.chats,None,None)
    def records(self,packet):
        return [x for x in retrieve(self.jobs.path,project=packet['project'],chat_id=packet['chat_id'],
                original=packet['original'],focus=packet['focus'],job_id=packet['job_id']) if x['observation']==self.note]
    def test_discovers_two_upcoming_steps_and_reconstructs_unfinished_work(self):
        packets=self.duty.scan()
        self.assertEqual(len(packets),2)
        self.assertEqual([p['job_id'] for p in packets],[self.job,self.job])
        self.assertTrue(all(p['phase']=='anticipatory_recall' for p in packets))
        self.duty.complete(packets[0],self.records(packets[0]))
        restarted=MemoryDuty(self.jobs.path,self.resolve)
        pending=restarted.scan()
        self.assertEqual([p['scope'] for p in pending],[packets[1]['scope']])
        self.assertEqual(self.jobs.get(self.job)['state'],'queued')
    def test_self_initiated_recall_reaches_both_role_checkpoints(self):
        calls=[];published=threading.Event()
        def select(evidence,prompt,tokens):
            calls.append(evidence)
            rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
            return json.dumps({'keep':[r['id'] for r in rows if r['observation']==self.note],'reason':'Relevant observed regression'})
        def report(event,**kw):
            if event=='memory_observer_findings':published.set()
        observer=MemoryObserver(path=self.jobs.path,select=select,available=lambda:True,report=report)
        try:
            observer.start_duty(self.duty)
            self.assertTrue(published.wait(5))
            self.assertTrue(calls)
            snapshot=observe_memory_duties(self.jobs.path)
            self.assertTrue(snapshot['available'])
            self.assertTrue(snapshot['reports'])
            self.assertEqual(snapshot['reports'][0]['recipients'],['janus','sentinel'])
            self.assertFalse(snapshot['reports'][0]['authority'])
            self.assertEqual(snapshot['reports'][0]['records'][0]['observation'],self.note)
            args=dict(project=self.project,chat_id=self.chat,original=self.original,job_id=self.job,focus='ship ownership loading')
            self.assertIn(self.note,observer.advice(**args,recipient='janus'))
            self.assertIn(self.note,observer.advice(**args,recipient='sentinel'))
            self.assertFalse(observer.advice(**dict(args,chat_id='different')))
        finally:
            observer.close()
            if observer._thread:observer._thread.join(5)
    def test_deleted_evidence_and_cancelled_scope_not_delivered(self):
        packet=self.duty.scan()[0]
        self.duty.complete(packet,self.records(packet))
        self.assertTrue(observe_memory_duties(self.jobs.path)['reports'])
        with self.jobs._conn() as db:
            db.execute('DELETE FROM task_memory_notes WHERE job_id=?',(self.old,))
        self.assertEqual(observe_memory_duties(self.jobs.path)['reports'],[])
        self.jobs.cancel(self.job)
        self.assertTrue(packet['cancelled']())
        self.assertEqual(self.duty.scan(),[])
    def test_durable_advice_after_worker_restart_and_scope_change(self):
        packet=self.duty.scan()[0];records=self.records(packet)
        self.duty.complete(packet,records)
        restarted=MemoryDuty(self.jobs.path,self.resolve)
        args=dict(project=self.project,chat_id=self.chat,original=self.original,job_id=self.job,
                  current={x['id']:x for x in records})
        self.assertEqual(restarted.advice_records(**args),records)
        self.assertEqual(restarted.advice_records(**dict(args,original=self.original+' changed')),[])
        self.jobs.cancel(self.job)
        self.assertEqual(restarted.advice_records(**args),[])

if __name__=='__main__':unittest.main()
