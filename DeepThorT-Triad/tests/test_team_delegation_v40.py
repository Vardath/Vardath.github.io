"""Scripted model-role fixtures for V40's staged dependency graph."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.team_delegation import TeamDelegationStore,run_team
from deepthort_local.team_plan import parse_plan,is_team_request
from deepthort_local.delegation import DelegationError
from deepthort_local.creative_core import request_packet,midi
from deepthort_local.agent_contract import validate_creative_assignment

class TeamTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.conversations=ConversationStore(self.root/'conversation.sqlite3')
        self.assets=self.root/'creative-tasks';self.assets.mkdir()
        self.store=TeamDelegationStore(self.conversations.path,self.assets)
        self.original='/delegate midi Create a four-note rising melody at 100 BPM.'
        self.plan={'tasks':[{'id':'spec','kind':'design','brief':'Specify the melody','depends_on':[]},
                            {'id':'asset','kind':'midi','brief':'Compose specified melody','depends_on':['spec']}]}
        self.ident=self.conversations.submit('team','project','chat',self.original)
    def stage(self,*,requester,scope,brief,cancelled,notify):
        self.assertEqual(requester,'implementation')
        self.assertIn(self.original,brief)
        self.assertIn('C4 D4 E4 F4',brief)
        folder=self.assets/'media-fixture';folder.mkdir()
        packet=request_packet(requester,scope,brief)
        raw=midi({'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]})
        receipt={'status':'artifact_created','artifact':'score.mid','assigned_role':'multimedia',
            'requester':requester,'scope':scope,'project_publication_authorized':False,
            'native_inference_verified':True,'assignment_sha256':validate_creative_assignment(packet),
            'sha256':hashlib.sha256(raw).hexdigest(),'notes':4,'bpm':100}
        (folder/'score.mid').write_bytes(raw)
        (folder/'request.json').write_text(json.dumps(packet),'utf-8')
        (folder/'receipt.json').write_text(json.dumps(receipt),'utf-8')
        return folder,receipt
    def start(self):
        self.assertTrue(self.store.start(self.ident))
        t=self.store.claim(self.ident,'janus')
        self.store.plan(t,json.dumps(self.plan))
        self.assertIsNone(self.store.claim(self.ident,'implementation'))
        self.assertIsNone(self.store.claim(self.ident,'multimedia'))
        return self.store.claim(self.ident,'sentinel')
    def test_actual_dispatch_role_order_and_independent_conversation(self):
        other=self.conversations.submit('other','project','chat','Explain trade.')
        self.assertTrue(self.store.start(self.ident))
        owner=self
        class Client:
            roles=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.roles.append(role)
                owner.assertIn(owner.original,prompt)
                owner.assertEqual(owner.store.next_foreground()['id'],other)
                if role=='janus':return json.dumps(owner.plan)
                if role=='implementation':return 'C4 D4 E4 F4 at 100 BPM.'
                return 'ACCEPT'
        c=Client()
        answer=run_team(self.store,self.ident,c,self.stage,lambda:False,lambda s:None)
        self.assertEqual(c.roles,['janus','sentinel','implementation','sentinel'])
        self.assertIn('score.mid',answer)
        self.assertIn('no project files were published',answer)
        self.assertEqual(self.conversations.get(self.ident)['state'],'responded')
        self.assertEqual(self.store.summary(self.ident)['state'],'complete')
    def test_rejected_plan_has_no_execution(self):
        review=self.start()
        with self.assertRaises(DelegationError):self.store.approve(review,'REJECT')
        self.assertIsNone(self.store.claim(self.ident,'multimedia'))
        self.store.fail(self.ident,'Rejected graph')
        self.assertEqual(self.conversations.get(self.ident)['state'],'failed')
    def test_receipt_dependency_and_cancel(self):
        review=self.start();self.store.approve(review,'ACCEPT')
        self.assertIsNone(self.store.claim(self.ident,'multimedia'))
        d=self.store.claim(self.ident,'implementation')
        _,bound,_=self.store.assignment(d)
        self.store.design_done(d,bound,'C4 D4 E4 F4 at 100 BPM.')
        m=self.store.claim(self.ident,'multimedia')
        bound,creative=self.store.midi_task(m)
        folder,receipt=self.stage(requester=creative['requester'],scope=creative['scope'],brief=creative['brief'],cancelled=lambda:False,notify=lambda s:None)
        self.store.midi_done(m,bound,folder,receipt)
        check=self.store.claim(self.ident,'sentinel')
        results=self.store.results(check)
        self.store.review_results(check,results,'ACCEPT')
        deliver=self.store.claim(self.ident,'host')
        (folder/'score.mid').write_bytes(b'MThd corrupted')
        with self.assertRaises(DelegationError):self.store.deliver_team(deliver)
        self.conversations.cancel_chat_requests('team','Cancelled')
        with self.assertRaises(DelegationError):self.store.deliver_team(deliver)
    def test_scope_and_dag_validation(self):
        self.assertTrue(is_team_request(self.original))
        self.assertFalse(is_team_request('/delegate anything'))
        for bad in [
            {'tasks':[{'id':'x','kind':'shell','brief':'run','depends_on':[]}]},
            {'tasks':[{'id':'x','kind':'midi','brief':'x','depends_on':['x']}]},
            {'tasks':[{'id':'x','kind':'midi','brief':'x','depends_on':[],'grant':True}]},
        ]:
            with self.assertRaises(ValueError):parse_plan(json.dumps(bad),self.original)
        with self.assertRaises(ValueError):parse_plan(json.dumps(self.plan),'/delegate design Discuss music.')
        with self.assertRaises(ValueError):parse_plan('{"tasks":[],"tasks":[]}',self.original)
    def test_fixed_probe(self):
        from deepthort_local.team_probe import exercise
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_restart_no_replay(self):
        review=self.start();self.store.approve(review,'ACCEPT')
        prior=self.store.claim(self.ident,'implementation')
        self.assertEqual(self.store.recover(),1)
        self.assertFalse(self.store.start(self.ident))
        self.conversations.change(self.ident,'pending','Retry requested by user',allowed=('failed',))
        self.assertTrue(self.store.start(self.ident))
        self.assertEqual(self.store.summary(self.ident)['attempt'],2)
        with self.assertRaises(DelegationError):self.store.assignment(prior)

if __name__=='__main__':unittest.main()
