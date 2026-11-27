import io,json,math,tempfile,unittest,wave,zipfile,hashlib
from array import array
from pathlib import Path
from deepthort_local import dialogue_generation as p
EN={'id':'en','name':'Host','culture':'en-AU','gender':'Female'}
FR={'id':'fr','name':'Guest','culture':'fr-FR','gender':'Male'}
SPEC={'title':'Fixture dialogue','description':'A local dialogue','pause_ms':250,'turns':[
    {'speaker':'Host','culture':'en-AU','voice_id':'en','text':'Welcome'},
    {'speaker':'Guest','culture':'fr-FR','voice_id':'fr','text':'Bonjour'},
    {'speaker':'Host','culture':'en-AU','voice_id':'en','text':'Goodbye'}]}
class Backend:
    def __init__(self):self.calls=[]
    def voices(self,cancelled):return [EN,FR]
    def synthesize(self,text,voice,dest,cancelled):
        from deepthort_local.local_speech import inspect_audio
        self.calls.append((text,voice['id']))
        samples=array('h',(int(1000*math.sin(i*.2)) for i in range(p.RATE)))
        with wave.open(str(dest),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(p.RATE);w.writeframes(samples.tobytes())
        return inspect_audio(dest)
class DialogueTests(unittest.TestCase):
    def test_dialogue_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'script.json';path.write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=p.review(td,'script.json','dialogue.zip',[EN,FR]);backend=Backend()
            with self.assertRaises(PermissionError):p.render(td,plan,backend=backend)
            result=p.render(td,plan,approved=True,backend=backend)
            self.assertEqual(backend.calls,[('Welcome','en'),('Bonjour','fr'),('Goodbye','en')])
            self.assertAlmostEqual(result['duration_seconds'],3.5,places=3)
            with zipfile.ZipFile(Path(td)/'dialogue.zip') as z:
                manifest=json.loads(z.read('dialogue.json'));audio=z.read('dialogue.wav')
                self.assertEqual(manifest['audio_sha256'],hashlib.sha256(audio).hexdigest())
                self.assertEqual(manifest['turns'][1]['speaker'],'Guest')
                self.assertEqual(manifest['speakers'],['Host','Guest'])
                self.assertAlmostEqual(manifest['turns'][1]['start_seconds'],1.25,places=3)
                self.assertIn('Bonjour',z.read('transcript.txt').decode())
                with wave.open(io.BytesIO(audio),'rb') as w:self.assertAlmostEqual(w.getnframes()/p.RATE,3.5,places=3)
            self.assertFalse(result['published_online'])
            with self.assertRaises(ValueError):p.render(td,plan,approved=True,backend=backend)
    def test_invalid_and_inconsistent_speaker(self):
        for row in (dict(SPEC['turns'][1],speaker='host'),dict(SPEC['turns'][1],speaker='Host'),dict(SPEC['turns'][1],speaker='Guest',culture='en-AU',voice_id='en')):
            with self.assertRaises(ValueError):p.checked(dict(SPEC,turns=[SPEC['turns'][0],row,SPEC['turns'][2]]))
        with self.assertRaises(ValueError):p.checked(dict(SPEC,turns=[SPEC['turns'][0],SPEC['turns'][2]]))
        self.assertEqual(len(p.checked(dict(SPEC,turns=SPEC['turns'][:2]))['turns']),2)
    def test_stale_script_and_cancel(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'script.json';path.write_text(json.dumps(SPEC),encoding='utf-8')
            plan,_=p.review(td,'script.json','dialogue.zip',[EN,FR])
            with self.assertRaises(ValueError):p.render(td,plan,lambda:True,approved=True,backend=Backend())
            path.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):p.render(td,plan,approved=True,backend=Backend())
            self.assertFalse((Path(td)/'dialogue.zip').exists())
