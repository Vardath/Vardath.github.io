import unittest
from deepthort_local.application_workflow_probe import exercise
from deepthort_local.video_planning import outline,scene_script
class ApplicationWorkflowTests(unittest.TestCase):
    def test_real_planning_and_acquisition_boundaries(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_reject_incomplete_scene(self):
        with self.assertRaises(ValueError):scene_script({'narration':'Missing visual'})
    def test_reject_unbounded_outline(self):
        with self.assertRaises(ValueError):outline({'title':'x','audience':'x','language':'x','style':'x','aspect':'16:9','target_seconds':301,'scenes':[{'title':'x','intent':'x'}]})
