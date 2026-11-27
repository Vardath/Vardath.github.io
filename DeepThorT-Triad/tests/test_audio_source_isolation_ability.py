from array import array
import io,json,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local.audio_source_isolation import checked,isolate,review,execute
from deepthort_local.noise_reduction import encode
from deepthort_local.tempo_detection import pcm
SPEC={'audio':'mix.wav','component':'center'}
def fixture():
    # Shared 1000 PCM center plus opposite 400 PCM side.
    return encode(array('h',[1400,600,32767,-32768]*12000),8000,2)
class IsolationTests(unittest.TestCase):
    def test_all_modes_and_exact_reconstruction(self):
        raw=fixture();original=pcm(raw)[0]
        expected={'center':[1000,1000,0,0],'side':[400,-400,32767,-32768],
                  'left':[1400,0,32767,0],'right':[0,600,0,-32768]}
        for mode in expected:
            data,r=isolate(raw,dict(SPEC,component=mode))
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                a=pcm(z.read('selected.wav'))[0];b=pcm(z.read('residual.wav'))[0]
                self.assertEqual(list(a[:4]),expected[mode]);self.assertTrue(all(x+y==v for x,y,v in zip(a,b,original)))
                self.assertEqual(json.loads(z.read('manifest.json')),r)
            self.assertTrue(r['sample_exact_reconstruction']);self.assertFalse(r['semantic_separation_verified'])
    def test_bounds(self):
        with self.assertRaises(ValueError):checked(dict(SPEC,component='vocals'))
        with self.assertRaises(ValueError):isolate(encode(array('h',[1]*24000),8000,1),SPEC)
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();raw=fixture();audio=root/'mix.wav';audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(SPEC));plan,_=review(root,'spec.json','out.zip')
            r=execute(root,plan);self.assertTrue(r['source_unchanged']);self.assertEqual(audio.read_bytes(),raw)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'out.zip').unlink();audio.write_bytes(encode(array('h',[10,20]*24000),8000,2))
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'out.zip').exists())
