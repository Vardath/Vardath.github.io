import tempfile
import unittest
from pathlib import Path
from deepthort_local.tool_acquisition import ToolAcquisition

class EnrollmentTests(unittest.TestCase):
    def test_new_tool_persists_and_change_invalidates(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);exe=p/'custom.exe';exe.write_bytes(b'v1')
            store=ToolAcquisition(p/'tools.sqlite')
            with self.assertRaises(PermissionError):store.enroll('Custom CLI',exe,'--help')
            store.enroll('Custom CLI',exe,'--help',user_approved=True)
            store=ToolAcquisition(p/'tools.sqlite')
            self.assertEqual(store.probe_command('Custom CLI'),[str(exe.resolve()),'--help'])
            self.assertEqual(len(store.enrolled()),1)
            exe.write_bytes(b'changed executable')
            self.assertEqual(store.enrolled(),[])
            with self.assertRaises(ValueError):store.probe_command('Custom CLI')
            store.enroll('Custom CLI',exe,'-h',user_approved=True)
            self.assertEqual(store.probe_command('Custom CLI')[-1],'-h')
    def test_no_shell_or_arbitrary_flags(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);exe=p/'cmd.exe';exe.write_bytes(b'fake')
            s=ToolAcquisition(p/'tools.sqlite')
            with self.assertRaises(ValueError):s.enroll('Unknown CLI',exe,'--help',user_approved=True)
            exe=p/'new.exe';exe.write_bytes(b'fake')
            with self.assertRaises(ValueError):s.enroll('Unknown CLI',exe,'--execute',user_approved=True)
            with self.assertRaises(ValueError):s.enroll('Python',exe,'--help',user_approved=True)
if __name__=='__main__':unittest.main()
