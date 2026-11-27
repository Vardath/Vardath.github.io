import json
import tempfile
import unittest
from pathlib import Path
from pptx import Presentation
from deepthort_local.presentation_edit import review,execute,package

class PresentationEditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'deck.pptx';self.spec=self.root/'edit.json'
        prs=Presentation()
        for title in ('Original','Keep'):
            slide=prs.slides.add_slide(prs.slide_layouts[0]);slide.shapes.title.text=title
        prs.save(self.source)
        self.data={'presentation':'deck.pptx','edits':[{'slide':1,'before':'Original','after':'Updated & revised'}]}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_real_edit_and_untouched_parts(self):
        raw=self.source.read_bytes();plan,_=review(self.root,'edit.json','out.pptx');r=execute(self.root,plan)
        out=self.root/'out.pptx';prs=Presentation(out)
        self.assertEqual(prs.slides[0].shapes.title.text,'Updated & revised')
        self.assertEqual(prs.slides[1].shapes.title.text,'Keep')
        a=package(raw);b=package(out.read_bytes())
        self.assertEqual([k for k in a if a[k]!=b[k]],['ppt/slides/slide1.xml'])
        self.assertEqual(self.source.read_bytes(),raw);self.assertTrue(r['untouched_part_bytes_verified'])
    def test_missing_and_ambiguous_text(self):
        self.data['edits'][0]['before']='missing';self.save()
        plan,_=review(self.root,'edit.json','out.pptx')
        with self.assertRaises(ValueError):execute(self.root,plan)
        prs=Presentation(self.source);prs.slides[0].placeholders[1].text='Original';prs.save(self.source)
        self.data['edits'][0]['before']='Original';self.save()
        plan,_=review(self.root,'edit.json','out.pptx')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_no_overwrite_and_stale(self):
        plan,_=review(self.root,'edit.json','out.pptx');out=self.root/'out.pptx';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_invalid_slide_and_excluded(self):
        self.data['edits'][0]['slide']=3;self.save()
        plan,_=review(self.root,'edit.json','out.pptx')
        with self.assertRaises(ValueError):execute(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'edit.json','out.pptx',['deck.pptx'])
