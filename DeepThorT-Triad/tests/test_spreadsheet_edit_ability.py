import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font
from deepthort_local.spreadsheet_edit import review,execute

class SpreadsheetEditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'base.xlsx';self.spec=self.root/'edits.json'
        wb=Workbook();ws=wb.active;ws.title='Data';ws['A1']=10;ws['A1'].font=Font(bold=True);ws['B1']='=A1*2';ws['C1']='Keep'
        wb.create_sheet('Other')['A1']=7;wb.save(self.source);wb.close()
        self.edits=[{'sheet':'Data','cell':'A1','value':25},{'sheet':'Data','cell':'A2','value':'=literal'},{'sheet':'Data','cell':'C1','value':None}]
        self.save()
    def save(self):self.spec.write_text(json.dumps({'workbook':'base.xlsx','edits':self.edits}),encoding='utf-8')
    def test_actual_edit_and_preservation(self):
        raw=self.source.read_bytes();plan,_=review(self.root,'edits.json','out.xlsx');receipt=execute(self.root,plan)
        wb=load_workbook(self.root/'out.xlsx')
        try:
            self.assertEqual(wb['Data']['A1'].value,25);self.assertTrue(wb['Data']['A1'].font.bold)
            self.assertEqual(wb['Data']['B1'].value,'=A1*2');self.assertEqual(wb['Data']['A2'].data_type,'s')
            self.assertIsNone(wb['Data']['C1'].value);self.assertEqual(wb['Other']['A1'].value,7)
        finally:wb.close()
        self.assertEqual(self.source.read_bytes(),raw);self.assertFalse(receipt['formula_values_recalculated'])
    def test_formula_target_refused(self):
        self.edits=[{'sheet':'Data','cell':'B1','value':0}];self.save()
        plan,_=review(self.root,'edits.json','out.xlsx')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse((self.root/'out.xlsx').exists())
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'edits.json','out.xlsx')
        (self.root/'out.xlsx').write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual((self.root/'out.xlsx').read_bytes(),b'keep')
        (self.root/'out.xlsx').unlink();self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_duplicate_and_excluded(self):
        self.edits.append(dict(self.edits[0]));self.save()
        with self.assertRaises(ValueError):review(self.root,'edits.json','out.xlsx')
        self.edits.pop();self.save()
        with self.assertRaises(ValueError):review(self.root,'edits.json','out.xlsx',['base.xlsx'])
