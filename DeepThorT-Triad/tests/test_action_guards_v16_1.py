import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import action_guards as guards
from deepthort_local.portable_procedures_probe import exercise

class FileIdentityTests(unittest.TestCase):
    def test_stable_file_and_modified_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.xml';path.write_bytes(b'<root/>')
            pin=guards.snapshot_file(path)
            self.assertEqual(pin['expected'],hashlib.sha256(b'<root/>').hexdigest())
            guards.verify_guards([pin])
            path.write_bytes(b'<tree/>')
            with self.assertRaises(ValueError):guards.verify_guards([pin])
    @unittest.skipUnless(os.name=='nt','native Windows handles')
    def test_native_handle_identity_and_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.xml';path.write_bytes(b'<root/>')
            other=Path(folder)/'other.xml';other.write_bytes(b'<root/>')
            with path.open('rb') as a,path.open('rb') as b,other.open('rb') as c:
                self.assertEqual(guards._windows_handle_identity(a),guards._windows_handle_identity(b))
                self.assertNotEqual(guards._windows_handle_identity(a)[:2],guards._windows_handle_identity(c)[:2])
            self.assertEqual(guards._file_digest(path),hashlib.sha256(b'<root/>').hexdigest())
    @unittest.skipUnless(os.name=='nt','native Windows handles')
    def test_inconsistent_handle_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.xml';path.write_bytes(b'<root/>')
            with path.open('rb') as f:ident=guards._windows_handle_identity(f)
            other=(ident[0],b'changed file id!',*ident[2:])
            with patch.object(guards,'_windows_handle_identity',side_effect=[ident,other]):
                with self.assertRaisesRegex(ValueError,'changed while opening'):guards._file_digest(path)
    def test_full_portable_procedure_regression(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
