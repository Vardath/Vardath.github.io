import json
import struct
import tempfile
import unittest
from pathlib import Path
from deepthort_local.mesh_conversion import checked,convert,review,execute
from deepthort_local.uv_unwrapping import unwrap
from deepthort_local.artifact_media_checks import glb
RAW=b'v 0 0 0\nv 2 0 0\nv 2 1 0\nv 0 1 0\nf 1 2 3\nf 1 3 4\n'
SPEC={'mesh':'a.obj','max_position_error':.0001}
def unpack(raw):
    n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def accessor(doc,data,idx,fmt):
    a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
    return list(struct.iter_unpack(fmt,data[v['byteOffset']:v['byteOffset']+v['byteLength']]))
class ConversionTests(unittest.TestCase):
    def test_plain_mesh_geometry(self):
        out,r=convert(RAW,SPEC);glb(out);d,b=unpack(out);prim=d['meshes'][0]['primitives'][0]
        self.assertEqual(accessor(d,b,prim['attributes']['POSITION'],'<3f'),[(0,0,0),(2,0,0),(2,1,0),(0,1,0)])
        self.assertEqual(accessor(d,b,prim['indices'],'<I'),[(0,),(1,),(2,),(0,),(2,),(3,)])
        self.assertEqual(r['triangles'],2);self.assertFalse(r['uvs_preserved'])
    def test_uv_islands_and_v_flip(self):
        raw,_=unwrap(RAW,{'tile_margin':.05});out,r=convert(raw,SPEC);d,b=unpack(out);prim=d['meshes'][0]['primitives'][0]
        tex=accessor(d,b,prim['attributes']['TEXCOORD_0'],'<2f')
        self.assertEqual(r['output_vertices'],6);self.assertTrue(r['uvs_preserved'])
        self.assertAlmostEqual(tex[0][0],.025);self.assertAlmostEqual(tex[0][1],.975)
    def test_refuse_precision_and_unsupported_attributes(self):
        raw=b'v 0.1 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
        with self.assertRaises(ValueError):convert(raw,dict(SPEC,max_position_error=1e-12))
        with self.assertRaises(ValueError):convert(RAW+b'vn 0 0 1\n',SPEC)
        with self.assertRaises(ValueError):checked(dict(SPEC,max_position_error=0))
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'a.obj').write_bytes(RAW);(root/'spec.json').write_text(json.dumps(SPEC))
            plan,p=review(root,'spec.json','model.glb');r=execute(root,plan)
            self.assertEqual(p['triangles'],2);self.assertTrue(r['geometry_roundtrip_verified'])
            self.assertEqual((root/'a.obj').read_bytes(),RAW);(root/'model.glb').unlink()
            (root/'a.obj').write_bytes(RAW+b'# changed\n')
            with self.assertRaises(ValueError):execute(root,plan)
