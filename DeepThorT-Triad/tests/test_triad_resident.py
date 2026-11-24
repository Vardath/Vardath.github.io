import unittest
from unittest.mock import patch,Mock
from triad_server import validate,admission,command,Pool
from deepthort_local.triad_profiles import PROFILES,role_for_council,MODEL_ID

class TriadTests(unittest.TestCase):
    def test_three_distinct_pinned_models(self):
        self.assertEqual(len({p[1] for p in PROFILES.values()}),3)
        self.assertEqual(len({p[3] for p in PROFILES.values()}),3)
        self.assertTrue(all(len(p[3])==64 for p in PROFILES.values()))
    def test_routing(self):
        self.assertEqual(role_for_council('SENTINEL_SPEC_0'),'sentinel')
        self.assertEqual(role_for_council('JANUS_WORKFLOW'),'janus')
        for role in PROFILES:
            body={'model':MODEL_ID,'triad_role':role,'messages':[{'role':'user','content':'test'}]}
            self.assertEqual(validate(body,'implementation')[0],role)
            argv=command(role,12345,'test')
            self.assertIn(PROFILES[role][2],argv[2])
            self.assertIn('--no-mmap',argv)
            self.assertEqual(argv[argv.index('--n-gpu-layers')+1],'0')
    def test_invalid_request(self):
        with self.assertRaises(ValueError):validate({'triad_role':'other'},'janus')
    def test_combined_admission(self):
        with self.assertRaises(RuntimeError):admission(9_000_000_000,30_000_000_000,40_000_000_000,8_910_000_000)
        admission(12_000_000_000,30_000_000_000,40_000_000_000,8_910_000_000)
    def test_all_models_required(self):
        p=Pool();p.ready=True
        p.children={r:(10,'secret',i,lambda:True) for i,r in enumerate(PROFILES)}
        self.assertTrue(p.healthy())
        self.assertEqual(len(p.status(False)['models']),3)
        p.children['sentinel']=(10,'secret',3,lambda:False)
        self.assertFalse(p.healthy())
        with self.assertRaises(RuntimeError):p.infer('janus',[],2)
