import json
import tempfile
import unittest
from pathlib import Path
from download_model import read_smoke_result
from deepthort_local.triad_profiles import PROFILES,model_path,smoke_verified,RUNTIME_VERSION

class InstallQualityTests(unittest.TestCase):
    def test_verified_generation_not_confused_with_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'probe.log'
            result={'role':'janus','native_generation':'passed','exact_arithmetic_reply':'failed'}
            log.write_text('Synthetic reply: explanation\nTRIAD_SMOKE_RESULT '+json.dumps(result))
            self.assertEqual(read_smoke_result(log,'janus'),result)
            with self.assertRaises(RuntimeError):read_smoke_result(log,'sentinel')
            log.write_text('no valid receipt')
            with self.assertRaises(RuntimeError):read_smoke_result(log,'janus')
    def test_receipt_matches_pinned_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=model_path('janus',tmp);p.mkdir(parents=True)
            receipt={'role':'janus','native_generation':'passed','exact_arithmetic_reply':'failed',
                'repo':PROFILES['janus'][1],'revision':PROFILES['janus'][2],'runtime':RUNTIME_VERSION}
            dest=p/'native-smoke.json'
            dest.write_text(json.dumps(receipt))
            self.assertTrue(smoke_verified('janus',tmp))
            receipt['revision']='wrong'
            dest.write_text(json.dumps(receipt))
            self.assertFalse(smoke_verified('janus',tmp))
