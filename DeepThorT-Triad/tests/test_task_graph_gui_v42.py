"""v42: integrated user-approved plan -> source graph -> tests -> explicit undo."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_gui_flow import FakeLocalModel


class GraphGuiTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Needs a Tk display')
    def test_graph_verified_then_manual_rollback_invalidates_previous_evidence(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);project=root/'project';project.mkdir()
            state=root/'state'
            with patch.object(mod,'STATE',state),\
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                 patch.object(mod.messagebox,'askyesno',return_value=True),\
                 patch.object(mod.messagebox,'showinfo'),\
                 patch.object(mod.messagebox,'showwarning'),\
                 patch.object(mod.messagebox,'showerror'),\
                 patch.object(mod.simpledialog,'askinteger',return_value=1):
                app=mod.DeepThorTDesktop()
                app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
                try:
                    app._set_project(project)
                    local=FakeLocalModel();app.client.chat=local.chat
                    app.input.insert('1.0','Create a Python application and its unittest')
                    app._queue_input('plan')
                    req=app.conversations.next_pending();app._execute_conversation(req)
                    self._poll(app,lambda:app.conversations.get(req['id'])['state']=='responded')
                    app._approve_conversation_plan()
                    job=app.jobs.items(str(project))[0];ident=job['id']
                    self.assertTrue(app.graphs.exists(ident))
                    self.assertEqual(len(app.checkpoints.list(ident)),1)
                    for _ in range(3):
                        app._execute_job(app.jobs.get(ident))
                        self._poll(app,lambda:app.jobs.get(ident)['state'] in
                                   ('queued','waiting_verification','needs_input'))
                    self.assertEqual(app.jobs.get(ident)['state'],'waiting_verification')
                    self.assertEqual(len(app.checkpoints.list(ident)),3)
                    self.assertTrue(all(x['state']=='saved' for x in app.jobs.steps(ident)))
                    app._project_work_once()
                    self._poll(app,lambda:app.jobs.get(ident)['state'] in ('complete','needs_input'),timeout=14)
                    self.assertEqual(app.jobs.get(ident)['state'],'complete')
                    graph=app.graphs.status(ident)
                    by_name={item['node']:item['state'] for item in graph['nodes']}
                    self.assertEqual(by_name['evidence'],'recorded')
                    self.assertEqual(by_name['verify'],'passed')
                    self.assertIsNone(graph['active_action'])
                    # Source revision selection 1 is the immutable approval baseline.
                    app.job_tree.selection_set(str(ident))
                    app._restore_source_checkpoint()
                    self.assertEqual(app.jobs.get(ident)['state'],'needs_input')
                    self.assertEqual(app.graphs.status(ident)['state'],'invalidated')
                    self.assertFalse((project/'main.py').exists())
                    self.assertFalse((project/'test_main.py').exists())
                    self.assertEqual(app.cycles.get(ident)['phase'],'needs_attention')
                    self.assertEqual(app.checkpoints.list(ident)[-1]['reason'],'restored')
                    with self.assertRaises(ValueError):
                        # v40 revoked grant: a test cannot start without new plan authority.
                        from deepthort_local.project_authority import authorize_test
                        authorize_test(state/'project-grants',app.jobs.get(ident),
                                       app.jobs.steps(ident),[mod.sys.executable,'-m','unittest','discover'],enabled=True)
                finally:app._quit()

    @staticmethod
    def _poll(app,done,timeout=10):
        finish=time.monotonic()+timeout
        while time.monotonic()<finish:
            app._handle_events();app.update_idletasks()
            if done():return
            time.sleep(.04)
        raise AssertionError('GUI event did not reach state within the test bound')

if __name__=='__main__':unittest.main()
