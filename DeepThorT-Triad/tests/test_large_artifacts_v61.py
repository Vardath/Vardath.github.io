import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch
from deepthort_local.tool_workflows import artifact,MAX_ARTIFACT
from deepthort_local.action_guards import MAX_HASH_BYTES,snapshot_file,verify_guards
from deepthort_local.large_artifacts import BLOCK,MAX_METADATA,BoundedReader

SIZE=MAX_ARTIFACT+1024

def sparse(path,header,size):
    with path.open('wb') as f:
        f.write(header)
        f.truncate(size)

class LargeArtifactTests(unittest.TestCase):
    def test_large_wav_has_hash_usable_as_next_input(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'sound.wav'
            header=b'RIFF'+struct.pack('<I',SIZE+36)+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,8000,16000,2,16)+b'data'+struct.pack('<I',SIZE)
            sparse(p,header,SIZE+44)
            with patch.object(Path,'read_bytes',side_effect=AssertionError('whole file read')):
                result=artifact(t,p.name)
                guard=snapshot_file(p)
            self.assertEqual(result['sha256'],guard['expected'])
            self.assertEqual(result['bytes'],SIZE+44)
            self.assertIn('8000 Hz',result['scope'])
            verify_guards([guard])
            with p.open('r+b') as f:f.truncate(SIZE+43)
            with self.assertRaises(ValueError):artifact(t,p.name)

    def test_large_glb_metadata_and_buffer_bounds(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'mesh.glb'
            raw=json.dumps({'asset':{'version':'2.0'},'meshes':[{}],'buffers':[{'byteLength':SIZE}]}).encode()
            raw+=b' '*((-len(raw))%4)
            header=struct.pack('<4sII',b'glTF',2,28+len(raw)+SIZE)+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',SIZE,0x004e4942)
            sparse(p,header,len(header)+SIZE)
            self.assertIn('GLB v2',artifact(t,p.name)['scope'])
            huge=MAX_METADATA+4
            sparse(p,struct.pack('<4sIIII',b'glTF',2,SIZE,huge,0x4e4f534a),SIZE)
            with self.assertRaisesRegex(ValueError,'metadata limit'):artifact(t,p.name)

    def test_large_png_crc_and_no_full_read(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'image.png'
            def chunk(kind,payload):
                return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
            block=b'\0'*BLOCK
            length=17*BLOCK
            with p.open('wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0)))
                f.write(struct.pack('>I',length)+b'IDAT')
                crc=zlib.crc32(b'IDAT')
                for _ in range(17):
                    f.write(block);crc=zlib.crc32(block,crc)
                f.write(struct.pack('>I',crc&0xffffffff)+chunk(b'IEND',b''))
            # Structural CRC evidence is deliberately not pixel decoding.
            with patch.object(Path,'read_bytes',side_effect=AssertionError('whole file read')):
                self.assertIn('pixels not decoded',artifact(t,p.name)['scope'])
            with p.open('r+b') as f:f.seek(50);f.write(b'x')
            with self.assertRaisesRegex(ValueError,'CRC'):artifact(t,p.name)

    def test_large_zip_and_unsupported_or_oversize(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/'package.zip';payload=root/'payload'
            sparse(payload,b'x',SIZE)
            with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_STORED) as z:z.write(payload,'asset.bin')
            with patch.object(Path,'read_bytes',side_effect=AssertionError('whole file read')):
                self.assertIn('archive structure and CRC',artifact(t,p.name)['scope'])
            with p.open('r+b') as f:f.seek(60);f.write(b'x')
            with self.assertRaises((ValueError,zipfile.BadZipFile)):artifact(t,p.name)
            sparse(root/'unknown.blend',b'x',SIZE)
            with self.assertRaisesRegex(ValueError,'no supported'):artifact(t,'unknown.blend')
            sparse(root/'too.wav',b'x',MAX_HASH_BYTES+1)
            with self.assertRaisesRegex(ValueError,'hash-check limit'):artifact(t,'too.wav')

if __name__=='__main__':unittest.main()
