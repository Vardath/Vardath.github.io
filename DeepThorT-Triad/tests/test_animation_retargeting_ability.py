import copy,json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import animation_retargeting as r
from deepthort_local.scene_composition import decode
from deepthort_local.automated_rendering import accessor
RAW=b'v 0 0 0\nv 0 2 0\nv 1 1 0\nf 1 2 3\n'
Q=math.sqrt(.5)
SPEC={'mesh':'mesh.obj','max_position_error':.001,'name':'Transferred',
      'source_joints':[{'name':'base','parent':None,'position':[0,0,0]},{'name':'arm','parent':0,'position':[0,1,0]}],
      'joints':[{'name':'root','parent':None,'position':[0,0,0]},{'name':'limb','parent':0,'position':[0,2,0]}],
      'source_tracks':[{'joint':1,'times':[0,1],'rotations_xyzw':[[0,0,0,1],[.6,0,0,.8]]}],
      'mapping':[{'source':0,'target':0,'basis_xyzw':[0,0,0,1]},{'source':1,'target':1,'basis_xyzw':[0,0,Q,Q]}]}
class RetargetTests(unittest.TestCase):
    def test_basis_and_export(self):
        s=r.transform(SPEC);q=s['tracks'][0]['rotations_xyzw'][1]
        self.assertAlmostEqual(q[0],0);self.assertAlmostEqual(q[1],.6);self.assertAlmostEqual(q[3],.8)
        payload,report=r.retarget(RAW,SPEC);d,b=decode(payload)
        clip=d['animations'][0];self.assertEqual(clip['channels'][0]['target']['node'],2)
        out=accessor(d,b,clip['samplers'][0]['output'],'<4f')
        self.assertAlmostEqual(out[1][1],.6);self.assertEqual(d['nodes'][2]['translation'],[0.,2.,0.])
        self.assertTrue(report['parent_correspondence_verified']);self.assertFalse(report['foot_contact_verified'])
    def test_reject_inconsistent_mapping(self):
        for mode in ('missing_parent','duplicate','unmapped','bad_basis'):
            s=copy.deepcopy(SPEC)
            if mode=='missing_parent':s['mapping']=s['mapping'][1:]
            elif mode=='duplicate':s['mapping'][1]['target']=0
            elif mode=='unmapped':s['mapping']=s['mapping'][:1]
            else:s['mapping'][1]['basis_xyzw']=[0,0,0,0]
            with self.subTest(mode=mode),self.assertRaises(ValueError):r.checked(s)
    def test_guarded_export(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'mesh.obj';src.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=r.review(root,'spec.json','transfer.glb')
            self.assertEqual(r.execute(root,plan)['status'],'retargeted_animation_structure_verified')
            with self.assertRaises(ValueError):r.execute(root,plan)
            (root/'transfer.glb').unlink();src.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):r.execute(root,plan)
            self.assertFalse((root/'transfer.glb').exists())
