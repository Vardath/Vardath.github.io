"""v18: closing a chat actually cancels inference without deleting history or jobs."""
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from deepthort_local.job_queue import ChatRegistry
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.agent_plan import generate_model_plan, PlanError, build_plan_prompt


class ChatLifecycleStoreTests(unittest.TestCase):
    def test_existing_chat_registry_migrates_without_losing_threads(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'chats.db'
            with sqlite3.connect(p) as db:
                db.execute('CREATE TABLE chat_threads (id TEXT PRIMARY KEY, project TEXT, title TEXT, created_at TEXT)')
                db.execute("INSERT INTO chat_threads VALUES ('old','p','Original','2026-11-21')")
            registry=ChatRegistry(p)
            self.assertEqual(registry.list('p'),[('old','Original')])
            self.assertTrue(registry.close('old','p'))
            self.assertEqual(registry.list('p'),[])
            self.assertEqual(registry.closed('p'),[('old','Original')])
            self.assertFalse(registry.close('old','p'))
            self.assertTrue(ChatRegistry(p).reopen('old','p'))
            self.assertEqual(ChatRegistry(p).list('p'),[('old','Original')])

    def test_cancel_only_target_conversation_and_preserve_records(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'conversations.db'
            store=ConversationStore(path)
            a=store.submit('chat-a','p','draft_plan','complex old request')
            b=store.submit('chat-a','p','chat','another pending request')
            c=store.submit('chat-a','p','chat','waiting for source extraction')
            other=store.submit('chat-b','p','chat','other chat must continue')
            store.change(a,'running','processing',allowed=('pending',))
            store.change(c,'running','processing',allowed=('pending',))
            store.change(c,'waiting_sources','extracting',allowed=('running',))
            self.assertEqual(store.cancel_chat_requests('chat-a','User closed the chat'),[a,b,c])
            for ident in (a,b,c):
                self.assertEqual(store.get(ident)['state'],'cancelled')
                self.assertFalse(store.change(ident,'responded','Late stale model answer',allowed=('running',)))
            self.assertEqual(store.get(other)['state'],'pending')
            reloaded=ConversationStore(path)
            self.assertEqual(reloaded.get(a)['prompt'],'complex old request')
            self.assertEqual(reloaded.get(other)['state'],'pending')
            self.assertIsNone(reloaded.latest_draft('chat-a','p'))
            self.assertEqual(reloaded.cancel_chat_requests('chat-a'),[])

    def test_existing_model_planner_checks_cancellation_before_further_requests(self):
        class Model:
            def __init__(self):self.calls=0
            def chat(self,*args,**kwargs):
                self.calls+=1
                return '{"files": [{"path": "README.md", "description": "Build a readme"}]}'
        model=Model()
        calls=[]
        def stop_after_first():
            calls.append(True)
            return model.calls>0
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(PlanError,'stopped by user'):
                generate_model_plan(model,'id','Build an X4 Xenon PE ship with 10x cargo 4x speed',td,
                                    build_plan_prompt('Build an X4 Xenon PE ship with 10x cargo 4x speed'),
                                    max_rounds=40,cancelled=stop_after_first)
        self.assertEqual(model.calls,1)


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Tk display needed')
class CloseChatGUI(unittest.TestCase):
    def setUp(self):
        import desktop_app
        self.mod=desktop_app
        self.tmp=tempfile.TemporaryDirectory()
        self.state=patch.object(desktop_app,'STATE',Path(self.tmp.name)/'state')
        self.inventory=patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda self:None)
        self.state.start();self.inventory.start()
        self.app=desktop_app.DeepThorTDesktop()

    def tearDown(self):
        self.app._quit()
        self.inventory.stop();self.state.stop();self.tmp.cleanup()

    def _send_in(self, chat, prompt):
        self.app.current_chat=chat
        self.app.input.delete('1.0','end')
        self.app.input.insert('1.0',prompt)
        with patch.object(self.app,'_auto_start_if_installed'):
            self.app._send()
        return self.app.conversations.thread(chat)[-1]['id']

    def test_close_active_chat_stops_worker_and_keeps_second_chat_waiting(self):
        old=self.app.current_chat
        active=self._send_in(old,'Draft a complex Python project plan')
        self.app.conversations.change(active,'running','inference',allowed=('pending',))
        self.app.active_conversation=active
        self.app.node=Mock()
        self.app.node.pid=5512
        self.app.node.poll.return_value=None
        self.app.node_ready=True
        new=self.app.chats.create('(general)','Next chat')
        second=self._send_in(new,'Build my game')
        self.app.current_chat=old
        with patch.object(self.mod.messagebox,'askyesno',return_value=True):
            self.app._close_chat()
        self.assertEqual(self.app.current_chat,new)
        self.assertNotIn(old,[x[0] for x in self.app.chats.list('(general)')])
        self.assertIn(old,[x[0] for x in self.app.chats.closed('(general)')])
        self.assertEqual(self.app.conversations.get(active)['state'],'cancelled')
        self.assertEqual(self.app.conversations.get(second)['state'],'pending')
        self.assertIsNone(self.app.active_conversation)
        self.app.node.terminate.assert_called_once()
        self.assertEqual(self.app._restart_cancelled_node_pid,5512)
        # A late response/error from the cancelled thread must not clear new work.
        self.app.active_conversation=second
        self.app.conversations.change(second,'running','infer B',allowed=('pending',))
        self.app._conversation_error(active,'terminated connection')
        self.app._conversation_reply(active,'stale output')
        self.assertEqual(self.app.active_conversation,second)
        self.assertEqual(self.app.conversations.get(second)['state'],'running')

    def test_stop_queued_reply_does_not_interrupt_another_chat(self):
        a=self.app.current_chat
        active=self._send_in(a,'First chat')
        self.app.conversations.change(active,'running','A is running',allowed=('pending',))
        self.app.active_conversation=active
        self.app.node=Mock()
        self.app.node.poll.return_value=None
        b=self.app.chats.create('(general)','Second')
        second=self._send_in(b,'Second chat is queued')
        self.app._stop_chat_reply()
        self.assertEqual(self.app.conversations.get(second)['state'],'cancelled')
        self.assertEqual(self.app.active_conversation,active)
        self.assertIsNone(self.app._restart_cancelled_node_pid)
        self.app.node.terminate.assert_not_called()

    def test_stale_worker_exit_schedules_single_reload(self):
        current=self.app.current_chat
        request=self._send_in(current,'Long reply')
        self.app.conversations.change(request,'running','working',allowed=('pending',))
        self.app.active_conversation=request
        self.app.node=Mock()
        self.app.node.pid=811
        self.app.node.poll.return_value=None
        self.app._cancel_chat_replies(current,reason='Stop')
        self.app.events.put(('node_end', -15, 811))
        with patch.object(self.app,'after') as later:
            self.app._handle_events()
        self.assertIsNone(self.app._restart_cancelled_node_pid)
        self.assertIsNone(self.app.node)
        self.assertIn('restarting',self.app.model_status.get())
        self.assertTrue(any(call.args[0]==350 for call in later.call_args_list))
        # An unrelated model-exit event from an earlier process is ignored.
        newer=Mock();newer.pid=812;newer.poll.return_value=None
        self.app.node=newer;self.app.node_ready=True
        self.app.events.put(('node_end',0,811))
        self.app._handle_events()
        self.assertIs(self.app.node,newer)
        self.assertTrue(self.app.node_ready)

    def test_all_controls_fit_in_original_small_window(self):
        self.app.geometry('1138x765');self.app.update()
        chat=self.app.chat_tabs.master
        buttons=[child for child in chat.winfo_children() if child.winfo_class()=='TFrame']
        top=next(frame for frame in buttons if any(w.winfo_class()=='TButton' and w.cget('text')=='+ New chat' for w in frame.winfo_children()))
        labels=[w.cget('text') for w in top.winfo_children() if w.winfo_class()=='TButton']
        self.assertIn('Close chat',labels)
        right=self.app.winfo_rootx()+self.app.winfo_width()
        self.assertLess(max(w.winfo_rootx()+w.winfo_width() for w in top.winfo_children() if w.winfo_class()=='TButton'),right)
        controls=[w for row in self.app.chat_actions.winfo_children() for w in row.winfo_children() if w.winfo_class()=='TButton']
        self.assertIn('Stop reply',[w.cget('text') for w in controls])
        self.assertTrue(all(w.winfo_ismapped() for w in controls))
        bottom=self.app.winfo_rooty()+self.app.winfo_height()
        self.assertLessEqual(max(w.winfo_rooty()+w.winfo_height() for w in controls),bottom)

if __name__=='__main__':unittest.main()
