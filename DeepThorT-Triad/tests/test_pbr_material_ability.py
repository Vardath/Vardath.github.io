import io,json,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import pbr_material as p
from deepthort_local.texture_pixels import encode,decode
SPEC={'height_map':'height.png','low_rgb':[10,20,30],'high_rgb':[110,120,130],
      'roughness_low':200,'roughness_high':20,'metallic':128,'strength':2,'edge':'wrap'}
class MaterialTests(unittest.TestCase):
    def test_exact_channel_packing_and_bundle(self):
        raw=encode(2,2,'L',bytes([0,255,128,64]))
        out,r=p.generate(raw,SPEC)
        with zipfile.ZipFile(io.BytesIO(out)) as z:
            self.assertEqual(z.read('height.png'),raw)
            self.assertEqual(decode(z.read('base_color.png'),('RGB',))[3][:6],bytes([10,20,30,110,120,130]))
            self.assertEqual(decode(z.read('metallic_roughness.png'),('RGB',))[3][:6],bytes([255,200,128,255,20,128]))
            self.assertEqual(decode(z.read('normal.png'),('RGB',))[:3],(2,2,'RGB'))
            self.assertEqual(json.loads(z.read('material.json'))['maps']['metallic_roughness']['green'],'roughness')
        self.assertTrue(r['bundle_roundtrip_verified']);self.assertFalse(r['physical_properties_measured'])
    def test_invalid_channels_and_height(self):
        for change in ({'metallic':256},{'roughness_low':True},{'strength':65},{'edge':'invalid'},{'low_rgb':[0,0]}):
            with self.subTest(change=change),self.assertRaises(ValueError):p.checked(dict(SPEC,**change))
        with self.assertRaises(ValueError):p.generate(encode(2,2,'RGB',bytes(12)),SPEC)
    def test_review_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'height.png';src.write_bytes(encode(2,2,'L',bytes([0,255,128,64])))
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=p.review(root,'spec.json','material.zip')
            self.assertEqual(p.execute(root,plan)['status'],'pbr_map_bundle_verified')
            with self.assertRaises(ValueError):p.execute(root,plan)
            (root/'material.zip').unlink();src.write_bytes(encode(2,2,'L',bytes(4)))
            with self.assertRaises(ValueError):p.execute(root,plan)
            self.assertFalse((root/'material.zip').exists())
