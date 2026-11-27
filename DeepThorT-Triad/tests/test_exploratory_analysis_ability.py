import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.exploratory_analysis import analyse,checked,review,execute
class EdaTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.csv.write_text('A,B,Kind\n1,2,x\n2,4,y\n2,4,y\n3,NA,x\n4,8,z\n',encoding='utf-8')
        self.data={'csv':'data.csv','delimiter':',','numeric_columns':['A','B'],'categorical_columns':['Kind'],'missing_tokens':['NA'],'top_categories':2,'correlations':True}
        self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_profile_counts_and_pairwise_correlation(self):
        r=analyse(self.csv.read_bytes(),checked(self.data))
        self.assertEqual(r['duplicate_full_rows_after_first'],1)
        self.assertEqual(r['columns']['A']['numeric_distinct'],4)
        self.assertEqual(r['columns']['B']['missing'],1)
        self.assertEqual(r['columns']['Kind']['top'],[{'value':'x','count':2},{'value':'y','count':2}])
        self.assertEqual(r['columns']['Kind']['other_count'],1)
        c=r['correlations'][0];self.assertEqual(c['paired_count'],4);self.assertEqual(c['omitted_count'],1);self.assertEqual(float(c['pearson_decimal']),1)
    def test_outliers_and_constant_pair(self):
        raw=b'A,B,Kind\n1,2,x\n1,2,x\n1,2,x\n1,2,x\n100,2,x\n'
        r=analyse(raw,checked(self.data))
        self.assertEqual(r['columns']['A']['iqr_flags']['above'],1)
        self.assertIsNone(r['correlations'][0]['pearson_decimal'])
        self.assertEqual(r['correlations'][0]['reason'],'constant_column')
    def test_invalid_numeric_and_duplicate_types(self):
        with self.assertRaises(ValueError):analyse(b'A,B,Kind\nbad,2,x\n',checked(self.data))
        self.data['categorical_columns']=['A']
        with self.assertRaises(ValueError):checked(self.data)
    def test_exact_output_and_stale(self):
        original=self.csv.read_bytes();plan,preview=review(self.root,'spec.json','out.json');execute(self.root,plan)
        self.assertEqual(json.loads((self.root/'out.json').read_text()),preview['exact_report'])
        self.assertEqual(self.csv.read_bytes(),original)
        (self.root/'out.json').unlink();self.csv.write_text('A,B,Kind\n7,8,x\n')
        with self.assertRaises(ValueError):execute(self.root,plan)
