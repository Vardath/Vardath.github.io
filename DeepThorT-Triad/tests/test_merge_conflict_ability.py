import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from deepthort_local.merge_conflict import review,execute
@unittest.skipUnless(shutil.which('git'),'Git executable required')
class MergeTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);self.root=Path(td.name).resolve()
        self.git('init','-q')
        self.file=self.root/'source.txt';self.file.write_bytes(b'conflicted worktree\n')
        (self.root/'spec.json').write_text(json.dumps({'path':'source.txt'}),encoding='utf-8')
        self.base=b'first\nmiddle 1\nmiddle 2\nmiddle 3\nlast\n'
        self.ours=self.base.replace(b'first',b'ours')
        self.theirs=self.base.replace(b'last',b'theirs')
        self.set_stages(self.base,self.ours,self.theirs)
    def git(self,*args,data=None):
        return subprocess.run([shutil.which('git'),'-C',str(self.root),*args],input=data,capture_output=True,check=True).stdout
    def set_stages(self,*blobs):
        rows=[]
        for i,raw in enumerate(blobs,1):
            oid=self.git('hash-object','-w','--stdin',data=raw).decode().strip()
            rows.append(f'100644 {oid} {i}\tsource.txt\n')
        self.git('update-index','--index-info',data=''.join(rows).encode())
    def test_clean_actual_index_proposal(self):
        prior=self.git('ls-files','-u','-z')
        plan,preview=review(self.root,'spec.json','merged.txt')
        self.assertIn('ours',preview['candidate']);self.assertIn('theirs',preview['candidate'])
        self.assertFalse(execute(self.root,plan)['index_modified'])
        self.assertEqual((self.root/'merged.txt').read_bytes(),self.ours.replace(b'last',b'theirs'))
        self.assertEqual(prior,self.git('ls-files','-u','-z'));self.assertEqual(self.file.read_bytes(),b'conflicted worktree\n')
    def test_overlap_not_guessed(self):
        self.set_stages(self.base,self.ours,self.base.replace(b'first',b'theirs'))
        with self.assertRaises(ValueError):review(self.root,'spec.json','merged.txt')
        self.assertFalse((self.root/'merged.txt').exists())
    def test_stage_change_blocks(self):
        plan,_=review(self.root,'spec.json','merged.txt')
        self.set_stages(self.base,self.ours,self.theirs.replace(b'theirs',b'changed'))
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse((self.root/'merged.txt').exists())
