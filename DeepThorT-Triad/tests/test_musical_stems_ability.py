from array import array
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from deepthort_local import musical_stems as m
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm
RATE=44100
class Backend:
    def __init__(self):self.calls=0
    def run(self,plan,raw,cancelled):
        self.calls+=1
        s,_,_,_=pcm(raw);a=array('h',(v//2 for v in s));b=array('h',(v-x for v,x in zip(s,a)))
        return {m.NAMES[0]:encode(a,RATE,2),m.NAMES[1]:encode(b,RATE,2)}
class StemTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(m,'MODEL_SHA',hashlib.sha256(b'fixture-model').hexdigest()))
        self.enterContext(patch.object(m,'MODEL_SIZE',len(b'fixture-model')))
    def fixture(self,folder):
        root=folder/'project';root.mkdir();exe=folder/m.EXE;model=folder/m.MODEL
        exe.write_bytes(b'fixture-exe');model.write_bytes(b'fixture-model')
        raw=encode(array('h',[1200,-500]*3*RATE),RATE,2);(root/'mix.wav').write_bytes(raw)
        plan=m.review(root,'mix.wav','stems.zip',str(exe),str(model))
        return root,plan,model,raw
    def test_bundle_and_native_command(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,_,raw=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(PermissionError):m.render(root,plan,backend=backend)
            r=m.render(root,plan,approved=True,backend=backend)
            self.assertEqual(backend.calls,1);self.assertEqual(r['relative_reconstruction_rmse'],0)
            self.assertEqual(m.MEMORY_LIMIT,512*1024**2)
            cmd=m.command(plan,root)
            self.assertIn('--provider=cpu',cmd);self.assertIn('--num-threads=1',cmd)
            self.assertTrue(any(x.startswith('--uvr-model=') for x in cmd))
            with zipfile.ZipFile(root/'stems.zip') as z:
                manifest=json.loads(z.read('manifest.json'))
                self.assertEqual(set(z.namelist()),{'manifest.json',*m.NAMES})
                self.assertFalse(manifest['semantic_quality_verified'])
                self.assertEqual(manifest['source_sha256'],hashlib.sha256(raw).hexdigest())
                for item in manifest['stems']:self.assertEqual(hashlib.sha256(z.read(item['file'])).hexdigest(),item['sha256'])
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=backend)
    def test_model_changed_and_cancelled(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,model,_=self.fixture(Path(td).resolve());backend=Backend()
            with self.assertRaises(ValueError):m.render(root,plan,lambda:True,approved=True,backend=backend)
            model.write_bytes(b'wrong-model')
            with self.assertRaises(ValueError):m.render(root,plan,approved=True,backend=backend)
            self.assertFalse((root/'stems.zip').exists());self.assertEqual(backend.calls,0)
    def test_wrong_output(self):
        with tempfile.TemporaryDirectory() as td:
            root,plan,_,raw=self.fixture(Path(td).resolve());outputs=Backend().run(plan,raw,None)
            outputs[m.NAMES[1]]=encode(array('h',[1]*3*RATE),RATE,1)
            with self.assertRaises(ValueError):m.verify(raw,outputs)
