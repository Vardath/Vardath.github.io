import json,math,tempfile,unittest,zipfile
from array import array
from pathlib import Path
from deepthort_local import custom_voice_design as m
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm

VOICE={'id':'en','name':'Fixture voice','culture':'en-AU','gender':'Female'}
SPEC={'name':'Radio character','voice':VOICE,'text':'A reviewed audition of the designed character.',
      'effects':{'speed_percent':125,'ring_hz':40,'ring_depth_percent':20,'lowpass_hz':1800}}
class Backend:
    def __init__(self):self.calls=[]
    def voices(self,_):return [VOICE]
    def synthesize(self,text,voice,path,_):
        self.calls.append((text,voice))
        rate=22050
        path.write_bytes(encode(array('h',(round(1800*math.sin(2*math.pi*220*i/rate)) for i in range(6*rate))),rate,1))
        return m.inspect_audio(path)

class VoiceDesignTests(unittest.TestCase):
    def fixture(self,td):
        root=Path(td).resolve();(root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
        return root
    def test_reusable_design_and_audition(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(td);plan,_=m.review(root,'spec.json','design.zip');b=Backend()
            self.assertFalse(b.calls)
            r=m.execute(root,plan,backend=b)
            self.assertEqual(r['status'],'voice_design_audition_verified')
            self.assertFalse(r['new_neural_voice_trained'])
            self.assertEqual(b.calls,[(SPEC['text'],VOICE)])
            with zipfile.ZipFile(root/'design.zip') as z:
                self.assertEqual(json.loads(z.read('voice-design.json')),SPEC)
                self.assertEqual(pcm(z.read('audition.wav'))[1:],(22050,1,105840))
                self.assertFalse(json.loads(z.read('receipt.json'))['listening_verified'])
            with self.assertRaises(ValueError):m.execute(root,plan,backend=b)
    def test_exact_voice_and_changed_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(td);plan,_=m.review(root,'spec.json','design.zip');b=Backend()
            b.voices=lambda _: [dict(VOICE,name='changed')]
            with self.assertRaises(ValueError):m.execute(root,plan,backend=b)
            self.assertFalse(b.calls)
            (root/'spec.json').write_text(json.dumps(dict(SPEC,text='changed')),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan,backend=Backend())
            self.assertFalse((root/'design.zip').exists())
    def test_invalid_and_noop_design(self):
        for bad in (dict(SPEC,name=''),dict(SPEC,effects=dict(SPEC['effects'],speed_percent=200)),
                    dict(SPEC,effects={'speed_percent':100,'ring_hz':0,'ring_depth_percent':0,'lowpass_hz':0})):
            with self.assertRaises(ValueError):m.checked(bad)
if __name__=='__main__':unittest.main()
