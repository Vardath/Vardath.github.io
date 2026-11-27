import copy,json,tempfile,unittest
from pathlib import Path
from deepthort_local import skeletal_animation as a
from deepthort_local.scene_composition import decode
from deepthort_local.automated_rendering import accessor
RAW=b'v 0 0 0\nv 0 2 0\nv 1 1 0\nf 1 2 3\n'
SPEC={'mesh':'mesh.obj','max_position_error':.001,'name':'Bend',
      'joints':[{'name':'root','parent':None,'position':[0,0,0]},{'name':'upper','parent':0,'position':[0,2,0]}],
      'tracks':[{'joint':1,'times':[0,1,2],'rotations_xyzw':[[0,0,0,1],[0,0,.6,.8],[0,0,-.6,-.8]]}]}
class AnimationTests(unittest.TestCase):
    def test_actual_animation_accessors(self):
        out,r=a.animate(RAW,SPEC);d,b=decode(out);clip=d['animations'][0];sampler=clip['samplers'][0]
        self.assertEqual(clip['channels'][0]['target'],{'node':2,'path':'rotation'})
        self.assertEqual(accessor(d,b,sampler['input'],'<f'),[(0.,),(1.,),(2.,)])
        qs=accessor(d,b,sampler['output'],'<4f');self.assertEqual(qs[1],qs[2])
        self.assertAlmostEqual(qs[1][2],.6);self.assertEqual(r['duration_seconds'],2)
        self.assertTrue(r['rest_skin_preserved']);self.assertFalse(r['native_playback_verified'])
    def test_invalid_tracks(self):
        for k,v in [('joint',2),('times',[0,1,1]),('rotations_xyzw',[[0,0,0,0]]*3)]:
            s=copy.deepcopy(SPEC);s['tracks'][0][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):a.checked(s)
        with self.assertRaises(ValueError):a.checked(dict(SPEC,tracks=SPEC['tracks']*2))
    def test_stale_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'mesh.obj';src.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=a.review(root,'spec.json','clip.glb')
            self.assertEqual(a.execute(root,plan)['status'],'skeletal_animation_structure_verified')
            with self.assertRaises(ValueError):a.execute(root,plan)
            (root/'clip.glb').unlink();src.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):a.execute(root,plan)
            self.assertFalse((root/'clip.glb').exists())
