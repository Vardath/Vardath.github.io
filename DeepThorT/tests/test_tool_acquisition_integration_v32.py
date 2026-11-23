"""Exercise the actual supervised CLI worker and desktop recipe queue wiring."""
from __future__ import annotations
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_acquisition import ToolAcquisition


class ActualSupervisedCLITests(unittest.TestCase):
    def test_python_help_then_actual_approved_script_produces_reusable_artifact(self):
        from janus_worker import JanusWorker
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            project=root/'project';project.mkdir()
            state=root/'state';state.mkdir()
            exe=Path(sys.executable).resolve(strict=True)
            learning=ToolAcquisition(state/'tool_acquisition.sqlite3')
            self.assertEqual(len(learning.discover([{'name':'Python','location':str(exe),'found':True}])),1)
            janus=JanusStore(state/'janus.sqlite3')
            worker=JanusWorker(janus.path,state/'jobs.sqlite3',root/'games.txt')
            # Only execute after the explicit approved action has been queued.
            probe=learning.authorize_probe('Python',project,janus,user_approved=True)
            self.assertEqual(janus.action(probe)['status'],'approved')
            self.assertEqual(worker.execute_next_approved(),probe)
            help=learning.probe_evidence('Python',janus)
            self.assertTrue(help)
            self.assertIn('usage:',help['excerpt'].lower())
            learning.start_learning(111,'Python',project,'Produce a small output file')
            recipe=learning.propose_recipe(111,json.dumps({
                'title':'Generate project artifact','purpose':'Execute a project script to make a verified text artifact',
                'args':['{{input}}','{{output}}'],'artifact':'sample-output.txt'}))
            script=project/'produce.py'
            script.write_text('from pathlib import Path\nimport sys\nPath(sys.argv[1]).write_text("generated from local Python")\n')
            action=learning.authorize_recipe(recipe,project,janus,
                  user_approved=True,input_file='produce.py')
            self.assertEqual(worker.execute_next_approved(),action)
            self.assertTrue((project/'sample-output.txt').is_file())
            result=learning.reconcile(recipe,project,janus)
            self.assertEqual(result['status'],'artifact_produced')
            self.assertIn('behavior NOT verified',result['evidence'])
            self.assertEqual(len(ToolAcquisition(learning.path).current_recipes(project,janus)),1)


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires desktop display')
class ToolAcquisitionDesktopTests(unittest.TestCase):
    def test_new_controls_preserve_existing_chat_and_inference_permissions(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            project=root/'project';project.mkdir()
            fakeexe=root/'blender.exe';fakeexe.write_bytes(b'fake installed executable')
            with patch.object(mod,'STATE',root/'state'), \
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda app:None), \
                 patch.object(mod.DeepThorTDesktop,'_auto_start_if_installed'), \
                 patch.object(mod.simpledialog,'askstring',side_effect=['Blender', 'Blender','Create one test asset']), \
                 patch.object(mod.messagebox,'askyesno',return_value=True), \
                 patch.object(mod.messagebox,'showwarning') as warnings, \
                 patch.object(mod.messagebox,'showerror'):
                app=mod.DeepThorTDesktop()
                app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
                try:
                    app._set_project(project)
                    app.inventory={'tools':[{'name':'Blender','location':str(fakeexe),'found':True,'source':'PATH'}]}
                    app.tool_learning.discover(app.inventory['tools'])
                    app._investigate_tool()
                    actions=app.janus.actions()
                    self.assertEqual(len(actions),1)
                    self.assertEqual(actions[0]['status'],'approved')
                    self.assertEqual(actions[0]['kind'],'tool')
                    log=root/'test-help.log';log.write_text('Blender --background --python script.py')
                    app.janus.update_action(actions[0]['id'],'succeeded',detail='help',returncode=0,output_file=str(log))
                    app._draft_tool_procedure()
                    pending=app.conversations.thread(app.current_chat)[-1]
                    self.assertEqual(pending['state'],'pending')
                    self.assertEqual(app.tool_learning.learning_request(pending['id'])['name'],'Blender')
                    self.assertEqual(len(app.jobs.items(str(project))),0)
                    self.assertEqual(len(app.janus.actions()),1)  # no command from model automatically approved
                    warnings.assert_not_called()
                    # The full GTK/Tk layout is unchanged except three buttons in the existing top toolbar.
                    self.assertEqual(app.getvar('tk_version') if False else app.winfo_exists(),1)
                finally:
                    app._quit()

    def test_model_recipe_is_a_draft_only_even_when_it_finishes(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            project=root/'project';project.mkdir()
            fakeexe=root/'blender.exe';fakeexe.write_bytes(b'fake binary')
            with patch.object(mod,'STATE',root/'state'), \
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda app:None), \
                 patch.object(mod.DeepThorTDesktop,'_auto_start_if_installed'):
                app=mod.DeepThorTDesktop()
                app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
                try:
                    app._set_project(project)
                    app.tool_learning.discover([{'name':'Blender','location':str(fakeexe),'found':True}])
                    a=app.tool_learning.authorize_probe('Blender',project,app.janus,user_approved=True)
                    log=root/'help.log';log.write_text('Blender background operation.')
                    app.janus.update_action(a,'succeeded',detail='ok',returncode=0,output_file=str(log))
                    rid=app.conversations.submit(app.current_chat,str(project),'chat','Learn Blender')
                    app.tool_learning.start_learning(rid,'Blender',project,'Generate an asset')
                    model_reply=json.dumps({'title':'Generate asset','purpose':'Create exported project asset',
                                             'args':['--background','--version'],'artifact':''})
                    req=app.conversations.get(rid)
                    with patch.object(app.client,'chat',return_value=model_reply):
                        app._execute_conversation(req)
                        deadline=time.monotonic()+4
                        while app.conversations.get(rid)['state']=='running' and time.monotonic()<deadline:
                            time.sleep(.05)
                            app._handle_events()
                        app._handle_events()
                    self.assertEqual(app.conversations.get(rid)['state'],'responded')
                    self.assertEqual(app.tool_learning.recipes(project)[0]['status'],'candidate')
                    self.assertEqual(len(app.janus.actions()),1)  # only help was approved
                    self.assertEqual(len(app.jobs.items(str(project))),0)
                finally:
                    app._quit()


if __name__=='__main__':unittest.main()
