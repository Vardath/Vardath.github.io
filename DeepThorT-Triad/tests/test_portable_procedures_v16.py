import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.portable_procedures import PortableProcedures,template_args
from deepthort_local.portable_procedures_probe import exercise,fixture

class PortableProcedureTests(unittest.TestCase):
    def test_probe(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
    def test_literal_paths_and_scripts_rejected(self):
        for args in [['folder/input.obj','{{output}}'],['{{script}}','{{output}}'],
                     ['--token','{{output}}'],['{{output}}','{{output}}']]:
            with self.assertRaises(ValueError):template_args(args)
        self.assertEqual(template_args(['--format','xml','{{input}}','{{output}}']),['--format','xml','{{input}}','{{output}}'])
    def test_stale_evidence_and_explicit_sharing(self):
        with tempfile.TemporaryDirectory() as folder:
            acq,janus,src,dest,recipe,exe=fixture(Path(folder))
            library=PortableProcedures(acq);row=library.preview(recipe,src,janus)
            with self.assertRaises(ValueError):library.publish(recipe,src,janus,expected_version='0'*64,user_approved=True)
            library.publish(recipe,src,janus,expected_version=row['version'],user_approved=True)
            with self.assertRaises(PermissionError):library.bind(row['version'],dest,'x.xml',janus)
            with self.assertRaises(ValueError):library.bind(row['version'],dest,'x.txt',janus,user_approved=True)
            (src/'old-input.py').write_text('changed')
            with self.assertRaises(ValueError):library.preview(recipe,src,janus)
            self.assertTrue(library.remove(row['version'],user_approved=True))
            self.assertEqual(library.list(),[])
