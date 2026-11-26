import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from deepthort_local.git_commit import preview,approved_plan,apply,preview_selected,branch_inventory,branch_plan,apply_branch,branch_operation_plan,apply_branch_operation

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
    def test_selected_file_commit(self):
        self.write('tracked.txt','reviewed\n')
        self.write('new.txt','new\n')
        self.write('other.txt','do not stage\n')
        review=preview_selected(self.exe,self.root,['tracked.txt','new.txt'])
        self.assertNotIn('other.txt',review['diff'])
        self.assertEqual(self.git('diff','--cached','--name-only'),'')
        result=apply(self.exe,self.root,approved_plan(review,'Selected'))
        self.assertEqual(self.git('show','HEAD:tracked.txt'),'reviewed')
        self.assertEqual(self.git('show','HEAD:new.txt'),'new')
        self.assertEqual(self.git('status','--short'),'?? other.txt')
    def test_selected_stale_and_staged_guard(self):
        self.write('tracked.txt','first\n')
        plan=approved_plan(preview_selected(self.exe,self.root,['tracked.txt']),'First')
        self.write('tracked.txt','second\n')
        with self.assertRaises(ValueError):apply(self.exe,self.root,plan)
        self.assertEqual(self.git('diff','--cached','--name-only'),'')
        self.git('add','tracked.txt')
        with self.assertRaises(ValueError):preview_selected(self.exe,self.root,['tracked.txt'])
    def test_branch_create_and_no_overwrite(self):
        before=self.git('rev-parse','HEAD')
        original=self.git('symbolic-ref','HEAD')
        review=branch_inventory(self.exe,self.root)
        plan=branch_plan(self.exe,self.root,review,'review/feature')
        result=apply_branch(self.exe,self.root,plan)
        self.assertEqual(self.git('rev-parse','refs/heads/review/feature'),before)
        self.assertEqual(self.git('symbolic-ref','HEAD'),original)
        self.assertFalse(result['checked_out'])
        with self.assertRaises(ValueError):apply_branch(self.exe,self.root,plan)
    def test_branch_stale_and_invalid(self):
        review=branch_inventory(self.exe,self.root)
        with self.assertRaises(ValueError):branch_plan(self.exe,self.root,review,'../escape')
        plan=branch_plan(self.exe,self.root,review,'feature')
        self.write('tracked.txt','new\n');self.git('add','tracked.txt')
        with self.assertRaises(ValueError):apply_branch(self.exe,self.root,plan)
    def test_rename_and_delete_merged_local_branch(self):
        self.git('branch','feature')
        plan=branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),'rename','feature','renamed')
        apply_branch_operation(self.exe,self.root,plan)
        self.assertEqual(self.git('rev-parse','refs/heads/renamed'),self.git('rev-parse','HEAD'))
        plan=branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),'delete','renamed')
        apply_branch_operation(self.exe,self.root,plan)
        self.assertNotIn('renamed',self.git('branch','--list'))
    def test_clean_switch_preserves_branch_contents_and_refuses_dirty(self):
        main=self.git('symbolic-ref','--short','HEAD')
        self.git('checkout','-qb','feature')
        self.write('tracked.txt','feature\n');self.git('add','tracked.txt');self.git('commit','-qm','feature')
        self.git('checkout','-q',main)
        plan=branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),'switch','feature')
        self.write('untracked.txt','keep\n')
        with self.assertRaises(ValueError):apply_branch_operation(self.exe,self.root,plan)
        (self.root/'untracked.txt').unlink()
        apply_branch_operation(self.exe,self.root,plan)
        self.assertEqual(self.git('symbolic-ref','--short','HEAD'),'feature')
        self.assertEqual((self.root/'tracked.txt').read_text('utf-8'),'feature\n')
    def test_reject_unmerged_delete_and_stale_ref(self):
        main=self.git('symbolic-ref','--short','HEAD')
        self.git('checkout','-qb','unmerged')
        self.write('tracked.txt','different\n');self.git('add','tracked.txt');self.git('commit','-qm','different')
        self.git('checkout','-q',main)
        with self.assertRaises(ValueError):branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),'delete','unmerged')
        self.git('branch','old')
        plan=branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),'rename','old','new')
        self.git('branch','-f','old','unmerged')
        with self.assertRaises(ValueError):apply_branch_operation(self.exe,self.root,plan)
    def test_refuse_checked_out_linked_worktree(self):
        self.git('branch','linked')
        with tempfile.TemporaryDirectory() as other:
            path=Path(other)/'linked'
            self.git('worktree','add',str(path),'linked')
            try:
                for operation,new in [('switch',None),('rename','new'),('delete',None)]:
                    with self.assertRaises(ValueError):branch_operation_plan(self.exe,self.root,branch_inventory(self.exe,self.root),operation,'linked',new)
            finally:self.git('worktree','remove',str(path))
if __name__=='__main__':unittest.main()
