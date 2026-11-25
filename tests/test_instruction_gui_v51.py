"""Real Tk regression: accepting an instruction does not interrupt coding."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

class GuiInstructionTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_durable_janus_inbox_does_not_interrupt_primary_request(self):
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'x4mods';project.mkdir()
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m.messagebox,'showerror') as error:
                app=m.DeepThorTDesktop()
                try:
                    app._set_project(project)
                    app.active_conversation=12345
                    app.input.insert('1.0','JANUS, check the other docking connection before continuing.')
                    app._queue_janus_instruction()
                    self.assertEqual(app.active_conversation,12345)
                    items=app.instruction_inbox.list(str(project))
                    self.assertEqual(len(items),1)
                    self.assertEqual(items[0]['state'],'pending')
                    self.assertIn('docking',items[0]['original'])
                    self.assertEqual(app.input.get('1.0','end').strip(),'')
                    self.assertEqual(app.jobs.items(str(project)),[])
                    self.assertFalse(error.called)
                    # The second worker must not be created on uncapped Linux.
                    with patch.object(m,'council_can_start',return_value=False):
                        app.node_ready=True
                        app._start_council()
                    self.assertIsNone(app.council_node)
                finally:
                    app.active_conversation=None
                    app._quit()

if __name__=='__main__':unittest.main()
