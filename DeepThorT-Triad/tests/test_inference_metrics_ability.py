import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.inference_metrics import measured,runtime_counts
from deepthort_local.planning_metrics import report

class InferenceMetricsTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.state=Path(tmp.name)
    def test_real_events_all_roles_and_failed_attempts(self):
        for role in ('implementation','janus','sentinel','memory','gemma'):
            with measured(self.state,role,'native',budget_tokens=20) as data:
                data.update(input_tokens=10,generated_tokens=4,private_text='do not log')
            with self.assertRaises(RuntimeError):
                with measured(self.state,role,'native'):
                    raise RuntimeError('private exception')
        with measured(self.state,'janus','admission'):pass
        with measured(self.state,'janus','broker'):pass
        result=report(self.state/'logs')['inference_by_role']
        for role,stages in result['roles'].items():
            native=stages['native']
            self.assertEqual((native['attempts'],native['succeeded'],native['failed']),(2,1,1))
            self.assertEqual(native['generated_tokens'],4)
            self.assertEqual(native['input_tokens'],10)
        self.assertEqual(result['roles']['janus']['broker']['attempts'],1)
        for path in (self.state/'logs').glob('inference_*.jsonl'):
            raw=path.read_text('utf-8');self.assertNotIn('private',raw)
    def test_unavailable_and_invalid_counters(self):
        class Metrics:
            def get_num_input_tokens(self):return 12
            def get_num_generated_tokens(self):return True
        class Out:perf_metrics=Metrics()
        self.assertEqual(runtime_counts(Out()),{'input_tokens':12})
        self.assertEqual(runtime_counts(object()),{})
        with measured(self.state,'gemma','native'):pass
        result=report(self.state/'logs')['inference_by_role']['roles']['gemma']['native']
        self.assertIsNone(result['generated_tokens']);self.assertIsNone(result['generated_tokens_per_second'])
    def test_rotated_logs_validation_and_percentile(self):
        logs=self.state/'logs';logs.mkdir()
        def row(seconds,**kw):
            return json.dumps({'event':'inference_measurement','data':dict(role='janus',kind='native',success=True,seconds=seconds,generated_tokens=10,**kw)})
        (logs/'inference_janus.jsonl.1').write_text(row(1)+'\n'+row(2)+'\n',encoding='utf-8')
        (logs/'inference_janus.jsonl').write_text(row(10)+'\n'+row(float('nan'))+'\nINVALID\n',encoding='utf-8')
        data=report(logs)['inference_by_role']['roles']['janus']['native']
        self.assertEqual(data['attempts'],3);self.assertEqual(data['p95_seconds'],10)
        self.assertAlmostEqual(data['generated_tokens_per_second'],30/13,places=3)
    def test_recorder_failure_does_not_break_inference(self):
        with patch('deepthort_local.inference_metrics.record',side_effect=OSError('disk')):
            with measured(self.state,'janus','native'):pass
            with self.assertRaisesRegex(ValueError,'original'):
                with measured(self.state,'janus','native'):raise ValueError('original')
