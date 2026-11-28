import json,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from deepthort_local import multilingual_dubbing as m
from deepthort_local.action_guards import snapshot_file

EN={'id':'en','name':'English fixture','culture':'en-AU','gender':'Female'}
FR={'id':'fr','name':'French fixture','culture':'fr-FR','gender':'Male'}
class Backend:
    def __init__(self):self.calls=[]
    def voices(self,_):return [EN,FR]
    def synthesize(self,text,voice,path,_):
        self.calls.append((text,voice['id']))
        with wave.open(str(path),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050);f.writeframes(b'\xe8\x03'*11025)
        return m.inspect_audio(path)

class DubbingTests(unittest.TestCase):
    def setup_inputs(self,root):
        s={'video':'clip.mp4','start_frame':2,'end_frame':50,'cues':[
           {'start_frame':0,'end_frame':18,'voice':EN,'text':'Hello'},
           {'start_frame':24,'end_frame':42,'voice':FR,'text':'Bonjour'}]}
        (root/'clip.mp4').write_bytes(b'fixture')
        (root/'spec.json').write_text(json.dumps(s),encoding='utf8')
        for n in ('ff','fp'):(root/n).write_bytes(n.encode())
        return s,tuple(snapshot_file(root/n) for n in ('ff','fp'))
    def test_exact_cues_and_padding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();_,tools=self.setup_inputs(root);b=Backend()
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':2,'height':2,'fps':24,'frames':60}),patch.object(m,'decode',return_value=b'0'*576),patch.object(m,'mux',return_value=b'output') as mux:
                plan,_=m.review(root,'spec.json','out.mp4')
                self.assertFalse(b.calls)
                r=m.execute(root,plan,backend=b)
                self.assertEqual(b.calls,[('Hello','en'),('Bonjour','fr')])
                pcm=mux.call_args.args[2]
                self.assertEqual(len(pcm),192000)
                self.assertEqual(pcm[:48000],b'\xe8\x03'*24000)
                self.assertEqual(pcm[48000:96000],bytes(48000))
                self.assertEqual(pcm[96000:144000],b'\xe8\x03'*24000)
                self.assertFalse(r['automatic_translation'])
                with self.assertRaises(ValueError):m.execute(root,plan,backend=b)
    def test_overlap_and_overlong(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();s,_=self.setup_inputs(root)
            s['cues'][1]['start_frame']=17
            with self.assertRaises(ValueError):m.checked(s)
        with self.assertRaises(ValueError):m.resample(b'\x01\x00'*11025,23999)
    def test_changed_voice_and_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();_,tools=self.setup_inputs(root);b=Backend()
            b.voices=lambda _: [EN,dict(FR,name='changed')]
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':2,'height':2,'fps':24,'frames':60}):
                plan,_=m.review(root,'spec.json','out.mp4')
                with self.assertRaises(ValueError):m.execute(root,plan,backend=b)
                self.assertFalse(b.calls)
                (root/'clip.mp4').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan,backend=b)
                self.assertFalse((root/'out.mp4').exists())
if __name__=='__main__':unittest.main()
