"""V45 isolated project MIDI handoff tests. Scripted native/semantic receipts only."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.roadmap_runs import RoadmapRuns
from deepthort_local.project_midi import ProjectMidi,review_text,sha
from deepthort_local.tool_workflows import digest,artifact
from deepthort_local.artifact_acceptance import verify
from deepthort_local.artifact_types import artifact_type
from deepthort_local.creative_core import midi,inspect_midi,request_packet
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.delegation import DelegationStore
from deepthort_local.mixed_roadmap import pending_task
from deepthort_local.agent_contract import validate_creative_assignment

class ProjectMidiTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.assets=self.root/'staging';self.assets.mkdir()
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.delegations=DelegationStore(self.chats.path,self.assets)
        self.runs=RoadmapRuns(self.root/'roadmap-runs.sqlite3')
        self.store=ProjectMidi(self.runs,self.delegations)
        self.request={'id':1,'chat_id':'a','project':str(self.project),'mode':'draft_plan',
                      'state':'responded','prompt':'Create a short four-note melody at 100 BPM.'}
        self.task={'id':'task1','after':0,'goal':'Compose rising four-note melody at 100 BPM',
                   'output':'audio/theme.mid','sections':[1],'artifact_type':artifact_type('audio/theme.mid'),
                   'acceptance':{'bpm':100,'notes':4}}
        body={'request_id':1,'code_sha':'c'*64,'tasks':[self.task]}
        self.plan={**body,'sha':digest(body)}
        self.approval={'request_id':1,'project':str(self.project.resolve()),'chat_id':'a',
                       'manifest_sha256':body['code_sha'],'mixed_sha':self.plan['sha'],'creative_midi':True}
        self.runs.approve(self.approval)
        self.score={'bpm':100,'notes':[[60,480],[62,120],[64,480],[65,1920]]}
    def begin(self):
        return self.store.begin(self.runs.get(1),self.plan,self.task,self.request,1,enabled=True)
    def stage(self,contract,score=None):
        score=score or self.score
        folder=Path(tempfile.mkdtemp(dir=self.assets));packet=request_packet('janus',contract['scope'],contract['brief'])
        raw=midi(score)
        receipt={'status':'artifact_created','artifact':'score.mid','assigned_role':'multimedia',
            'requester':'janus','scope':contract['scope'],'project_publication_authorized':False,
            'native_inference_verified':True,'assignment_sha256':validate_creative_assignment(packet),
            'sha256':hashlib.sha256(raw).hexdigest(),'notes':len(score['notes']),'bpm':score['bpm']}
        (folder/'score.mid').write_bytes(raw)
        (folder/'request.json').write_text(json.dumps(packet),'utf-8')
        (folder/'receipt.json').write_text(json.dumps(receipt),'utf-8')
        review={'accepted':True,'verified':False,'original_sha':contract['original_sha'],
                'proposal_sha':sha(review_text(contract,score)),'evidence_sha':'e'*64}
        return folder,receipt,review
    def ready(self):
        lease,contract=self.begin()
        folder,receipt,review=self.stage(contract)
        self.store.reviewed(lease,contract,folder,receipt,review)
        return lease,contract,folder
    def publish(self,lease):
        return self.store.publish(lease,self.runs.get(1),self.plan,self.task,self.request,1,enabled=True)
    def test_canonical_midi_and_numeric_acceptance(self):
        raw=midi(self.score)
        self.assertEqual(inspect_midi(raw),self.score)
        for bad in (raw[:-1],raw+b'x',b'MThd'+b'0'*60,raw[:35]+b'\x00'+raw[36:]):
            with self.assertRaises(ValueError):inspect_midi(bad)
        dest=self.project/'audio.mid';dest.write_bytes(raw)
        proof=artifact(self.project,'audio.mid')
        self.assertEqual(verify(self.project,'audio.mid',{'bpm':100,'notes':4},proof)['observed'],{'bpm':100,'notes':4})
        with self.assertRaises(ValueError):verify(self.project,'audio.mid',{'bpm':110},proof)
    def test_approved_native_project_file_and_boundary_gate(self):
        lease,_,_=self.ready()
        class Workflows:
            def roadmap_members(self,ident):return []
        self.assertEqual(pending_task(self.plan,Workflows(),1,creative=self.store),self.task)
        self.assertFalse((self.project/self.task['output']).exists())
        result=self.publish(lease)
        self.assertFalse(result['runtime_verified'])
        self.assertEqual((self.project/self.task['output']).read_bytes(),midi(self.score))
        self.assertIsNone(pending_task(self.plan,Workflows(),1,creative=self.store))
        (self.project/self.task['output']).write_bytes(midi(dict(self.score,bpm=120)))
        with self.assertRaises(ValueError):pending_task(self.plan,Workflows(),1,creative=self.store)
    def test_old_consent_does_not_authorize_native_adapter(self):
        self.runs.approve(dict(self.approval,creative_midi=False))
        with self.assertRaises(ValueError):self.begin()
        self.runs.approve(self.approval)
        with self.assertRaises(ValueError):self.store.begin(self.runs.get(1),self.plan,self.task,self.request,2,enabled=True)
        with self.assertRaises(PermissionError):self.store.begin(self.runs.get(1),self.plan,self.task,self.request,1,enabled=False)
    def test_changed_score_or_rejected_review_cannot_publish(self):
        lease,contract=self.begin()
        folder,receipt,review=self.stage(contract,dict(self.score,bpm=120))
        with self.assertRaises(ValueError):self.store.reviewed(lease,contract,folder,receipt,review)
        folder,receipt,review=self.stage(contract)
        with self.assertRaises(ValueError):self.store.reviewed(lease,contract,folder,receipt,dict(review,accepted=False))
        self.store.reviewed(lease,contract,folder,receipt,review)
        (folder/'score.mid').write_bytes(b'MThd invalid')
        with self.assertRaises(ValueError):self.publish(lease)
        self.assertFalse((self.project/self.task['output']).exists())
    def test_no_overwrite_and_interrupted_attempt_not_replayed(self):
        lease,_,_=self.ready()
        target=self.project/self.task['output'];target.parent.mkdir();target.write_bytes(b'user owned')
        with self.assertRaises(ValueError):self.publish(lease)
        self.assertEqual(target.read_bytes(),b'user owned')
        target.unlink();self.store.recover()
        self.assertEqual(self.store.status(self.task['id']),'interrupted')
        with self.assertRaises(ValueError):self.begin()
    def test_pause_or_new_specification_rejects_publication(self):
        lease,_,_=self.ready()
        revised=dict(self.request,prompt='Different specification')
        with self.assertRaises(ValueError):
            self.store.publish(lease,self.runs.get(1),self.plan,self.task,revised,1,enabled=True)
        self.runs.change(1,'paused','User paused')
        with self.assertRaises(ValueError):self.publish(lease)
        self.assertFalse((self.project/self.task['output']).exists())

if __name__=='__main__':unittest.main()
