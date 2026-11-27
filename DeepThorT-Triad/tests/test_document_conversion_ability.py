import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from deepthort_local.document_conversion import review,execute

class DocumentConversionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'source.txt'
        self.source.write_text('First paragraph\n\nSecond & third < literal\n',encoding='utf-8')
    def convert(self,a,b):
        return execute(self.root,review(self.root,a,b))
    def test_actual_docx_roundtrip(self):
        before=self.source.read_bytes()
        receipt=self.convert('source.txt','out.docx')
        self.assertFalse(receipt['layout_preserved'])
        self.convert('out.docx','roundtrip.txt')
        self.assertEqual((self.root/'roundtrip.txt').read_text('utf-8'),self.source.read_text('utf-8'))
        self.assertEqual(self.source.read_bytes(),before)
    def test_actual_pdf_conversion(self):
        self.convert('source.txt','out.pdf')
        with (self.root/'out.pdf').open('rb') as f:
            self.assertIn('Second & third',PdfReader(f).pages[0].extract_text())
        self.convert('out.pdf','extracted.txt')
        self.assertIn('First paragraph',(self.root/'extracted.txt').read_text('utf-8'))
    def test_pdf_missing_text_page_refused(self):
        c=canvas.Canvas(str(self.root/'scan.pdf'))
        c.drawString(40,700,'Visible text');c.showPage();c.rect(40,40,100,100);c.showPage();c.save()
        with self.assertRaises(ValueError):self.convert('scan.pdf','out.txt')
        self.assertFalse((self.root/'out.txt').exists())
    def test_stale_output_and_unsafe_paths(self):
        plan=review(self.root,'source.txt','out.docx')
        (self.root/'out.docx').write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual((self.root/'out.docx').read_bytes(),b'keep')
        (self.root/'out.docx').unlink();self.source.write_text('changed',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'source.txt','../out.docx')
        with self.assertRaises(ValueError):review(self.root,'source.txt','out.docx',['source.txt'])
