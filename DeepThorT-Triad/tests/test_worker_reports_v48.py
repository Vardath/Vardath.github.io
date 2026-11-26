"""V48: typed production worker report is scoped advice, never source or a grant."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_graph import TaskGraphStore,GraphError
from deepthort_local.project_authority import issue_grant
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient
from deepthort_local.worker_reports import PREFIX,parse_report,WorkerReport,observe_worker_reports,counsel_fields,still_current
from deepthort_local.reviewed_generation import generate_reviewed

class WorkerReportTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.original='Create a Python program preserving ship ownership during loading.'
        self.jobs=JobStore(self.root/'jobs.sqlite3');self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.request=self.chats.submit('c',str(self.project),'draft_plan',self.original)
        plan=[{'path':'ship.py','description':'Preserve ship ownership during loading'}]
        draft=self.chats.save_draft(self.request,plan)
        self.chats.change(self.request,'responded','Draft ready',response='Plan ready')
        self.jobid=self.jobs.submit_approved_build(str(self.project),'c',self.original,plan,'draft:'+str(draft))
        self.chats.approve(draft,self.jobid)
        self.steps=self.jobs.steps(self.jobid);self.step=self.steps[0]
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3')
        self.grants=self.root/'grants'
        queued=self.jobs.get(self.jobid)
        issue_grant(self.grants,queued,self.steps);self.graph.create(queued,self.steps)
        self.store=ProjectAssignments(self.graph)
        self.jobs.change(self.jobid,'running','Generating')
        self.report={'kind':'interface_conflict','need':'Ship ownership save schema','reason':'No serialization interface was supplied.'}
        self.attempt,self.contract=self.begin()
    def begin(self):
        return self.store.begin(self.jobs.get(self.jobid),self.steps,self.step,self.original,[],self.grants,enabled=True)
    def publish(self):
        return self.store.report_dependency(self.attempt,self.request,self.report)
    def test_report_disallows_source_and_keeps_independent_job_ready(self):
        class Client:
            def __init__(self,answer):self.answer=answer;self.calls=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.calls.append((role,prompt));return self.answer
        client=Client(PREFIX+json.dumps(self.report))
        scoped=ProjectRoleClient(client,self.contract,report=lambda r:self.store.report_dependency(self.attempt,self.request,r))
        with self.assertRaises(WorkerReport):
            scoped.chat('assignment','Return ship.py source')
        self.assertEqual(client.calls[0][0],'implementation')
        self.assertIn(PREFIX,client.calls[0][1])
        with self.assertRaises(GraphError):self.store.seal(self.attempt,'print(42)')
        self.assertFalse((self.project/'ship.py').exists())
        self.jobs.change(self.jobid,'needs_input','Awaiting dependency coordination')
        other=self.root/'other';other.mkdir()
        other_job=self.jobs.submit(str(other),'other','plan','Plan another project')
        self.assertEqual(self.jobs.next_any_queued()['id'],other_job)
        snapshot=observe_worker_reports(self.jobs.path)
        self.assertTrue(snapshot['available'])
        self.assertEqual(len(snapshot['reports']),1)
        item=snapshot['reports'][0]
        self.assertEqual(item['report'],self.report)
        self.assertEqual(item['recipients'],['janus','sentinel'])
        self.assertFalse(item['authority']);self.assertFalse(item['verified'])
        self.assertTrue(still_current(self.jobs.path,item['receipt_sha']))
        self.assertIn(self.original,counsel_fields(item,self.jobs.path)[1])
        # Reopen the actual ledger rather than rely on the original model thread.
        ProjectAssignments(TaskGraphStore(self.graph.path))
        self.assertEqual(observe_worker_reports(self.jobs.path),snapshot)
    def test_cancel_and_supersession_hide_old_claim(self):
        self.publish()
        self.assertTrue(observe_worker_reports(self.jobs.path)['reports'])
        self.jobs.cancel(self.jobid)
        self.assertEqual(observe_worker_reports(self.jobs.path)['reports'],[])
        with self.assertRaises(GraphError):self.publish()
    def test_new_attempt_withholds_old_report(self):
        self.publish()
        fresh,_=self.begin()
        self.assertNotEqual(fresh,self.attempt)
        self.assertEqual(observe_worker_reports(self.jobs.path)['reports'],[])
    def test_tampered_message_and_wrong_scope_rejected(self):
        with self.assertRaises(GraphError):
            self.store.report_dependency(self.attempt,self.request+100,self.report)
        self.publish()
        with self.graph._db() as db:
            db.execute("UPDATE worker_reports_v48 SET report=? WHERE attempt=?",(json.dumps(dict(self.report,need='changed')),self.attempt))
        self.assertEqual(observe_worker_reports(self.jobs.path)['reports'],[])
    def test_reserved_schema_and_normal_source(self):
        self.assertIsNone(parse_report('print(42)'))
        for bad in ('{}','{"kind":"missing_dependency","need":"a","reason":"b","authority":true}',
                    '{"kind":"missing_dependency","need":"a","need":"b","reason":"c"}',
                    '{"kind":"execute","need":"a","reason":"b"}'):
            with self.assertRaises(ValueError):parse_report(PREFIX+bad)
        self.assertEqual(parse_report(PREFIX+json.dumps(self.report)),self.report)
    def test_ordinary_source_is_not_a_report(self):
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):return 'print(42)'
        scoped=ProjectRoleClient(Client(),self.contract,report=lambda r:self.fail('Unexpected report'))
        self.assertEqual(scoped.chat('assignment','Produce source'),'print(42)')
        self.assertEqual(observe_worker_reports(self.jobs.path)['reports'],[])

if __name__=='__main__':unittest.main()
