import io,json,tempfile,unittest,wave
from array import array
from pathlib import Path
from deepthort_local import sound_effect_generation as m

SPEC={'effect':'ui_beep','duration_ms':500,'start_hz':440,'end_hz':440,'noise_percent':0,'seed':12,'peak_dbfs':-6}
class SoundTests(unittest.TestCase):
    def test_tonal_duration_pitch_and_peak(self):
        raw,r=m.generate(SPEC)
        with wave.open(io.BytesIO(raw),'rb') as f:
            self.assertEqual((f.getframerate(),f.getnchannels(),f.getnframes()),(24000,1,12000))
            samples=array('h');samples.frombytes(f.readframes(f.getnframes()))
        self.assertEqual((samples[0],samples[-1]),(0,0))
        self.assertLessEqual(r['peak_pcm'],16423)
        self.assertLess(abs(sum(a<=0<b for a,b in zip(samples,samples[1:]))-220),3)
    def test_seeded_noise_and_profiles(self):
        s=dict(SPEC,effect='whoosh',noise_percent=100,end_hz=1400)
        a,_=m.generate(s);b,_=m.generate(s);c,_=m.generate(dict(s,seed=13))
        self.assertEqual(a,b);self.assertNotEqual(a,c)
        for mode in ('impact','sweep'):
            self.assertTrue(m.generate(dict(s,effect=mode,noise_percent=20))[1]['pcm_verified'])
        for bad in (dict(s,noise_percent=0),dict(SPEC,duration_ms=3001),dict(SPEC,end_hz=500)):
            with self.assertRaises(ValueError):m.checked(bad)
    def test_review_source_guard_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav')
            self.assertTrue(m.execute(root,plan)['pcm_verified'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.wav');p.write_text(json.dumps(dict(SPEC,seed=1)),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
