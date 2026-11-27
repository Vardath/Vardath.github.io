import json,tempfile,unittest
from pathlib import Path
from deepthort_local import texture_generation as t
from deepthort_local.texture_pixels import decode
SPEC={'size':64,'seed':123,'base_cells':4,'octaves':3,'persistence_percent':50,
      'low_rgb':[10,20,30],'high_rgb':[200,180,160]}
class TextureTests(unittest.TestCase):
    def test_repeatability_and_period(self):
        raw,r=t.generate(SPEC)
        self.assertEqual(t.generate(SPEC)[0],raw)
        self.assertNotEqual(t.generate(dict(SPEC,seed=124))[0],raw)
        w,h,mode,pixels=decode(raw,('RGB',));self.assertEqual((w,h,mode),(64,64,'RGB'))
        self.assertGreater(len(set(pixels[::3])),10)
        self.assertTrue(r['periodic_field_verified']);self.assertFalse(r['neural_generation_used'])
        g=t.grid(123,4,0)
        for x,y in ((3,7),(-1,63),(0,0),(31,33)):
            self.assertEqual(t.sample(g,4,x,y,64),t.sample(g,4,x+64,y-64,64))
    def test_bounds(self):
        for k,v in (('size',65),('seed',-1),('base_cells',16),('persistence_percent',0),('high_rgb',[10,20,30])):
            with self.subTest(k=k),self.assertRaises(ValueError):t.checked(dict(SPEC,**{k:v}))
    def test_review_stale_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'spec.json';src.write_text(json.dumps(SPEC))
            plan,_=t.review(root,'spec.json','tile.png')
            self.assertEqual(t.execute(root,plan)['status'],'periodic_texture_pixels_verified')
            with self.assertRaises(ValueError):t.execute(root,plan)
            (root/'tile.png').unlink();src.write_text(json.dumps(dict(SPEC,seed=124)))
            with self.assertRaises(ValueError):t.execute(root,plan)
            self.assertFalse((root/'tile.png').exists())
