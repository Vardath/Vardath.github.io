import io
import json
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from deepthort_local.music_metadata import checked,parse,chunk,edit,review,execute
def source(with_info=True):
    b=io.BytesIO()
    with wave.open(b,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\x10\x00'*800)
    body=b.getvalue()[8:]+chunk(b'JUNK',b'odd')
    if with_info:body+=chunk(b'LIST',b'INFO'+chunk(b'INAM',b'Old title\0')+chunk(b'IART',b'Old artist\0')+chunk(b'ZZZZ',b'opaque'))
    return b'RIFF'+struct.pack('<I',len(body))+body
class MetadataTests(unittest.TestCase):
    def test_edit_remove_and_keep_audio(self):
        raw=source();spec={'audio':'a.wav','tags':{'title':'New title','artist':None,'album':'New album'}}
        result,r=edit(raw,checked(spec))
        self.assertEqual(r['before'],{'title':'Old title','artist':'Old artist'})
        self.assertEqual(r['after'],{'title':'New title','album':'New album'})
        self.assertEqual(parse(raw)[-1],parse(result)[-1]);self.assertIn(chunk(b'JUNK',b'odd'),result)
        self.assertIn(chunk(b'ZZZZ',b'opaque'),result);self.assertTrue(r['untouched_chunks_verified'])
    def test_add_info_to_plain_wave(self):
        raw=source(False);result,r=edit(raw,checked({'audio':'a.wav','tags':{'artist':'Artist'}}))
        self.assertEqual(parse(result)[3],{'artist':'Artist'});self.assertEqual(parse(raw)[-1],parse(result)[-1])
    def test_invalid_and_malformed(self):
        for value in ('bad\nvalue','café',123):
            with self.assertRaises(ValueError):checked({'audio':'a.wav','tags':{'title':value}})
        with self.assertRaises(ValueError):parse(source()[:-1])
    def test_review_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=source();audio=root/'a.wav';audio.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'audio':'a.wav','tags':{'title':'New'}}))
            plan,preview=review(root,'spec.json','out.wav');r=execute(root,plan)
            self.assertEqual(r['after'],preview['reviewed_metadata']['after']);self.assertEqual(audio.read_bytes(),raw)
            (root/'out.wav').unlink();audio.write_bytes(source(False))
            with self.assertRaises(ValueError):execute(root,plan)
