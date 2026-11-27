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

    def test_inpainting_preserves_unmasked_pixels_and_rejects_stale_mask(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=encode(256,256,'RGB',bytes([20,40,60])*(256*256))
            (root/'source.png').write_bytes(src)
            mask=encode(256,256,'L',bytes([255])+bytes(256*256-1));mp=root/'mask.png';mp.write_bytes(mask)
            s=m.review_mask(root,'source.png','mask.png','out.png','repair region',256,15,80,7)
            def backend(model,raw,mask_raw,plan):
                self.assertEqual(raw,src);self.assertEqual(mask_raw,mask);return OUT
            r=m.execute(root,'unused',s,mask_backend=backend)
            pixels=decode((root/'out.png').read_bytes(),('RGB',))[3]
            self.assertEqual(pixels[:3],bytes([30,60,90]))
            self.assertEqual(pixels[3:],bytes([20,40,60])*(256*256-1))
            self.assertTrue(r['unmasked_pixels_preserved'])
            (root/'out.png').unlink()
            def changed(*_):
                mp.write_bytes(encode(256,256,'L',bytes([0,255])+bytes(256*256-2)));return OUT
            with self.assertRaises(ValueError):m.execute(root,'unused',s,mask_backend=changed)
            self.assertFalse((root/'out.png').exists())
    def test_invalid_inpainting_mask(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(OUT)
            for invalid in (encode(256,256,'L',bytes(256*256)),encode(256,256,'L',bytes([128])*(256*256)),encode(256,256,'L',bytes([255])*(256*256))):
                (root/'mask.png').write_bytes(invalid)
                with self.assertRaises(ValueError):m.review_mask(root,'source.png','mask.png','out.png','repair',256)

    def test_outpainting_preserves_source_at_offset(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW)
            s=m.review_outpaint(root,'source.png','out.png','extend landscape',256,10,20,15,90,5)
            def backend(model,raw,mask,plan):
                w,h,_,mp=decode(mask,('L',));self.assertEqual((w,h),(256,256))
                self.assertEqual(mp[20*256+10:20*256+12],bytes(2))
                self.assertEqual(mp.count(0),2);return OUT
            r=m.execute(root,'unused',s,mask_backend=backend)
            pixels=decode((root/'out.png').read_bytes(),('RGB',))[3]
            start=(20*256+10)*3
            self.assertEqual(pixels[start:start+6],decode(RAW,('RGB',))[3])
            self.assertEqual(pixels[:3],bytes([30,60,90]))
            self.assertEqual(r['source_offset'],[10,20]);self.assertTrue(r['source_pixels_preserved'])
    def test_outpainting_rejects_invalid_canvas(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(RAW)
            for x,y in ((255,0),(-1,0),(0,256)):
                with self.assertRaises(ValueError):m.review_outpaint(root,'source.png','out.png','extend',256,x,y)
            (root/'source.png').write_bytes(OUT)
            with self.assertRaises(ValueError):m.review_outpaint(root,'source.png','out.png','extend',256,0,0)

    def test_object_removal_discards_original_selected_content(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();n=256*256
            source=encode(256,256,'RGB',bytes([250,0,0])+bytes([20,40,60])*(n-1))
            mask=encode(256,256,'L',bytes([255])+bytes(n-1))
            (root/'source.png').write_bytes(source);(root/'mask.png').write_bytes(mask)
            s=m.review_removal(root,'source.png','mask.png','out.png','empty background','red ball',256)
            def backend(model,raw,mask_raw,plan):
                self.assertEqual(decode(raw,('RGB',))[3],bytes([20,40,60])*n)
                self.assertEqual(plan['removed_object'],'red ball');return OUT
            r=m.execute(root,'unused',s,mask_backend=backend)
            self.assertTrue(r['original_masked_pixels_discarded_before_diffusion'])
            self.assertFalse(r['object_absence_verified'])
            self.assertEqual(decode((root/'out.png').read_bytes(),('RGB',))[3][3:],bytes([20,40,60])*(n-1))
            with self.assertRaises(ValueError):m.checked(dict(s,removed_object=''))
    def test_object_removal_rejects_noop_and_insufficient_context(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(OUT)
            (root/'mask.png').write_bytes(encode(256,256,'L',bytes([255])+bytes(256*256-1)))
            s=m.review_removal(root,'source.png','mask.png','out.png','background','ball',256)
            with self.assertRaises(ValueError):m.execute(root,'unused',s,mask_backend=lambda *_:OUT)
            self.assertFalse((root/'out.png').exists())
            (root/'mask.png').write_bytes(encode(256,256,'L',bytes([255])*(256*256-1)+bytes(1)))
            with self.assertRaises(ValueError):m.review_removal(root,'source.png','mask.png','out.png','background','ball',256)

    def test_object_replacement_distinct_positive_and_negative_guidance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();n=256*256
            source=encode(256,256,'RGB',bytes([250,0,0])+bytes([20,40,60])*(n-1))
            (root/'source.png').write_bytes(source)
            (root/'mask.png').write_bytes(encode(256,256,'L',bytes([255])+bytes(n-1)))
            s=m.review_replacement(root,'source.png','mask.png','out.png','soft daylight','red ball','blue cube',256)
            def backend(model,raw,mask_raw,plan):
                self.assertEqual(decode(raw,('RGB',))[3],bytes([20,40,60])*n)
                self.assertEqual(m.positive_prompt(plan),'blue cube, soft daylight, integrated into the surrounding scene')
                self.assertEqual(plan['removed_object'],'red ball');return OUT
            r=m.execute(root,'unused',s,mask_backend=backend)
            self.assertEqual(r['replacement_object'],'blue cube');self.assertFalse(r['replacement_identity_verified'])
            self.assertEqual(decode((root/'out.png').read_bytes(),('RGB',))[3][3:],bytes([20,40,60])*(n-1))
            for invalid in (dict(s,replacement_object=' RED  BALL '),dict(s,replacement_object=''),dict(s,operation='remove_object')):
                with self.assertRaises(ValueError):m.checked(invalid)
    def test_object_replacement_rejects_noop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'source.png').write_bytes(OUT)
            (root/'mask.png').write_bytes(encode(256,256,'L',bytes([255])+bytes(256*256-1)))
            s=m.review_replacement(root,'source.png','mask.png','out.png','room','ball','cube',256)
            with self.assertRaises(ValueError):m.execute(root,'unused',s,mask_backend=lambda *_:OUT)
            self.assertFalse((root/'out.png').exists())

    def test_pose_guidance_is_bound_and_rasterized(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            coords=[[500,120],[500,230],[390,260],[610,260],[310,420],[690,420],[260,550],[740,550],[440,530],[560,530],[400,710],[600,710],[380,880],[620,880]]
            pose={'joints':dict(zip(m.POSE_JOINTS,coords))};src=root/'pose.json';src.write_text(json.dumps(pose),encoding='utf-8')
            s=m.review_pose(root,'pose.json','out.png','person in a space suit',256)
            expected=m.pose_guide(src.read_bytes(),256)
            def backend(model,raw,plan):
                self.assertEqual(raw,expected);self.assertEqual(plan['guide_kind'],'pose')
                self.assertGreater(len(set(decode(raw,('RGB',))[3])),2);return OUT
            r=m.execute(root,'unused',s,backend=backend)
            self.assertEqual(r['pose_conditioning'],'joint_raster_initialisation')
            self.assertFalse(r['pose_fidelity_verified']);self.assertFalse(r['controlnet_used'])
            (root/'out.png').unlink()
            def changed(*_):
                pose['joints']['head']=[510,120];src.write_text(json.dumps(pose),encoding='utf-8');return OUT
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=changed)
            self.assertFalse((root/'out.png').exists())
    def test_pose_rejects_invalid_joints(self):
        import json
        coords=dict(zip(m.POSE_JOINTS,[[500,120],[500,230],[390,260],[610,260],[310,420],[690,420],[260,550],[740,550],[440,530],[560,530],[400,710],[600,710],[380,880],[620,880]]))
        for joints in ({},dict(coords,head=[True,100]),dict(coords,head=[1001,100]),dict(coords,head=coords['neck'])):
            with self.assertRaises(ValueError):m.pose_guide(json.dumps({'joints':joints}).encode(),256)

    def test_depth_guidance_polarity_and_exact_input(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'depth.png'
            pixels=bytes(range(256))*256
            src.write_bytes(encode(256,256,'L',pixels))
            near=m.depth_guide(src.read_bytes(),256,True,0)
            far=m.depth_guide(src.read_bytes(),256,False,0)
            self.assertEqual(decode(near,('RGB',))[3][:3],bytes([32])*3)
            self.assertEqual(decode(far,('RGB',))[3][:3],bytes([223])*3)
            self.assertNotEqual(near,m.depth_guide(src.read_bytes(),256,True,50))
            s=m.review_depth(root,'depth.png','out.png','metal structures',256,15,60,5,True,0)
            def backend(model,raw,plan):
                self.assertEqual(raw,near);self.assertEqual(plan['guide_kind'],'depth');return OUT
            r=m.execute(root,'unused',s,backend=backend)
            self.assertEqual(r['depth_conditioning'],'relative_depth_raster_initialisation')
            self.assertFalse(r['depth_fidelity_verified'])
            (root/'out.png').unlink()
            def changed(*_):
                src.write_bytes(encode(256,256,'L',bytes(reversed(range(256)))*256));return OUT
            with self.assertRaises(ValueError):m.execute(root,'unused',s,backend=changed)
            self.assertFalse((root/'out.png').exists())
    def test_depth_guide_rejects_flat_and_mismatched(self):
        for raw in (encode(256,256,'L',bytes([55])*(256*256)),encode(128,128,'L',bytes(range(128))*128),OUT):
            with self.assertRaises(ValueError):m.depth_guide(raw,256,True,35)
