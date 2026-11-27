import json,tempfile,unittest
from pathlib import Path
from deepthort_local import image_colourisation as c
from deepthort_local.texture_pixels import encode,decode
RAW=encode(2,2,'L',bytes([100,120,140,160]))
A=encode(2,2,'L',bytes([255,0,0,0]))
B=encode(2,2,'L',bytes([0,255,0,0]))
SPEC={'image':'gray.png','regions':[{'mask':'a.png','rgb':[255,0,0],'strength_percent':80},{'mask':'b.png','rgb':[0,0,255],'strength_percent':80}]}
class ColourTests(unittest.TestCase):
    def test_luma_and_regions(self):
        out,r=c.generate(RAW,[A,B],SPEC);w,h,mode,p=decode(out,('RGB',))
        self.assertEqual((w,h,mode),(2,2,'RGB'));self.assertGreater(p[0],p[1]);self.assertGreater(p[5],p[3])
        self.assertEqual(p[6:],bytes([140]*3+[160]*3))
        self.assertLessEqual(r['maximum_encoded_luma_error'],.500001)
        self.assertTrue(r['unmasked_grayscale_preserved']);self.assertFalse(r['historical_color_verified'])
    def test_invalid_masks(self):
        with self.assertRaises(ValueError):c.generate(RAW,[A,A],SPEC)
        with self.assertRaises(ValueError):c.generate(RAW,[A,encode(2,2,'L',bytes([128]*4))],SPEC)
        with self.assertRaises(ValueError):c.generate(RAW,[A],SPEC)
        with self.assertRaises(ValueError):c.checked(dict(SPEC,regions=SPEC['regions']*2))
    def test_review_and_changed_mask(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'gray.png').write_bytes(RAW);(root/'a.png').write_bytes(A);(root/'b.png').write_bytes(B)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=c.review(root,'spec.json','color.png')
            self.assertEqual(c.execute(root,plan)['status'],'regional_colour_pixels_verified')
            with self.assertRaises(ValueError):c.execute(root,plan)
            (root/'color.png').unlink();(root/'b.png').write_bytes(A)
            with self.assertRaises(ValueError):c.execute(root,plan)
            self.assertFalse((root/'color.png').exists())
