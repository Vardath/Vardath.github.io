from array import array
import json,math,tempfile,unittest
from pathlib import Path
from deepthort_local.audio_restoration import checked,restore,review,execute
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm

SPEC={'audio':'a.wav','remove_dc':True,'hum_hz':0,'click_threshold':5000}
RATE=8000
def fixture():
    x=array('h',[2000]*24000);x[4000]=20000
    return encode(x,RATE,1)
def amplitude(values,hz):
    # Ignore filter settling at the beginning; use a whole number of periods.
    values=values[16000:32000]
    return 2*abs(sum(v*complex(math.cos(2*math.pi*hz*i/RATE),math.sin(2*math.pi*hz*i/RATE)) for i,v in enumerate(values)))/len(values)
class RestorationTests(unittest.TestCase):
    def test_dc_and_click(self):
        raw=fixture();out,r=restore(raw,SPEC)
        s,rate,c,f=pcm(out)
        self.assertEqual((rate,c,f),(8000,1,24000))
        self.assertEqual(r['isolated_sample_repairs'],[1])
        self.assertEqual(r['dc_removed_pcm'],[2000.0]);self.assertEqual(max(abs(v) for v in s),0)
    def test_hum_and_wanted_tone(self):
        values=array('h',(round(4000*math.sin(2*math.pi*50*i/RATE)+6000*math.sin(2*math.pi*1000*i/RATE)) for i in range(32000)))
        raw=encode(values,RATE,1);out,r=restore(raw,dict(SPEC,remove_dc=False,hum_hz=50,click_threshold=0))
        s,_,_,_=pcm(out)
        self.assertLess(amplitude(s,50),amplitude(values,50)*.15)
        self.assertGreater(amplitude(s,1000),amplitude(values,1000)*.95)
        self.assertEqual(r['linked_headroom_gain'],1.0);self.assertFalse(r['listening_verified'])
    def test_bounds_and_stale(self):
        for spec in (dict(SPEC,hum_hz=55),dict(SPEC,click_threshold=True),dict(SPEC,remove_dc=False,click_threshold=0)):
            with self.assertRaises(ValueError):checked(spec)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();raw=fixture();audio=root/'a.wav';audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=review(root,'spec.json','repair.wav')
            r=execute(root,plan);self.assertTrue(r['source_unchanged']);self.assertEqual(audio.read_bytes(),raw)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'repair.wav').unlink();audio.write_bytes(encode(array('h',[1]*24000),RATE,1))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'repair.wav').exists())
