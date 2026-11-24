import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock
import zlib

from deepthort_local.specification_library import SpecificationIndex
from deepthort_local.x4_geometry import GeometryError,export_mesh,inspect_fit,mesh_positions,stage_geometry


def make_mesh(extent):
    header=bytearray(64+2*188)
    struct.pack_into('<4sHHBBB',header,0,b'XUMF',3,64,2,188,0)
    struct.pack_into('<II',header,14,3,3)
    raw=b''.join(struct.pack('<3f',*p)+bytes(range(16)) for p in (
        (0,0,0),extent,(1,1,1)))
    packed=zlib.compress(raw)
    topology=zlib.compress(struct.pack('<3H',0,1,2))
    struct.pack_into('<9I',header,64,0,0,0,1,0,32,len(packed),3,28)
    struct.pack_into('<9I',header,252,30,0,len(packed),1,0,30,len(topology),3,2)
    return bytes(header)+packed+topology


class GeometryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.ship='assets/units/size_m/ship_demo.xml'
        self.rock='assets/environments/asteroids/env_ast_ore_m_01.xml'
        files={}
        for name,extent,kind in ((self.ship,(8,4,8),'ship_m'),(self.rock,(10,10,10),'asteroid')):
            folder=name[:-4]+'_data'
            files[name]=(f'<components><component name="{Path(name).stem}" class="{kind}"><source geometry="{folder}"/>'
                         '<parts><part name="part_main"><lods><lod index="0"/></lods></part></parts></component></components>').encode()
            files[folder+'/part_main-lod0.xmf']=make_mesh(extent)
        (self.root/'01.cat').write_bytes(b''.join(f'{p} {len(d)} 0 {hashlib.md5(d).hexdigest()}\n'.encode() for p,d in files.items()))
        (self.root/'01.dat').write_bytes(b''.join(files.values()))

    def test_native_scale_preserves_indices_and_nonposition_bytes(self):
        raw=make_mesh((10,10,10))
        _,out=mesh_positions(raw,.4)
        self.assertEqual(mesh_positions(out)[0]['dimensions'],[4,4,4])
        for blob in (raw,out):
            offset=struct.unpack_from('<I',blob,260)[0]
            self.assertEqual(zlib.decompress(blob[440+offset:]),struct.pack('<3H',0,1,2))
            stream=zlib.decompress(blob[440:440+offset])
            self.assertEqual([stream[i+12:i+28] for i in range(0,len(stream),28)],[bytes(range(16))]*3)

    def test_bad_chunk_and_catalog_hash_are_rejected(self):
        data=bytearray(make_mesh((10,10,10)))
        struct.pack_into('<I',data,260,0)
        with self.assertRaises(GeometryError):mesh_positions(data)
        path=self.root/'01.dat'
        path.write_bytes(b'X'+path.read_bytes()[1:])
        with self.assertRaisesRegex(GeometryError,'checksum'):inspect_fit(self.root,self.ship)

    def test_persistent_choice_is_scoped_and_exports_once(self):
        index=SpecificationIndex(self.root/'spec.db')
        model=Mock(spec=['chat'])
        model.chat.return_value=Path(self.rock).stem
        args=(model,index,1,'sess','original',self.root,dict(game_dir=self.root,pe_component_file=self.ship))
        self.assertEqual(stage_geometry(*args)[1],1)
        self.assertEqual(stage_geometry(*args)[1],0)
        model.chat.assert_called_once()
        self.assertIsNone(index.latest_mesh(self.root/'other'))
        blob=index.latest_mesh(self.root)[4]
        target=self.root/'fitted.xmf'
        export_mesh(target,blob)
        self.assertEqual(target.read_bytes(),blob)
        with self.assertRaises(FileExistsError):export_mesh(target,blob)
        obj=self.root/'fitted.obj'
        export_mesh(obj,blob)
        self.assertEqual(obj.read_text().splitlines()[-1],'f 1 2 3')

    def test_uninspected_identifier_never_generates_a_mesh(self):
        index=SpecificationIndex(self.root/'spec.db')
        model=Mock(spec=['chat'])
        model.chat.return_value='../uninspected'
        note,_=stage_geometry(model,index,1,'s','spec',self.root,dict(game_dir=self.root,pe_component_file=self.ship))
        self.assertIn('unresolved',note)
        self.assertIsNone(index.latest_mesh(self.root))
