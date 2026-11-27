import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import character_rigging as r
from deepthort_local.scene_composition import decode
from deepthort_local.automated_rendering import accessor
RAW=b'v 0 0 0\nv 0 2 0\nv 1 1 0\nf 1 2 3\n'
SPEC={'mesh':'mesh.obj','max_position_error':.001,
      'joints':[{'name':'root','parent':None,'position':[0,0,0]},{'name':'upper','parent':0,'position':[0,2,0]}]}
class RigTests(unittest.TestCase):
    def test_skin_weights_and_bind(self):
        out,report=r.rig(RAW,SPEC);d,b=decode(out)
        attrs=d['meshes'][0]['primitives'][0]['attributes']
        ids=accessor(d,b,attrs['JOINTS_0'],'<4H')
        w=accessor(d,b,attrs['WEIGHTS_0'],'<4f')
        self.assertEqual(ids[0][0],0);self.assertEqual(ids[1][0],1)
        self.assertEqual(w[:2],[(1.,0.,0.,0.)]*2);self.assertEqual(w[2],(.5,.5,0.,0.))
        self.assertEqual(d['nodes'][1]['children'],[2])
        self.assertEqual(d['skins'][0]['joints'],[1,2])
        matrices=accessor(d,b,d['skins'][0]['inverseBindMatrices'],'<16f')
        self.assertEqual(matrices[1][12:15],(0.,-2.,0.))
        self.assertTrue(report['rest_bind_and_hierarchy_verified'])
        self.assertFalse(report['automatic_skeleton_discovery_verified'])
    def test_invalid_hierarchy(self):
        for k,v in [('parent',1),('position',[0,0,0]),('name','root')]:
            s=copy.deepcopy(SPEC);s['joints'][1][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):r.checked(s)
        with self.assertRaises(ValueError):r.checked(dict(SPEC,joints=SPEC['joints'][:1]))
    def test_guarded_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'mesh.obj';src.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=r.review(root,'spec.json','rig.glb')
            self.assertEqual(r.execute(root,plan)['status'],'skin_structure_verified')
            with self.assertRaises(ValueError):r.execute(root,plan)
            (root/'rig.glb').unlink();src.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):r.execute(root,plan)
            self.assertFalse((root/'rig.glb').exists())
