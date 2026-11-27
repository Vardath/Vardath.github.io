import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.texture_pixels import encode,decode
from deepthort_local.height_map import checked,generate,review,execute
from deepthort_local.normal_map import generate as normal
SPEC={'image':'a.png','channel':'luma','black':0,'white':255,'gamma':1,'invert':False}
class HeightTests(unittest.TestCase):
    def test_luma_and_channel(self):
        raw=encode(3,1,'RGB',bytes([255,0,0,0,255,0,0,0,255]))
        out,r=generate(raw,SPEC)
        self.assertEqual(decode(out,('L',))[3],bytes([54,182,18]))
        self.assertFalse(r['physical_depth_recovered'])
        out,_=generate(raw,dict(SPEC,channel='red'))
        self.assertEqual(decode(out,('L',))[3],bytes([255,0,0]))
    def test_levels_gamma_inversion_and_normal_chain(self):
        raw=encode(4,1,'L',bytes([0,64,128,255]))
        out,_=generate(raw,dict(SPEC,black=64,white=192,gamma=2,invert=True))
        self.assertEqual(decode(out,('L',))[3],bytes([255,255,191,0]))
        normals,r=normal(out,{'strength':2,'convention':'opengl','edge':'clamp'})
        self.assertEqual(decode(normals,('RGB',))[:3],(4,1,'RGB'))
        self.assertTrue(r['pixel_roundtrip_verified'])
    def test_refuse_invalid_options(self):
        with self.assertRaises(ValueError):checked(dict(SPEC,black=200,white=100))
        with self.assertRaises(ValueError):checked(dict(SPEC,gamma=float('inf')))
        with self.assertRaises(ValueError):generate(encode(1,1,'L',b'\0'),dict(SPEC,channel='red'))
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=encode(2,2,'L',bytes([0,64,128,255]));(root/'a.png').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,p=review(root,'spec.json','height.png')
            r=execute(root,plan);self.assertEqual(p['preview_height_range'],[0,255]);self.assertTrue(r['source_unchanged'])
            self.assertEqual((root/'a.png').read_bytes(),raw);(root/'height.png').unlink()
            (root/'a.png').write_bytes(encode(1,1,'L',b'\0'))
            with self.assertRaises(ValueError):execute(root,plan)
