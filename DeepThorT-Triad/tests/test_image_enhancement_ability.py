import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.image_enhancement import checked,generate,review,execute
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import image_module
SPEC={'image':'source.png','brightness':100,'contrast':100,'saturation':100,'sharpness':100}
def png():
    s=io.BytesIO()
    with image_module().frombytes('RGBA',(2,1),bytes([60,80,100,77,120,140,160,255])) as im:
        im.save(s,format='PNG')
    return s.getvalue()
class EnhancementTests(unittest.TestCase):
    def test_identity_and_alpha(self):
        raw=png();out,r=generate(raw,SPEC)
        with decode_layer(raw) as a,decode_layer(out) as b:self.assertEqual(a.tobytes(),b.tobytes())
        self.assertEqual(r['changed_pixels'],0);self.assertTrue(r['alpha_preserved'])
        self.assertFalse(r['visual_quality_verified'])
    def test_brightness_and_saturation(self):
        out,r=generate(png(),dict(SPEC,brightness=50))
        with decode_layer(out) as im:self.assertEqual(im.tobytes(),bytes([30,40,50,77,60,70,80,255]))
        self.assertEqual(r['changed_pixels'],2)
        out,_=generate(png(),dict(SPEC,saturation=0))
        with decode_layer(out) as im:
            a,b=list(im.getdata())
            self.assertEqual(a[0],a[1]);self.assertEqual(a[1],a[2]);self.assertEqual(a[3],77)
            self.assertEqual(b[0],b[2]);self.assertEqual(b[3],255)
    def test_invalid_spec(self):
        for options in ({'brightness':301},{'sharpness':True},{'contrast':-1},{'saturation':1.2}):
            with self.assertRaises(ValueError):checked(dict(SPEC,**options))
    def test_review_execute_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=png()
            (root/'source.png').write_bytes(raw);(root/'spec.json').write_text(json.dumps(dict(SPEC,contrast=150,sharpness=120)))
            plan,p=review(root,'spec.json','new.png');r=execute(root,plan)
            self.assertEqual(p['source_dimensions'],[2,1]);self.assertTrue(r['pixel_roundtrip_verified'])
            self.assertEqual((root/'source.png').read_bytes(),raw)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'new.png').unlink();(root/'spec.json').write_text(json.dumps(SPEC))
            with self.assertRaises(ValueError):execute(root,plan)
