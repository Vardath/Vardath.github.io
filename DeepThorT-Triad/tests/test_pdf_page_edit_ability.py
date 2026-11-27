import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader,PdfWriter
from deepthort_local.pdf_page_edit import review,execute,page_plan

class PdfPageEditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'source.pdf'
        writer=PdfWriter();writer.add_blank_page(100,200);writer.add_blank_page(300,400)
        with self.source.open('wb') as f:writer.write(f)
    def test_actual_reorder_rotate_duplicate_and_preserve(self):
        before=self.source.read_bytes()
        result=execute(self.root,review(self.root,'source.pdf','out.pdf','2:90,1,2:180'))
        self.assertEqual(result['status'],'structurally_verified')
        self.assertEqual(self.source.read_bytes(),before)
        with (self.root/'out.pdf').open('rb') as f:
            reader=PdfReader(f)
            self.assertEqual([int(p.mediabox.width) for p in reader.pages],[300,100,300])
            self.assertEqual([p.rotation for p in reader.pages],[90,0,180])
        self.assertFalse(result['visual_render_verified'])
    def test_stale_source_output_and_exclusion(self):
        plan=review(self.root,'source.pdf','out.pdf','1')
        (self.root/'out.pdf').write_bytes(b'preserve')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual((self.root/'out.pdf').read_bytes(),b'preserve')
        with self.assertRaises(ValueError):review(self.root,'source.pdf','other.pdf','1',['source.pdf'])
        (self.root/'out.pdf').unlink()
        self.source.write_bytes(b'%PDF-changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_invalid_operations_and_protected_paths(self):
        for text in ('0','1:45','1,,2','129','1:360'):
            with self.assertRaises(ValueError):page_plan(text)
        with self.assertRaises(ValueError):review(self.root,'source.pdf','../out.pdf','1')
        with self.assertRaises(ValueError):execute(self.root,review(self.root,'source.pdf','out.pdf','3'))
    def test_encrypted_refused(self):
        writer=PdfWriter();writer.add_blank_page(100,100);writer.encrypt('test')
        with self.source.open('wb') as f:writer.write(f)
        with self.assertRaises(ValueError):execute(self.root,review(self.root,'source.pdf','out.pdf','1'))
        self.assertFalse((self.root/'out.pdf').exists())
