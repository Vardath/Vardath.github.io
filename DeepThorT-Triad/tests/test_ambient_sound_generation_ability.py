import io,json,tempfile,unittest,wave
from array import array
from pathlib import Path
from deepthort_local import ambient_sound_generation as m

SPEC={'profile':'wind','duration_seconds':4,'intensity_percent':60,'stereo_width_percent':0,'seed':19,'peak_dbfs':-12}
class AmbientTests(unittest.TestCase):
    def test_periodic_filter(self):
        self.assertEqual(list(m.circular_mean([1,2,3,4],2)),[2.5,1.5,2.5,3.5])
        self.assertEqual(list(m.circular_mean([1,2,3],1)),[1,2,3])
    def test_exact_format_width_seed_and_profiles(self):
        raw,r=m.generate(SPEC)
        with wave.open(io.BytesIO(raw),'rb') as f:
            self.assertEqual((f.getframerate(),f.getnchannels(),f.getnframes()),(24000,2,96000))
            a=array('h');a.frombytes(f.readframes(f.getnframes()))
        self.assertEqual(a[::2],a[1::2])
        self.assertEqual(r['loop_boundary_delta_pcm'],[abs(a[0]-a[-2]),abs(a[1]-a[-1])])
        self.assertLessEqual(r['peak_pcm'],8231)
        self.assertEqual(raw,m.generate(SPEC)[0])
        self.assertNotEqual(raw,m.generate(dict(SPEC,seed=20))[0])
        for profile in ('rain','machine_hum'):
            b,receipt=m.generate(dict(SPEC,profile=profile,stereo_width_percent=80))
            with wave.open(io.BytesIO(b),'rb') as f:
                samples=array('h');samples.frombytes(f.readframes(f.getnframes()))
            self.assertNotEqual(samples[::2],samples[1::2])
            self.assertFalse(receipt['seam_audibility_verified'])
    def test_review_guards_and_invalid_settings(self):
        for bad in (dict(SPEC,duration_seconds=21),dict(SPEC,stereo_width_percent=-1),dict(SPEC,profile='unknown')):
            with self.assertRaises(ValueError):m.checked(bad)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav')
            self.assertTrue(m.execute(root,plan)['pcm_verified'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','new.wav');p.write_text(json.dumps(dict(SPEC,seed=3)),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'new.wav').exists())
if __name__=='__main__':unittest.main()
