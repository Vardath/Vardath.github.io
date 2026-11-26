"""Real approved draft scope; reuse only actual prior exact intention evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_graph import TaskGraphStore
from deepthort_local.project_authority import issue_grant
from deepthort_local.project_assignments import ProjectAssignments
from deepthort_local.project_assignment_probe import fixture_receipt
from deepthort_local.supervision_policy import record,prior_plan,review_depth
from deepthort_local.specification_guard import inspect_proposal

class SupervisionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.original='Create a simple program returning 42.'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.reqid=self.chats.submit('c',str(self.project),'draft_plan',self.original)
        self.intent={'path':'main.py','description':'Implement return value'}
        self.proposal=json.dumps(self.intent,ensure_ascii=False)
        self.focus='main.py: Implement return value'
        self.req=self.chats.get(self.reqid)
        draft=self.chats.save_draft(self.reqid,[self.intent])
        self.chats.change(self.reqid,'responded','Plan ready',response='Plan ready')
        self.id=self.jobs.submit_approved_build(str(self.project),'c',self.original,[self.intent],'draft:'+str(draft))
        self.chats.approve(draft,self.id)
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3');self.store=ProjectAssignments(self.graph)
        self.grants=self.root/'grants';job=self.jobs.get(self.id);self.steps=self.jobs.steps(self.id)
        issue_grant(self.grants,job,self.steps);self.graph.create(job,self.steps)
        self.jobs.change(self.id,'running','Production');self.job=self.jobs.get(self.id)
        self.attempt,self.contract=self.store.begin(self.job,self.steps,self.steps[0],self.original,[],self.grants,enabled=True)
        self.path=self.root/'reasoning.sqlite3'
        self.receipt=fixture_receipt(self.original,self.proposal)
        self.policy=review_depth(self.contract,[])
    def lookup(self,policy=None,proposal=None):
        return prior_plan(self.path,self.jobs.path,self.jobs.get(self.id),self.contract,self.original,
                          proposal or self.proposal,self.focus,policy or self.policy)
    def test_exact_prior_review_reused_only_for_intention(self):
        self.assertIsNone(self.lookup())
        self.assertTrue(record(self.path,self.req,self.original,self.proposal,self.focus,self.receipt))
        receipt=self.lookup();self.assertEqual(receipt['supervision'],'reused_exact_prior_sentinel_intention')
        self.assertFalse(self.store.prior_attempt(self.attempt))
        self.store.review(self.attempt,'plan',self.proposal,receipt)
        with self.assertRaises(ValueError):self.store.seal(self.attempt,'print(42)')
        self.assertIsNone(self.lookup(proposal='changed intent'))
        self.assertIsNone(self.lookup(review_depth(self.contract,[],corrective=True)))
        self.assertIsNone(self.lookup(review_depth(self.contract,[],advice='New memory warning')))
        self.jobs.cancel(self.id);self.assertIsNone(self.lookup())
    def test_amended_or_section_review_not_reusable(self):
        self.assertFalse(record(self.path,self.req,self.original,self.proposal,self.focus,self.receipt,section='Create'))
        self.assertFalse(record(self.path,self.req,self.original,self.proposal,self.focus,self.receipt,amendments=['revision']))
        self.assertFalse(record(self.path,self.req,self.original,self.proposal,self.focus,dict(self.receipt,verified=True)))
    def test_elevated_source_still_independently_reviewed(self):
        class Council:
            def _run(self,client,**kw):
                self.prompt=kw['prompt'];return '{"verdict":"ACCEPT","reason":"Exact return value matches."}'
        c=Council()
        policy=review_depth(self.contract,[],corrective=True)
        result=inspect_proposal(c,None,original=self.original,project=self.project,session='s',
            focus=self.focus,proposal='def answer(): return 42',kind='code',supervision=policy)
        self.assertIn('Elevated independent supervision',c.prompt)
        self.assertIn('corrective or repeated assignment',c.prompt)
        self.assertTrue(result['accepted']);self.assertFalse(result['verified'])

if __name__=='__main__':unittest.main()
