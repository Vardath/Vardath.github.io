import io,json,tempfile,unittest
from pathlib import Path
from PIL import Image
from deepthort_local import image_upscaling as u
from deepthort_local.image_composition import decode_layer
SPEC={'image':'source.png','scale':2,'method':'nearest','sharpen_percent':0}
def fixture():
    b=io.BytesIO()
    with Image.new('RGBA',(2,1)) as im:
        im.putdata([(255,0,0,255),(0,255,0,0)]);im.save(b,format='PNG')
    return b.getvalue()
class UpscaleTests(unittest.TestCase):
    def test_exact_nearest_and_alpha(self):
        raw,r=u.generate(fixture(),SPEC)
        with decode_layer(raw) as im:
            self.assertEqual(im.size,(4,2))
            self.assertEqual(list(im.getdata()),[(255,0,0,255)]*2+[(0,255,0,0)]*2+[(255,0,0,255)]*2+[(0,255,0,0)]*2)
        self.assertTrue(r['pixel_roundtrip_verified']);self.assertFalse(r['neural_super_resolution_used'])
    def test_interpolation_and_bounds(self):
        for method in ('bicubic','lanczos'):
            raw,_=u.generate(fixture(),dict(SPEC,method=method,sharpen_percent=50))
            with decode_layer(raw) as im:
                self.assertEqual(im.size,(4,2))
                self.assertTrue(all(g==0 for _,g,_,a in im.getdata() if a))
        with self.assertRaises(ValueError):u.dimensions((1025,1),SPEC)
        with self.assertRaises(ValueError):u.checked(dict(SPEC,sharpen_percent=10))
        with self.assertRaises(ValueError):u.checked(dict(SPEC,scale=True))
    def test_guarded_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'source.png';src.write_bytes(fixture())
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=u.review(root,'spec.json','large.png')
            self.assertEqual(u.execute(root,plan)['status'],'upscaled_pixels_verified')
            with self.assertRaises(ValueError):u.execute(root,plan)
            (root/'large.png').unlink();src.write_bytes(b'changed')
            with self.assertRaises(ValueError):u.execute(root,plan)
            self.assertFalse((root/'large.png').exists())
