import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import automatic_lighting as l
from deepthort_local import scene_composition as s
RAW=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
SPEC={'objects':[{'name':'mesh','mesh':'a.obj','translation':[0,0,0],'rotation_xyzw':[0,0,0,1],'scale':[1,1,1]}],
      'max_position_error':.001,'view_azimuth_deg':30,'key_lux':500,'preset':'warm'}
class LightingTests(unittest.TestCase):
    def test_three_lights_preserve_geometry(self):
        original,_=s.compose([RAW],l.scene_spec(SPEC))
        output,r=l.add_lighting([RAW],SPEC)
        d,b=s.decode(output);od,ob=s.decode(original)
        self.assertEqual(b,ob);self.assertEqual(d['meshes'],od['meshes'])
        self.assertEqual(d['nodes'][0],od['nodes'][0])
        self.assertEqual(d['scenes'][0]['nodes'],[0,1,2,3])
        lights=d['extensions'][l.EXT]['lights']
        self.assertEqual([v['intensity'] for v in lights],[500,225,400])
        self.assertEqual([d['nodes'][i+1]['extensions'][l.EXT]['light'] for i in range(3)],list(range(3)))
        for node in d['nodes'][1:]:self.assertAlmostEqual(sum(v*v for v in node['rotation']),1)
        self.assertTrue(r['lighting_metadata_verified']);self.assertFalse(r['render_verified'])
    def test_orientation_and_invalid_settings(self):
        for az in (-180,-90,0,90,180,330):
            q,d=l.facing(az,38);x,y,z,w=q
            actual=(-2*(x*z+y*w),-2*(y*z-x*w),-(1-2*(x*x+y*y)))
            for a,b in zip(actual,d):self.assertAlmostEqual(a,b)
        for k,v in (('key_lux',0),('key_lux',float('nan')),('view_azimuth_deg',181),('preset','arbitrary')):
            with self.subTest(k=k),self.assertRaises(ValueError):l.checked(dict(SPEC,**{k:v}))
    def test_source_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'a.obj';src.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=l.review(root,'spec.json','lit.glb')
            self.assertEqual(l.execute(root,plan)['status'],'scene_lighting_metadata_verified')
            with self.assertRaises(ValueError):l.execute(root,plan)
            (root/'lit.glb').unlink();src.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):l.execute(root,plan)
            self.assertFalse((root/'lit.glb').exists())
