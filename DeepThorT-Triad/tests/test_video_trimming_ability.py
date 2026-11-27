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
