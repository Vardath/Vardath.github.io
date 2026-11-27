import json,tempfile,unittest
from pathlib import Path
from deepthort_local import mesh_repair as m
from deepthort_local.mesh_geometry import parse
from deepthort_local.mesh_retopology import incidence

SPEC={'mesh':'source.obj'}
RAW=b'v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nv 0 0 0\nv 2 2 2\nf 1 2 3\nf 5 4 3\nf 3 2 1\nf 1 5 2\n'
class RepairTests(unittest.TestCase):
    def test_exact_weld_cleanup_winding(self):
        out,r=m.repair(RAW,SPEC)
        v,f,_,_=parse(out)
        self.assertEqual((len(v),len(f)),(4,2))
        for key in ('exact_duplicate_vertices_welded','unused_vertices_removed','degenerate_triangles_removed','duplicate_triangles_removed','winding_flips'):
            self.assertEqual(r[key],1,key)
        self.assertEqual(r['remaining_boundary_edges'],4)
        self.assertFalse(r['watertight_edge_topology'])
        self.assertFalse(r['self_intersections_checked'])
        incidence(f)
        _,clean=m.repair(out,SPEC)
        self.assertEqual(clean['winding_flips'],0)
        self.assertEqual(clean['duplicate_triangles_removed'],0)
    def test_refuse_unresolved_or_unsupported(self):
        header=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nv 0 -1 0\n'
        for faces in (b'f 1 2 3\nf 1 2 4\nf 1 2 5\n',b'f 1 2 3\nf 1 4 5\n',b'f 1 1 1\n',b'vt 0 0\nf 1 2 3\n'):
            with self.subTest(faces=faces),self.assertRaises(ValueError):m.repair(header+faces,SPEC)
    def test_review_stale_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();source=root/'source.obj';source.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=m.review(root,'spec.json','out.obj')
            result=m.execute(root,plan)
            self.assertEqual(result['status'],'mesh_cleanup_verified')
            self.assertEqual(source.read_bytes(),RAW)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'out.obj').unlink();source.write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'out.obj').exists())
