"""Actual durable jobs, grants, graphs and independent corrective review."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_graph import TaskGraphStore
from deepthort_local.project_authority import issue_grant,record_file
from deepthort_local.project_assignments import ProjectAssignments
from deepthort_local.agent_contract import canonical_sha
from deepthort_local.worker_reports import observe_granite_reports,counsel_fields,still_current
from deepthort_local.branch_holds import park,blocked_steps,wait
from deepthort_local.corrective_coordination import eligible,propose,pending_review,review,approved,requeue,queued_target,consume

class BranchTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.original='Build an engine, UI and an independent reference manual.'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.request=self.chats.submit('c',str(self.project),'draft_plan',self.original)
        plan=[{'path':'engine.py','description':'Engine; depends-on: none'},
              {'path':'ui.py','description':'Interface; depends-on: engine.py'},
              {'path':'manual.md','description':'Reference manual; depends-on: none'}]
        draft=self.chats.save_draft(self.request,plan)
        self.chats.change(self.request,'responded','Draft ready',response='Plan ready')
        self.id=self.jobs.submit_approved_build(str(self.project),'c',self.original,plan,'draft:'+str(draft))
        self.chats.approve(draft,self.id)
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3');self.store=ProjectAssignments(self.graph)
        self.grants=self.root/'grants';issue_grant(self.grants,self.job(),self.steps())
        self.graph.create(self.job(),self.steps())
        self.jobs.change(self.id,'running','Production')
    def job(self):return self.jobs.get(self.id)
    def steps(self):return self.jobs.steps(self.id)
    def begin(self,step):
        return self.store.begin(self.job(),self.steps(),step,self.original,[],self.grants,enabled=True)
    def report(self,step):
        attempt,_=self.begin(step)
        raw=self.store.report_dependency(attempt,self.request,
            {'kind':'interface_conflict','need':'Engine interface','reason':'Need clarification of approved interface.'})
        self.assertTrue(park(self.jobs,self.graph,self.job(),canonical_sha(raw)))
        return observe_granite_reports(self.jobs.path,receipt_sha=canonical_sha(raw))['reports'][0]
    def ready(self):
        return self.graph.ready_step(self.job(),self.steps(),exclude=blocked_steps(self.jobs.path,self.id))
    def accept(self,item):
        self.assertTrue(eligible(self.jobs.path,item))
        self.assertTrue(propose(self.jobs.path,item,json.dumps({'decision':'retry','guidance':'Implement the documented interface only.',
                     'reason':'The approved goal supplies the intended interface.'})))
        live,row=pending_review(self.jobs.path)
        self.assertEqual(item,live)
        self.assertTrue(review(self.jobs.path,item,row,json.dumps({'decision':'accept','reason':'Same approved scope.'})))
    def save(self,step):
        (self.project/step['path']).write_text('Manual',encoding='utf-8')
        receipt=record_file(self.grants,self.job(),self.steps(),step,enabled=True)
        self.graph.record_artifact(self.job(),self.steps(),step,receipt['sha256'])
        self.jobs.set_step(step['id'],'saved','Saved')
    def test_branch_continues_and_correction_can_be_reviewed_concurrently(self):
        first=self.ready();self.assertEqual(first['path'],'engine.py')
        item=self.report(first)
        self.assertEqual(self.job()['state'],'queued')
        self.assertTrue(still_current(self.jobs.path,item['receipt_sha']))
        self.assertIn(self.original,counsel_fields(item,self.jobs.path)[1])
        self.assertEqual(self.ready()['path'],'manual.md')
        self.jobs.change(self.id,'running','Independent manual')
        self.accept(item)
        self.assertEqual(approved(self.jobs.path),[]) # no override of active production
        self.save(self.ready())
        self.jobs.change(self.id,'queued','Manual saved')
        self.assertTrue(requeue(self.jobs,approved(self.jobs.path)[0],validate=lambda i:True))
        queued=self.job();self.assertEqual(queued_target(self.jobs,queued),first['id'])
        self.jobs.change(self.id,'running','Reviewed engine retry')
        attempt,contract=self.begin(first)
        self.assertIn('documented interface',consume(self.jobs,queued,contract))
        self.assertIsNone(self.ready())
        self.assertFalse((self.project/'engine.py').exists())
        self.assertFalse((self.project/'ui.py').exists())
    def test_parked_branch_survives_restart_and_cancel(self):
        item=self.report(self.ready())
        self.jobs=JobStore(self.jobs.path)
        self.assertEqual(self.ready()['path'],'manual.md')
        self.jobs.cancel(self.id)
        self.assertFalse(eligible(self.jobs.path,item))
        self.assertEqual(observe_granite_reports(self.jobs.path)['reports'],[])
    def test_multiple_holds_do_not_false_complete(self):
        one=self.report(self.ready())
        self.jobs.change(self.id,'running','Independent manual')
        two=self.report(self.ready())
        self.assertEqual(self.job()['state'],'needs_input')
        self.assertIsNone(self.ready())
        self.assertEqual(len(blocked_steps(self.jobs.path,self.id)),2)
        self.assertTrue(eligible(self.jobs.path,one))
        self.assertTrue(eligible(self.jobs.path,two))
        self.assertFalse((self.project/'ui.py').exists())

if __name__=='__main__':unittest.main()
