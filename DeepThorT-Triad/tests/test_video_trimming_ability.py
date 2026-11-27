import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.video_trimming import checked,review,execute,run,decode
from deepthort_local.video_tools import find_pair

class VideoTrimmingTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.ff,self.fp=find_pair()
        self.a=self.fixture('a',[(255,0,0),(0,255,0),(0,0,255)])
        self.b=self.fixture('b',[(12,34,56),(78,90,123),(220,100,40)])
        self.s={'fps':24,'clips':[{'video':'b.mp4','start_frame':1,'end_frame':3},{'video':'a.mp4','start_frame':0,'end_frame':1}]}
        self.save()
    def fixture(self,name,colors):
        raw=b''.join(bytes(c)*16*16 for c in colors);(self.root/(name+'.rgb')).write_bytes(raw)
        run(self.ff,['-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','16x16','-framerate','24',
                     '-i',name+'.rgb','-an','-threads','1','-c:v','libx264rgb','-preset','ultrafast','-crf','0',
                     '-pix_fmt','rgb24',name+'.mp4'],self.root)
        return raw
    def save(self):(self.root/'spec.json').write_text(json.dumps(self.s))
    def test_exact_order_and_trim(self):
        plan,p=review(self.root,'spec.json','out.mp4');r=execute(self.root,plan)
        self.assertEqual(r['frames'],3);self.assertTrue(r['decoded_rgb_sequence_verified'])
        actual=decode(self.ff,self.root/'out.mp4',0,3,16,16)
        self.assertEqual(actual,self.b[16*16*3:]+self.a[:16*16*3]);self.assertEqual(len(plan['guards']),5)
    def test_single_trim(self):
        self.s['clips']=self.s['clips'][:1];self.save()
        plan,_=review(self.root,'spec.json','out.mp4');r=execute(self.root,plan)
        self.assertEqual(r['frames'],2);self.assertFalse(r['audio_supported'])
    def test_invalid_ranges_and_rate(self):
        with self.assertRaises(ValueError):checked(dict(self.s,fps=29))
        self.s['clips'][0]['end_frame']=4;self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','out.mp4')
        self.s['clips'][0]['end_frame']=200
        with self.assertRaises(ValueError):checked(self.s)
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'spec.json','out.mp4');out=self.root/'out.mp4';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        src=self.root/'a.mp4';src.write_bytes(src.read_bytes()+b'x')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())


    def test_video_report_json_roundtrip(self):
        from deepthort_local.video_interpretation import report_bytes
        result={'observations':[{'caption':'First line\nSecond line'}]}
        raw=report_bytes(result)
        self.assertEqual(json.loads(raw),result)
        self.assertTrue(raw.endswith(b'\n'))

    def test_sampled_video_observations(self):
        from deepthort_local.video_interpretation import inspect,checked
        from deepthort_local.action_guards import snapshot_file
        import hashlib
        tools=[snapshot_file(Path(p).resolve(),kind='stat') for p in (self.ff,self.fp)]
        raw=(self.root/'a.mp4').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            result=inspect(raw,{'video':'a.mp4','frames':[0,2]},tools,tmp,interpret=True,
                captioner=lambda paths,guards:['red','blue'])
        self.assertEqual([x['frame'] for x in result['observations']],[0,2])
        self.assertEqual(result['observations'][1]['rgb_sha256'],hashlib.sha256(self.a[-16*16*3:]).hexdigest())
        self.assertEqual(result['observations'][1]['seconds'],2/24)
        self.assertFalse(result['native_caption_engine_invoked'])
        self.assertFalse(result['semantic_accuracy_verified'])
        for frames in ([2,0],[0,0],[True],[],[300]):
            with self.assertRaises(ValueError):checked({'video':'a.mp4','frames':frames})
    def test_video_caption_count_and_range(self):
        from deepthort_local.video_interpretation import inspect
        from deepthort_local.action_guards import snapshot_file
        tools=[snapshot_file(Path(p).resolve(),kind='stat') for p in (self.ff,self.fp)]
        raw=(self.root/'a.mp4').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):inspect(raw,{'video':'a.mp4','frames':[3]},tools,tmp)
            with self.assertRaises(ValueError):inspect(raw,{'video':'a.mp4','frames':[0,1]},tools,tmp,
                interpret=True,captioner=lambda paths,guards:['one'])


    def test_reviewed_crop_rotation_and_flip(self):
        from deepthort_local.video_trimming import edit_frames
        raw=bytes([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18])
        edit={'crop':[1,0,2,2],'rotation':90,'flip':'horizontal'}
        # Crop selects B,C,E,F; clockwise then horizontal gives B,E,C,F.
        self.assertEqual(edit_frames(raw,(3,2),edit),bytes([4,5,6,13,14,15,7,8,9,16,17,18]))
        self.s['clips']=self.s['clips'][:1]
        self.s['clips'][0]['edit']={'crop':[1,2,8,6],'rotation':90,'flip':'vertical'}
        self.save()
        plan,p=review(self.root,'spec.json','edit.mp4');r=execute(self.root,plan)
        self.assertEqual((r['width'],r['height'],r['frames']),(6,8,2))
        self.assertEqual(decode(self.ff,self.root/'edit.mp4',0,2,6,8),bytes([78,90,123])*48+bytes([220,100,40])*48)
        self.assertTrue(r['decoded_rgb_sequence_verified'])
    def test_edit_bounds_and_common_output_geometry(self):
        self.s['clips'][0]['edit']={'crop':[10,0,8,8],'rotation':0,'flip':'none'}
        self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','edit.mp4')
        self.s['clips'][0]['edit']['crop']=[0,0,8,8];self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','edit.mp4')
        self.s['clips'][0]['edit']['rotation']=True
        with self.assertRaises(ValueError):checked(self.s)


    def test_crossfade_verified_and_duration(self):
        self.s={'fps':24,'clips':[{'video':'a.mp4','start_frame':0,'end_frame':3},
                    {'video':'b.mp4','start_frame':0,'end_frame':3}],
                    'transitions':[{'kind':'crossfade','frames':1}]}
        self.save();plan,preview=review(self.root,'spec.json','fade.mp4')
        self.assertEqual(preview['observations']['output_frames'],5)
        r=execute(self.root,plan)
        # Last blue frame and first B frame, at half opacity.
        stride=16*16*3
        expected=self.a[:2*stride]+bytes([6,17,155])*256+self.b[stride:]
        self.assertEqual(decode(self.ff,self.root/'fade.mp4',0,5,16,16),expected)
        self.assertEqual(r['frames'],5);self.assertTrue(r['decoded_rgb_sequence_verified'])
    def test_reject_transition_overlap_and_schema(self):
        self.s['transitions']=[{'kind':'crossfade','frames':1}]
        with self.assertRaises(ValueError):checked(self.s) # One-frame final clip.
        self.s['transitions']=[{'kind':'cut','frames':1}]
        with self.assertRaises(ValueError):checked(self.s)
        self.s['transitions']=[]
        with self.assertRaises(ValueError):checked(self.s)
        self.s['transitions']=[{'kind':'cut','frames':0}]
        self.assertEqual(checked(self.s),self.s)

    def test_patch_tracking_translation_and_loss(self):
        from deepthort_local.video_motion_tracking import track
        def frame(x,y):
            data=bytearray(16*16*3)
            for j in range(4):
                for i in range(4):
                    p=((y+j)*16+x+i)*3
                    data[p:p+3]=bytes([10+i*30,20+j*40,100])
            return bytes(data)
        s={'video':'a.mp4','start_frame':0,'end_frame':3,'box':[2,2,4,4],'radius':3,'max_error':0}
        rows=track(frame(2,2)+frame(4,3)+bytes(16*16*3),(16,16),s)
        self.assertEqual(rows[1]['box'],[4,3,4,4])
        self.assertIsNone(rows[2]['box'])
        self.assertIn(rows[2]['state'],('lost','ambiguous'))
        with self.assertRaises(ValueError):track(bytes(3*16*16*3),(16,16),s)
    def test_motion_review_and_stale_source(self):
        from deepthort_local.video_motion_tracking import review,execute
        s={'video':'a.mp4','start_frame':0,'end_frame':3,'box':[2,2,4,4],'radius':2,'max_error':10}
        (self.root/'track.json').write_text(json.dumps(s))
        plan,_=review(self.root,'track.json','motion.json')
        (self.root/'a.mp4').write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse((self.root/'motion.json').exists())


    def test_frame_interpolation_duration_and_exact_pixels(self):
        from deepthort_local.video_trimming import interpolate_frames,probe
        self.s={'fps':24,'clips':[{'video':'a.mp4','start_frame':0,'end_frame':3}],
                'interpolation':'blend2x'}
        self.save();plan,p=review(self.root,'spec.json','smooth.mp4')
        r=execute(self.root,plan)
        self.assertEqual((r['fps'],r['frames'],r['duration_seconds']),(48,6,3/24))
        expected=b''.join(bytes(c)*256 for c in [(255,0,0),(127,127,0),(0,255,0),(0,127,127),(0,0,255),(0,0,255)])
        self.assertEqual(interpolate_frames(self.a,(16,16)),expected)
        self.assertEqual(decode(self.ff,self.root/'smooth.mp4',0,6,16,16),expected)
        self.assertEqual(probe(self.fp,self.root/'smooth.mp4',allow_double=True)['fps'],48)
    def test_interpolation_respects_hard_cut_and_bound(self):
        self.s={'fps':24,'clips':[{'video':'a.mp4','start_frame':0,'end_frame':1},
                    {'video':'b.mp4','start_frame':0,'end_frame':1}],'interpolation':'blend2x'}
        self.save();plan,_=review(self.root,'spec.json','cut.mp4')
        execute(self.root,plan);stride=16*16*3
        self.assertEqual(decode(self.ff,self.root/'cut.mp4',0,4,16,16),self.a[:stride]*2+self.b[:stride]*2)
        self.s['clips'][0]['end_frame']=61
        with self.assertRaises(ValueError):checked(self.s)
        self.s['interpolation']='neural'
        with self.assertRaises(ValueError):checked(self.s)
