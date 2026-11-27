import json,tempfile,unittest
from pathlib import Path
from deepthort_local import image_style_transfer as t
from deepthort_local.texture_pixels import encode,decode

RAW=encode(2,2,'RGB',bytes([20,20,20,60,60,60,100,100,100,200,200,200]))
REF=encode(2,1,'RGB',bytes([10,40,100,150,200,240]))
SPEC={'image':'source.png','reference':'ref.png','strength_percent':100}

class StyleTests(unittest.TestCase):
    def test_quantile_transfer(self):
        out,r=t.generate(RAW,REF,SPEC)
        self.assertEqual(decode(out,('RGB',)),(2,2,'RGB',bytes([10,40,100]*2+[150,200,240]*2)))
        self.assertEqual(r['changed_pixels'],4)
        self.assertTrue(r['spatial_layout_preserved'])
        self.assertFalse(r['neural_style_transfer'])
    def test_strength_and_uniform_reference(self):
        ref=encode(1,1,'RGB',bytes([100,120,140]))
        out,_=t.generate(RAW,ref,dict(SPEC,strength_percent=50))
        self.assertEqual(decode(out,('RGB',))[3][:3],bytes([60,70,80]))
        with self.assertRaises(ValueError):t.checked(dict(SPEC,strength_percent=True))
        with self.assertRaises(ValueError):t.checked(dict(SPEC,reference='SOURCE.PNG'))
        with self.assertRaises(ValueError):t.generate(RAW,encode(1,1,'L',b'\x00'),SPEC)
    def test_review_guards_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW);(root/'ref.png').write_bytes(REF)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=t.review(root,'spec.json','out.png')
            self.assertEqual(t.execute(root,plan)['status'],'reference_palette_pixels_verified')
            self.assertEqual((root/'source.png').read_bytes(),RAW)
            with self.assertRaises(ValueError):t.execute(root,plan)
            (root/'out.png').unlink();(root/'ref.png').write_bytes(RAW)
            with self.assertRaises(ValueError):t.execute(root,plan)
            self.assertFalse((root/'out.png').exists())
