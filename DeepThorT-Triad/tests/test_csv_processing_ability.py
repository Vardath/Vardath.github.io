import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.csv_processing import review,execute,parse,formula_like

class CSVProcessingTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'data.csv';self.spec=self.root/'process.json'
        self.source.write_bytes(b'item,notes,amount\r\n001,"quoted, text",-1.5\r\n002,"multi\r\nline",20\r\n003,last,30\r\n')
        self.data={'csv':'data.csv','input_delimiter':',','output_delimiter':';','columns':['amount','item','notes'],
                   'start_row':2,'row_count':1,'formula_like_cells':'reject'}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_actual_projection_window_and_multiline(self):
        raw=self.source.read_bytes();plan,_=review(self.root,'process.json','out.csv');r=execute(self.root,plan)
        self.assertEqual(r['source_rows'],3);self.assertEqual(r['output_rows'],1)
        header,rows=parse((self.root/'out.csv').read_bytes(),';')
        self.assertEqual(header,['amount','item','notes']);self.assertEqual(rows,[['20','002','multi\r\nline']])
        self.assertEqual(self.source.read_bytes(),raw)
    def test_formula_like_policy(self):
        self.source.write_bytes(b'item,notes,amount\n001,=1+2,-1.5\n')
        self.data['start_row']=1;self.save();plan,_=review(self.root,'process.json','out.csv')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.data['formula_like_cells']='preserve';self.save();plan,_=review(self.root,'process.json','out.csv')
        self.assertEqual(execute(self.root,plan)['formula_like_cells_preserved'],1)
        self.assertFalse(formula_like('-1.5'));self.assertTrue(formula_like('  =1+2'))
    def test_bad_csv_and_missing_column(self):
        for raw in (b'a,a\n1,2\n',b'a,b\n1\n',b'a,b\n"unfinished,2\n'):
            with self.assertRaises(ValueError):parse(raw,',')
        self.data['columns']=['absent'];self.save();plan,_=review(self.root,'process.json','out.csv')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_stale_excluded_and_no_overwrite(self):
        plan,_=review(self.root,'process.json','out.csv');out=self.root/'out.csv';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'process.json','../out.csv')
        with self.assertRaises(ValueError):review(self.root,'process.json','out.csv',['data.csv'])
