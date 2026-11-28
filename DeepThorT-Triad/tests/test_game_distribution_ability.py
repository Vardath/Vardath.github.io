import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from deepthort_local import game_distribution as tool

def fixture():
    # Synthetic header only: intentionally not an executable game.
    raw=bytearray(512);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,64)
    raw[64:68]=b'PE\0\0';struct.pack_into('<HH',raw,68,0x8664,1)
    struct.pack_into('<HH',raw,84,112,2);struct.pack_into('<H',raw,88,0x20b)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('Game.exe',raw);z.writestr('data.txt',b'game assets')
    return buf.getvalue()

class DistributionTests(unittest.TestCase):
    def spec(self,raw):
        return {'artifact':'game.zip','name':'Example','version':'1.2.3','sha256':hashlib.sha256(raw).hexdigest(),
                'entrypoint':'Game.exe','release_notes':'First release'}
    def test_exact_build_preserved_and_receipt(self):
        raw=fixture();s=self.spec(raw);bundle,r=tool.bundle(raw,s)
        self.assertEqual(r['architecture'],'x64');self.assertFalse(r['gameplay_verified'])
        with zipfile.ZipFile(io.BytesIO(bundle)) as z:
            self.assertEqual(z.read('Example-1.2.3-windows.zip'),raw)
            self.assertEqual(json.loads(z.read('JANUS-DISTRIBUTION.json')),r)
            self.assertEqual(z.read('RELEASE_NOTES.txt'),b'First release\n')
        self.assertEqual(len(r['files']),2)
    def test_reject_wrong_entrypoint_and_hash(self):
        raw=fixture();s=self.spec(raw)
        with self.assertRaises(ValueError):tool.inspect(raw,dict(s,entrypoint='Other.exe'))
        with self.assertRaises(ValueError):tool.inspect(raw,dict(s,sha256='0'*64))
        with self.assertRaises(ValueError):tool.pe_header(b'not a PE')
    def test_review_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=fixture();s=self.spec(raw)
            (root/'game.zip').write_bytes(raw);(root/'spec.json').write_text(json.dumps(s))
            plan,_=tool.review(root,'spec.json','Example-1.2.3-distribution.zip')
            r=tool.execute(root,plan);self.assertEqual(r['status'],'game_distribution_bundle_prepared')
            self.assertEqual((root/'game.zip').read_bytes(),raw)
            with self.assertRaises(ValueError):tool.execute(root,plan)

if __name__=='__main__':unittest.main()
