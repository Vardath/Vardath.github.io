"""V50 scoped two-society recovery: real stores, scripted advisory replies."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_graph import TaskGraphStore,GraphError
from deepthort_local.project_authority import issue_grant,revoke_grant
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient
from deepthort_local.worker_reports import observe_granite_reports
from deepthort_local.agent_contract import canonical_sha
from deepthort_local.corrective_coordination import (
    WAIT,READY,eligible,propose,pending_review,review,approved,requeue,consume,parse,invalidate_review)

PROPOSAL=json.dumps({'decision':'retry','guidance':'Preserve the documented owner field; use the approved serialization interface.',
                     'reason':'The approved file obligation already specifies the owner field.'})
ACCEPT=json.dumps({'decision':'accept','reason':'Same scope and owner requirement, no new dependency or permission.'})
REJECT=json.dumps({'decision':'reject','reason':'The interface is not evidenced.'})

class CorrectiveCoordinationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.original='Create a Python program preserving the documented owner field during loading.'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.request=self.chats.submit('c',str(self.project),'draft_plan',self.original)
        plan=[{'path':'ship.py','description':'Preserve owner field during loading'}]
        draft=self.chats.save_draft(self.request,plan)
        self.chats.change(self.request,'responded','Draft ready',response='Plan ready')
        self.ident=self.jobs.submit_approved_build(str(self.project),'c',self.original,plan,'draft:'+str(draft))
        self.chats.approve(draft,self.ident)
        self.steps=self.jobs.steps(self.ident);self.step=self.steps[0]
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3')
        self.grants=self.root/'grants'
        job=self.jobs.get(self.ident)
        issue_grant(self.grants,job,self.steps);self.graph.create(job,self.steps)
        self.store=ProjectAssignments(self.graph)
        self.jobs.change(self.ident,'running','Generating')
        self.attempt,self.contract=self.begin()
        self.report={'kind':'interface_conflict','need':'Owner serialization interface','reason':'Interface unclear.'}
    def begin(self):
        return self.store.begin(self.jobs.get(self.ident),self.jobs.steps(self.ident),self.step,self.original,[],self.grants,enabled=True)
    def blocked(self):
        item=self.store.report_dependency(self.attempt,self.request,self.report)
        self.jobs.change(self.ident,'needs_input',WAIT+canonical_sha(item),allowed=('running',))
        result=observe_granite_reports(self.jobs.path)['reports']
        self.assertEqual(len(result),1)
        return result[0]
    def propose_and_review(self,answer=ACCEPT):
        item=self.blocked()
        self.assertTrue(propose(self.jobs.path,item,PROPOSAL))
        live,row=pending_review(self.jobs.path)
        self.assertEqual(live,item)
        self.assertTrue(review(self.jobs.path,item,row,answer))
        return item
    def test_actual_retry_lifecycle_and_fresh_role_context(self):
        item=self.blocked()
        self.assertTrue(eligible(self.jobs.path,item))
        self.assertTrue(propose(self.jobs.path,item,PROPOSAL))
        self.assertFalse(eligible(self.jobs.path,item))
        self.assertEqual(approved(self.jobs.path),[])
        live,row=pending_review(self.jobs.path)
        self.assertTrue(review(self.jobs.path,live,row,ACCEPT))
        ready=approved(self.jobs.path)[0]
        self.assertFalse(requeue(self.jobs,ready,validate=lambda item:False))
        self.assertTrue(requeue(self.jobs,ready,validate=lambda item:True))
        self.assertFalse(requeue(self.jobs,ready,validate=lambda item:True))
        queued=self.jobs.get(self.ident)
        self.assertEqual(queued['detail'],READY+item['receipt_sha'])
        self.jobs.change(self.ident,'running','Processing local job',allowed=('queued',))
        self.attempt,contract=self.begin()
        self.assertEqual(contract,self.contract)
        context=consume(self.jobs,queued,contract)
        self.assertIn('documented owner field',context)
        with self.assertRaises(ValueError):consume(self.jobs,queued,contract)
        class Client:
            def __init__(self):self.calls=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.calls.append((role,session,prompt));return 'owner = None'
        client=Client()
        plain=ProjectRoleClient(client,contract)
        corrected=ProjectRoleClient(client,contract,correction=context)
        plain.chat('same','Original approved task')
        self.assertEqual(corrected.chat('same','Original approved task'),'owner = None')
        self.assertNotEqual(client.calls[0][1],client.calls[1][1])
        self.assertIn('Original approved task',client.calls[1][2])
        self.assertIn(context,client.calls[1][2])
        self.assertFalse((self.project/'ship.py').exists())
        with self.assertRaises(GraphError):self.store.seal(self.attempt,'owner = None')
        second=self.blocked()
        self.assertFalse(eligible(self.jobs.path,second))
        self.assertFalse(propose(self.jobs.path,second,PROPOSAL))
    def test_rejected_or_held_decision_never_queues(self):
        self.propose_and_review(REJECT)
        self.assertEqual(approved(self.jobs.path),[])
        self.assertIsNone(pending_review(self.jobs.path))
        self.assertEqual(self.jobs.get(self.ident)['state'],'needs_input')
    def test_changed_contract_or_cancelled_job_cannot_dispatch(self):
        self.propose_and_review()
        row=approved(self.jobs.path)[0]
        self.jobs.cancel(self.ident)
        self.assertFalse(requeue(self.jobs,row,validate=lambda item:True))
        self.assertEqual(self.jobs.get(self.ident)['state'],'cancelled')
    def test_corrupt_proposal_or_verdict_cannot_authorize(self):
        self.propose_and_review()
        with self.jobs._conn() as db:
            db.execute("UPDATE corrective_assignments_v50 SET verdict=?",(json.dumps({'decision':'accept'}),))
        row=approved(self.jobs.path)[0]
        with self.assertRaises((ValueError,KeyError)):requeue(self.jobs,row,validate=lambda item:True)
        self.assertEqual(self.jobs.get(self.ident)['state'],'needs_input')
    def test_expired_or_revoked_grant_blocks_fresh_assignment(self):
        self.propose_and_review()
        self.assertTrue(requeue(self.jobs,approved(self.jobs.path)[0],validate=lambda item:True))
        queued=self.jobs.get(self.ident)
        self.jobs.change(self.ident,'running','Processing local job',allowed=('queued',))
        revoke_grant(self.grants,self.ident)
        with self.assertRaises(ValueError):self.begin()
        with self.assertRaises(ValueError):consume(self.jobs,queued,dict(self.contract,baseline_sha256='changed'))
    def test_malformed_review_and_tool_claim_do_not_schedule(self):
        item=self.blocked()
        self.assertTrue(propose(self.jobs.path,item,PROPOSAL))
        live,row=pending_review(self.jobs.path)
        with self.assertRaises(ValueError):review(self.jobs.path,live,row,'APPROVED')
        invalidate_review(self.jobs.path,row)
        self.assertEqual(approved(self.jobs.path),[])
        self.assertIsNone(pending_review(self.jobs.path))
        self.assertFalse(eligible(self.jobs.path,dict(item,report=dict(item['report'],kind='tool_requirement'))))
    def test_hold_and_strict_output_schema(self):
        item=self.blocked()
        self.assertTrue(propose(self.jobs.path,item,json.dumps({'decision':'hold','guidance':'','reason':'Need real interface evidence.'})))
        self.assertIsNone(pending_review(self.jobs.path))
        self.assertEqual(approved(self.jobs.path),[])
        for bad in ('{}','{"decision":"retry","guidance":"","reason":"x"}',
                    '{"decision":"retry","guidance":"x","reason":"y","command":"run"}',
                    '{"decision":"hold","guidance":"x","reason":"y"}'):
            with self.assertRaises(ValueError):parse(bad)

if __name__=='__main__':unittest.main()
