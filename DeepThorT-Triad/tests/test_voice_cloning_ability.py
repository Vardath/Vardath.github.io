import json,tempfile,unittest
from array import array
from pathlib import Path
from deepthort_local import voice_cloning as m
from deepthort_local.noise_reduction import encode

class Backend:
    def __init__(self):self.calls=[]
    def render(self,s,raw,cancelled):
        self.calls.append((s['language'],s['text'],m.reference(raw)['frames']))
        return encode(array('h',[1000,-1000]*12000),24000,1)

class CloneTests(unittest.TestCase):
    def setup_inputs(self,td):
        base=Path(td).resolve();root=base/'project';root.mkdir()
        engine=base/'tts.exe';engine.write_bytes(b'trusted fixture')
        model=base/'model';model.mkdir()
        (model/'config.json').write_text(json.dumps({'model':'xtts','audio':{'output_sample_rate':24000},'languages':['en']}),encoding='utf8')
        for n in ('model.pth','vocab.json','speakers_xtts.pth'):(model/n).write_bytes(n.encode())
        (root/'ref.wav').write_bytes(encode(array('h',[1000,-1000]*48000),16000,1))
        s={'reference':'ref.wav','engine':str(engine),'model_directory':str(model),'language':'en','text':'Reviewed narration',
           'consent':{'basis':'own_voice','scope':'Private narration','non_deceptive':True}}
        (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
        return root,s,model
    def test_review_render_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root,s,_=self.setup_inputs(td);plan,review=m.review(root,'spec.json','out.wav');b=Backend()
            with self.assertRaises(PermissionError):m.execute(root,plan,backend=b)
            self.assertFalse(b.calls)
            result=m.execute(root,plan,backend=b,approved=True)
            self.assertEqual(b.calls,[('en','Reviewed narration',96000)])
            self.assertEqual(result['sample_rate'],24000)
            self.assertFalse(result['similarity_verified']);self.assertFalse(result['consent_independently_verified'])
            self.assertEqual(result['reference_sha256'],review['reference_format']['sha256'])
            with self.assertRaises(ValueError):m.execute(root,plan,backend=b,approved=True)
    def test_consent_language_and_command(self):
        with tempfile.TemporaryDirectory() as td:
            root,s,_=self.setup_inputs(td)
            for bad in (dict(s,consent=dict(s['consent'],non_deceptive=False)),dict(s,language='xx'),dict(s,consent=dict(s['consent'],basis='unknown'))):
                with self.assertRaises(ValueError):m.checked(bad)
            args=m.command(s,root/'ref.wav',root/'out.wav')
            self.assertEqual(args[args.index('--device')+1],'cpu')
            self.assertNotIn('--model_name',args)
            self.assertEqual(args[args.index('--speaker_wav')+1],str(root/'ref.wav'))
    def test_changed_reference_engine_and_model(self):
        with tempfile.TemporaryDirectory() as td:
            root,s,model=self.setup_inputs(td);plan,_=m.review(root,'spec.json','out.wav');b=Backend()
            (model/'model.pth').write_bytes(b'changed checkpoint')
            with self.assertRaises(ValueError):m.execute(root,plan,backend=b,approved=True)
            self.assertFalse(b.calls)
            plan,_=m.review(root,'spec.json','out.wav')
            (root/'ref.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan,backend=b,approved=True)
            self.assertFalse((root/'out.wav').exists())
if __name__=='__main__':unittest.main()
