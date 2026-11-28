import hashlib
from pathlib import Path
import tempfile
import unittest
from deepthort_local import restricted_environment as tool
from deepthort_local.triad_job import isolated_env

class RestrictedEnvironmentTests(unittest.TestCase):
    def test_allowlist_and_exact_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp).resolve()
            env=isolated_env(stage,{'SystemRoot':'C:/Windows','API_TOKEN':'dummy','PYTHONPATH':'outside'})
            self.assertNotIn('API_TOKEN',env);self.assertNotIn('PYTHONPATH',env)
            self.assertEqual(env['TEMP'],str(stage))
            raw=b'raise RuntimeError("not executed")'
            r={'sha256':hashlib.sha256(raw).hexdigest(),'environment_keys':sorted(env),
               'isolated':True,'no_site':True,'cwd':str(stage),'syntax_valid':True,'error_line':None}
            self.assertFalse(tool.assess(raw,r,stage,env)['project_code_executed'])
            for bad in (dict(r,environment_keys=sorted(env)+['API_TOKEN']),dict(r,no_site=False),dict(r,sha256='0'*64)):
                with self.assertRaises(ValueError):tool.assess(raw,bad,stage,env)
    def test_scope(self):
        with self.assertRaises(ValueError):tool.checked({'document':'source.py','command':'other'})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):isolated_env(tmp,{})

if __name__=='__main__':unittest.main()
