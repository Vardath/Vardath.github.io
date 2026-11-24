import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

class ReadyQueueDispatch(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'), 'Requires graphical desktop')
    def test_old_unapproved_chat_moves_to_conversation_not_work_queue(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(mod,'STATE',root/'state'),patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(mod.messagebox,'showerror'),patch.object(mod.messagebox,'showinfo'):
                ui=mod.DeepThorTDesktop()
                try:
                    ui.node=type('FakeNode',(),{'poll':lambda self:None,'pid':12345,'terminate':lambda self:None})()
                    ui.node_ready=True
                    ui.node_loading=False
                    ui.client.chat=lambda *args,**kwargs:'Hello from the simulated local model'
                    queued=ui.jobs.submit(str(root/'old-project'),'chat-previous','chat','Say hello')
                    ui._migrate_unapproved_requests()
                    self.assertEqual(ui.jobs.get(queued)['state'],'cancelled')
                    turn=ui.conversations.next_pending()
                    self.assertEqual(turn['source_job_id'],queued)
                    ui._scheduler_once()
                    self.assertIsNone(ui.active_job)
                    until=time.monotonic()+4
                    while time.monotonic()<until:
                        ui._handle_events()
                        if ui.conversations.get(turn['id'])['state']=='responded':break
                        time.sleep(.05)
                    self.assertEqual(ui.conversations.get(turn['id'])['state'],'responded')
                    self.assertEqual(ui.jobs.get(queued)['state'],'cancelled')
                    logs=(root/'state'/'logs'/'desktop.jsonl').read_text()
                    self.assertIn('conversation_dispatch',logs)
                finally:
                    ui._quit()

if __name__=='__main__':unittest.main()
