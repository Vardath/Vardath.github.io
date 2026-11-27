import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import scene_composition as s
RAW=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
UV=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nf 1/1 2/2 3/3\n'
A={'name':'first','mesh':'a.obj','translation':[0,0,0],'rotation_xyzw':[0,0,0,1],'scale':[1,1,1]}
B={'name':'second','mesh':'b.obj','translation':[2,3,4],'rotation_xyzw':[0,0,1,0],'scale':[2,1,3]}
SPEC={'objects':[A,B],'max_position_error':.001}
class SceneTests(unittest.TestCase):
    def test_nodes_and_geometry(self):
        payload,r=s.compose([RAW,UV],SPEC)
        d,data=s.decode(payload)
        self.assertEqual(d['scenes'][0]['nodes'],[0,1])
        self.assertEqual(d['nodes'][1]['translation'],[2,3,4])
        self.assertEqual(d['nodes'][1]['rotation'],[0,0,1,0])
        self.assertEqual(d['nodes'][1]['scale'],[2,1,3])
        self.assertEqual(r['triangles'],2)
        self.assertIn('TEXCOORD_0',d['meshes'][1]['primitives'][0]['attributes'])
        self.assertNotIn('TEXCOORD_0',d['meshes'][0]['primitives'][0]['attributes'])
        self.assertFalse(r['render_verified'])
    def test_invalid_transforms(self):
        for k,v in (('name','first'),('rotation_xyzw',[0,0,0,0]),('scale',[-1,1,1]),('translation',[float('inf'),0,0])):
            bad=copy.deepcopy(SPEC);bad['objects'][1][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):s.checked(bad)
    def test_guarded_multi_source_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'a.obj').write_bytes(RAW);(root/'b.obj').write_bytes(UV)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=s.review(root,'spec.json','scene.glb')
            self.assertEqual(s.execute(root,plan)['status'],'static_scene_verified')
            with self.assertRaises(ValueError):s.execute(root,plan)
            (root/'scene.glb').unlink();(root/'b.obj').write_bytes(UV+b'# changed\n')
            with self.assertRaises(ValueError):s.execute(root,plan)
            self.assertFalse((root/'scene.glb').exists())
