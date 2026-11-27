from array import array
import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local import automated_mastering as m
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm
RATE=8000
SPEC={'audio':'mix.wav','threshold_dbfs':-18,'ratio':4,'attack_ms':5,'release_ms':100,
      'target_rms_dbfs':-18,'max_boost_db':6,'peak_dbfs':-3}
def fixture():
    s=array('h')
    for i in range(3*RATE):
        a=2000 if i<RATE else 24000
        v=round(a*math.sin(2*math.pi*440*i/RATE));s.extend((v,v//2))
    return encode(s,RATE,2)
class MasterTests(unittest.TestCase):
    def test_linked_compression_and_peak(self):
        raw=fixture();data,r=m.master(raw,SPEC);out,rate,c,n=pcm(data)
        self.assertEqual((rate,c,n),(RATE,2,3*RATE))
        self.assertGreater(r['max_compression_reduction_db'],5)
        self.assertLessEqual(r['output_peak_pcm'],math.floor(32767*10**(-3/20)))
        self.assertLessEqual(r['makeup_gain_db'],6)
        self.assertTrue(all(abs(a-2*b)<=3 for a,b in zip(out[::2],out[1::2])))
        self.assertFalse(r['true_peak_verified']);self.assertEqual(m.master(raw,SPEC)[0],data)
    def test_silence_and_controls(self):
        with self.assertRaises(ValueError):m.master(encode(array('h',[0]*3*RATE),RATE,1),SPEC)
        with self.assertRaises(ValueError):m.checked(dict(SPEC,ratio=0))
        with self.assertRaises(ValueError):m.checked(dict(SPEC,release_ms=float('nan')))
        _,r=m.master(fixture(),dict(SPEC,ratio=1));self.assertEqual(r['max_compression_reduction_db'],0)
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();src=root/'mix.wav';raw=fixture();src.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=m.review(root,'spec.json','master.wav')
            result=m.execute(root,plan);self.assertTrue(result['source_unchanged']);self.assertEqual(src.read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'master.wav').unlink();src.write_bytes(encode(array('h',[2000]*3*RATE),RATE,1))
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'master.wav').exists())
