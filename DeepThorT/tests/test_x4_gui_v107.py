"""GUI smoke tests for X4 source discovery and fail-closed planning."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

class X4DesktopSmokeTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Needs virtual desktop or Windows')
    def test_x4_without_verified_sources_blocks_draft_outside_work_queue(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'x4mods';project.mkdir()
            with patch.object(mod,'STATE',root/'state'),\
                 patch('deepthort_local.x4_sources.likely_installations',return_value=[]),\
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                 patch.object(mod.messagebox,'showwarning'),\
                 patch.object(mod.messagebox,'showerror'),\
                 patch.object(mod.filedialog,'askdirectory',return_value=''):
                app=mod.DeepThorTDesktop()
                try:
                    app._set_project(project)
                    self.assertTrue(hasattr(app,'x4_source_info'))
                    app._inspect_x4_sources()
                    end=time.monotonic()+4
                    while time.monotonic()<end and app.x4_report is None:
                        app._handle_events();time.sleep(.02)
                    self.assertIsNotNone(app.x4_report)
                    self.assertFalse(app.x4_report['ready_for_planning'])
                    app.input.insert('1.0','Make an X4 Xenon PE extension with 4x base speed, 10x cargo and 60-second respawn')
                    app._queue_input('plan')
                    req=app.conversations.next_pending()
                    self.assertEqual(req['mode'],'draft_plan')
                    def fail_model(*args,**kwargs):raise AssertionError('should not call model for unsupported X4 plan')
                    app.client.chat=fail_model
                    app._execute_conversation(req)
                    end=time.monotonic()+4
                    while time.monotonic()<end and app.conversations.get(req['id'])['state']=='running':
                        app._handle_events();time.sleep(.02)
                    self.assertEqual(app.conversations.get(req['id'])['state'],'failed')
                    self.assertIn('could not locate the installation',app.conversations.get(req['id'])['detail'])
                    self.assertEqual(app.jobs.items(str(project)),[])
                finally:app._quit()

if __name__=='__main__':unittest.main()
