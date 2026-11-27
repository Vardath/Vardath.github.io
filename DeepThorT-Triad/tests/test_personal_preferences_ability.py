import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.personal_preferences import load,save,context,DEFAULT,checked
class PreferenceTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.path=Path(tmp.name)/'prefs.json'
    def test_save_restart_context_and_reset(self):
        old=load(self.path);self.assertEqual(old,DEFAULT)
        new=dict(old,spelling='australian',response_length='detailed')
        save(self.path,new,expected=old)
        self.assertEqual(load(self.path),new)
        self.assertIn('spelling: australian',context(self.path,budget=500))
        self.assertIn('current explicit request overrides',context(self.path,budget=500))
        save(self.path,DEFAULT,expected=new);self.assertEqual(context(self.path,budget=500),'')
    def test_stale_editor(self):
        save(self.path,dict(DEFAULT,units='metric'),expected=DEFAULT)
        with self.assertRaises(ValueError):save(self.path,dict(DEFAULT,units='imperial'),expected=DEFAULT)
        self.assertEqual(load(self.path)['units'],'metric')
    def test_no_arbitrary_instructions(self):
        for v in (dict(DEFAULT,units='run commands'),dict(DEFAULT,permissions='all'),{'units':'metric'}):
            with self.assertRaises(ValueError):checked(v)
        self.assertFalse(self.path.exists())
    def test_bad_file_and_context_budget(self):
        self.path.write_text('invalid',encoding='utf-8')
        self.assertEqual(context(self.path,budget=500),'')
        with self.assertRaises(ValueError):load(self.path)
        self.path.unlink();save(self.path,dict(DEFAULT,units='metric'),expected=DEFAULT)
        self.assertEqual(context(self.path,budget=10),'')
