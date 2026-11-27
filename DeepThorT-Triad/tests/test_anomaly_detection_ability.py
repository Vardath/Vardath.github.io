import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.anomaly_detection import analyze,review,execute
SPEC={'csv':'data.csv','delimiter':',','column':'value','baseline_rows':4,
      'missing_tokens':['NA'],'iqr_multiplier':'1.5'}
RAW=b'value\n1\n2\n3\n4\n-2\n2\n8\nNA\n'
class AnomalyTests(unittest.TestCase):
    def test_exact_threshold_and_rows(self):
        r=analyze(RAW,SPEC)
        self.assertEqual(r['lower_threshold']['exact'],'-1/2')
        self.assertEqual(r['upper_threshold']['exact'],'11/2')
        self.assertEqual([x['data_row'] for x in r['examples']],[5,7])
        self.assertEqual((r['below'],r['above'],r['unflagged'],r['monitoring_missing']),(1,1,1,1))
        self.assertFalse(r['anomalies_verified'])
    def test_zero_iqr_and_missing_baseline(self):
        r=analyze(b'value\n2\n2\n2\n2\n2\n3\n',SPEC)
        self.assertTrue(r['degenerate_zero_iqr']);self.assertEqual(r['above'],1)
        with self.assertRaises(ValueError):analyze(b'value\n2\nNA\n2\n2\n3\n',SPEC)
    def test_guarded_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'data.csv').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=review(root,'spec.json','flags.json')
            self.assertEqual(execute(root,plan)['flagged'],2)
            self.assertEqual(json.loads((root/'flags.json').read_text()),analyze(RAW,SPEC))
            plan,_=review(root,'spec.json','later.json')
            (root/'data.csv').write_bytes(RAW+b'4\n')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
