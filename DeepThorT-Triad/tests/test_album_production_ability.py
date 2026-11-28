import io,json,tempfile,unittest,wave,zipfile
from pathlib import Path
from deepthort_local import album_production as m
from deepthort_local.music_metadata import parse

def wav(rate=8000):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b'\x00\x10\x00\xf0'*(3*rate//2))
    return b.getvalue()

class AlbumTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.spec={'album':'Example','artist':'Artist','tracks':[{'audio':'a.wav','title':'First'},{'audio':'b.wav','title':'Second'}],
                   'mastering':{'threshold_dbfs':-18,'ratio':2,'attack_ms':10,'release_ms':100,'target_rms_dbfs':-18,'max_boost_db':6,'peak_dbfs':-2}}
        for name in ('a.wav','b.wav'):(self.root/name).write_bytes(wav())
        self.write()
    def write(self):
        (self.root/'album.json').write_text(json.dumps(self.spec),encoding='utf8')
    def test_order_tags_and_exclusive_archive(self):
        plan,_=m.review(self.root,'album.json','album.zip')
        result=m.execute(self.root,plan)
        self.assertEqual(result['status'],'album_bundle_verified')
        self.assertFalse(result['listening_verified'])
        with zipfile.ZipFile(self.root/'album.zip') as z:
            self.assertEqual(z.read('PLAYLIST.m3u8'),b'tracks/01.wav\ntracks/02.wav\n')
            self.assertEqual(parse(z.read('tracks/02.wav'))[3]['title'],'Second')
            self.assertEqual(parse(z.read('tracks/02.wav'))[3]['track'],'2')
            self.assertEqual(parse(z.read('tracks/01.wav'))[3]['album'],'Example')
        self.assertEqual((self.root/'a.wav').read_bytes(),wav())
        with self.assertRaises(ValueError):m.execute(self.root,plan)
    def test_stale_source(self):
        plan,_=m.review(self.root,'album.json','album.zip')
        (self.root/'b.wav').write_bytes(wav(16000))
        with self.assertRaises(ValueError):m.execute(self.root,plan)
        self.assertFalse((self.root/'album.zip').exists())
    def test_invalid_track_and_format(self):
        self.spec['tracks'][1]['audio']='a.wav'
        with self.assertRaises(ValueError):m.checked(self.spec)
        self.spec['tracks'][1]['audio']='b.wav';self.write()
        (self.root/'b.wav').write_bytes(wav(16000))
        with self.assertRaises(ValueError):m.review(self.root,'album.json','album.zip')

if __name__=='__main__':unittest.main()
