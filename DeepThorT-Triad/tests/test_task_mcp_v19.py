import unittest
from deepthort_local.task_mcp_probe import exercise
class TaskMCPTests(unittest.TestCase):
    def test_task_bound_mcp_integration(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
