import tempfile
import unittest
from pathlib import Path
from deepthort_local.interactive_editor import snapshot,prepare,save
from deepthort_local.workspace import WorkspaceError

class InteractiveEditorTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/'project';self.root.mkdir()
        self.backups=Path(tmp.name)/'backups'
        self.file=self.root/'code.py'
        self.file.write_bytes(b'\xef\xbb\xbfvalue = 1\r\n')
    def test_exact_edit_preserves_encoding_and_backup(self):
        original=self.file.read_bytes()
        base=snapshot(self.root,'code.py')
        review=prepare(base,'value = 2\n')
        self.assertTrue(review['syntax_checked'])
        self.assertIn('+value = 2',review['diff'])
        save(review,self.backups)
        self.assertEqual(self.file.read_bytes(),b'\xef\xbb\xbfvalue = 2\r\n')
        self.assertEqual(next(self.backups.rglob('code.py')).read_bytes(),original)
    def test_stale_review_and_tampered_candidate(self):
        base=snapshot(self.root,'code.py')
        review=prepare(base,'value = 2\n')
        self.file.write_bytes(b'value = 99\n')
        with self.assertRaises(WorkspaceError):save(review,self.backups)
        self.assertEqual(self.file.read_bytes(),b'value = 99\n')
        review=prepare(snapshot(self.root,'code.py'),'value = 2\n')
        review['rendered']='value = 8\n'
        with self.assertRaises(WorkspaceError):save(review,self.backups)
    def test_new_file_and_syntax_and_protected(self):
        with self.assertRaises(ValueError):prepare(snapshot(self.root,'code.py'),'def broken(\n')
        with self.assertRaises(WorkspaceError):snapshot(self.root,'../outside.py')
        with self.assertRaises(WorkspaceError):snapshot(self.root,'.git/config',allow_missing=True)
        base=snapshot(self.root,'new.py',allow_missing=True)
        review=prepare(base,'print("new")\n')
        save(review,self.backups)
        self.assertEqual((self.root/'new.py').read_bytes(),b'print("new")\n')
    def test_mixed_newlines_and_unchanged(self):
        with self.assertRaises(WorkspaceError):prepare(snapshot(self.root,'code.py'),'value = 1\n')
        self.file.write_bytes(b'a=1\r\nb=2\n')
        with self.assertRaises(WorkspaceError):snapshot(self.root,'code.py')
if __name__=='__main__':unittest.main()
