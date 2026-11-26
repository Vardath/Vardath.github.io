"""Scripted staging fixtures; no native inference or project publication claimed."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.delegation import DelegationStore,DelegationError
from deepthort_local.creative_core import request_packet,midi
from deepthort_local.agent_contract import validate_creative_assignment

class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.conversations=ConversationStore(self.root/'conversations.sqlite3')
        self.assets=self.root/'creative-tasks'
        self.assets.mkdir()
        self.store=DelegationStore(self.conversations.path,self.assets)
        self.brief='Compose a short ascending MIDI melody at 100 BPM.'
        self.req=self.conversations.submit('chat-a','project-a','chat',self.brief)
    def stage(self,task):
        # Simulated native boundary receipt; production requires an actual
        # native worker result. The fixture does not call a model.
        folder=self.assets/('media-fixture-'+str(task['attempt']))
        folder.mkdir()
        packet=request_packet('user',task['scope'],task['brief'])
        raw=midi({'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]})
        receipt={'status':'artifact_created','artifact':'score.mid','assigned_role':'multimedia',
            'requester':'user','scope':task['scope'],'project_publication_authorized':False,
            'native_inference_verified':True,'assignment_sha256':validate_creative_assignment(packet),
            'sha256':hashlib.sha256(raw).hexdigest(),'notes':4,'bpm':100}
        (folder/'score.mid').write_bytes(raw)
        (folder/'request.json').write_text(json.dumps(packet),'utf-8')
        (folder/'receipt.json').write_text(json.dumps(receipt),'utf-8')
        return folder,receipt
    def test_independent_thread_and_dependency_order(self):
        same=self.conversations.submit('chat-a','project-a','chat','Explain sector economics.')
        other=self.conversations.submit('chat-b','project-b','chat','Explain sector economics.')
        self.assertEqual(self.store.next_candidate()['id'],self.req)
        self.assertEqual(self.store.next_foreground()['id'],other)
        self.assertTrue(self.store.start(self.req))
        self.assertFalse(self.store.start(self.req))
        self.assertEqual(self.store.next_foreground()['id'],other)
        self.assertIsNone(self.store.claim(self.req,'host'))
        task=self.store.claim(self.req,'multimedia')
        self.assertIsNone(self.store.claim(self.req,'multimedia'))
        folder,receipt=self.stage(task)
        self.store.composed(task,folder,receipt)
        check=self.store.claim(self.req,'host')
        self.assertIsNotNone(check)
        answer=self.store.verify_and_deliver(check)
        self.assertIn('score.mid',answer)
        self.assertEqual(self.conversations.get(self.req)['state'],'responded')
        self.assertEqual(self.store.summary(self.req)['state'],'complete')
        self.assertEqual(self.store.next_foreground()['id'],same)
        with self.assertRaises(DelegationError):self.store.verify_and_deliver(check)
    def test_cancelled_request_never_delivers(self):
        self.assertTrue(self.store.start(self.req))
        task=self.store.claim(self.req,'multimedia')
        folder,receipt=self.stage(task)
        self.store.composed(task,folder,receipt)
        check=self.store.claim(self.req,'host')
        self.conversations.cancel_chat_requests('chat-a','Stopped')
        self.assertFalse(self.store.current(self.req))
        with self.assertRaises(DelegationError):self.store.verify_and_deliver(check)
        self.store.fail(self.req,'Stopped',interrupted=True)
        self.assertEqual(self.conversations.get(self.req)['state'],'cancelled')
        self.assertEqual(self.store.summary(self.req)['state'],'interrupted')
    def test_corrupt_or_stale_artifact_never_delivers(self):
        self.assertTrue(self.store.start(self.req))
        task=self.store.claim(self.req,'multimedia')
        folder,receipt=self.stage(task)
        self.store.composed(task,folder,receipt)
        check=self.store.claim(self.req,'host')
        (folder/'score.mid').write_bytes(b'MThd corrupted')
        with self.assertRaises(DelegationError):self.store.verify_and_deliver(check)
        self.store.fail(self.req,'Corrupt artifact')
        self.assertEqual(self.conversations.get(self.req)['state'],'failed')
    def test_restart_requires_explicit_retry(self):
        self.assertTrue(self.store.start(self.req))
        task=self.store.claim(self.req,'multimedia')
        folder,receipt=self.stage(task)
        self.store.composed(task,folder,receipt)
        restarted=ConversationStore(self.conversations.path)
        new=DelegationStore(restarted.path,self.assets)
        self.assertEqual(new.recover(),1)
        self.assertEqual(restarted.get(self.req)['state'],'failed')
        self.assertFalse(new.start(self.req))
        restarted.change(self.req,'pending','Retry requested by user',allowed=('failed',))
        self.assertTrue(new.start(self.req))
        self.assertEqual(new.summary(self.req)['attempt'],2)
        with self.assertRaises(DelegationError):new.composed(task,folder,receipt)
        fresh=new.claim(self.req,'multimedia')
        self.assertNotEqual(fresh['scope'],task['scope'])
        with self.assertRaises(DelegationError):new.composed(fresh,folder,receipt)
    def test_fixed_acceptance_probe(self):
        from deepthort_local.delegation_probe import exercise
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_attachment_and_noncreative_requests_not_dispatched(self):
        self.conversations.change(self.req,'cancelled','Cancelled',allowed=('pending',))
        ident=self.conversations.submit('chat-a','project-a','chat',self.brief,attachments=['test.png'])
        self.assertIsNone(self.store.next_candidate())
        self.assertFalse(self.store.start(ident))
        self.assertEqual(self.store.next_foreground()['id'],ident)
    def test_changed_prompt_or_scope_rejected(self):
        self.assertTrue(self.store.start(self.req))
        task=self.store.claim(self.req,'multimedia')
        folder,receipt=self.stage(task)
        with self.store.db() as db:
            db.execute('UPDATE conversation_requests SET prompt=? WHERE id=?',('Changed brief',self.req))
        self.assertFalse(self.store.current(self.req))
        with self.assertRaises(DelegationError):self.store.composed(task,folder,receipt)
if __name__=='__main__':unittest.main()
