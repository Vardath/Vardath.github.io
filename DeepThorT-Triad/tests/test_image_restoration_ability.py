import json,tempfile,unittest
from pathlib import Path
from deepthort_local import image_restoration as r
from deepthort_local.texture_pixels import encode
from deepthort_local.image_composition import decode_layer
SPEC={'image':'source.png','mask':None,'threshold':100,'passes':1}
PIXELS=bytes([50,60,70]*12+[255,255,255]+[50,60,70]*12)
RAW=encode(5,5,'RGB',PIXELS)
MASK=encode(5,5,'L',bytes([0]*12+[255]+[0]*12))
class RestorationTests(unittest.TestCase):
    def test_impulse_and_masked_repair(self):
        for mask,s in ((None,SPEC),(MASK,dict(SPEC,mask='mask.png'))):
            out,report=r.generate(RAW,mask,s)
            with decode_layer(out) as im:
                self.assertEqual(list(im.getdata()),[(50,60,70,255)]*25)
            self.assertEqual(report['changed_pixels'],1)
            self.assertTrue(report['pixel_roundtrip_verified']);self.assertFalse(report['historical_detail_recovered'])
    def test_invalid_masks_and_settings(self):
        s=dict(SPEC,mask='mask.png')
        for raw in (encode(5,5,'L',bytes([128]*25)),encode(4,4,'L',bytes([0]*15+[255])),encode(5,5,'L',bytes([255]*25))):
            with self.assertRaises(ValueError):r.generate(RAW,raw,s)
        with self.assertRaises(ValueError):r.checked(dict(s,passes=2))
        with self.assertRaises(ValueError):r.generate(RAW,MASK,SPEC)
    def test_guarded_mask(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW);mask=root/'mask.png';mask.write_bytes(MASK)
            (root/'spec.json').write_text(json.dumps(dict(SPEC,mask='mask.png')))
            plan,_=r.review(root,'spec.json','fixed.png')
            self.assertEqual(r.execute(root,plan)['status'],'restored_pixels_verified')
            with self.assertRaises(ValueError):r.execute(root,plan)
            (root/'fixed.png').unlink();mask.write_bytes(b'changed')
            with self.assertRaises(ValueError):r.execute(root,plan)
            self.assertFalse((root/'fixed.png').exists())
