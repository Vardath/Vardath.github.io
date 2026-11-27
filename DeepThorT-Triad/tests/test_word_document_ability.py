import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from deepthort_local.word_document import review,execute,checked,render,W

class WordDocumentTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.src=self.root/'doc.json'
        self.data={'title':'Project report','subtitle':'Reviewed results','theme':'navy','page_size':'A4','blocks':[
            {'type':'heading','level':1,'text':'Results'},
            {'type':'paragraph','text':'Literal <text> & Unicode café 日本語.'},
            {'type':'bullets','items':['First','Second']},
            {'type':'table','headers':['Name','Value'],'rows':[['Alpha','12'],['Beta','']]}]}
        self.save()
    def save(self):self.src.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
    def test_real_editable_ooxml(self):
        original=self.src.read_bytes();plan,_=review(self.root,'doc.json','report.docx');r=execute(self.root,plan)
        self.assertEqual(r['tables'],1);self.assertEqual(r['bullet_items'],2);self.assertFalse(r['visual_render_verified'])
        with zipfile.ZipFile(self.root/'report.docx') as z:
            self.assertIsNone(z.testzip());body=ET.fromstring(z.read('word/document.xml')).find(W+'body')
            self.assertIn('Literal <text> & Unicode café 日本語.',[t.text for t in body.iter(W+'t')])
            self.assertEqual(len(list(body.iter(W+'numId'))),2)
            self.assertEqual(len(list(body.iter(W+'tblHeader'))),1)
            self.assertEqual(len(list(body.iter(W+'tc'))),6)
            styles=ET.fromstring(z.read('word/styles.xml'))
            self.assertIn('Heading1',[s.get(W+'styleId') for s in styles])
        self.assertEqual(self.src.read_bytes(),original)
    def test_invalid_structure(self):
        self.data['blocks'][0]['level']=3
        with self.assertRaises(ValueError):checked(self.data)
        self.data['blocks'][0]['level']=1;self.data['blocks'][-1]['rows'][0]=['bad']
        with self.assertRaises(ValueError):checked(self.data)
    def test_theme_and_page_size(self):
        self.data['theme']='forest';self.data['page_size']='Letter'
        raw,_=render(checked(self.data))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            b=ET.fromstring(z.read('word/document.xml')).find(W+'body')
            self.assertEqual(b.find(W+'sectPr/'+W+'pgSz').get(W+'w'),'12240')
            self.assertIn(b'315C48',z.read('word/styles.xml'))
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'doc.json','report.docx');out=self.root/'report.docx';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        self.data['title']='Changed';self.save()
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
