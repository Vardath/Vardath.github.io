"""V44 deterministic concurrent dispatcher fixtures, not native inference benchmarks."""
import hashlib
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.team_delegation import TeamDelegationStore,run_team
from deepthort_local.creative_core import request_packet,midi,budget_ok,GIB
from deepthort_local.agent_contract import validate_creative_assignment
from deepthort_local.delegation import DelegationError

class ReadyRoleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.assets=self.root/'assets';self.assets.mkdir()
        self.store=TeamDelegationStore(self.chats.path,self.assets)
        self.original='/delegate midi Create a four-note melody and a separate interface design.'
        self.req=self.chats.submit('thread','project','chat',self.original)
        self.plan={'tasks':[{'id':'design','kind':'design','brief':'Design interface','depends_on':[]},
                            {'id':'music','kind':'midi','brief':'Compose melody','depends_on':[]}]}
        self.design_started=threading.Event()
        self.design_finished=threading.Event()
        self.media_started=threading.Event()
        self.media_finished=threading.Event()
        self.external_stop=threading.Event()
        self.roles=[]
    def client(self,design):
        owner=self
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                owner.roles.append(role)
                if role=='janus':return json.dumps(owner.plan)
                if role=='implementation':
                    owner.design_started.set()
                    try:return design()
                    finally:owner.design_finished.set()
                if 'staged result evidence' in prompt:
                    owner.assertTrue(owner.design_finished.is_set())
                    owner.assertTrue(owner.media_finished.is_set())
                return 'ACCEPT'
        return Client()
    def media(self,**kw):
        self.media_started.set()
        try:
            packet=request_packet(kw['requester'],kw['scope'],kw['brief'])
            folder=self.assets/'music';folder.mkdir()
            raw=midi({'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]})
            receipt={'status':'artifact_created','artifact':'score.mid','assigned_role':'multimedia',
                'requester':kw['requester'],'scope':kw['scope'],'project_publication_authorized':False,
                'native_inference_verified':True,'assignment_sha256':validate_creative_assignment(packet),
                'sha256':hashlib.sha256(raw).hexdigest(),'notes':4,'bpm':100}
            (folder/'score.mid').write_bytes(raw)
            (folder/'request.json').write_text(json.dumps(packet),'utf-8')
            (folder/'receipt.json').write_text(json.dumps(receipt),'utf-8')
            return folder,receipt
        finally:self.media_finished.set()
    def run_batch(self,design,media=None,gate=None):
        self.assertTrue(self.store.start(self.req))
        return run_team(self.store,self.req,self.client(design),media or self.media,
                       lambda:self.external_stop.is_set() or not self.store.current(self.req),
                       lambda s:None,overlap_allowed=gate)
    def test_distinct_ready_roles_overlap_and_final_review_waits(self):
        both=threading.Barrier(2,timeout=5)
        def design():
            both.wait()
            self.assertTrue(self.media_started.is_set())
            return 'Interface design.'
        def media(**kw):
            self.media_started.set()
            both.wait()
            self.assertTrue(self.design_started.is_set())
            return self.media(**kw)
        answer=self.run_batch(design,media,lambda active,role:True)
        self.assertIn('score.mid',answer)
        self.assertEqual(self.store.summary(self.req)['state'],'complete')
        self.assertEqual(self.roles,['janus','sentinel','implementation','sentinel'])
    def test_denied_admission_preserves_serial_work(self):
        def design():
            self.assertFalse(self.media_started.is_set())
            time.sleep(.15)
            return 'Interface design.'
        def media(**kw):
            self.assertTrue(self.design_finished.is_set())
            return self.media(**kw)
        self.run_batch(design,media,lambda active,role:False)
        self.assertEqual(self.store.summary(self.req)['state'],'complete')
    def test_dependency_blocks_even_with_positive_admission(self):
        self.plan['tasks'][1]['depends_on']=['design']
        def design():
            time.sleep(.15)
            self.assertFalse(self.media_started.is_set())
            return 'Interface design.'
        def media(**kw):
            self.assertTrue(self.design_finished.is_set())
            self.assertEqual(kw['requester'],'implementation')
            return self.media(**kw)
        self.run_batch(design,media,lambda active,role:True)
    def test_failure_invalidates_batch_before_sibling_drains(self):
        both=threading.Barrier(2,timeout=5)
        invalidated=threading.Event()
        def design():
            both.wait()
            raise ValueError('Design failed')
        def media(**kw):
            both.wait()
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                if not self.store.current(self.req):
                    invalidated.set()
                    break
                time.sleep(.02)
            self.assertTrue(kw['cancelled']())
            return self.media(**kw)
        with self.assertRaisesRegex(ValueError,'Design failed'):
            self.run_batch(design,media,lambda active,role:True)
        self.assertTrue(invalidated.is_set())
        self.assertTrue(self.media_finished.is_set())
        self.assertEqual(self.store.summary(self.req)['state'],'failed')
        self.assertEqual(self.chats.get(self.req)['state'],'failed')
        self.assertEqual(self.roles.count('sentinel'),1)
    def test_external_stop_with_two_active_leases(self):
        both=threading.Barrier(2,timeout=5)
        def design():
            both.wait();self.external_stop.set()
            return 'No publication.'
        def media(**kw):
            both.wait()
            self.external_stop.wait(5)
            self.assertTrue(kw['cancelled']())
            self.media_finished.set()
            raise DelegationError('Stopped media')
        with self.assertRaises(DelegationError):
            self.run_batch(design,media,lambda active,role:True)
        self.assertTrue(self.media_finished.is_set())
        self.assertEqual(self.store.summary(self.req)['state'],'interrupted')
        self.assertNotEqual(self.chats.get(self.req)['state'],'responded')
    def test_admission_reserve_not_cap_increase(self):
        self.assertTrue(budget_ok(19*GIB,20*GIB,40*GIB,10*GIB,extra=GIB))
        self.assertTrue(budget_ok(18*GIB,20*GIB,40*GIB,10*GIB))
        self.assertFalse(budget_ok(18*GIB,20*GIB,40*GIB,10*GIB,extra=GIB))
        self.assertFalse(budget_ok(24*GIB,11*GIB,40*GIB,10*GIB,extra=GIB))
        self.assertFalse(budget_ok(24*GIB,20*GIB,40*GIB,0,extra=GIB))
        self.assertFalse(budget_ok(24*GIB,20*GIB,40*GIB,10*GIB,extra=-1))

if __name__=='__main__':unittest.main()
