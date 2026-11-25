"""Loading status must reflect elapsed time, not imaginary progress."""
import os, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.diagnostics import format_diagnostic, inspect_local_setup

class LoadingDiagnostics(unittest.TestCase):
    def test_diagnostic_reports_elapsed_without_fake_percentage(self):
        with tempfile.TemporaryDirectory() as d:
            info=inspect_local_setup(Path(d),node_path='C:/node.exe')
        report=format_diagnostic(info,model_running=True,model_ready=False,model_loading=True,queued=1,loading_seconds=246)
        self.assertIn('4m 06s',report)
        self.assertIn('no verified percentage',report)

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Needs desktop')
class LoadingUI(unittest.TestCase):
    def test_loading_status_is_elapsed_and_not_fake_percent(self):
        import desktop_app
        with tempfile.TemporaryDirectory() as d, patch.object(desktop_app,'STATE',Path(d)/'state'), patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda self:None):
            app=desktop_app.DeepThorTDesktop()
            try:
                app.node_loading=True
                app.node_started=time.monotonic()-185
                with patch.object(desktop_app.threading,'Thread'):
                    app._poll_server()
                self.assertIn('3m',app.model_status.get())
                self.assertIn('Check Processes',app.chat_connection.get())
            finally:app._quit()
