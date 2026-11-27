import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.data_transformation import review,execute,transform,checked
from deepthort_local.csv_processing import parse
class TransformationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'data.csv';self.spec=self.root/'transform.json'
        self.source.write_bytes(b'ID,Qty,Price\n001,2,1.25\n002,10,3\n003,1,5\n')
        self.data={'csv':'data.csv','delimiter':',','formula_like_cells':'reject','operations':[
            {'type':'filter','column':'Qty','operator':'ge','value':'2','mode':'decimal'},
            {'type':'derive','name':'Total','left':'Qty','operator':'multiply','right':{'column':'Price'}},
            {'type':'sort','column':'Total','mode':'decimal','descending':True},
            {'type':'rename','column':'Qty','name':'Quantity'}]}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_actual_pipeline(self):
        raw=self.source.read_bytes();plan,_=review(self.root,'transform.json','out.csv');r=execute(self.root,plan)
        h,rows=parse((self.root/'out.csv').read_bytes(),',')
        self.assertEqual(h,['ID','Quantity','Price','Total'])
        self.assertEqual(rows,[['002','10','3','30'],['001','2','1.25','2.5']])
        self.assertEqual(r['output_rows'],2);self.assertEqual(self.source.read_bytes(),raw)
    def test_invalid_numeric_and_division(self):
        self.data['operations']=[{'type':'derive','name':'X','left':'ID','operator':'divide','right':{'decimal':'0'}}]
        with self.assertRaises(ValueError):transform(self.source.read_bytes(),checked(self.data))
        self.data['operations'][0].update(left='Price',right={'decimal':'NaN'})
        with self.assertRaises(ValueError):checked(self.data)
    def test_duplicate_header_and_missing(self):
        self.data['operations']=[{'type':'rename','column':'ID','name':'Qty'}]
        with self.assertRaises(ValueError):transform(self.source.read_bytes(),checked(self.data))
        self.data['operations'][0]['column']='missing'
        with self.assertRaises(ValueError):transform(self.source.read_bytes(),checked(self.data))
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'transform.json','out.csv');out=self.root/'out.csv';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
