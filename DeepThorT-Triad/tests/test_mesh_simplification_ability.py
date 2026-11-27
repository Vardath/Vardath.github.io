import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.mesh_geometry import parse
from deepthort_local.mesh_simplification import checked,simplify,review,execute
RAW=b'v 0 0 0\nv 0.01 0.01 0\nv 2 0 0\nv 0 2 0\nf 1 3 4\nf 2 3 4\nf 1 2 4\n'
SPEC={'mesh':'a.obj','cell_size':.1,'max_displacement':.02}
class SimplificationTests(unittest.TestCase):
    def test_reduction_and_displacement(self):
        out,r=simplify(RAW,SPEC);v,f,_,_=parse(out)
        self.assertEqual((len(v),len(f)),(3,1))
        self.assertEqual(r['collapsed_triangles'],1);self.assertEqual(r['duplicate_triangles_removed'],1)
        self.assertLessEqual(r['maximum_cluster_displacement'],.02)
        self.assertFalse(r['topology_preservation_verified'])
    def test_reject_excess_displacement_and_total_collapse(self):
        with self.assertRaises(ValueError):simplify(RAW,dict(SPEC,max_displacement=.001))
        with self.assertRaises(ValueError):simplify(RAW,dict(SPEC,cell_size=10,max_displacement=10))
        with self.assertRaises(ValueError):checked(dict(SPEC,cell_size=0))
    def test_noop_and_unsupported_attributes(self):
        raw=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
        out,r=simplify(raw,SPEC);self.assertEqual(parse(out)[:2],parse(raw)[:2])
        self.assertEqual(r['triangle_reduction_fraction'],0)
        with self.assertRaises(ValueError):simplify(raw+b'vn 0 0 1\n',SPEC)
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'a.obj').write_bytes(RAW);(root/'spec.json').write_text(json.dumps(SPEC))
            plan,p=review(root,'spec.json','simple.obj');r=execute(root,plan)
            self.assertEqual(p['source_triangles'],3);self.assertEqual(r['status'],'mesh_reduction_verified')
            self.assertEqual((root/'a.obj').read_bytes(),RAW);(root/'simple.obj').unlink()
            (root/'a.obj').write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):execute(root,plan)
