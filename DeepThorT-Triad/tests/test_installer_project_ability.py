import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.installer_project import checked,review,execute
S={'app_name':'Example App','app_id':'Example','version':'1.2.0','files':['bin/app.exe','data/info.txt'],'entrypoint':'bin/app.exe'}
class InstallerTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);self.root=Path(td.name)
        for name in S['files']:
            p=self.root/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'fixture payload')
        (self.root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
    def test_reviewed_per_user_source(self):
        plan,preview=review(self.root,'spec.json','setup.iss')
        result=execute(self.root,plan);script=(self.root/'setup.iss').read_text(encoding='utf-8-sig')
        self.assertIn('PrivilegesRequired=lowest',script)
        self.assertIn('Source: "bin\\app.exe"; DestDir: "{app}\\bin"',script)
        self.assertNotIn('[Run]',script);self.assertNotIn('[Code]',script)
        self.assertEqual(preview['payload_hashes'],result['payload_sha256'])
        self.assertFalse(result['compiled']);self.assertFalse(result['installed'])
    def test_paths_and_injection(self):
        for change in ({'app_name':'Bad\n[Run]'},{'files':['../app.exe'],'entrypoint':'../app.exe'},
                       {'files':['bin/app.exe','BIN/APP.EXE']},{'version':'1;bad'}):
            with self.assertRaises(ValueError):checked(dict(S,**change))
    def test_changed_payload_blocks_publication(self):
        plan,_=review(self.root,'spec.json','setup.iss')
        (self.root/'data/info.txt').write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse((self.root/'setup.iss').exists())
