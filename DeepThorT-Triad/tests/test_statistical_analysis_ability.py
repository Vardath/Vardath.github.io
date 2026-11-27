import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from deepthort_local.statistical_analysis import analyse,checked,review,execute,summary
class StatisticsTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.csv.write_text('A,B\n1,2\n2,NA\n3,4\n4,6\n',encoding='utf-8')
        self.data={'csv':'data.csv','delimiter':',','columns':['A','B'],'missing_tokens':['NA'],'variance':'sample'}
        self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_exact_descriptive_values(self):
        r=analyse(self.csv.read_bytes(),checked(self.data));a=r['columns']['A'];b=r['columns']['B']
        self.assertEqual(a['mean']['exact'],'5/2');self.assertEqual(a['q1']['exact'],'7/4')
        self.assertEqual(a['q3']['exact'],'13/4');self.assertEqual(a['variance']['exact'],'5/3')
        self.assertEqual(b['count'],3);self.assertEqual(b['missing'],1);self.assertEqual(b['variance']['exact'],'4')
    def test_empty_single_and_population(self):
        self.assertIsNone(summary([],4,'sample')['mean'])
        self.assertIsNone(summary([Fraction(2)],0,'sample')['variance'])
        self.assertEqual(summary([Fraction(2)],0,'population')['variance']['exact'],'0')
        self.data['variance']='population';a=analyse(self.csv.read_bytes(),checked(self.data))['columns']['A']
        self.assertEqual(a['variance']['exact'],'5/4')
    def test_reject_bad_numeric(self):
        with self.assertRaises(ValueError):analyse(b'A,B\nNaN,3\n',checked(self.data))
        self.data['columns']=['unknown']
        with self.assertRaises(ValueError):analyse(self.csv.read_bytes(),checked(self.data))
    def test_review_output_and_stale(self):
        original=self.csv.read_bytes();plan,preview=review(self.root,'spec.json','out.json');execute(self.root,plan)
        self.assertEqual(json.loads((self.root/'out.json').read_text()),preview['exact_report'])
        self.assertEqual(self.csv.read_bytes(),original)
        (self.root/'out.json').unlink();self.csv.write_text('A,B\n8,9\n')
        with self.assertRaises(ValueError):execute(self.root,plan)
