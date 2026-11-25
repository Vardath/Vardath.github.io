import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from deepthort_local.workflow_design import WorkflowDrafts,source_binding
from deepthort_local.workflow_resume import resume,observations
from deepthort_local.conversation_workflow import ConversationStore

class WorkflowResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.c=ConversationStore(root/'chat.sqlite')
        self.d=WorkflowDrafts(root/'workflow.sqlite')
        self.source=self.c.get(self.c.submit('chat',str(root),'draft_plan','Build a mesh game'))
        self.ident=self.c.submit('chat',str(root),'chat','Design workflow')
        self.d.queue(self.ident,source_binding(self.source),'Create mesh')
        self.proposal={'stages':[],'missing':[{'capability':'Blender','goal':'Create mesh','output':'mesh.glb'}]}
        self.d.save(self.ident,self.proposal,None)
        self.c.change(self.ident,'responded','missing')
    def wake(self,tokens):
        with patch('deepthort_local.workflow_resume.observations',return_value=tokens):
            return resume(self.d,self.c,None,None,self.source)
    def test_only_positive_new_evidence_resumes_same_request(self):
        self.assertIsNone(self.wake(['a']))
        self.assertIsNone(self.wake([]))
        self.assertIsNone(self.wake(['a']))
        task={'output':'mesh.glb'}
        self.d.bind_mixed(self.ident,task)
        self.assertEqual(self.wake(['a','b']),self.ident)
        self.assertEqual(self.c.get(self.ident)['state'],'pending')
        self.assertEqual(self.d.mixed(self.ident),task)
        self.assertEqual(self.d.get(self.ident)['state'],'missing')
        self.assertIsNone(self.wake(['a','b','c']))
    def test_retry_budget_survives_restart(self):
        self.d.observe_resume(self.ident,['original'])
        for i in range(3):
            self.d=WorkflowDrafts(self.d.path)
            self.assertEqual(self.wake([str(i)]),self.ident)
            self.c.change(self.ident,'responded','still missing')
        self.assertIsNone(self.wake(['fourth']))
    def test_amendment_and_cancel_block_resume(self):
        self.d.observe_resume(self.ident,['a'])
        self.c.change(self.ident,'cancelled','user cancelled')
        self.assertIsNone(self.wake(['b']))
        self.c.change(self.ident,'responded','fixture')
        self.c.amend_project('chat',self.source['project'],'Use other geometry')
        self.assertIsNone(self.wake(['c']))
    def test_observed_help_and_exact_recipe_evidence(self):
        a=Mock();a.enrolled.return_value=[]
        a.tool.return_value={'executable_signature':'sig','probe_action':1}
        a.probe_evidence.return_value={'sha256':'help'}
        a.recipes.return_value=[{'artifact':'unrelated.glb'},{'artifact':'mesh.glb','id':7,
             'executable_signature':'sig','args_json':'["{{output}}"]','script_saved_sha':''}]
        a.script_needs_review.return_value=False
        result=observations(a,None,self.source['project'],self.proposal)
        self.assertEqual(len(result),3)
        a.tool.assert_called_once_with('Blender')
        a.probe_evidence.return_value=None
        self.assertEqual(len(observations(a,None,self.source['project'],self.proposal)),2)

if __name__=='__main__':unittest.main()
