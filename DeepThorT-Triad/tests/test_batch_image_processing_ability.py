import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from deepthort_local.batch_image_processing import checked,generate,review,execute
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import image_module

def raw(size,color):
    b=io.BytesIO()
    with image_module().new('RGBA',size,color) as im:im.save(b,format='PNG')
    return b.getvalue()
def spec():
    return {'images':[{'image':'a.png','output':'A.png'},{'image':'b.png','output':'B.png'}],
            'brightness':50,'contrast':100,'saturation':100,'sharpness':100,'max_edge':2}
class BatchTests(unittest.TestCase):
    def test_actual_resize_and_enhancement(self):
        a=raw((4,2),(120,80,40,255));b=raw((1,1),(60,80,100,77))
        out,m=generate([a,b],spec())
        with zipfile.ZipFile(io.BytesIO(out)) as z:
            self.assertEqual(z.namelist(),['A.png','B.png','manifest.json'])
            with decode_layer(z.read('A.png')) as im:
                self.assertEqual(im.size,(2,1));self.assertEqual(im.getpixel((0,0)),(60,40,20,255))
            with decode_layer(z.read('B.png')) as im:self.assertEqual(im.getpixel((0,0)),(30,40,50,77))
            self.assertEqual(json.loads(z.read('manifest.json')),m)
        self.assertFalse(m['images'][0]['alpha_preserved_exactly']);self.assertTrue(m['images'][1]['alpha_preserved_exactly'])
    def test_deterministic_bundle_no_upscale(self):
        inputs=[raw((1,1),(120,80,40,255)),raw((1,2),(60,80,100,77))]
        a,m=generate(inputs,spec());b,_=generate(inputs,spec())
        self.assertEqual(a,b);self.assertEqual(m['images'][1]['output_dimensions'],[1,2])
    def test_invalid_names_duplicates_and_bounds(self):
        s=spec();s['images'][1]['output']='../B.png'
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['images'][1]['output']='a.png'
        with self.assertRaises(ValueError):checked(s)
        s=spec();s['images'][1]['image']='A.PNG'
        with self.assertRaises(ValueError):checked(s)
        with self.assertRaises(ValueError):checked(dict(spec(),max_edge=True))
    def test_guarded_atomic_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();a=raw((2,2),(120,80,40,255));b=raw((1,1),(60,80,100,77))
            (root/'a.png').write_bytes(a);(root/'b.png').write_bytes(b);(root/'spec.json').write_text(json.dumps(spec()))
            plan,preview=review(root,'spec.json','batch.zip');r=execute(root,plan)
            self.assertEqual(r['manifest'],preview['manifest']);self.assertEqual((root/'a.png').read_bytes(),a)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'batch.zip').unlink();(root/'b.png').write_bytes(a)
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'batch.zip').exists())
