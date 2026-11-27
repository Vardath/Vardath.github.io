import unittest
from deepthort_local import unreal_integration as tool

class UnrealIntegrationTests(unittest.TestCase):
    def test_fixed_profile_and_descriptor(self):
        s={'project_name':'JanusTest'}
        self.assertEqual(tool.descriptor(s)['Plugins'],[{'Name':'PythonScriptPlugin','Enabled':True}])
        cmd=tool.command('UnrealEditor-Cmd.exe','JanusTest.uproject','probe.py')
        self.assertIn('-run=pythonscript',cmd);self.assertIn('-script=probe.py',cmd)
        self.assertIn('-nullrhi',cmd)
        for name in ('../escape','a b','a;command',''):
            with self.assertRaises(ValueError):tool.descriptor({'project_name':name})

    def test_native_evidence_requires_exact_identity(self):
        s={'project_name':'JanusTest'}
        r={'engine_version':'5.5.4-123+++UE5+Release-5.5','project_file':'C:/Temp/JanusTest.uproject'}
        log='LogPython: '+tool.MARKER+r['engine_version']
        self.assertTrue(tool.assess(s,r,log)['native_editor_python_verified'])
        for bad in ('',log+'\n'+log,log+'\nLogPython: Error: failed'):
            with self.assertRaises(ValueError):tool.assess(s,r,bad)
        with self.assertRaises(ValueError):tool.assess(s,dict(r,project_file='wrong.uproject'),log)

if __name__=='__main__':unittest.main()
