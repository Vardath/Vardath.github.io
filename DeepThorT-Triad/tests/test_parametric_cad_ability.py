import io,json,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import parametric_cad as c
from deepthort_local.mesh_geometry import parse
SPEC={'polygon':[[0,0],[4,0],[4,3],[0,3]],'height_mm':5}
class CadTests(unittest.TestCase):
    def test_closed_extrusion_and_code(self):
        payload,r=c.produce(SPEC)
        self.assertEqual(r['vertices'],8);self.assertEqual(r['triangles'],12)
        self.assertAlmostEqual(r['verified_mesh_volume_mm3'],60)
        self.assertTrue(r['closed_oriented_mesh_verified'])
        self.assertFalse(r['native_scad_execution_verified'])
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            self.assertIn(b'linear_extrude',z.read('design.scad'))
            v,f,_,_=parse(z.read('design.obj'))
            self.assertEqual((min(x[2] for x in v),max(x[2] for x in v)),(0,5))
            self.assertEqual(json.loads(z.read('receipt.json')),r)
    def test_invalid_polygon_and_dimensions(self):
        for p in ([[0,0],[4,0],[1,1],[4,3],[0,3]],[[0,0],[4,3],[4,0],[0,3]],list(reversed(SPEC['polygon'])),[[0,0],[1,0],[2,0]]):
            with self.subTest(p=p),self.assertRaises(ValueError):c.checked(dict(SPEC,polygon=p))
        for h in (0,True,float('nan'),10001):
            with self.assertRaises(ValueError):c.checked(dict(SPEC,height_mm=h))
    def test_exact_review_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'spec.json';src.write_text(json.dumps(SPEC))
            plan,_=c.review(root,'spec.json','out.zip')
            r=c.execute(root,plan);self.assertEqual(r['status'],'cad_bundle_verified')
            with self.assertRaises(ValueError):c.execute(root,plan)
            (root/'out.zip').unlink();src.write_text(json.dumps(dict(SPEC,height_mm=6)))
            with self.assertRaises(ValueError):c.execute(root,plan)
            self.assertFalse((root/'out.zip').exists())
