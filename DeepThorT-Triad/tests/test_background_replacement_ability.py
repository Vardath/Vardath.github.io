import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.background_replacement import checked,generate,review,execute
from deepthort_local.background_removal import generate as remove
from deepthort_local.texture_pixels import decode,image_module

def png(mode,size,pixels):
    b=io.BytesIO()
    with image_module().frombytes(mode,size,pixels) as im:im.save(b,format='PNG')
    return b.getvalue()
FRONT=png('RGBA',(3,1),bytes([255,0,0,255,255,0,0,128,0,0,0,0]))
SOLID={'foreground':'a.png','mode':'solid','color':[0,0,255]}
IMAGE={'foreground':'a.png','mode':'image','background':'b.png','fit':'exact'}
class ReplacementTests(unittest.TestCase):
    def test_solid_alpha_composite(self):
        out,r=generate(FRONT,SOLID)
        self.assertEqual(decode(out,('RGB',))[3],bytes([255,0,0,128,0,127,0,0,255]))
        self.assertEqual(r['background_visible_pixels'],2);self.assertTrue(r['pixel_roundtrip_verified'])
    def test_image_and_fit(self):
        bg=png('RGB',(1,1),bytes([0,255,0]))
        with self.assertRaises(ValueError):generate(FRONT,IMAGE,bg)
        out,r=generate(FRONT,dict(IMAGE,fit='stretch'),bg)
        self.assertEqual(decode(out,('RGB',))[3],bytes([255,0,0,128,127,0,0,255,0]))
        self.assertEqual(r['background_source_dimensions'],[1,1])
        with self.assertRaises(ValueError):generate(FRONT,dict(IMAGE,fit='stretch'),png('RGBA',(1,1),bytes([0,0,0,50])))
    def test_removal_pipeline_and_opaque_refusal(self):
        original=png('RGB',(2,1),bytes([0,255,0,255,0,0]))
        with self.assertRaises(ValueError):generate(original,SOLID)
        removed,_=remove(original,{'image':'a.png','mode':'color_key','key':[0,255,0],'tolerance':0,'feather':0})
        out,_=generate(removed,SOLID)
        self.assertEqual(decode(out,('RGB',))[3],bytes([0,0,255,255,0,0]))
        with self.assertRaises(ValueError):checked(dict(IMAGE,background='A.PNG'))
    def test_stale_background_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();a=root/'a.png';a.write_bytes(FRONT)
            b=root/'b.png';b.write_bytes(png('RGB',(3,1),bytes([0,255,0])*3))
            (root/'spec.json').write_text(json.dumps(IMAGE));plan,p=review(root,'spec.json','out.png')
            r=execute(root,plan);self.assertEqual(p['verification']['pixel_sha256'],r['pixel_sha256'])
            self.assertEqual(a.read_bytes(),FRONT)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'out.png').unlink();b.write_bytes(png('RGB',(3,1),bytes([0,0,0])*3))
            with self.assertRaises(ValueError):execute(root,plan)
