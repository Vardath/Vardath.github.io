import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import neural_text_mesh as m
from deepthort_local.mesh_geometry import parse

class NeuralTextMeshTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.spec={'prompt':'a small spacecraft','seed':12,'steps':16,'guidance':4}
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
        self.mock=patch.object(m,'inventory',return_value={'path':'fixture','inventory_sha':'a'*64,'bytes':123})
        self.inventory=self.mock.start();self.addCleanup(self.mock.stop)
        self.v=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
        self.f=[(0,1,2),(0,3,1),(0,2,3),(1,3,2)]
    def plan(self):return m.review(self.root,'spec.json','out.obj')[0]
    def test_generated_geometry_roundtrip(self):
        plan=self.plan()
        def backend(s):
            self.assertEqual(s,self.spec);return self.v,self.f
        r=m.execute(self.root,plan,backend=backend)
        self.assertEqual(parse((self.root/'out.obj').read_bytes())[:2],(self.v,self.f))
        self.assertEqual((r['vertices'],r['triangles'],r['backend']),(4,4,'injected_fixture'))
        self.assertFalse(r['semantic_quality_verified'])
    def test_bad_mesh_rejected_without_output(self):
        plan=self.plan()
        for v,f in [(self.v,[(0,1,4)]),(self.v,[(0,1,1)]),(self.v,[(0,1,2),(2,1,0)]),([(float('nan'),0.,0.),*self.v[1:]],self.f)]:
            with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda _: (v,f))
        self.assertFalse((self.root/'out.obj').exists())
        with self.assertRaises(ValueError):m.checked(dict(self.spec,steps=99))
    def test_stale_model_or_spec_rejected(self):
        plan=self.plan();old=self.inventory.return_value
        self.inventory.return_value={}
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda _:self.fail('stale model'))
        self.inventory.return_value=old
        (self.root/'spec.json').write_text(json.dumps(dict(self.spec,seed=13)),encoding='utf8')
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda _:self.fail('stale spec'))
        self.assertFalse((self.root/'out.obj').exists())
if __name__=='__main__':unittest.main()
