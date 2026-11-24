import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.janus_engine import JanusStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.workflow_design import WorkflowDrafts,source_binding
from deepthort_local.workflow_recovery import recovery_snapshot
from deepthort_local.workflow_script_repair import repair

class ScriptRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.root=root/'project';self.root.mkdir()
        self.j=JanusStore(root/'janus.sqlite')
        self.w=ToolWorkflows(self.j);self.a=ToolAcquisition(root/'tools.sqlite')
        self.d=WorkflowDrafts(root/'draft.sqlite')
        exe=root/'python.exe';exe.write_bytes(b'fixture')
        self.a.discover([{'name':'Python','location':str(exe),'found':True}])
        helpid=self.a.authorize_probe('Python',self.root,self.j,user_approved=True)
        log=root/'help.log';log.write_text('Python script.py arguments')
        self.j.update_action(helpid,'succeeded',detail='fixture',returncode=0,output_file=str(log))
        self.recipe=self.a.propose_recipe_for_goal('Python',self.root,'Write data',json.dumps(
            dict(title='Write data script',purpose='Write data',args=['{{script}}','{{output}}'],artifact='result.json',
                 script=dict(path='tools/create.py',source='raise RuntimeError("fixture")\n'))))
        self.a.stage_script(self.recipe,self.root,root/'backups',user_approved=True)
        conversations=ConversationStore(root/'conversations.sqlite3')
        self.request=conversations.get(conversations.submit('chat',str(self.root),'draft_plan','Create JSON data'))
        manifest=freeze(self.a,self.root,[{'recipe_id':self.recipe,'input':''}],continuation=True)
        manifest['specification']=source_binding(self.request)
        self.run=self.w.approve(manifest,user_approved=True)
        self.w.tick(conversations=conversations)
        action=self.j.claim_next_action()
        self.assertIsNotNone(action)
        log=root/'failure.log';log.write_text('RuntimeError: fixture')
        self.log=log
        self.j.update_action(action['id'],'failed',detail='script failed',returncode=1,output_file=str(log))
        self.w.tick(conversations=conversations)
        self.snap=recovery_snapshot(self.w,self.run)
        self.client=Mock();self.client.chat.return_value=json.dumps({'source':'import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text("{}")\n'})
        self.review=Mock()
    def attempt(self,snap=None):
        return repair(self.d,self.a,self.w,self.client,request=self.request,recovery=snap or self.snap,review=self.review)
    def test_repair_is_distinct_and_unapproved(self):
        result=self.attempt()
        self.assertEqual(result['state'],'needs_script_review')
        self.assertNotEqual(result['recipe_id'],self.recipe)
        self.assertFalse((self.root/result['script_path']).exists())
        self.assertEqual((self.root/'tools/create.py').read_text(),'raise RuntimeError("fixture")\n')
        self.assertEqual(len(self.j.actions()),2)
        self.assertEqual(self.attempt(),result)
        self.client.chat.assert_called_once()
        self.review.assert_called_once()
    def test_changed_log_blocks_repair(self):
        self.log.write_text('changed')
        with self.assertRaises(ValueError):self.attempt()
        self.client.chat.assert_not_called()
    def test_partial_output_preserved(self):
        (self.root/'result.json').write_text('partial')
        self.assertIsNone(self.attempt(recovery_snapshot(self.w,self.run)))
        self.assertEqual((self.root/'result.json').read_text(),'partial')
        self.client.chat.assert_not_called()
    def test_rejected_correction_does_not_create_recipe(self):
        self.review.side_effect=ValueError('Sentinel rejected')
        with self.assertRaises(ValueError):self.attempt()
        self.assertEqual(len(self.a.recipes(self.root)),1)
        self.assertIsNone(self.attempt())
        self.client.chat.assert_called_once()

if __name__=='__main__':unittest.main()
