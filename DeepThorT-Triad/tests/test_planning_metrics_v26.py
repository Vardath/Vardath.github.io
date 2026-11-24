"""Metrics must remain text-free and resilient to partial log writes."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.planning_metrics import report


class MetricsV26(unittest.TestCase):
    def test_empty_log_is_explicit(self):
        with tempfile.TemporaryDirectory() as root:
            result=report(root)
            self.assertEqual(result['completed_model_requests'],0)
            self.assertIsNone(result['median_seconds'])

    def test_measures_repeated_inference_and_planning_stalls(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            rows=[{'event':'request_completed','data':{'seconds':v}} for v in (10,20,30)]
            (p/'model_client.jsonl').write_text('\n'.join(map(json.dumps,rows)),encoding='utf-8')
            passes=[{'event':'model_plan_pass','data':{'net_new_files':0,'remaining_gap_count':9,'invalid_json':True,'output_token_budget':640}},
                    {'event':'model_plan_pass','data':{'net_new_files':1,'remaining_gap_count':8,'invalid_json':False,'output_token_budget':384}},
                    {'event':'model_plan_pass','data':{'net_new_files':0,'remaining_gap_count':8,'invalid_json':False,'output_token_budget':0}}]
            (p/'planner.jsonl').write_text('\n'.join(map(json.dumps,passes))+'\nINVALID JSON\n',encoding='utf-8')
            r=report(p)
            self.assertEqual((r['mean_seconds'],r['median_seconds'],r['maximum_seconds']),(20,20,30))
            self.assertEqual(r['planner_passes_logged'],3)
            self.assertEqual(r['malformed_format_passes'],1)
            self.assertEqual(r['passes_with_new_files'],1)
            self.assertEqual(r['cached_completed_passes'],1)
            self.assertEqual(r['last_remaining_gap_count'],8)
            self.assertNotIn('prompt',json.dumps(r))


if __name__=='__main__':
    unittest.main()
