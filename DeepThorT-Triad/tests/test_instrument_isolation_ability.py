from array import array
import hashlib,json,struct,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import instrument_isolation as m
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm
RATE=m.RATE
def float_wav(frames,value):
    data=struct.pack('<ff',value,value)*frames
    fmt=struct.pack('<HHIIHH',3,2,RATE,RATE*8,8,32)
    body=b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(data))+data
    return b'RIFF'+struct.pack('<I',len(body))+body
class Backend:
    def __init__(self):self.calls=0
    def run(self,plan,raw,cancelled):
        self.calls+=1
        return {n:float_wav(plan['frames'],.125 if n in ('bass','guitar') else 0) for n in m.NAMES}
class InstrumentTests(unittest.TestCase):
    def fixture(self,folder):
        root=folder/'project';root.mkdir();exe=folder/m.EXE;model=folder/m.MODEL
        exe.write_bytes(b'fixture-exe');model.write_bytes(b'fixture-model')
        raw=encode(array('h',[8192,8192]*3*RATE),RATE,2);(root/'mix.wav').write_bytes(raw)
        plan=m.review(root,'mix.wav','instrument.zip',str(exe),str(model),'bass')
        return root,plan,model,raw
    def test_selected_and_complement(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,_,raw=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(PermissionError):m.render(root,plan,backend=backend)
            r=m.render(root,plan,approved=True,backend=backend)
            self.assertEqual(r['relative_reconstruction_rmse'],0)
            self.assertEqual(r['target'],'bass');self.assertFalse(r['semantic_quality_verified'])
            with zipfile.ZipFile(root/'instrument.zip') as z:
                self.assertEqual(pcm(z.read('instrument.wav'))[0][0],4096)
                self.assertEqual(pcm(z.read('other_stems.wav'))[0][0],4096)
                self.assertEqual(json.loads(z.read('manifest.json'))['model_sha256'],hashlib.sha256(b'fixture-model').hexdigest())
            self.assertEqual(m.command(plan,root),[plan['files'][0]['path'],plan['files'][1]['path'],str(root/'mix.wav'),str(root/'out')])
            self.assertEqual(m.filename('piano'),'target_5_piano.wav')
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=backend)
    def test_cancel_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,model,_=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(ValueError):m.render(root,plan,lambda:True,approved=True,backend=backend)
            model.write_bytes(b'changed')
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=backend)
            self.assertFalse((root/'instrument.zip').exists());self.assertEqual(backend.calls,0)
    def test_malformed_and_nonfinite(self):
        with self.assertRaises(ValueError):m.instrument('violin')
        with self.assertRaises(ValueError):m.decode_float(float_wav(3,float('nan')),3)
        with self.assertRaises(ValueError):m.decode_float(float_wav(3,.5),4)
        with self.assertRaises(ValueError):m.decode_float(b'bad',3)
