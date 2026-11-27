from array import array
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.audio_conversion import checked,review,execute
from deepthort_local.noise_reduction import encode
class AudioConversionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.raw=encode(array('h',[(i%200-100)*60 for i in range(96000)]),32000,1)
        (self.root/'a.wav').write_bytes(self.raw);self.spec={'audio':'a.wav','format':'flac','bitrate_kbps':None}
        self.save()
    def save(self):(self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf-8')
    def test_actual_flac_lossless(self):
        plan,preview=review(self.root,'spec.json','out.flac');r=execute(self.root,plan)
        self.assertEqual(len(plan['guards']),4);self.assertEqual(len(preview['installed_tools']),2)
        self.assertTrue(r['lossless_pcm_verified']);self.assertEqual(r['source_pcm_sha256'],r['decoded_pcm_sha256'])
        self.assertEqual((self.root/'out.flac').read_bytes()[:4],b'fLaC')
        self.assertEqual((self.root/'a.wav').read_bytes(),self.raw)
    def test_actual_mp3_decoding(self):
        self.spec.update(format='mp3',bitrate_kbps=128);self.save()
        plan,_=review(self.root,'spec.json','out.mp3');r=execute(self.root,plan)
        self.assertEqual(r['codec'],'mp3');self.assertFalse(r['lossless_pcm_verified'])
        self.assertLessEqual(abs(r['decoded_frames']-r['source_frames']),6400)
        self.assertGreater((self.root/'out.mp3').stat().st_size,1000)
    def test_format_and_bitrate_refusal(self):
        with self.assertRaises(ValueError):review(self.root,'spec.json','out.mp3')
        with self.assertRaises(ValueError):checked(dict(self.spec,bitrate_kbps=128))
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'spec.json','out.flac')
        out=self.root/'out.flac';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink()
        (self.root/'a.wav').write_bytes(self.raw+b'x')
        with self.assertRaises(ValueError):execute(self.root,plan)
