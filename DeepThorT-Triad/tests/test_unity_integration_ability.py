import unittest
from deepthort_local import unity_integration as tool

class UnityIntegrationTests(unittest.TestCase):
    def test_fixed_batch_profile(self):
        s={'editor_version':'6000.0.42f1'}
        files=tool.stage_files(s)
        self.assertEqual(files['ProjectSettings/ProjectVersion.txt'],'m_EditorVersion: 6000.0.42f1\n')
        self.assertIn('EditorSceneManager.OpenScene',files['Assets/Editor/JanusSceneProbe.cs'])
        cmd=tool.command('Unity.exe','temporary')
        self.assertEqual(cmd[1:],['-batchmode','-nographics','-quit','-projectPath','temporary','-executeMethod','JanusSceneProbe.Run','-logFile','-'])
        for v in ('6000.0.42f1 -executeMethod Other','2022.3.1b1','',None):
            with self.assertRaises(ValueError):tool.stage_files({'editor_version':v})

    def test_evidence_rejects_missing_or_wrong_native_result(self):
        s={'editor_version':'2022.3.62f1'}
        r={'version':s['editor_version'],'project':'temporary','scene':'Assets/JanusProbe.unity','rootCount':1}
        log=tool.MARKER+r['version']
        self.assertTrue(tool.assess(s,r,log)['native_scene_reopen_verified'])
        for bad in ('',log+'\n'+log,log+'\nerror CS1000: failed'):
            with self.assertRaises(ValueError):tool.assess(s,r,bad)
        for bad in (dict(r,rootCount=True),dict(r,version='2022.3.61f1'),dict(r,scene='Assets/Other.unity')):
            with self.assertRaises(ValueError):tool.assess(s,bad,log)

if __name__=='__main__':unittest.main()
