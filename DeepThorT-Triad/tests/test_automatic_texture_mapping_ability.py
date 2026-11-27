import json,tempfile,unittest
from pathlib import Path
from deepthort_local import automatic_texture_mapping as m
from deepthort_local.mesh_geometry import parse
from deepthort_local.scene_composition import decode
from deepthort_local.texture_pixels import encode
RAW=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 2 3\nf 1 4 2\n'
SPEC={'mesh':'mesh.obj','texture':'color.png','max_position_error':.001}
class MappingTests(unittest.TestCase):
    def test_projection_and_embedded_texture(self):
        mapped,axes=m.project(RAW)
        v,f,u,uf=parse(mapped,allow_uv=True)
        self.assertEqual((v,f),parse(RAW)[:2]);self.assertEqual(axes,[0,1,1])
        self.assertEqual(len(u),6);self.assertTrue(all(0<=x<=1 for uv in u for x in uv))
        texture=encode(2,2,'RGB',bytes(range(12)))
        out,r=m.map_texture(RAW,texture,SPEC)
        d,b=decode(out);p=d['meshes'][0]['primitives'][0]
        self.assertIn('TEXCOORD_0',p['attributes']);self.assertEqual(p['material'],0)
        view=d['bufferViews'][d['images'][0]['bufferView']]
        self.assertEqual(b[view['byteOffset']:view['byteOffset']+view['byteLength']],texture)
        self.assertTrue(r['texture_embedding_verified']);self.assertFalse(r['render_verified'])
    def test_refuse_invalid_sources(self):
        with self.assertRaises(ValueError):m.map_texture(RAW,b'not a PNG',SPEC)
        with self.assertRaises(ValueError):m.project(RAW+b'vn 0 0 1\n')
        with self.assertRaises(ValueError):m.checked(dict(SPEC,max_position_error=0))
    def test_guarded_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'mesh.obj').write_bytes(RAW)
            p=root/'color.png';p.write_bytes(encode(2,2,'RGB',bytes(range(12))))
            (root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=m.review(root,'spec.json','mapped.glb')
            self.assertEqual(m.execute(root,plan)['status'],'mapped_texture_embedded')
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'mapped.glb').unlink();p.write_bytes(encode(2,2,'RGB',bytes([0])*12))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'mapped.glb').exists())
