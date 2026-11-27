import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.predictive_modelling import analyze,review,execute
SPEC={'csv':'data.csv','delimiter':',','predictor':'x','target':'y','train_rows':4,'missing_tokens':['NA'],
      'predict_values':['2','10']}
RAW=b'x,y\n0,1\n1,3\n2,5\n3,7\n4,9\n5,11\n'
class PredictiveTests(unittest.TestCase):
    def test_exact_training_and_heldout(self):
        r=analyze(RAW,SPEC)
        self.assertEqual(r['coefficients']['slope']['exact'],'2')
        self.assertEqual(r['coefficients']['intercept']['exact'],'1')
        self.assertEqual(r['holdout_metrics']['mean_squared_error']['exact'],'0')
        self.assertEqual(r['holdout_metrics']['r_squared']['exact'],'1')
        self.assertEqual(r['predictions'][1]['prediction']['exact'],'21')
        self.assertTrue(r['predictions'][1]['outside_training_range'])
        self.assertFalse(r['generalisation_verified'])
    def test_no_holdout_leakage_and_missing(self):
        r=analyze(b'x,y\n0,1\n1,NA\n2,5\n3,7\n4,100\n5,100\n',SPEC)
        self.assertEqual(r['coefficients']['slope']['exact'],'2')
        self.assertEqual(r['train_missing_rows'],1)
        self.assertIsNone(r['holdout_metrics']['r_squared'])
        self.assertNotEqual(r['holdout_metrics']['mean_squared_error']['exact'],'0')
        with self.assertRaises(ValueError):analyze(b'x,y\n1,1\n1,3\n1,5\n1,7\n4,9\n5,11\n',SPEC)
    def test_source_guards_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'data.csv').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=review(root,'spec.json','fit.json')
            self.assertEqual(execute(root,plan)['holdout_rows'],2)
            self.assertEqual(json.loads((root/'fit.json').read_text()),analyze(RAW,SPEC))
            plan,_=review(root,'spec.json','later.json')
            (root/'data.csv').write_bytes(RAW+b'6,13\n')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
