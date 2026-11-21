"""User-facing JANUS/Sentinel panel regression."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Needs graphical environment')
class JanusPanelTests(unittest.TestCase):
    def test_panel_has_state_and_user_pauses_persist(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as d:
            with patch.object(mod,'STATE',Path(d)/'state'),patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None):
                app=mod.DeepThorTDesktop()
                try:
                    titles=[app.tabs.tab(x,'text') for x in app.tabs.tabs()]
                    self.assertIn('JANUS & Sentinel',titles)
                    app._show_janus_status()
                    self.assertIn('SENTINEL',app.janus_events_text.get('1.0','end'))
                    app._set_janus_paused(True)
                    self.assertTrue(app.janus.status()['paused'])
                    app._set_janus_paused(False)
                    self.assertFalse(app.janus.status()['paused'])
                    app._write_desktop_heartbeat()
                    self.assertTrue((Path(d)/'state'/'desktop-heartbeat.json').is_file())
                    self.assertIn('JANUS',app.janus_status_text.get('1.0','end'))
                finally:app._quit()

    def test_project_check_is_queued_only_after_user_confirmation(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as d:
            with patch.object(mod,'STATE',Path(d)/'state'),patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None):
                app=mod.DeepThorTDesktop()
                try:
                    app.project=Path(d)
                    app.check_choice.set('Git: status')
                    with patch.object(mod.messagebox,'askyesno',return_value=False):
                        app._run_project_check()
                    self.assertEqual(app.janus.actions(),[])
                    with patch.object(mod.messagebox,'askyesno',return_value=True):
                        app._run_project_check()
                    actions=app.janus.actions()
                    self.assertEqual(len(actions),1)
                    self.assertEqual(actions[0]['status'],'approved')
                    self.assertIn('git',actions[0]['argv_json'])
                    self.assertEqual(actions[0]['approval_source'],'desktop-user-confirmation')
                finally:app._quit()
