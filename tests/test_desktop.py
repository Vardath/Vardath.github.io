import tempfile
import unittest
from pathlib import Path
from deepthort_local.workspace import (safe_target, read_project_file, list_project_files,
    apply_approved_file, diff_preview, strip_single_code_fence, WorkspaceError)
from deepthort_local.tasks import TaskBoard

class WorkspaceTests(unittest.TestCase):
    def test_safe_paths_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'project';root.mkdir()
            self.assertEqual(safe_target(root,'src/new.py'),root/'src'/'new.py')
            for name in ('../secret.txt','/etc/passwd','src/../secret.txt','.'):
                with self.assertRaises(WorkspaceError): safe_target(root,name)
    def test_prevent_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'p';root.mkdir()
            outside=Path(tmp)/'outside';outside.mkdir()
            try: (root/'linked').symlink_to(outside, target_is_directory=True)
            except OSError: self.skipTest('symlinks unsupported')
            with self.assertRaises(WorkspaceError):safe_target(root,'linked/steal.py')
    def test_file_approval_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'work';root.mkdir()
            backup=Path(tmp)/'backups'
            (root/'main.py').write_text('old\n')
            target=apply_approved_file(root,'main.py','new\n',backup)
            self.assertEqual(target.read_text(),'new\n')
            self.assertTrue(any(p.read_text()=='old\n' for p in backup.rglob('main.py')))
            self.assertIn('new',diff_preview('old\n','new\n','main.py'))
            self.assertEqual(list_project_files(root),['main.py'])
    def test_reject_binary_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'binary').write_bytes(b'a\x00b')
            with self.assertRaises(WorkspaceError): read_project_file(root,'binary')
            with self.assertRaises(WorkspaceError): apply_approved_file(root,'hello.py','x'*230000,root/'b')
    def test_code_fence(self):
        self.assertEqual(strip_single_code_fence('```python\nprint(1)\n```'),'print(1)\n')
        self.assertEqual(strip_single_code_fence('hello'),'hello')
        with self.assertRaises(WorkspaceError):strip_single_code_fence('```python\nx\n```\nNot really')
    def test_task_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'tasks.db'
            board=TaskBoard(db)
            ident=board.add('p1','make a game')
            self.assertEqual(TaskBoard(db).items('p1')[0][1],'make a game')
            self.assertEqual(board.items('p2'),[])
            board.mark('p1',ident,True)
            self.assertEqual(TaskBoard(db).items('p1')[0][2],1)

if __name__=='__main__': unittest.main()
