"""Regression checks: chat must not silently wait for an unstarted model."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.diagnostics import inspect_local_setup, format_diagnostic, MIN_MODEL_BYTES


class SetupDiagnostics(unittest.TestCase):
    def test_empty_install_provides_actionable_explanation(self):
        with tempfile.TemporaryDirectory() as d:
            info = inspect_local_setup(Path(d), node_path='')
            self.assertFalse(info['ready_to_launch'])
            report = format_diagnostic(info,model_running=False,model_ready=False,model_loading=False,queued=3)
            self.assertIn('NOT RUNNING',report)
            self.assertIn('Waiting chat/jobs: 3',report)
            self.assertIn('Click Install AI',report)
            self.assertIn('not a generated AI response',report)

    def test_complete_install_passes_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'inference_server.mjs').write_text('')
            (root/'node_modules/@huggingface/transformers').mkdir(parents=True)
            weights=root/'models/onnx-community/Qwen2.5-Coder-1.5B-Instruct/onnx/model_q4.onnx'
            weights.parent.mkdir(parents=True)
            with weights.open('wb') as f:f.truncate(MIN_MODEL_BYTES)
            info=inspect_local_setup(root,node_path='C:/Program Files/nodejs/node.exe')
            self.assertTrue(info['ready_to_launch'])
            self.assertFalse(info['issues'])


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'),'Needs desktop environment')
class ActualChatUiTests(unittest.TestCase):
    def setUp(self):
        import desktop_app as mod
        self.mod=mod
        self.temp=tempfile.TemporaryDirectory()
        self.state=patch.object(mod,'STATE',Path(self.temp.name)/'state');self.state.start()
        self.inventory=patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None);self.inventory.start()
        self.app=mod.DeepThorTDesktop()

    def tearDown(self):
        self.app._quit()
        self.inventory.stop();self.state.stop();self.temp.cleanup()

    def test_send_message_is_visible_and_boots_installed_model(self):
        with patch.object(self.app,'_auto_start_if_installed') as start:
            self.app.input.insert('1.0','Can you explain what the Python logging module does?')
            self.app._send()
        self.assertEqual(start.call_count,1)
        content=self.app.chat_history.get('1.0','end')
        self.assertIn('You:',content)
        self.assertIn('Can you explain what the Python logging module does?',content)
        self.assertIn('Conversation [pending]',content)
        self.assertEqual(self.app.jobs.items('(general)'),[])
        self.assertEqual(self.app.conversations.next_pending()['mode'],'chat')
        self.app._reload_chat()
        self.assertIn('Can you explain what the Python logging module does?',self.app.chat_history.get('1.0','end'))

    def test_diagnose_without_model_does_not_fake_a_chatbot_reply(self):
        with patch.object(self.mod,'ROOT',Path(self.temp.name)):
            report=self.app._diagnose()
        self.assertIn('NOT RUNNING',report)
        self.assertIn('LOCAL COMPUTER DIAGNOSTIC',report)
        self.assertIn('not a generated AI response',self.app.chat_history.get('1.0','end'))
        self.assertFalse(self.app.node_ready)

    def test_self_diagnosis_prompt_replies_without_model_and_is_persistent(self):
        self.app.input.insert('1.0','Give me a self diagnosis of DeepThorT')
        self.app._send()
        self.assertEqual(self.app.jobs.items('(general)'),[])
        messages=self.app.client.history(self.app.current_chat)
        self.assertEqual(messages[0]['role'],'user')
        self.assertIn('self diagnosis',messages[0]['content'])
        self.assertIn('LOCAL COMPUTER DIAGNOSTIC',messages[1]['content'])
        self.assertIn('DeepThorT:',self.app.chat_history.get('1.0','end'))

    def test_normal_chat_response_has_no_executable_job(self):
        self.app.input.insert('1.0','Say hello from the coding assistant')
        with patch.object(self.app,'_auto_start_if_installed'):
            self.app._send()
        turn=self.app.conversations.next_pending()
        self.assertEqual(turn['mode'],'chat')
        self.assertEqual(self.app.jobs.items('(general)'),[])
        def fake_chat(thread,prompt,max_tokens=384,visible_prompt=None):
            with self.app.client._connect() as conn:
                conn.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',
                    [(thread,'user',visible_prompt or prompt),(thread,'assistant','Hello, local coding is connected.')])
            return 'Hello, local coding is connected.'
        with patch.object(self.app.client,'chat',side_effect=fake_chat):
            self.app._execute_conversation(turn)
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                self.app._handle_events()
                if self.app.conversations.get(turn['id'])['state']=='responded':break
                time.sleep(.03)
        self.assertEqual(self.app.conversations.get(turn['id'])['state'],'responded')
        self.assertEqual(self.app.jobs.items('(general)'),[])
        text=self.app.chat_history.get('1.0','end')
        self.assertIn('Hello, local coding is connected.',text)
        self.assertEqual(text.count('Say hello from the coding assistant'),1)

    def test_gui_chat_is_chronological_across_legacy_and_new_inbox(self):
        chat=self.app.current_chat
        with self.app.client._connect() as conn:
            for stamp,label in (("2026-11-21 00:51:00","EARLY legacy diagnostic"),
                                ("2026-11-21 00:55:23","LATE legacy diagnostic")):
                conn.execute("INSERT INTO messages(session_id,role,content,created_at) VALUES(?,?,?,?)",
                             (chat,'user',label+' prompt',stamp))
                conn.execute("INSERT INTO messages(session_id,role,content,created_at) VALUES(?,?,?,?)",
                             (chat,'assistant',label+' response',stamp))
        item=self.app.conversations.submit(chat,'(general)','chat','MIDDLE pending prompt')
        with self.app.conversations._db() as conn:
            conn.execute("UPDATE conversation_requests SET created_at=? WHERE id=?",
                         ('2026-11-21 00:53:00',item))
        self.app._reload_chat()
        shown=self.app.chat_history.get('1.0','end')
        self.assertLess(shown.index('EARLY legacy diagnostic'), shown.index('MIDDLE pending prompt'))
        self.assertLess(shown.index('MIDDLE pending prompt'), shown.index('LATE legacy diagnostic'))
        self.assertEqual(shown.count('MIDDLE pending prompt'),1)

    def test_general_chat_is_not_misclassified_as_diagnostic(self):
        self.assertFalse(self.app._is_local_diagnostic_request('How do I write a diagnostic utility in C?'))
        self.assertTrue(self.app._is_local_diagnostic_request('Please diagnose DeepThorT'))

    def test_exited_model_displays_error_and_preserves_pending_chat(self):
        with patch.object(self.mod.messagebox,'showerror') as alert:
            self.app.node_loading=True
            self.app.events.put(('log','[AI] Cannot load local model'))
            self.app.events.put(('node_end',2))
            self.app._handle_events()
        self.assertEqual(self.app.model_status.get(),'AI: STARTUP FAILED')
        self.assertIn('Cannot load local model',self.app.last_ai_error)
        alert.assert_called_once()
        self.assertIn('failed to start',self.app.chat_connection.get())


if __name__=='__main__':unittest.main()
