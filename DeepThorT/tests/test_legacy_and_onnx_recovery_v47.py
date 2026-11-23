"""v47: safely reuse historical local state, recover transport, clarify budgets."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from deepthort_local.client import LocalModelClient
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.specification_library import SpecificationIndex, sections
from deepthort_local.agent_plan import generate_model_plan, build_plan_prompt, PlanError, MAX_PLAN_ATTEMPTS


class HistoricalRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.state=self.root/'state'
        self.project=self.root/'x4mods';self.project.mkdir()
        self.other=self.root/'other';self.other.mkdir()
        self.client=LocalModelClient(self.state/'sessions.sqlite3')
        self.conv=ConversationStore(self.state/'conversations.sqlite3')
        self.req='Make an X4 extension for the Xenon PE'
        self.chat='chat-abc'
        self.first=build_plan_prompt(self.req)
        self.output=json.dumps({'files':[{'path':'content.xml','description':'X4 extension metadata for player ship'}]})
        self.old=self.conv.submit(self.chat,str(self.project),'draft_plan',self.req)

    def save_model_pair(self,session=None,prompt=None,response=None):
        with self.client._connect() as db:
            db.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',(
                (session or f'plan-{self.old}-{self.chat}-1','user',prompt or self.first),
                (session or f'plan-{self.old}-{self.chat}-1','assistant',response or self.output)))

    def test_pre_v46_exact_completed_exchange_restored(self):
        self.save_model_pair()
        self.assertEqual(self.client.historical_plan_exchange(self.first,project=self.project,
                         request=self.req,chat_id=self.chat),self.output)
        self.assertIsNone(self.client.historical_plan_exchange(self.first+'modified',project=self.project,
                         request=self.req,chat_id=self.chat))

    def test_no_cross_project_request_chat_or_attachment_reuse(self):
        self.save_model_pair()
        for project,req,chat in [(self.other,self.req,self.chat),(self.project,self.req+'x',self.chat),
                                  (self.project,self.req,self.chat+'x')]:
            self.assertIsNone(self.client.historical_plan_exchange(self.first,project=project,request=req,chat_id=chat))
        with self.conv._db() as db:
            db.execute('UPDATE conversation_requests SET attachments=? WHERE id=?',('["external.txt"]',self.old))
        self.assertIsNone(self.client.historical_plan_exchange(self.first,project=self.project,
                          request=self.req,chat_id=self.chat))

    def test_historical_exchange_must_be_adjacent_and_matched(self):
        sid=f'plan-{self.old}-{self.chat}-1'
        with self.client._connect() as db:
            db.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',(
                (sid,'user',self.first),(sid,'user','other text'),(sid,'assistant',self.output)))
        self.assertIsNone(self.client.historical_plan_exchange(self.first,project=self.project,
                          request=self.req,chat_id=self.chat))

    def test_old_structural_fragment_recovered_then_normal_validator_applies(self):
        self.save_model_pair()
        class Fake(LocalModelClient):
            def chat(self,*args,**kwargs):
                raise AssertionError('Legacy reply should be used')
        model=Fake(self.state/'sessions.sqlite3')
        with self.assertRaises(PlanError):
            generate_model_plan(model,'plan-new-'+self.chat,self.req,self.project,self.first,
                                max_rounds=1,chat_id=self.chat)
        # X4 spec requires more than an extension metadata file; the old
        # fragment was not accidentally authorized as a complete plan.
        self.assertIsNotNone(model.historical_plan_exchange(self.first,
            project=self.project,request=self.req,chat_id=self.chat))

    def test_large_document_sections_inherit_exact_progress(self):
        long_text='X4 mod: '+('Requirement of ship ownership and docking behavior.\n'*85)
        store=SpecificationIndex(self.state/'specification_index.sqlite3')
        old_id=self.conv.submit(self.chat,str(self.project),'draft_plan',long_text)
        new_id=self.conv.submit(self.chat,str(self.project),'draft_plan',long_text)
        store.index(old_id,long_text)
        store.save_response(old_id,long_text,0,self.output,project=self.project)
        store.index(new_id,long_text)
        self.assertEqual(store.inherit_exact_progress(new_id,long_text,self.project,self.chat),1)
        self.assertEqual(store.status(new_id,long_text)['reviewed'],1)
        self.assertEqual(store.inherit_exact_progress(new_id,long_text,self.project,self.chat),0)
        self.assertTrue(store.status(new_id,long_text)['pending'] >= 1)
        self.assertGreaterEqual(MAX_PLAN_ATTEMPTS,40)

    def test_large_document_progress_scope_and_corrupt_replies(self):
        long_text='X4 '+('Look for PE equipment in extracted references.\n'*85)
        store=SpecificationIndex(self.state/'specification_index.sqlite3')
        old_id=self.conv.submit(self.chat,str(self.project),'draft_plan',long_text)
        other_id=self.conv.submit('different chat',str(self.project),'draft_plan',long_text)
        store.index(old_id,long_text);store.index(other_id,long_text)
        store.save_response(old_id,long_text,0,self.output,project=self.project)
        self.assertEqual(store.inherit_exact_progress(other_id,long_text,self.project,'different chat'),0)
        # A corrupted old stored path must never be copied to new request.
        new_id=self.conv.submit(self.chat,str(self.project),'draft_plan',long_text)
        store.index(new_id,long_text)
        with store._db() as db:
            db.execute('UPDATE specification_sections SET steps_json=? WHERE request_id=? AND ordinal=?',
                       (json.dumps([{'path':'../../bad.xml','description':'unsafe escape'}]),old_id,0))
        self.assertEqual(store.inherit_exact_progress(new_id,long_text,self.project,self.chat),0)


class DesktopRecoveryTests(unittest.TestCase):
    def test_reset_is_classified_as_resume_not_permanent_failure(self):
        import desktop_app as appmodule
        # Use unbound method with a minimal mock desktop, avoiding Windows API
        # and Tk; transport handling has no direct thread or GUI dependencies.
        state=Mock();state.conversations.get.return_value={'state':'running','chat_id':'chat'}
        state.conversations.change.return_value=True
        state._model_transport_retries={}
        state._model_transport_waiting=False
        state.active_conversation=5
        state.node_ready=True
        state.node=Mock();state.node.poll.return_value=None
        state._log=Mock();state._reload_chat=Mock();state._render_reply_notice=Mock()
        state.after=Mock()
        with patch.object(appmodule,'record'):
            appmodule.DeepThorTDesktop._conversation_transport_lost(state,5,'ConnectionResetError','reset')
        state.conversations.change.assert_called_once()
        self.assertEqual(state.conversations.change.call_args.args[1],'pending')
        self.assertFalse(state.node_ready)
        self.assertTrue(state._model_transport_waiting)
        self.assertEqual(state._model_transport_retries[5],1)
        self.assertTrue(state.after.called)

    def test_transport_recovery_stops_after_two_failures(self):
        import desktop_app as appmodule
        state=Mock();state.conversations.get.return_value={'state':'running','chat_id':'chat'}
        state._model_transport_retries={5:2}
        state.node=Mock();state.node.poll.return_value=1
        state._conversation_error=Mock()
        with patch.object(appmodule,'record'):
            appmodule.DeepThorTDesktop._conversation_transport_lost(state,5,'ConnectionResetError','reset')
        state._conversation_error.assert_called_once()
        self.assertIn('two supervised recovery attempts',state._conversation_error.call_args.args[1])

    def test_busy_model_cannot_be_replayed(self):
        import desktop_app as appmodule
        state=Mock();state._explicit_model_stop=False;state._quitting=False
        state.node=Mock();state.node.poll.return_value=None
        state._model_transport_waiting=True
        state.node_ready=False
        with patch.object(appmodule,'local_server_status',return_value={'ready':True,'inference_busy':True}):
            appmodule.DeepThorTDesktop._resume_transport_if_idle(state)
        self.assertTrue(state._model_transport_waiting)
        self.assertFalse(state.node_ready)
        state.after.assert_called()

    def test_idle_model_releases_gate(self):
        import desktop_app as appmodule
        state=Mock();state._explicit_model_stop=False;state._quitting=False
        state.node=Mock();state.node.poll.return_value=None
        state._model_transport_waiting=True
        state.node_ready=False
        with patch.object(appmodule,'local_server_status',return_value={'ready':True,'inference_busy':False}):
            appmodule.DeepThorTDesktop._resume_transport_if_idle(state)
        self.assertFalse(state._model_transport_waiting)
        self.assertTrue(state.node_ready)

if __name__=='__main__': unittest.main()
