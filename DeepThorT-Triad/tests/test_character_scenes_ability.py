import tempfile,unittest
from pathlib import Path
from deepthort_local import image_to_image as m
from deepthort_local.texture_pixels import encode,decode

class CharacterScenesTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        n=256*256;self.source=encode(256,256,'RGB',bytes([20,40,60])*n)
        self.mask=encode(256,256,'L',bytes(n//2)+bytes([255])*(n//2))
        (self.root/'character.png').write_bytes(self.source);(self.root/'mask.png').write_bytes(self.mask)
    def review(self,name):
        return m.review_character(self.root,'character.png','mask.png',name,'different scene','Pilot',256)
    def test_two_scenes_preserve_same_region(self):
        hashes=[]
        for name,colour in [('one.png',[40,50,60]),('two.png',[80,90,100])]:
            s=self.review(name)
            r=m.execute(self.root,'unused',s,mask_backend=lambda *_:encode(256,256,'RGB',bytes(colour)*(256*256)))
            hashes.append(r['character_region_sha256'])
            self.assertTrue(r['same_reference_pixels_verified'])
            self.assertFalse(r['new_pose_generated'])
            self.assertEqual(decode((self.root/name).read_bytes(),('RGB',))[3][:256*256*3//2],bytes([20,40,60])*(256*256//2))
        self.assertEqual(hashes[0],hashes[1])
        self.assertNotEqual((self.root/'one.png').read_bytes(),(self.root/'two.png').read_bytes())
    def test_stale_mask_and_identity(self):
        s=self.review('one.png')
        with self.assertRaises(ValueError):m.execute(self.root,'unused',dict(s,character_region_sha256='0'*64),mask_backend=lambda *_:self.source)
        (self.root/'mask.png').write_bytes(encode(256,256,'L',bytes([255])*(256*256//2)+bytes(256*256//2)))
        with self.assertRaises(ValueError):m.execute(self.root,'unused',s,mask_backend=lambda *_:self.source)
        self.assertFalse((self.root/'one.png').exists())
    def test_noop_and_tiny_region_rejected(self):
        s=self.review('one.png')
        with self.assertRaises(ValueError):m.execute(self.root,'unused',s,mask_backend=lambda *_:self.source)
        (self.root/'mask.png').write_bytes(encode(256,256,'L',bytes(1)+bytes([255])*(256*256-1)))
        with self.assertRaises(ValueError):self.review('one.png')
if __name__=='__main__':unittest.main()
