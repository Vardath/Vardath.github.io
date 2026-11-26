"""V51 evidence-directed cooperation uses actual saved source, not invented guidance."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_graph import TaskGraphStore
from deepthort_local.project_authority import issue_grant,record_file,revoke_grant
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient
from deepthort_local.worker_reports import observe_granite_reports,counsel_fields,saved_dependency_catalog
from deepthort_local.agent_contract import canonical_sha
from deepthort_local.corrective_coordination import WAIT,propose,pending_review,review,approved,requeue,consume,parse

class EvidenceCoordination(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.original='Create a Python program preserving the owner field.'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.request=self.chats.submit('c',str(self.project),'draft_plan',self.original)
        plan=[{'path':'schema.py','description':'Define owner field'},{'path':'ship.py','description':'Use owner field'}]
        draft=self.chats.save_draft(self.request,plan)
        self.chats.change(self.request,'responded','Draft ready',response='Plan ready')
        self.ident=self.jobs.submit_approved_build(str(self.project),'c',self.original,plan,'draft:'+str(draft))
        self.chats.approve(draft,self.ident)
        self.graph=TaskGraphStore(self.root/'task-graph.sqlite3')
        self.grants=self.root/'grants'
        job=self.jobs.get(self.ident);steps=self.jobs.steps(self.ident)
        issue_grant(self.grants,job,steps);self.graph.create(job,steps)
        self.jobs.change(self.ident,'running','Generating')
        job=self.jobs.get(self.ident)
        self.source='OWNER_FIELD = "owner"\n'
        (self.project/'schema.py').write_bytes(self.source.encode())
        receipt=record_file(self.grants,job,steps,steps[0],enabled=True)
        self.graph.record_artifact(job,steps,steps[0],receipt['sha256'])
        self.jobs.set_step(steps[0]['id'],'saved','Saved')
        self.step=self.jobs.steps(self.ident)[1];self.store=ProjectAssignments(self.graph)
        self.attempt,self.contract=self.begin()
        claim={'kind':'interface_conflict','need':'Serialization interface','reason':'Need exact owner field.'}
        item=self.store.report_dependency(self.attempt,self.request,claim)
        self.jobs.change(self.ident,'needs_input',WAIT+canonical_sha(item),allowed=('running',))
        self.item=observe_granite_reports(self.jobs.path)['reports'][0]
    def begin(self):
        return self.store.begin(self.jobs.get(self.ident),self.jobs.steps(self.ident),self.step,
            self.original,[],self.grants,enabled=True)
    def proposal(self,path='schema.py'):
        return json.dumps({'decision':'retry','guidance':'Use the verified owner field definition.',
            'reason':'The graph contains the approved interface.','evidence_path':path})
    def accept(self):
        self.assertTrue(propose(self.jobs.path,self.item,self.proposal()))
        item,row=pending_review(self.jobs.path)
        self.assertTrue(review(self.jobs.path,item,row,json.dumps({'decision':'accept','reason':'Exact existing predecessor, conditional on verification.'})))
        return approved(self.jobs.path)[0]
    def preview(self,item,path,exclude=()):
        return self.store.preview_corrective_dependency(self.jobs.get(self.ident),self.jobs.steps(self.ident),
            item,path,self.grants,enabled=True,exclude=exclude)
    def queue(self,row):
        return requeue(self.jobs,row,validate=lambda item:True,validate_evidence=self.preview)
    def resolve(self,path):
        return self.store.supply_dependency(self.attempt,self.jobs.get(self.ident),self.jobs.steps(self.ident),
            self.step,self.original,[],self.grants,{'kind':'evidence_gap','need':path,'reason':'Reviewed request'},2100,enabled=True)
    def test_actual_evidence_supplied_after_independent_review(self):
        self.assertEqual(saved_dependency_catalog(self.jobs.path,self.item),
                         [{'path':'schema.py','sha256':hashlib.sha256(self.source.encode()).hexdigest()}])
        self.assertIn('schema.py',counsel_fields(self.item,self.jobs.path)[1])
        row=self.accept()
        self.assertFalse(requeue(self.jobs,row,validate=lambda item:True))
        self.assertTrue(self.queue(row))
        queued=self.jobs.get(self.ident)
        self.jobs.change(self.ident,'running','Processing',allowed=('queued',))
        self.attempt,contract=self.begin()
        with self.assertRaises(ValueError):consume(self.jobs,queued,contract)
        context=consume(self.jobs,queued,contract,resolve_evidence=self.resolve)
        self.assertIn(self.source,context)
        self.assertIn(hashlib.sha256(self.source.encode()).hexdigest(),context)
        self.assertEqual(self.resolve('schema.py'),'')
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                self.prompt=prompt
                return 'from schema import OWNER_FIELD'
        client=Client()
        role=ProjectRoleClient(client,contract,correction=context)
        role.chat('source','Original approved ship.py task')
        self.assertIn(self.source,client.prompt)
        self.assertIn('Original approved ship.py task',client.prompt)
        self.assertFalse((self.project/'ship.py').exists())
        with self.assertRaises(ValueError):self.store.seal(self.attempt,'from schema import OWNER_FIELD')
    def test_no_arbitrary_or_traversal_request(self):
        self.assertFalse(propose(self.jobs.path,self.item,self.proposal('unapproved.py')))
        with self.assertRaises(ValueError):parse(self.proposal('../schema.py'))
        with self.assertRaises(ValueError):parse(self.proposal('C:/schema.py'))
        self.assertTrue(propose(self.jobs.path,self.item,self.proposal()))
    def test_excluded_or_changed_source_blocks_queue(self):
        row=self.accept()
        self.assertFalse(requeue(self.jobs,row,validate=lambda item:True,
            validate_evidence=lambda item,path:self.preview(item,path,{'schema.py'})))
        (self.project/'schema.py').write_text('changed',encoding='utf-8')
        self.assertFalse(self.queue(row))
        self.assertEqual(self.jobs.get(self.ident)['state'],'needs_input')
    def test_revoked_grant_blocks_queue(self):
        row=self.accept()
        revoke_grant(self.grants,self.ident)
        self.assertFalse(self.queue(row))
    def test_changed_bytes_after_queue_block_fresh_assignment(self):
        row=self.accept()
        self.assertTrue(self.queue(row))
        self.jobs.change(self.ident,'running','Processing',allowed=('queued',))
        (self.project/'schema.py').write_text('changed',encoding='utf-8')
        with self.assertRaises(ValueError):self.begin()

if __name__=='__main__':unittest.main()
