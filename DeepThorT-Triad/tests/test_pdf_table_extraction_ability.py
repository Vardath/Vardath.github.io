import json
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen import canvas
from deepthort_local.pdf_table_extract import review,execute,selected_pages

class PDFTableExtractionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'tables.pdf'
        c=canvas.Canvas(str(self.source),pagesize=(300,300))
        for x in (30,130,230):c.line(x,150,x,240)
        for y in (150,180,210,240):c.line(30,y,230,y)
        for i,row in enumerate((('Item','Count'),('Alpha','12'),('Beta','34'))):
            for x,value in zip((40,140),row):c.drawString(x,220-i*30,value)
        c.showPage();c.drawString(40,220,'No ruled table here');c.showPage();c.save()
    def test_real_ruled_table_and_page_provenance(self):
        before=self.source.read_bytes()
        receipt=execute(self.root,review(self.root,'tables.pdf','out.json','1,2'))
        self.assertEqual(receipt['status'],'extracted_candidates')
        result=json.loads((self.root/'out.json').read_text('utf-8'))
        self.assertEqual(result['tables'][0]['rows'],[['Item','Count'],['Alpha','12'],['Beta','34']])
        self.assertEqual(result['tables'][0]['page'],1)
        self.assertEqual(result['pages'][1]['tables'],0)
        self.assertEqual(self.source.read_bytes(),before)
        self.assertFalse(result['exhaustive_extraction_verified'])
    def test_no_table_is_explicit(self):
        receipt=execute(self.root,review(self.root,'tables.pdf','out.json','2'))
        self.assertEqual(receipt['status'],'no_supported_tables')
        self.assertEqual(receipt['tables'],0)
    def test_stale_and_no_overwrite(self):
        plan=review(self.root,'tables.pdf','out.json','1')
        (self.root/'out.json').write_text('keep',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual((self.root/'out.json').read_text('utf-8'),'keep')
        (self.root/'out.json').unlink();self.source.write_bytes(b'%PDF-changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_scope_validation(self):
        for pages in ('0','1,1','129','1-3'):
            with self.assertRaises(ValueError):selected_pages(pages)
        with self.assertRaises(ValueError):review(self.root,'tables.pdf','../out.json','1')
        with self.assertRaises(ValueError):review(self.root,'tables.pdf','out.json','1',['tables.pdf'])
        with self.assertRaises(ValueError):execute(self.root,review(self.root,'tables.pdf','out.json','3'))
