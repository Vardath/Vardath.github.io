import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.installer_project import checked,review,execute,MAX_FILES,MAX_FILE
from deepthort_local.action_guards import snapshot_file,validate_guards,MAX_GUARDS,MAX_HASH_BYTES
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

    def test_real_queue_guard_budget(self):
        self.assertEqual(MAX_FILES,MAX_GUARDS-4);self.assertEqual(MAX_FILE,MAX_HASH_BYTES)
        files=['bin/app.exe']+['file'+str(i)+'.txt' for i in range(MAX_FILES-1)]
        for name in files[1:]:(self.root/name).write_bytes(b'fixture')
        (self.root/'spec.json').write_text(json.dumps(dict(S,files=files)),encoding='utf-8')
        plan,_=review(self.root,'spec.json','setup.iss')
        root=self.root.resolve()
        guards=[snapshot_file(root/'script.py',kind='absent'),*plan['guards'],snapshot_file(root/'setup.iss',kind='absent'),snapshot_file(root/'exclusions.json',kind='absent')]
        self.assertEqual(len(validate_guards(guards)),MAX_GUARDS)
        self.assertLess(len(json.dumps(plan,ensure_ascii=True)),4096)
        with self.assertRaises(ValueError):checked(dict(S,files=files+['extra.txt']))
