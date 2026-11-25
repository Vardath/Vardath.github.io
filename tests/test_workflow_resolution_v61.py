import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.workflow_design import WorkflowDrafts,source_binding,learn_missing
from deepthort_local.workflow_resolution import resolve

class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.request=dict(id=1,chat_id='chat',project=str(self.root),mode='draft_plan',prompt='Build a game with a mesh')
        self.drafts=WorkflowDrafts(self.root/'draft.sqlite')
        self.drafts.queue(2,source_binding(self.request),'Generate mesh')
        self.gap=dict(capability='mesh converter',goal='Export mesh',output='mesh.glb')
        self.proposal=dict(stages=[],missing=[self.gap])
        self.drafts.save(2,self.proposal,None)
    def run_resolution(self,learn,design,**kwargs):
        return resolve(self.drafts,None,None,None,None,request_id=2,request=self.request,goal='Generate mesh',
                       proposal=self.proposal,manifest=None,review=Mock(),learn=learn,design=design,**kwargs)
    def test_learned_recipe_redesign_once_and_keep_binding(self):
        learn=Mock(return_value=[dict(gap=1,state='candidate',recipe_id=9)])
        ready=dict(stages=[dict(recipe_id=9,input='')],missing=[])
        manifest={'stages':[{'output':'mesh.glb'}]}
        design=Mock(return_value=(ready,manifest))
        task={'output':'mesh.glb'}
        self.assertEqual(self.run_resolution(learn,design,mixed_task=task)[:2],(ready,manifest))
        self.assertEqual(self.drafts.get(2)['state'],'review')
        self.assertEqual(design.call_args.kwargs['mixed_task'],task)
        self.run_resolution(learn,design,mixed_task=task)
        self.assertEqual(design.call_count,1)
    def test_failed_redesign_retains_draft(self):
        learn=Mock(return_value=[dict(gap=1,state='candidate',recipe_id=9)])
        design=Mock(side_effect=ValueError('blocked'))
        self.assertEqual(self.run_resolution(learn,design)[0],self.proposal)
        self.assertEqual(self.drafts.get(2)['state'],'missing')
    def test_unknown_discovery_only_with_policy_and_once(self):
        learn=Mock(return_value=[dict(gap=1,state='needs_tool')])
        discover=Mock(return_value=[{'package_id':'Fixture.Tool'}])
        design=Mock()
        self.run_resolution(learn,design,discovery=discover)
        discover.assert_not_called()
        self.assertEqual(self.run_resolution(learn,design,discovery=discover,online=True)[3],[{'package_id':'Fixture.Tool'}])
        self.run_resolution(learn,design,discovery=discover,online=True)
        self.assertEqual(discover.call_count,1)
        design.assert_not_called()
    def test_cancel_prevents_learning(self):
        learn=Mock()
        with self.assertRaises(ValueError):self.run_resolution(learn,Mock(),cancelled=lambda:True)
        learn.assert_not_called()
    def test_generic_missing_tool_maps_only_to_reviewed_installed_name(self):
        acq=Mock();acq.enrolled.return_value=[]
        def tool(name):
            if name!='Blender':raise ValueError('not installed')
            return {}
        acq.tool.side_effect=tool
        acq.probe_evidence.return_value=None
        council=Mock();council._run.return_value='Blender'
        review=Mock()
        rows=learn_missing(self.drafts,acq,None,council,None,request_id=2,request=self.request,
                           proposal=self.proposal,review=review)
        self.assertEqual(rows,[{'gap':1,'state':'needs_help','capability':'Blender'}])
        review.assert_called_once()
        council._run.return_value='Invented application'
        rows=learn_missing(self.drafts,acq,None,council,None,request_id=2,request=self.request,
                           proposal=self.proposal,review=review)
        self.assertEqual(rows[0]['state'],'needs_tool')
        self.assertEqual(review.call_count,1)

if __name__=='__main__':unittest.main()
