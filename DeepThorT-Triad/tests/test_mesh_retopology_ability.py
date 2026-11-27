import json,tempfile,unittest
from pathlib import Path
from deepthort_local import mesh_retopology as m
from deepthort_local.mesh_geometry import encode,parse
V=[(0.,0.,0.),(3.,0.,0.),(3.,1.,0.),(1.,1.,0.)]
F=[(0,1,2),(0,2,3)]
SPEC={'mesh':'source.obj','passes':3,'min_quality_gain':.001}
class RetopologyTests(unittest.TestCase):
    def test_improve_and_keep_boundary(self):
        raw=encode(V,F);out,r=m.retopologize(raw,SPEC)
        self.assertEqual(r['flipped_edges'],1)
        self.assertGreater(r['minimum_triangle_quality_after'],r['minimum_triangle_quality_before'])
        v,f,_,_=parse(out);self.assertEqual(v,V)
        self.assertEqual(len(f),2);self.assertIn((1,3),m.incidence(f))
        self.assertEqual({e for e,x in m.incidence(f).items() if len(x)==1},{e for e,x in m.incidence(F).items() if len(x)==1})
    def test_reject_nonmanifold_and_skip_curved(self):
        with self.assertRaises(ValueError):m.incidence([(0,1,2),(0,1,3)])
        with self.assertRaises(ValueError):m.incidence([(0,1,2),(0,3,4)])
        curved=list(V);curved[3]=(1.,1.,.1)
        _,r=m.retopologize(encode(curved,F),SPEC)
        self.assertEqual(r['flipped_edges'],0)
        with self.assertRaises(ValueError):m.checked(dict(SPEC,passes=6))
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'source.obj';raw=encode(V,F);src.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=m.review(root,'spec.json','out.obj')
            r=m.execute(root,plan);self.assertTrue(r['source_unchanged']);self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'out.obj').unlink();src.write_bytes(raw+b'# changed\n')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'out.obj').exists())
