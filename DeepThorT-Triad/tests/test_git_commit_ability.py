import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from deepthort_local.git_commit import preview,approved_plan,apply

@unittest.skipUnless(shutil.which('git'),'Git required')
class GitCommitTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.exe=shutil.which('git')
        self.git('init','-q')
        self.git('config','user.name','JANUS fixture');self.git('config','user.email','fixture@example.invalid')
        self.write('tracked.txt','base\n');self.git('add','tracked.txt');self.git('commit','-qm','baseline')
    def git(self,*args):
        return subprocess.check_output([self.exe,'-C',str(self.root),*args],stderr=subprocess.STDOUT).decode('utf-8').strip()
    def write(self,path,text): (self.root/path).write_text(text,encoding='utf-8')
    def test_exact_staged_tree_preserves_unstaged_and_untracked(self):
        self.write('tracked.txt','staged\n');self.git('add','tracked.txt')
        self.write('tracked.txt','unstaged\n');self.write('private.txt','untracked\n')
        rev=preview(self.exe,self.root)
        self.assertIn('+staged',rev['diff']);self.assertNotIn('unstaged',rev['diff'])
        parent=self.git('rev-parse','HEAD')
        result=apply(self.exe,self.root,approved_plan(rev,'Reviewed change'))
        self.assertEqual(self.git('rev-parse','HEAD'),result['commit'])
        self.assertEqual(result['parent'],parent)
        self.assertEqual(self.git('show','HEAD:tracked.txt'),'staged')
        self.assertIn('M tracked.txt',self.git('status','--short'))
        self.assertIn('?? private.txt',self.git('status','--short'))
        self.assertFalse(result['remote_published']);self.assertFalse(result['tests_verified'])
    def test_staged_change_invalidates_approval(self):
        self.write('tracked.txt','first\n');self.git('add','tracked.txt')
        plan=approved_plan(preview(self.exe,self.root),'First')
        parent=self.git('rev-parse','HEAD')
        self.write('tracked.txt','second\n');self.git('add','tracked.txt')
        with self.assertRaises(ValueError):apply(self.exe,self.root,plan)
        self.assertEqual(self.git('rev-parse','HEAD'),parent)
    def test_empty_detached_subdirectory_and_expiry(self):
        with self.assertRaises(ValueError):preview(self.exe,self.root)
        self.write('tracked.txt','next\n');self.git('add','tracked.txt')
        plan=approved_plan(preview(self.exe,self.root),'Next');plan['expires_at']=0
        with self.assertRaises(ValueError):apply(self.exe,self.root,plan)
        sub=self.root/'sub';sub.mkdir()
        with self.assertRaises(ValueError):preview(self.exe,sub)
        self.git('checkout','--detach')
        with self.assertRaises(ValueError):preview(self.exe,self.root)
if __name__=='__main__':unittest.main()
