import tempfile,unittest
from pathlib import Path
from deepthort_local import image_to_image as m
from deepthort_local.texture_pixels import encode,decode

RAW=encode(2,1,'RGB',bytes([12,20,30,100,120,140]))
OUT=encode(256,256,'RGB',bytes([30,60,90])*(256*256))
class ImageToImageTests(unittest.TestCase):
    def test_reviewed_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW)
            s=m.review(root,'source.png','out.png','painted landscape',256,15,60,12)
            def backend(model,raw,spec):
                self.assertEqual(raw,RAW);self.assertEqual(spec['seed'],12)
                self.assertEqual(spec['prompt'],'painted landscape');return OUT
            r=m.execute(root,'unused',s,backend=backend)
            self.assertEqual(r['status'],'generated_image_pixels_verified')
            self.assertEqual((root/'out.png').read_bytes(),OUT)
            self.assertEqual((root/'source.png').read_bytes(),RAW)
            self.assertFalse(r['visual_quality_verified'])
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=backend)
    def test_invalid_spec_and_wrong_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW)
            s=m.review(root,'source.png','out.png','painted landscape',256)
            for patch in ({'strength_percent':0},{'size':True},{'steps':31},{'output':'../out.png'},{'seed':-1}):
                with self.assertRaises(ValueError):m.execute(root,'unused',dict(s,**patch),backend=lambda *_:OUT)
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=lambda *_:RAW)
            self.assertFalse((root/'out.png').exists())
    def test_stale_source_during_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();source=root/'source.png';source.write_bytes(RAW)
            s=m.review(root,'source.png','out.png','painted landscape',256)
            def backend(*_):
                source.write_bytes(OUT);return OUT
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=backend)
            self.assertFalse((root/'out.png').exists())
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=lambda *_:OUT)

    def test_reference_guidance_and_stale_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW)
            reference=root/'ref.png';reference.write_bytes(encode(1,1,'RGB',bytes([200,30,80])))
            s=m.review_reference(root,'source.png','ref.png','out.png','painted scene',256,15,60,7,100)
            def backend(model,raw,plan):
                self.assertEqual(decode(raw,('RGB',))[3],bytes([200,30,80])*2)
                return OUT
            r=m.execute(root,'unused',s,backend=backend)
            self.assertEqual(r['reference_method'],'classical_palette_initialisation')
            self.assertFalse(r['semantic_reference_conditioning'])
            (root/'out.png').unlink()
            def changed(*_):
                reference.write_bytes(RAW);return OUT
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=changed)
            self.assertFalse((root/'out.png').exists())
