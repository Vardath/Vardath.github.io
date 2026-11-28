import io
import json
from pathlib import Path
import unittest
import zipfile
from deepthort_local import ide_integration as tool
from deepthort_local.language_server import analyze

class IDEIntegrationTests(unittest.TestCase):
    def test_version_and_fixed_profile(self):
        log='1.99.3\n'+'a'*40+'\nx64\n'
        self.assertEqual(tool.assess(log)['version'],'1.99.3')
        for bad in ('',log+'unexpected\n',log.replace('x64','other')):
            with self.assertRaises(ValueError):tool.assess(bad)
        cmd=tool.command('Code.exe',Path('stage'))
        self.assertIn('--disable-extensions',cmd)
        self.assertNotIn('--install-extension',cmd)

    def test_real_lsp_and_portable_workspace_bundle(self):
        source=b'def example():\n    return 42\n'
        analysis=analyze(source)
        editor=tool.assess('1.99.3\n'+'b'*40+'\nx64\n')
        raw,receipt=tool.bundle({'document':'src/main.py'},analysis,editor)
        self.assertEqual(receipt['symbols'][0]['name'],'example')
        self.assertFalse(receipt['project_code_executed'])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            workspace=json.loads(z.read('JANUS.code-workspace'))
            self.assertEqual(workspace['folders'],[{'path':'.'}])
            self.assertNotIn('tasks',workspace)
            self.assertEqual(workspace['settings']['task.allowAutomaticTasks'],'off')
            self.assertEqual(json.loads(z.read('janus-ide-receipt.json')),receipt)

if __name__=='__main__':unittest.main()
