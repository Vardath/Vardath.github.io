import json,tempfile,unittest
from pathlib import Path
from deepthort_local import blender_mesh_workflow as m
from deepthort_local.mesh_geometry import encode
V=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
F=[(0,1,2)]
class Backend:
    def run(self,plan,data,cancelled):
        return b'BLENDER'+b'fixture'*20,(m.MARKER+json.dumps(m.expected(data))+'\n').encode()
class BlenderWorkflowTests(unittest.TestCase):
    def test_review_command_and_publish(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td).resolve();root=base/'project';root.mkdir();exe=base/m.EXE;exe.write_bytes(b'fixture')
            raw=encode(V,F);(root/'mesh.obj').write_bytes(raw)
            plan=m.review(root,'mesh.obj','out.blend',str(exe))
            self.assertEqual(plan['geometry']['vertices'],3)
            argv=m.command(plan,root);self.assertIn('--disable-autoexec',argv);self.assertIn('--factory-startup',argv)
            self.assertIn(str(root/'build.py'),argv)
            with self.assertRaises(PermissionError):m.render(root,plan,backend=Backend())
            r=m.render(root,plan,approved=True,backend=Backend());self.assertFalse(r['native_engine_used'])
            self.assertTrue((root/'out.blend').read_bytes().startswith(b'BLENDER'))
            self.assertEqual((root/'mesh.obj').read_bytes(),raw)
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=Backend())
    def test_stale_and_cancel(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td).resolve();root=base/'project';root.mkdir();exe=base/m.EXE;exe.write_bytes(b'fixture')
            (root/'mesh.obj').write_bytes(encode(V,F));plan=m.review(root,'mesh.obj','out.blend',str(exe))
            with self.assertRaises(ValueError):m.render(root,plan,lambda:True,approved=True,backend=Backend())
            exe.write_bytes(b'changed')
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=Backend())
            self.assertFalse((root/'out.blend').exists())
    def test_receipt_and_geometry(self):
        p=m.expected(m.packet(encode(V,F)));payload=b'BLENDER'+b'x'*64
        with self.assertRaises(ValueError):m.verify(payload,b'no receipt',p)
        with self.assertRaises(ValueError):m.verify(payload,(m.MARKER+json.dumps(dict(p,vertices=4))).encode(),p)
        with self.assertRaises(ValueError):m.packet(encode(V,F+F))
