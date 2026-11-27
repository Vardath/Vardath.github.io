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


    def test_game_sprite_atlas_pixels_and_animation(self):
        import io,zipfile
        from deepthort_local.game_asset_generation import generate,checked
        from deepthort_local.texture_pixels import image_module
        s={'size':8,'palette':{'A':[10,20,30,255],'B':[40,50,60,128]},
           'sprites':[{'name':'idle','rows':['A.......']+['........']*7,'pivot':[0,0]},
                      {'name':'walk','rows':['.B......']+['........']*7,'pivot':[1,0]}],
           'animations':[{'name':'move','frames':['idle','walk'],'fps':6,'loop':True}]}
        data,r=generate(s)
        self.assertEqual(data,generate(s)[0]);self.assertTrue(r['pixel_roundtrip_verified'])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            m=json.loads(z.read('atlas.json'));self.assertEqual(m['sprites']['walk']['rect'],[8,0,8,8])
            self.assertEqual(m['animations'],s['animations'])
            with image_module().open(io.BytesIO(z.read('atlas.png'))) as im:
                self.assertEqual(im.getpixel((0,0)),(10,20,30,255))
                self.assertEqual(im.getpixel((9,0)),(40,50,60,128))
                self.assertEqual(im.getpixel((8,0)),(0,0,0,0))
        with self.assertRaises(ValueError):checked(dict(s,animations=[dict(s['animations'][0],frames=['missing'])]))
    def test_game_sprite_review_stale_and_nonoverwrite(self):
        from deepthort_local.game_asset_generation import review,execute
        s={'size':8,'palette':{'A':[1,2,3,255]},'sprites':[{'name':'tile','rows':['A.......']*8,'pivot':[0,0]}],'animations':[]}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'spec.json';src.write_text(json.dumps(s))
            plan,_=review(root,'spec.json','atlas.zip');self.assertEqual(execute(root,plan)['status'],'sprite_atlas_pixels_verified')
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'atlas.zip').unlink();src.write_text(json.dumps(dict(s,animations=[{'name':'idle','frames':['tile'],'fps':1,'loop':True}])))
            with self.assertRaises(ValueError):execute(root,plan)
