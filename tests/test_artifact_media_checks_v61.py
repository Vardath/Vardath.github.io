import struct
import unittest
import zlib
from deepthort_local.artifact_media_checks import png,obj,PNG_SIGNATURE

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)

class MediaChecksTests(unittest.TestCase):
    def test_png_header_crc_and_end(self):
        valid=PNG_SIGNATURE+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\0\0\0'))+chunk(b'IEND',b'')
        self.assertIn('1x1',png(valid))
        with self.assertRaises(ValueError):png(valid[:-1])
        with self.assertRaises(ValueError):png(valid[:-1]+bytes([valid[-1]^1]))
    def test_obj_rejects_invalid_references(self):
        mesh=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
        self.assertIn('3 vertices',obj(mesh))
        with self.assertRaises(ValueError):obj(mesh.replace(b'f 1 2 3',b'f 1 2 4'))
        with self.assertRaises(ValueError):obj(mesh.replace(b'f 1 2 3',b'f -4 -2 -1'))
        with self.assertRaises(ValueError):obj(mesh.replace(b'v 0 0 0',b'v nan 0 0'))
if __name__=='__main__':unittest.main()
