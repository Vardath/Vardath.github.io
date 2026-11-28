import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from deepthort_local.git_commit import worktree_inventory,worktree_batch_plan,apply_worktree_batch

@unittest.skipUnless(shutil.which('git'),'Git required')
class WorktreeBatchTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name).resolve();self.root=self.base/'repo';self.root.mkdir()
        self.git=shutil.which('git')
        self.run_git('init','-q')
        self.run_git('config','user.name','JANUS fixture');self.run_git('config','user.email','fixture@example.invalid')
        (self.root/'file.txt').write_text('base')
        self.run_git('add','file.txt');self.run_git('commit','-qm','initial')
        self.run_git('branch','first-work');self.run_git('branch','second-work')
    def run_git(self,*args):
        return subprocess.check_output([self.git,'-C',str(self.root),*args],stderr=subprocess.STDOUT)
    def assignments(self):
        return [{'branch':'first-work','parent':str(self.base),'name':'first'},
                {'branch':'second-work','parent':str(self.base),'name':'second'}]
    def plan(self,items=None):
        return worktree_batch_plan(self.git,self.root,worktree_inventory(self.git,self.root),self.assignments() if items is None else items)
    def test_real_distinct_worktrees(self):
        r=apply_worktree_batch(self.git,self.root,self.plan())
        self.assertEqual(len(r['worktrees']),2);self.assertFalse(r['security_sandbox'])
        (self.base/'first'/'file.txt').write_text('changed')
        self.assertEqual((self.base/'second'/'file.txt').read_text(),'base')
        self.assertEqual((self.root/'file.txt').read_text(),'base')
    def test_duplicate_and_stale_approval(self):
        a=self.assignments();a[1]['name']='first'
        with self.assertRaises(ValueError):self.plan(a)
        p=self.plan();(self.base/'second').mkdir()
        with self.assertRaises(ValueError):apply_worktree_batch(self.git,self.root,p)
        self.assertFalse((self.base/'first').exists())

if __name__=='__main__':unittest.main()
