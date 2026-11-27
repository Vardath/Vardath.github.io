import json,math,tempfile,unittest
from array import array
from pathlib import Path
from deepthort_local import voice_transformation as m

def fixture():
    rate=8000
    return m.encode(array('h',(round(2000*math.sin(2*math.pi*200*i/rate)) for i in range(rate*6))),rate,1)

SPEC={'audio':'speech.wav','speed_percent':150,'ring_hz':0,'ring_depth_percent':0,'lowpass_hz':0}

class VoiceTests(unittest.TestCase):
    def test_varispeed_changes_pitch_and_duration(self):
        raw=fixture();payload,r=m.transform(raw,SPEC)
        samples,rate,channels,n=m.pcm(payload)
        self.assertEqual((rate,channels,n),(8000,1,32000))
        crossings=sum(a<=0<b for a,b in zip(samples,samples[1:]))
        self.assertLess(abs(crossings-1200),4)
        self.assertEqual(r['pitch_ratio'],1.5)
        self.assertFalse(r['duration_preserved'])
        self.assertFalse(r['independent_pitch_shift'])
    def test_ring_and_lowpass_and_invalid_controls(self):
        raw=fixture();s=dict(SPEC,speed_percent=100,ring_hz=40,ring_depth_percent=100,lowpass_hz=800)
        payload,r=m.transform(raw,s)
        self.assertTrue(r['duration_preserved']);self.assertNotEqual(payload,raw)
        self.assertFalse(r['voice_identity_conversion']);self.assertLessEqual(r['output_peak_pcm'],2000)
        for bad in (dict(SPEC,speed_percent=74),dict(SPEC,ring_hz=40),dict(SPEC,lowpass_hz=100),dict(SPEC,speed_percent=100)):
            with self.assertRaises(ValueError):m.checked(bad)
    def test_exact_source_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=fixture();(root/'speech.wav').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.wav')
            r=m.execute(root,plan)
            self.assertTrue(r['pcm_verified']);self.assertEqual((root/'speech.wav').read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.wav')
            (root/'speech.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.wav').exists())
if __name__=='__main__':unittest.main()
