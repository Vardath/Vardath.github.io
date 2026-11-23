"""v33 dialog/approval integration: model script file and actual tool run are distinct."""
from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires desktop display')
class ScriptGuiApprovalTests(unittest.TestCase):
    def test_stages_script_only_on_first_click_then_queues_command_on_second(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);project=root/'workspace';project.mkdir()
            exe=root/'python.exe';exe.write_bytes(b'fake executable for UI only')
            with patch.object(mod,'STATE',root/'state'), \
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda app:None), \
                 patch.object(mod.DeepThorTDesktop,'_auto_start_if_installed'), \
                 patch.object(mod.messagebox,'showinfo'), \
                 patch.object(mod.messagebox,'showwarning') as warning, \
                 patch.object(mod.messagebox,'askyesno',return_value=True):
                app=mod.DeepThorTDesktop()
                app.disk_gate.gaming = lambda: False  # This fixture exercises an idle gaming PC.
                try:
                    app._set_project(project)
                    app.inventory={'tools':[{'name':'Python','location':str(exe),'found':True}]}
                    app.tool_learning.discover(app.inventory['tools'])
                    action=app.tool_learning.authorize_probe('Python',project,app.janus,user_approved=True)
                    help_path=root/'help.log';help_path.write_text('usage: python --help\n')
                    app.janus.update_action(action,'succeeded',detail='help',returncode=0,output_file=str(help_path))
                    app.tool_learning.start_learning(10,'Python',project,'Generate output.txt using a script')
                    recipe=app.tool_learning.propose_recipe(10,json.dumps({
                        'title':'Produce output file','purpose':'Create local output from an approved script',
                        'artifact':'output.txt','args':['{{script}}','{{output}}'],
                        'script':{'path':'automation/produce.py',
                                  'source':'from pathlib import Path\nimport sys\nPath(sys.argv[1]).write_text("result")\n'}}))
                    with patch.object(mod.simpledialog,'askinteger',return_value=recipe), \
                         patch.object(app,'_approve_learned_script',return_value=True) as reviewed:
                        app._run_learned_procedure()
                    self.assertTrue(reviewed.called)
                    self.assertTrue((project/'automation/produce.py').is_file())
                    self.assertEqual(len(app.janus.actions()),1)  # Only the initial help probe
                    self.assertEqual(app.tool_learning.recipes(project)[0]['status'],'candidate')
                    with patch.object(mod.simpledialog,'askinteger',return_value=recipe), \
                         patch.object(app,'_approve_learned_script',side_effect=AssertionError('already reviewed')):
                        app._run_learned_procedure()
                    self.assertEqual(len(app.janus.actions()),2)
                    self.assertEqual(app.janus.actions()[0]['status'],'approved')
                    warning.assert_not_called()
                finally:app._quit()

if __name__=='__main__':unittest.main()
