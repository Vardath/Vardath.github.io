from array import array
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.noise_reduction import checked,encode,reduce,review,execute
from deepthort_local.tempo_detection import pcm
SPEC={'audio':'a.wav','threshold_dbfs':-30,'attenuation_db':-30,'attack_ms':5,'release_ms':50}
def fixture(channels=1):
    return encode(array('h',[v for i in range(32000) for v in ([100 if i<16000 else 12000]*channels)]),8000,channels)
class NoiseTests(unittest.TestCase):
    def test_quiet_attenuation_and_loud_recovery(self):
        raw=fixture();out,r=reduce(raw,checked(SPEC));samples,rate,c,f=pcm(out)
        self.assertEqual((rate,c,f),(8000,1,32000))
        self.assertLess(r['low_level_rms_after'],r['low_level_rms_before']/2)
        self.assertLess(abs(samples[10000]),10);self.assertEqual(samples[-1],12000)
    def test_linked_stereo(self):
        raw=encode(array('h',[v for _ in range(24000) for v in (12000,100)]),8000,2)
        out,r=reduce(raw,SPEC);self.assertEqual(pcm(out)[0],pcm(raw)[0]);self.assertEqual(r['low_level_frames'],0)
    def test_bounds_and_zero_attenuation(self):
        with self.assertRaises(ValueError):checked(dict(SPEC,threshold_dbfs=float('nan')))
        with self.assertRaises(ValueError):checked(dict(SPEC,attack_ms=0))
        raw=fixture();out,_=reduce(raw,dict(SPEC,attenuation_db=0));self.assertEqual(pcm(out)[0],pcm(raw)[0])
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=fixture();audio=root/'a.wav';audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=review(root,'spec.json','out.wav')
            r=execute(root,plan);self.assertTrue(r['source_unchanged']);self.assertEqual(audio.read_bytes(),raw)
            (root/'out.wav').unlink();audio.write_bytes(fixture(2))
            with self.assertRaises(ValueError):execute(root,plan)
