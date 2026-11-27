import io
import json
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from deepthort_local.pdf_layout import analyze,review,execute

def fixture():
    stream=io.BytesIO();c=Canvas(stream,pagesize=(400,300))
    c.setFont('Helvetica-Bold',18);c.drawString(30,260,'Heading')
    c.setFont('Helvetica',10);c.drawString(30,200,'Left column')
    c.drawString(240,200,'Right column')
    c.showPage();c.showPage();c.save();return stream.getvalue()
class LayoutTests(unittest.TestCase):
    def test_geometry_and_columns(self):
        r=analyze(fixture(),[1,2]);p=r['pages'][0]
        self.assertEqual(p['page_bbox_points_top_origin'],[0.,0.,400.,300.])
        self.assertEqual([x['text'] for x in p['text_segments']],['Heading','Left column','Right column'])
        self.assertEqual(p['text_segments'][0]['font_size_range_points'],[18.,18.])
        self.assertAlmostEqual(p['text_image_margins_ltrb_points'][0],30)
        self.assertFalse(p['reading_order_verified']);self.assertFalse(r['visual_render_verified'])
        self.assertIsNone(r['pages'][1]['text_image_content_bounds'])
    def test_stale_source_and_exact_report(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=fixture();(root/'a.pdf').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'document':'a.pdf','pages':[1,2]}),encoding='utf-8')
            plan,_=review(root,'spec.json','layout.json')
            self.assertEqual(execute(root,plan)['text_segments'],3)
            self.assertEqual(json.loads((root/'layout.json').read_text()),analyze(raw,[1,2]))
            plan,_=review(root,'spec.json','later.json')
            (root/'a.pdf').write_bytes(raw+b'changed')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
