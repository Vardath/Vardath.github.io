import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import load_workbook
from deepthort_local.spreadsheet_create import checked,review,execute

class SpreadsheetCreationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'book.json'
        self.spec={'sheets':[{'name':'Sales','headers':['Item','Amount','Rate'],'rows':[['A',12.5,.25],['=literal',20,None]],'formats':['text','decimal','percent']},
                             {'name':'Notes','headers':['Note'],'rows':[['Ready']],'formats':['general']}]}
        self.save()
    def save(self):self.source.write_text(json.dumps(self.spec),encoding='utf-8')
    def test_actual_workbook_and_formatting(self):
        plan,_=review(self.root,'book.json','book.xlsx');receipt=execute(self.root,plan)
        self.assertEqual(receipt['sheets'],2);self.assertFalse(receipt['visual_render_verified'])
        wb=load_workbook(self.root/'book.xlsx')
        try:
            self.assertEqual(wb.sheetnames,['Sales','Notes'])
            ws=wb['Sales'];self.assertEqual(ws['B2'].value,12.5);self.assertEqual(ws['B2'].number_format,'#,##0.00')
            self.assertEqual(ws['C2'].number_format,'0.0%');self.assertEqual(ws['A3'].data_type,'s')
            self.assertEqual(ws['A3'].value,'=literal');self.assertEqual(ws.freeze_panes,'A2')
            self.assertEqual(ws.auto_filter.ref,'A1:C3');self.assertTrue(ws['A1'].font.bold)
        finally:wb.close()
    def test_invalid_row_duplicate_sheet_and_format(self):
        self.spec['sheets'][0]['rows'][0].append(2)
        with self.assertRaises(ValueError):checked(self.spec)
        self.spec['sheets'][0]['rows'][0].pop()
        self.spec['sheets'][1]['name']='sales'
        with self.assertRaises(ValueError):checked(self.spec)
        self.spec['sheets'][1]['name']='Notes';self.spec['sheets'][1]['formats']=['arbitrary']
        with self.assertRaises(ValueError):checked(self.spec)
    def test_stale_and_existing_output(self):
        plan,_=review(self.root,'book.json','book.xlsx')
        out=self.root/'book.xlsx';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        self.source.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_empty_data_allowed_and_protected_paths(self):
        self.spec['sheets'][0]['rows']=[];self.save()
        plan,_=review(self.root,'book.json','book.xlsx')
        self.assertEqual(execute(self.root,plan)['data_rows'],1)
        with self.assertRaises(ValueError):review(self.root,'book.json','../other.xlsx')
        with self.assertRaises(ValueError):review(self.root,'book.json','other.xlsx',['book.json'])
