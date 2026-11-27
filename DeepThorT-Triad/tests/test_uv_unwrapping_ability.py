import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.mesh_geometry import parse,norm,sub
from deepthort_local.uv_unwrapping import checked,unwrap,review,execute
RAW=b'v 0 0 0\nv 2 0 0\nv 2 1 0\nv 0 1 0\nf 1 2 3\nf -4 -2 -1\n'
SPEC={'mesh':'a.obj','tile_margin':.05}
class UVTests(unittest.TestCase):
    def test_geometry_and_disjoint_tiles(self):
        out,r=unwrap(RAW,SPEC);v,f,u,uf=parse(out,allow_uv=True)
        self.assertEqual((v,f),parse(RAW)[:2]);self.assertEqual(r['atlas_grid'],2)
        self.assertEqual(len(u),6);self.assertTrue(all(0<x<.5 for x,y in u[:3]))
        self.assertTrue(all(.5<x<1 for x,y in u[3:]))
        self.assertEqual(uf,[(0,1,2),(3,4,5)])
    def test_triangle_shape_preserved(self):
        out,_=unwrap(RAW,SPEC);v,f,u,uf=parse(out,allow_uv=True)
        for face,uvface in zip(f,uf):
            a,b,c=[v[i] for i in face];p,q,r=[u[i] for i in uvface]
            self.assertAlmostEqual(norm(sub(b,a))/norm(sub(c,a)),norm(sub(q,p))/norm(sub(r,p)))
    def test_unsupported_and_degenerate(self):
        for raw in (RAW+b'usemtl test\n',b'v 0 0 0\nv 1 0 0\nv 2 0 0\nf 1 2 3\n',RAW+b'f 1 2 9\n'):
            with self.assertRaises(ValueError):unwrap(raw,SPEC)
        with self.assertRaises(ValueError):checked(dict(SPEC,tile_margin=0))
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'a.obj').write_bytes(RAW);(root/'spec.json').write_text(json.dumps(SPEC))
            plan,p=review(root,'spec.json','uv.obj');r=execute(root,plan)
            self.assertEqual(p['triangles'],2);self.assertTrue(r['geometry_preserved'])
            self.assertEqual((root/'a.obj').read_bytes(),RAW);(root/'uv.obj').unlink()
            (root/'a.obj').write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):execute(root,plan)
