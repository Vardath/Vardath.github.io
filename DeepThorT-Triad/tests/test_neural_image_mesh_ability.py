import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from deepthort_local import neural_image_mesh as m
from deepthort_local.mesh_geometry import parse

class NeuralImageMeshTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.spec={'image':'source.png','seed':12,'steps':16,'guidance':4}
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
        with Image.new('RGB',(64,64),(10,30,80)) as image:image.save(self.root/'source.png')
        self.original=(self.root/'source.png').read_bytes()
        p=patch.object(m.mesh,'inventory',return_value={'path':'image','inventory_sha':'b'*64,'bytes':123})
        self.inventory=p.start();self.addCleanup(p.stop)
        self.v=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)];self.f=[(0,1,2)]
    def plan(self):return m.review(self.root,'spec.json','out.obj')[0]
    def test_exact_image_and_geometry(self):
        plan=self.plan()
        def backend(s,image):
            self.assertEqual(s,self.spec);self.assertEqual(image.getpixel((0,0)),(10,30,80))
            return self.v,self.f
        r=m.execute(self.root,plan,backend=backend)
        self.assertEqual(parse((self.root/'out.obj').read_bytes())[:2],(self.v,self.f))
        self.assertEqual((self.root/'source.png').read_bytes(),self.original)
        self.assertFalse(r['metric_accuracy_verified'])
        self.assertEqual(r['backend'],'injected_fixture')
    def test_invalid_image_or_geometry(self):
        plan=self.plan()
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda *_:(self.v,[(0,1,3)]))
        with Image.new('RGBA',(64,64)) as image:image.save(self.root/'source.png')
        with self.assertRaises(ValueError):self.plan()
        self.assertFalse((self.root/'out.obj').exists())
    def test_stale_image_and_model_refused(self):
        plan=self.plan();old=self.inventory.return_value
        self.inventory.return_value={}
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda *_:self.fail('stale model'))
        self.inventory.return_value=old
        with Image.new('RGB',(64,64),(1,2,3)) as image:image.save(self.root/'source.png')
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda *_:self.fail('stale image'))
        self.assertFalse((self.root/'out.obj').exists())
if __name__=='__main__':unittest.main()
