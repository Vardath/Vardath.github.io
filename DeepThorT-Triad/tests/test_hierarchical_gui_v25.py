"""Real Tk chat/approval wiring with the v25 durable milestone scheduler."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk display')
class HierarchicalGuiV25(unittest.TestCase):
    def test_roadmap_never_queues_until_approval_and_earlier_verification(self):
        import desktop_app as mod
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            project=path/'development';project.mkdir()
            with patch.object(mod,'STATE',path/'state'), \
                 patch.object(mod.DeepThorTDesktop,'_refresh_inventory',lambda self: None), \
                 patch.object(mod.messagebox,'askyesno',return_value=True), \
                 patch.object(mod.messagebox,'showinfo') as info, \
                 patch.object(mod.messagebox,'showwarning'), \
                 patch.object(mod.messagebox,'showerror') as error:
                app=mod.DeepThorTDesktop()
                try:
                    app._set_project(project)
                    original=''.join(f'Milestone requirement {i}: '+'x'*3100+'\n' for i in range(1,4))
                    request_id=app.conversations.submit(app.current_chat,str(project),'draft_plan',original)
                    app.conversations.change(request_id,'running','Preparing roadmap',allowed=('pending',))
                    app.active_conversation=request_id
                    app.specifications.index(request_id,original)
                    for i in range(1,4):
                        item=app.specifications.next_section(request_id,original)
                        self.assertIsNotNone(item)
                        model_response=json.dumps({'files':[{'path':f'src/system{i}.py',
                                                  'description':f'Implement subsystem {i} and tests'}]})
                        app.specifications.save_response(request_id,original,item['ordinal'],
                                                         model_response,project=project)
                    roadmap=app.hierarchies.prepare(app.specifications,request_id,original,
                                                      project,chat_id=app.current_chat)
                    self.assertEqual(roadmap['milestones_total'],3)
                    app._conversation_reply(request_id,json.dumps({'hierarchy_ready':roadmap}))
                    self.assertEqual(app.conversations.get(request_id)['state'],'responded')
                    self.assertEqual(app.jobs.items(str(project)),[])
                    self.assertIsNone(app.conversations.latest_draft(app.current_chat,str(project)))
                    app._approve_conversation_plan()
                    jobs=app.jobs.items(str(project))
                    self.assertEqual(len(jobs),1)
                    self.assertEqual(jobs[0]['approval_key'].split(':')[0],'milestone')
                    app._approve_conversation_plan()
                    self.assertEqual(len(app.jobs.items(str(project))),1)
                    self.assertTrue(info.called)
                    first=jobs[0]['id']
                    for step in app.jobs.steps(first):
                        app.jobs.set_step(step['id'],'saved','Approved content saved')
                    app.jobs.change(first,'running','Verify',allowed=('queued',))
                    app.jobs.change(first,'complete','Verified: test command exited 0 (test)',allowed=('running',))
                    app._approve_conversation_plan()
                    self.assertEqual(len(app.jobs.items(str(project))),2)
                    self.assertEqual(app.hierarchies.status(app.specifications,request_id,original)['milestones_verified'],1)
                    error.assert_not_called()
                finally:
                    app._quit()


if __name__=='__main__':
    unittest.main()
