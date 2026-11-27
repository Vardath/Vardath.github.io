from array import array
import copy,json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import automated_audio_mixing as m
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm
RATE=8000
SPEC={'tracks':[{'audio':'a.wav','offset_ms':0,'trim_db':0,'pan':-1},
                {'audio':'b.wav','offset_ms':1000,'trim_db':0,'pan':1}],
      'target_rms_dbfs':-24,'max_boost_db':12,'peak_dbfs':-3}
def fixture(amplitude,rate=RATE):
    return encode(array('h',(amplitude if i%2 else -amplitude for i in range(3*rate))),rate,1)
class MixingTests(unittest.TestCase):
    def test_auto_balance_pan_offset(self):
        raw,r=m.mix([fixture(1000),fixture(4000)],SPEC);s,rate,c,n=pcm(raw)
        self.assertEqual((rate,c,n),(RATE,2,4*RATE))
        self.assertTrue(all(v==0 for v in s[1:2*RATE:2]))
        self.assertAlmostEqual(abs(s[2*RATE]),abs(s[2*RATE+1]),delta=1)
        self.assertTrue(all(v==0 for v in s[6*RATE::2]))
        self.assertGreater(r['tracks'][0]['automatic_gain_db'],0)
        self.assertLess(r['tracks'][1]['automatic_gain_db'],0)
        self.assertFalse(r['perceptual_balance_verified'])
    def test_peak_and_bounds(self):
        spec=copy.deepcopy(SPEC);spec['target_rms_dbfs']=-12;spec['peak_dbfs']=-12
        for t in spec['tracks']:t['pan']=0;t['trim_db']=6;t['offset_ms']=0
        _,r=m.mix([fixture(10000),fixture(10000)],spec)
        self.assertLess(r['shared_headroom_gain'],1)
        self.assertLessEqual(r['peak_pcm'],math.floor(32767*10**(-12/20)))
        with self.assertRaises(ValueError):m.mix([fixture(0),fixture(1000)],SPEC)
        with self.assertRaises(ValueError):m.mix([fixture(1000),fixture(1000,16000)],SPEC)
        with self.assertRaises(ValueError):m.checked(dict(SPEC,max_boost_db=13))
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();a=root/'a.wav';b=root/'b.wav'
            a.write_bytes(fixture(1000));b.write_bytes(fixture(4000))
            (root/'mix.json').write_text(json.dumps(SPEC));plan,_=m.review(root,'mix.json','mix.wav')
            r=m.execute(root,plan);self.assertTrue(r['source_unchanged'])
            self.assertEqual(a.read_bytes(),fixture(1000))
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'mix.wav').unlink();b.write_bytes(fixture(2000))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'mix.wav').exists())
