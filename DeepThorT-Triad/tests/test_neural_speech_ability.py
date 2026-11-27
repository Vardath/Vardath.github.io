import io,json,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import neural_speech as n
def fixture_audio():
    b=io.BytesIO()
    with wave.open(b,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050);f.writeframes(b'\xe8\x03'*22050)
    return b.getvalue()
class Backend:
    def __init__(self):self.calls=0
    def render(self,plan,cancelled):self.calls+=1;return fixture_audio()
class NeuralTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);base=Path(td.name).resolve()
        self.project=base/'project';self.project.mkdir()
        install=base/'install';install.mkdir()
        self.exe=install/'piper.exe';self.exe.write_bytes(b'not an executable: fixture')
        self.voice=install/'voice.onnx';self.voice.write_bytes(b'fixture voice')
        self.config=install/'voice.onnx.json';self.config.write_text(json.dumps({'audio':{'sample_rate':22050},'num_speakers':1,'phoneme_type':'espeak'}),encoding='utf-8')
    def plan(self):return n.review(self.project,self.exe,self.voice,'speech.wav','Fixture text',1,.667,.8)
    def test_reviewed_fixture_publication(self):
        plan=self.plan();backend=Backend()
        with self.assertRaises(PermissionError):n.render(self.project,plan,backend=backend)
        self.assertEqual(backend.calls,0)
        result=n.render(self.project,plan,approved=True,backend=backend)
        self.assertFalse(result['expressive_quality_verified'])
        self.assertEqual((self.project/'speech.wav').read_bytes(),fixture_audio())
        with self.assertRaises(ValueError):n.render(self.project,plan,approved=True,backend=backend)
    def test_changed_model_and_protected_output(self):
        plan=self.plan();self.voice.write_bytes(b'changed')
        with self.assertRaises(ValueError):n.render(self.project,plan,approved=True,backend=Backend())
        with self.assertRaises(ValueError):n.review(self.project,self.exe,self.voice,'../bad.wav','x',1,.5,.5)
        with self.assertRaises(ValueError):n.review(self.project,self.exe,self.voice,'speech.wav','[[ raw ]]',1,.5,.5)
    def test_unsupported_voice_and_controls(self):
        self.config.write_text(json.dumps({'audio':{'sample_rate':22050},'num_speakers':2,'phoneme_type':'espeak'}),encoding='utf-8')
        with self.assertRaises(ValueError):self.plan()
        with self.assertRaises(ValueError):n.settings('x',2,.5,.5)
        with self.assertRaises(ValueError):n.inspect(b'bad',22050)
