import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from deepthort_local import software_deployment as tool

def archive(name='app/readme.txt'):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:z.writestr(name,b'example')
    return buf.getvalue()

class DeploymentTests(unittest.TestCase):
    def spec(self,raw):
        return {'artifact':'artifact.zip','name':'Example','version':'1.2.3','sha256':hashlib.sha256(raw).hexdigest()}
    def test_exact_release_and_previous_version(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();raw=archive();s=self.spec(raw)
            (root/'artifact.zip').write_bytes(raw);(root/'spec.json').write_text(json.dumps(s))
            (root/'releases').mkdir();old=root/'releases/Example-1.2.2.zip';old.write_bytes(b'old')
            with self.assertRaises(ValueError):tool.review(root,'spec.json','releases/wrong.zip')
            plan,_=tool.review(root,'spec.json','releases/Example-1.2.3.zip')
            r=tool.execute(root,plan)
            self.assertEqual(r['status'],'local_versioned_release_deployed')
            self.assertEqual((root/r['output']).read_bytes(),raw);self.assertEqual(old.read_bytes(),b'old')
            self.assertFalse(r['installed']);self.assertFalse(r['remote_deployed'])
            with self.assertRaises(ValueError):tool.execute(root,plan)
    def test_reject_unsafe_archive_and_wrong_hash(self):
        for name in ('../escape.txt','app/CON.txt','/abs.txt'):
            raw=archive(name)
            with self.assertRaises(ValueError):tool.inspect(raw,self.spec(raw))
        raw=archive();s=self.spec(raw);s['sha256']='0'*64
        with self.assertRaises(ValueError):tool.inspect(raw,s)

if __name__=='__main__':unittest.main()
