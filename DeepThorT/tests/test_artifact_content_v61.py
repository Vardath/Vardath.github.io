import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from deepthort_local.artifact_acceptance import validate,verify,AcceptanceMismatch
from deepthort_local.tool_workflows import artifact

def png(raw,width=2,height=2,color=6,depth=8,interlace=0):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,depth,color,0,0,interlace))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

class ContentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def verify(self,name,data,checks):
        (self.root/name).write_bytes(data)
        return verify(self.root,name,checks,artifact(self.root,name))
    def test_decoded_visible_colors_and_sub_filter(self):
        # Row 1: red opaque, transparent black. Row 2: two green
        # pixels encoded with Sub (second pixel is a zero difference).
        raw=bytes([0,255,0,0,255,0,0,0,0,1,0,255,0,255,0,0,0,0])
        rec=self.verify('tex.png',png(raw),{'min_visible_pixels':3,'min_distinct_visible_colors':2})
        self.assertEqual(rec['observed'],{'min_visible_pixels':3,'min_distinct_visible_colors':2})
        with self.assertRaises(AcceptanceMismatch):self.verify('tex.png',png(raw),{'min_visible_pixels':4})
    def test_blank_image_and_invalid_scanlines(self):
        raw=bytes(18)
        with self.assertRaises(AcceptanceMismatch):self.verify('tex.png',png(raw),{'min_visible_pixels':1})
        for data in (bytes(19),bytes(17),bytes([9])+bytes(17)):
            with self.assertRaises(ValueError) as cm:self.verify('tex.png',png(data),{'min_visible_pixels':1})
            self.assertNotIsInstance(cm.exception,AcceptanceMismatch)
    def test_unsupported_image_and_pixel_bound(self):
        for data in (png(b'abc',color=3),png(b'abc',width=2048,height=2048)):
            with self.assertRaises(ValueError):self.verify('tex.png',data,{'min_visible_pixels':1})
    def test_geometry_actual_extents(self):
        data=b'v -2 0 1\nv 4 1 1\nv 0 5 3\nf 1 2 3\n'
        rec=self.verify('mesh.obj',data,{'min_extent_x':5.5,'max_extent_x':6,'min_extent_y':5,'max_extent_z':2})
        self.assertEqual(rec['observed'],{'min_extent_x':6.,'max_extent_x':6.,'min_extent_y':5.,'max_extent_z':2.})
        with self.assertRaises(AcceptanceMismatch):self.verify('mesh.obj',data,{'max_extent_x':5})
    def test_invalid_or_ambiguous_extent(self):
        for checks in ({'max_extent_x':True},{'min_extent_x':float('nan')},{'min_extent_x':2,'max_extent_x':1}):
            with self.assertRaises(ValueError):validate('mesh.obj',checks)
        with self.assertRaises(ValueError):self.verify('mesh.obj',b'v 0 0 0 2\nv 1 0 0\nv 0 1 0\nf 1 2 3\n',{'max_extent_x':1})
if __name__=='__main__':unittest.main()
