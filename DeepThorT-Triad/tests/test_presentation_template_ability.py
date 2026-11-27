import json
import tempfile
import unittest
from pathlib import Path
from pptx import Presentation
from deepthort_local.presentation_template import review,execute,checked
from deepthort_local.presentation_edit import package

class TemplateTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'template.pptx';self.spec=self.root/'fill.json'
        prs=Presentation()
        for title in ('{{TITLE}}','{{TITLE}}'):
            s=prs.slides.add_slide(prs.slide_layouts[0]);s.shapes.title.text=title;s.placeholders[1].text='{{SUBTITLE}}' if len(prs.slides)==1 else 'Keep'
        prs.save(self.source)
        self.data={'template':'template.pptx','values':{'TITLE':'New title','SUBTITLE':'Reviewed content'}}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_actual_template_and_preserved_parts(self):
        raw=self.source.read_bytes();plan,preview=review(self.root,'fill.json','out.pptx');r=execute(self.root,plan)
        self.assertEqual(len(preview['resolved_replacements']),3);self.assertEqual(r['placeholders_filled'],3)
        prs=Presentation(self.root/'out.pptx')
        self.assertEqual(prs.slides[0].shapes.title.text,'New title')
        self.assertEqual(prs.slides[1].shapes.title.text,'New title')
        self.assertEqual(prs.slides[0].placeholders[1].text,'Reviewed content')
        a=package(raw);b=package((self.root/'out.pptx').read_bytes())
        self.assertEqual({k for k in a if a[k]!=b[k]},{'ppt/slides/slide1.xml','ppt/slides/slide2.xml'})
        self.assertEqual(self.source.read_bytes(),raw)
    def test_missing_unused_and_placeholder_in_replacement(self):
        del self.data['values']['SUBTITLE'];self.save()
        with self.assertRaises(ValueError):review(self.root,'fill.json','out.pptx')
        self.data['values'].update(SUBTITLE='Subtitle',UNUSED='Extra');self.save()
        with self.assertRaises(ValueError):review(self.root,'fill.json','out.pptx')
        self.data['values']['TITLE']='{{OTHER}}'
        with self.assertRaises(ValueError):checked(self.data)
    def test_ambiguous_template(self):
        prs=Presentation(self.source);prs.slides[0].placeholders[1].text='{{TITLE}}';prs.save(self.source)
        with self.assertRaises(ValueError):review(self.root,'fill.json','out.pptx')
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'fill.json','out.pptx');out=self.root/'out.pptx';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
