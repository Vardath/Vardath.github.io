import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.data_cleaning import review,execute,clean,checked
from deepthort_local.csv_processing import parse

class CleaningTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'raw.csv';self.spec=self.root/'clean.json'
        self.source.write_bytes(b'id,name,value\n001, A ,NA\n001,A,9\n002,B,3\n003,C,\n')
        self.data={'csv':'raw.csv','delimiter':',','trim_columns':['name'],'missing_tokens':['NA',''],
                   'missing_columns':['value'],'missing_action':'fill','fill_value':'0','deduplicate_by':['id'],'formula_like_cells':'reject'}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_actual_cleaning_and_counts(self):
        raw=self.source.read_bytes();plan,_=review(self.root,'clean.json','out.csv');r=execute(self.root,plan)
        self.assertEqual(parse((self.root/'out.csv').read_bytes(),',')[1],[['001','A','0'],['002','B','3'],['003','C','0']])
        self.assertEqual((r['filled_cells'],r['duplicate_rows_removed'],r['trimmed_cells']),(2,1,1))
        self.assertEqual(self.source.read_bytes(),raw)
    def test_drop_then_dedup(self):
        self.data.update(missing_action='drop_row',fill_value='')
        payload,r=clean(self.source.read_bytes(),checked(self.data))
        self.assertEqual(r['missing_rows_removed'],2);self.assertEqual(r['duplicate_rows_removed'],0)
        self.assertEqual(parse(payload,',')[1],[['001','A','9'],['002','B','3']])
    def test_missing_column_and_formula_policy(self):
        self.data['trim_columns']=['absent']
        with self.assertRaises(ValueError):clean(self.source.read_bytes(),checked(self.data))
        self.data['trim_columns']=[];self.data['fill_value']='=1+2'
        with self.assertRaises(ValueError):clean(self.source.read_bytes(),checked(self.data))
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'clean.json','out.csv');out=self.root/'out.csv';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
