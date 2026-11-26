import json
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader
from deepthort_local.pdf_document import review,execute,checked

class PDFProductionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'report.json'
        self.doc={'title':'Project report','subtitle':'Verified draft','theme':'navy','page_size':'A4',
                  'blocks':[{'type':'heading','text':'Overview'},{'type':'paragraph','text':'A & B < C is literal text.'},
                            {'type':'bullet','text':'Next action'},
                            {'type':'table','headers':['Item','Status'],'rows':[['Alpha','Ready'],['Beta','Pending']]}]}
        self.save()
    def save(self):self.source.write_text(json.dumps(self.doc),encoding='utf-8')
    def test_actual_document_and_non_overwrite(self):
        before=self.source.read_bytes();plan,doc=review(self.root,'report.json','report.pdf')
        result=execute(self.root,plan)
        self.assertEqual(result['status'],'structurally_verified')
        self.assertTrue(result['text_presence_verified']);self.assertFalse(result['visual_render_verified'])
        self.assertEqual(before,self.source.read_bytes())
        with (self.root/'report.pdf').open('rb') as f:
            r=PdfReader(f);text=r.pages[0].extract_text()
            self.assertIn('Project report',text);self.assertIn('A & B < C',text);self.assertIn('Pending',text)
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_pagination(self):
        self.doc['blocks']=[{'type':'paragraph','text':('Paragraph number '+str(i)+' contains meaningful content. ')*12} for i in range(30)]
        self.save();plan,_=review(self.root,'report.json','long.pdf')
        self.assertGreater(execute(self.root,plan)['pages'],1)
    def test_stale_and_exclusions(self):
        plan,_=review(self.root,'report.json','report.pdf')
        self.doc['title']='Changed';self.save()
        with self.assertRaises(ValueError):execute(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'report.json','../outside.pdf')
        with self.assertRaises(ValueError):review(self.root,'report.json','report.pdf',['report.json'])
    def test_schema_and_unsupported_glyphs(self):
        self.doc['blocks']=[{'type':'script','text':'not executable'}]
        with self.assertRaises(ValueError):checked(self.doc)
        self.doc['blocks']=[{'type':'paragraph','text':'Unsupported \u4e2d'}]
        with self.assertRaises(ValueError):checked(self.doc)
