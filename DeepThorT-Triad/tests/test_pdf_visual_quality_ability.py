import io
import json
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from PIL import Image,ImageDraw
from deepthort_local.pdf_visual_quality import analyze,review,execute,raster_metrics
SPEC={'document':'a.pdf','pages':[1,2,3],'minimum_margin_points':12,'allow_blank_pages':False}
def fixture():
    b=io.BytesIO();c=Canvas(b,pagesize=(300,200))
    c.rect(30,30,100,80,fill=1);c.showPage()
    c.rect(1,1,60,50,fill=1);c.showPage()
    c.showPage();c.save();return b.getvalue()
class VisualQualityTests(unittest.TestCase):
    def test_actual_render_pass_warning_and_blank(self):
        result=analyze(fixture(),SPEC)
        self.assertEqual([p['checks_passed'] for p in result['pages']],[True,False,False])
        self.assertEqual(result['pages'][1]['warnings'],['visible_content_inside_requested_margin'])
        self.assertEqual(result['pages'][2]['warnings'],['blank_or_near_white_render'])
        self.assertTrue(result['visual_raster_observed']);self.assertFalse(result['general_visual_quality_verified'])
        self.assertFalse(result['selected_checks_passed'])
    def test_color_ink_and_blank_policy(self):
        image=Image.new('RGB',(100,100),'white')
        self.assertTrue(raster_metrics(image,0,True)['checks_passed'])
        ImageDraw.Draw(image).rectangle((20,20,39,39),fill=(255,255,100))
        r=raster_metrics(image,12,False)
        self.assertEqual(r['visible_pixel_count'],400)
        self.assertEqual(r['visible_bounds_pixels'],[20,20,40,40])
        self.assertTrue(r['checks_passed'])
    def test_review_output_and_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=fixture();(root/'a.pdf').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=review(root,'spec.json','visual.json')
            self.assertFalse(execute(root,plan)['selected_checks_passed'])
            self.assertEqual(json.loads((root/'visual.json').read_text()),analyze(raw,SPEC))
            plan,_=review(root,'spec.json','later.json')
            (root/'a.pdf').write_bytes(raw+b'changed')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
