import json
import tempfile
import unittest
from pathlib import Path
from pptx import Presentation
from deepthort_local.presentation_create import review,execute,checked

class PresentationCreationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.source=self.root/'deck.json'
        self.spec={'theme':'navy','slides':[{'layout':'title','title':'Project report','body':['Current status']},
             {'layout':'bullets','title':'Next steps','body':['Inspect source','Run tests']},
             {'layout':'two_columns','title':'Comparison','body':[{'heading':'Before','points':['Manual']},{'heading':'After','points':['Automated']}]}]}
        self.save()
    def save(self):self.source.write_text(json.dumps(self.spec),encoding='utf-8')
    def test_actual_editable_slides(self):
        plan,_=review(self.root,'deck.json','deck.pptx');r=execute(self.root,plan)
        self.assertEqual(r['slides'],3);self.assertTrue(r['editable_text']);self.assertFalse(r['visual_render_verified'])
        prs=Presentation(self.root/'deck.pptx')
        self.assertEqual(len(prs.slides),3)
        self.assertIn('Run tests',[s.text for s in prs.slides[1].shapes if s.has_text_frame])
        self.assertIn('Automated',[s.text for s in prs.slides[2].shapes if s.has_text_frame])
    def test_invalid_layout_and_excessive_content(self):
        self.spec['slides'][1]['body']=['X'*111]
        with self.assertRaises(ValueError):checked(self.spec)
        self.spec['slides'][1]['body']=['X'];self.spec['slides'][1]['layout']='arbitrary'
        with self.assertRaises(ValueError):checked(self.spec)
    def test_stale_and_existing_output(self):
        plan,_=review(self.root,'deck.json','deck.pptx');out=self.root/'deck.pptx';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.source.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
    def test_protected_output(self):
        with self.assertRaises(ValueError):review(self.root,'deck.json','../deck.pptx')
        with self.assertRaises(ValueError):review(self.root,'deck.json','deck.pptx',['deck.json'])
