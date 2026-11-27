import tempfile,unittest
from pathlib import Path
from deepthort_local import speech_to_text as s,microphone_input as m
class Backend:
    def __init__(self):self.calls=[]
    def recognize(self,staged,culture,cancelled):
        self.calls.append((staged,culture))
        return {'culture':culture,'recognizer_id':'fixture','segments':[{'text':'Fixture words','confidence':.8,'start_seconds':0,'duration_seconds':.9}]}
class SpeechTests(unittest.TestCase):
    def test_reviewed_audio_and_result(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.wav';raw=m.wav_bytes(b'\x01\x00'*32000,2);p.write_bytes(raw)
            plan,seconds=s.review(td,'input.wav','en-AU');self.assertEqual(seconds,2)
            backend=Backend()
            with self.assertRaises(PermissionError):s.recognize(td,plan,backend=backend)
            self.assertEqual(backend.calls,[])
            result=s.recognize(td,plan,approved=True,backend=backend)
            self.assertEqual(result['text'],'Fixture words');self.assertFalse(result['accuracy_verified'])
            self.assertFalse(result['automatically_submitted']);self.assertEqual(p.read_bytes(),raw)
            p.write_bytes(m.wav_bytes(b'\x02\x00'*32000,2))
            with self.assertRaises(ValueError):s.recognize(td,plan,approved=True,backend=backend)
    def test_result_validation(self):
        base={'culture':'en-US','recognizer_id':'fixture','segments':[]}
        self.assertEqual(s.normalize(base,'en-US',2)['status'],'no_speech_recognized')
        with self.assertRaises(ValueError):s.normalize(base,'en-AU',2)
        for row in ({'text':'x','confidence':1.2,'start_seconds':0,'duration_seconds':1},{'text':'x','confidence':.5,'start_seconds':2,'duration_seconds':1}):
            with self.assertRaises(ValueError):s.normalize(dict(base,segments=[row]),'en-US',2)
    def test_refusal_and_cancellation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.wav';p.write_bytes(m.wav_bytes(b'\0'*32000,1))
            with self.assertRaises(ValueError):s.review(td,'input.wav','en-US',['input.wav'])
            plan,_=s.review(td,'input.wav','en-US')
            with self.assertRaises(ValueError):s.recognize(td,plan,lambda:True,approved=True,backend=Backend())
        with self.assertRaises(ValueError):s.audio(b'not a wav')
