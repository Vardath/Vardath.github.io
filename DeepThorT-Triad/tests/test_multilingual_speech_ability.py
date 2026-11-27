import json,tempfile,unittest,wave,math
from pathlib import Path
from array import array
from deepthort_local import multilingual_speech as m
EN={'id':'en','name':'English fixture','culture':'en-AU','gender':'Female'}
FR={'id':'fr','name':'French fixture','culture':'fr-FR','gender':'Male'}
SPEC={'segments':[{'culture':'en-AU','voice_id':'en','text':'Hello'},{'culture':'fr-FR','voice_id':'fr','text':'Bonjour'},{'culture':'en-AU','voice_id':'en','text':'Again'}],'pause_ms':250}
class Backend:
    def __init__(self):self.calls=[]
    def voices(self,cancelled):return [EN,FR]
    def synthesize(self,text,voice,dest,cancelled):
        self.calls.append((text,voice['id']))
        samples=array('h',(int(1000*math.sin(i*.2)) for i in range(m.RATE)))
        with wave.open(str(dest),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(m.RATE);w.writeframes(samples.tobytes())
        return m.inspect_audio(dest)
class MultiTests(unittest.TestCase):
    def test_exact_multilingual_render(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=m.review(td,'spec.json','out.wav',[EN,FR])
            backend=Backend()
            with self.assertRaises(PermissionError):m.render(td,plan,backend=backend)
            r=m.render(td,plan,approved=True,backend=backend)
            self.assertEqual(backend.calls,[('Hello','en'),('Bonjour','fr'),('Again','en')])
            self.assertAlmostEqual(r['duration_seconds'],3.5,places=3)
            self.assertAlmostEqual(r['segments'][1]['start_seconds'],1.25,places=3)
            self.assertFalse(r['pronunciation_verified']);self.assertFalse(r['translation_performed'])
            with self.assertRaises(ValueError):m.render(td,plan,approved=True,backend=backend)
    def test_missing_changed_voice_and_source(self):
        with self.assertRaises(ValueError):m.select([EN],SPEC)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'spec.json';p.write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=m.review(td,'spec.json','out.wav',[EN,FR])
            b=Backend();b.voices=lambda _: [EN,dict(FR,name='changed')]
            with self.assertRaises(ValueError):m.render(td,plan,approved=True,backend=b)
            self.assertEqual(b.calls,[])
            p.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):m.render(td,plan,approved=True,backend=Backend())
    def test_exact_culture_and_bounded_settings(self):
        for bad in (dict(SPEC,pause_ms=3000),{'segments':[dict(SPEC['segments'][0],culture='en')],'pause_ms':0}):
            with self.assertRaises(ValueError):m.checked(bad)
        with self.assertRaises(ValueError):m.select([EN,dict(FR,name=EN['name'])],SPEC)
