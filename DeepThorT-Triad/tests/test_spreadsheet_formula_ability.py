import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook,load_workbook
from deepthort_local.spreadsheet_formula import checked,review,execute,compile_formula

class SpreadsheetFormulaTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'base.xlsx';self.spec=self.root/'formula.json'
        wb=Workbook();wb.active.title='Data';wb.active['A1']=3;wb.active['A2']=4;wb.save(self.source);wb.close()
        self.formulas=[{'sheet':'Data','cell':'B1','replace':False,'expression':{'op':'SUM','args':[{'range':'A1:A2'}]}},
                       {'sheet':'Data','cell':'B2','replace':False,'expression':{'op':'MUL','args':[{'cell':'B1'},{'literal':2}]}}]
        self.save()
    def save(self):self.spec.write_text(json.dumps({'workbook':'base.xlsx','formulas':self.formulas}),encoding='utf-8')
    def test_actual_formulas_and_review_preview(self):
        before=self.source.read_bytes();plan,preview=review(self.root,'formula.json','out.xlsx')
        self.assertEqual(preview['formulas'][0]['generated_formula'],'=SUM(A1:A2)')
        result=execute(self.root,plan);self.assertFalse(result['formula_values_recalculated'])
        wb=load_workbook(self.root/'out.xlsx')
        try:
            self.assertEqual(wb.active['B1'].value,'=SUM(A1:A2)');self.assertEqual(wb.active['B2'].value,'=(B1*2)')
            self.assertEqual(wb.active['A1'].value,3)
        finally:wb.close()
        self.assertEqual(self.source.read_bytes(),before)
    def test_unsupported_and_cycles(self):
        with self.assertRaises(ValueError):compile_formula({'op':'WEBSERVICE','args':[{'literal':'https://example.org'}]})
        with self.assertRaises(ValueError):compile_formula({'op':'SUM','args':[{'range':'Other!A1:A2'}]})
        self.formulas[0]['expression']={'op':'SUM','args':[{'range':'B1:B2'}]}
        with self.assertRaises(ValueError):checked({'workbook':'base.xlsx','formulas':self.formulas})
    def test_occupied_requires_explicit_replace(self):
        self.formulas[0]['cell']='A1';self.formulas[0]['expression']={'op':'ABS','args':[{'cell':'A2'}]}
        self.save();plan,_=review(self.root,'formula.json','out.xlsx')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.formulas[0]['replace']=True;self.save();plan,_=review(self.root,'formula.json','out.xlsx')
        self.assertEqual(execute(self.root,plan)['formulas'],2)
    def test_stale_and_literal_escape(self):
        plan,_=review(self.root,'formula.json','out.xlsx')
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
        formula,_=compile_formula({'op':'IF','args':[{'literal':True},{'literal':'a"b'},{'literal':'c'}]})
        self.assertEqual(formula,'=IF(TRUE,"a""b","c")')
