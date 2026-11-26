"""V49 real scoped stores and scripted worker responses; not native intelligence tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.worker_reports import PREFIX,WorkerReport,observe_worker_reports,counsel_fields
from deepthort_local.creative_core import generate_score_reply,create_midi
from deepthort_local.project_midi import ProjectMidi
from deepthort_local.roadmap_runs import RoadmapRuns
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.delegation import DelegationStore
from deepthort_local.tool_workflows import digest
from deepthort_local.artifact_types import artifact_type
from deepthort_local.job_queue import JobStore
from deepthort_local.task_graph import TaskGraphStore
from deepthort_local.project_assignments import ProjectAssignments,ProjectRoleClient
from deepthort_local.project_authority import issue_grant,record_file

REPORT={'kind':'missing_dependency','need':'schema.py','reason':'Exact interface needed.'}
ANSWER=PREFIX+json.dumps(REPORT)

class CreativeCoordination(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        original='Create a short four-note melody at 100 BPM.'
        ident=self.chats.submit('a',str(self.project),'draft_plan',original)
        self.chats.change(ident,'responded','Plan ready',response='Plan')
        self.req=self.chats.get(ident)
        self.runs=RoadmapRuns(self.root/'roadmap-runs.sqlite3')
        self.store=ProjectMidi(self.runs,DelegationStore(self.chats.path,self.root/'staging'))
        self.task={'id':'task1','after':0,'goal':'Compose rising four-note melody at 100 BPM',
                   'output':'audio/theme.mid','sections':[1],'artifact_type':artifact_type('audio/theme.mid'),
                   'acceptance':{'bpm':100,'notes':4}}
        body={'request_id':ident,'code_sha':'c'*64,'tasks':[self.task]}
        self.plan={**body,'sha':digest(body)}
        self.runs.approve({'request_id':ident,'project':str(self.project.resolve()),'chat_id':'a',
                           'manifest_sha256':body['code_sha'],'mixed_sha':self.plan['sha'],'creative_midi':True})
        self.lease,self.contract=self.store.begin(self.runs.get(ident),self.plan,self.task,self.req,1,enabled=True)
    def test_report_accepted_only_in_project_score_lane(self):
        self.assertEqual(generate_score_reply(lambda p:ANSWER,'brief',allow_report=True),ANSWER)
        with self.assertRaises(ValueError):generate_score_reply(lambda p:ANSWER,'brief')
        with self.assertRaises(WorkerReport) as caught:
            create_midi(requester='janus',scope=self.contract['scope'],brief=self.contract['brief'],
                        root=self.root,generate=lambda *a:(ANSWER,42))
        self.assertEqual(caught.exception.sender,'multimedia')
        self.assertFalse(list(self.root.rglob('score.mid')))
        self.store.report_dependency(self.lease,self.contract,caught.exception.report)
        self.assertEqual(self.runs.get(self.req['id'])['state'],'blocked')
        snap=observe_worker_reports(self.root/'jobs.sqlite3')
        item=snap['reports'][0]
        self.assertEqual(item['sender'],'multimedia')
        self.assertEqual(item['recipients'],['janus','sentinel'])
        self.assertFalse(item['authority'])
        self.assertIn(self.req['prompt'],counsel_fields(item,self.root/'jobs.sqlite3')[1])
        self.assertFalse((self.project/self.task['output']).exists())
        with self.assertRaises(ValueError):self.store.report_dependency(self.lease,self.contract,REPORT)
    def test_report_not_published_after_pause(self):
        self.runs.change(self.req['id'],'paused','Stopped')
        with self.assertRaises(ValueError):self.store.report_dependency(self.lease,self.contract,REPORT)
        self.assertEqual(observe_worker_reports(self.root/'jobs.sqlite3')['reports'],[])
    def test_modified_report_withheld(self):
        self.store.report_dependency(self.lease,self.contract,REPORT)
        with self.runs.db() as db:
            db.execute("UPDATE creative_reports_v49 SET report=?",(json.dumps(dict(REPORT,need='changed')),))
        self.assertEqual(observe_worker_reports(self.root/'jobs.sqlite3')['reports'],[])

class EvidenceRecovery(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'game';self.project.mkdir()
        self.original='Create Python source preserving ship ownership.'
        self.jobs=JobStore(self.root/'jobs.sqlite3')
        self.grants=self.root/'grants';self.graph=TaskGraphStore(self.root/'task-graph.sqlite3')
        plan=[{'path':'schema.py','description':'Define ownership schema'},{'path':'ship.py','description':'Use ownership schema'}]
        self.ident=self.jobs.submit_approved_build(str(self.project),'c',self.original,plan,'draft:1')
        job=self.jobs.get(self.ident);steps=self.jobs.steps(self.ident)
        issue_grant(self.grants,job,steps);self.graph.create(job,steps)
        self.jobs.change(self.ident,'running','Generating')
        job=self.jobs.get(self.ident)
        self.source='OWNER_FIELD = "owner"\n'
        (self.project/'schema.py').write_bytes(self.source.encode())
        receipt=record_file(self.grants,job,steps,steps[0],enabled=True)
        self.graph.record_artifact(job,steps,steps[0],receipt['sha256'])
        self.jobs.set_step(steps[0]['id'],'saved','Saved')
        self.steps=self.jobs.steps(self.ident);self.job=self.jobs.get(self.ident)
        self.step=self.steps[1];self.store=ProjectAssignments(self.graph)
        self.attempt,self.contract=self.store.begin(self.job,self.steps,self.step,self.original,[],self.grants,enabled=True)
    def supply(self,report=REPORT,budget=2000,exclude=()):
        return self.store.supply_dependency(self.attempt,self.job,self.steps,self.step,self.original,[],self.grants,
                                            report,budget,enabled=True,exclude=exclude)
    def test_fresh_retry_receives_actual_source_and_retains_review(self):
        class Client:
            def __init__(self):self.prompts=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.prompts.append(prompt)
                return ANSWER if len(self.prompts)==1 else 'from schema import OWNER_FIELD'
        client=Client()
        role=ProjectRoleClient(client,self.contract,report=lambda r:self.fail('Unexpected unresolved claim'),
                               resolve=lambda r,b:self.supply(r,b))
        answer=role.chat('source','Create ship.py')
        self.assertEqual(answer,'from schema import OWNER_FIELD')
        self.assertEqual(len(client.prompts),2)
        self.assertIn(self.source,client.prompts[1])
        self.assertIn(hashlib.sha256(self.source.encode()).hexdigest(),client.prompts[1])
        self.assertEqual(self.supply(),'')
        self.assertFalse((self.project/'ship.py').exists())
        with self.assertRaises(ValueError):self.store.seal(self.attempt,answer)
    def test_refuse_unapproved_excluded_or_insufficient_evidence(self):
        self.assertEqual(self.supply(dict(REPORT,need='unapproved.py')),'')
        self.assertEqual(self.supply(exclude={'schema.py'}),'')
        self.assertEqual(self.supply(budget=30),'')
        self.assertTrue(self.supply())
    def test_changed_dependency_cannot_recover(self):
        (self.project/'schema.py').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.supply()

if __name__=='__main__':unittest.main()
