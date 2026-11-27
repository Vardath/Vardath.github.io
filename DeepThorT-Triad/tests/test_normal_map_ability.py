import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.texture_pixels import encode,decode
from deepthort_local.normal_map import checked,generate,review,execute
SPEC={'height_map':'h.png','strength':4,'convention':'opengl','edge':'clamp'}
class NormalTests(unittest.TestCase):
    def test_flat_and_zero_strength(self):
        raw=encode(3,2,'L',bytes([128]*6));out,r=generate(raw,SPEC)
        self.assertEqual(decode(out,('RGB',))[3],bytes([128,128,255]*6))
        self.assertTrue(r['pixel_roundtrip_verified'])
        raw=encode(3,2,'L',bytes([0,128,255]*2));out,_=generate(raw,dict(SPEC,strength=0))
        self.assertEqual(decode(out,('RGB',))[3],bytes([128,128,255]*6))
    def test_slope_convention_and_edges(self):
        raw=encode(3,3,'L',bytes([0,0,0,128,128,128,255,255,255]))
        a,_=generate(raw,SPEC);b,_=generate(raw,dict(SPEC,convention='directx'))
        pa=decode(a,('RGB',))[3];pb=decode(b,('RGB',))[3]
        self.assertGreater(pa[13],128);self.assertLess(pb[13],128)
        self.assertEqual(pa[13]+pb[13],255)
        c,_=generate(raw,dict(SPEC,edge='wrap'));self.assertNotEqual(decode(c,('RGB',))[3][:3],pa[:3])
    def test_unsupported_options_and_input(self):
        with self.assertRaises(ValueError):checked(dict(SPEC,strength=65))
        with self.assertRaises(ValueError):generate(encode(1,1,'RGB',bytes([0,0,0])),SPEC)
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=encode(2,2,'L',bytes([0,64,128,255]));(root/'h.png').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,p=review(root,'spec.json','normal.png')
            r=execute(root,plan);self.assertEqual(p['source_dimensions'],[2,2]);self.assertTrue(r['source_unchanged'])
            self.assertEqual((root/'h.png').read_bytes(),raw);(root/'normal.png').unlink()
            (root/'h.png').write_bytes(encode(1,1,'L',b'\0'))
            with self.assertRaises(ValueError):execute(root,plan)
