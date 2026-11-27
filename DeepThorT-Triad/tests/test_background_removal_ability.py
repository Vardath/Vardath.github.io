import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.background_removal import checked,generate,review,execute
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import image_module

def png(mode,size,pixels):
    b=io.BytesIO()
    with image_module().frombytes(mode,size,pixels) as im:im.save(b,format='PNG')
    return b.getvalue()
RAW=bytes([0,255,0,255,0,205,0,128,255,0,0,255])
KEY={'image':'a.png','mode':'color_key','key':[0,255,0],'tolerance':0,'feather':100}
MASK={'image':'a.png','mode':'mask','mask':'m.png'}
class RemovalTests(unittest.TestCase):
    def test_color_key_and_existing_alpha(self):
        out,r=generate(png('RGBA',(3,1),RAW),KEY)
        with decode_layer(out) as im:self.assertEqual(im.tobytes(),bytes([0,255,0,0,0,205,0,64,255,0,0,255]))
        self.assertEqual(r['transparent_pixels'],1);self.assertEqual(r['partial_alpha_pixels'],1)
        self.assertTrue(r['rgb_preserved']);self.assertFalse(r['semantic_segmentation'])
    def test_mask_exact_and_dimensions(self):
        a=png('RGBA',(3,1),RAW);m=png('L',(3,1),bytes([255,0,128]))
        out,r=generate(a,MASK,m)
        with decode_layer(out) as im:self.assertEqual(im.tobytes()[3::4],bytes([255,0,128]))
        self.assertIsNotNone(r['mask_sha256'])
        with self.assertRaises(ValueError):generate(a,MASK,png('L',(1,1),b'\xff'))
    def test_invalid_modes(self):
        for s in (dict(KEY,feather=256),dict(KEY,tolerance=True),dict(KEY,key=[0,0,256]),dict(MASK,mask='A.PNG')):
            with self.assertRaises(ValueError):checked(s)
    def test_review_nonoverwrite_and_stale_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();a=png('RGBA',(3,1),RAW)
            (root/'a.png').write_bytes(a);m=root/'m.png';m.write_bytes(png('L',(3,1),bytes([255,0,128])))
            (root/'spec.json').write_text(json.dumps(MASK));plan,p=review(root,'spec.json','out.png')
            r=execute(root,plan);self.assertEqual(p['verification']['pixel_sha256'],r['pixel_sha256'])
            self.assertEqual((root/'a.png').read_bytes(),a)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'out.png').unlink();m.write_bytes(png('L',(3,1),bytes([0,0,0])))
            with self.assertRaises(ValueError):execute(root,plan)
