import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.time_series_forecast import analyze,review,execute
S={'csv':'series.csv','delimiter':',','date_column':'day','value_column':'v','train_rows':4,'horizon':2,'season_length':2}
RAW=b'day,v\n2026-01-01,1\n2026-01-02,3\n2026-01-03,5\n2026-01-04,7\n2026-01-05,9\n2026-01-06,11\n'
class ForecastTests(unittest.TestCase):
    def test_drift_and_dates(self):
        r=analyze(RAW,S)
        self.assertEqual(r['selected_by_holdout_mae'],'drift')
        self.assertEqual(r['holdout_metrics']['drift']['mae']['exact'],'0')
        self.assertEqual([x['value']['exact'] for x in r['forecasts']],['13','15'])
        self.assertEqual(r['forecasts'][0]['date'],'2026-01-07')
        self.assertFalse(r['independent_final_test'])
    def test_seasonal_and_invalid_gap(self):
        r=analyze(RAW.replace(b',3\n',b',2\n').replace(b',5\n',b',1\n').replace(b',7\n',b',2\n').replace(b',9\n',b',1\n').replace(b',11\n',b',2\n'),S)
        self.assertEqual(r['selected_by_holdout_mae'],'seasonal_naive')
        with self.assertRaises(ValueError):analyze(RAW.replace(b'2026-01-06',b'2026-01-08'),S)
    def test_publication_and_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'series.csv').write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
            plan,_=review(root,'spec.json','result.json')
            self.assertEqual(execute(root,plan)['horizon'],2)
            self.assertEqual(json.loads((root/'result.json').read_text()),analyze(RAW,S))
            plan,_=review(root,'spec.json','later.json')
            (root/'series.csv').write_bytes(RAW+b'2026-01-07,13\n')
            with self.assertRaises(ValueError):execute(root,plan)
