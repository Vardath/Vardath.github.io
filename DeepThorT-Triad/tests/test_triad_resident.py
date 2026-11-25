import unittest
from pathlib import Path
from triad_server import validate,admission,command,Pool
from deepthort_local.triad_profiles import PROFILES,role_for_council,MODEL_ID,MODEL_SET_DIR,model_path
from deepthort_local.triad_acceptance import resident_roles

class TriadTests(unittest.TestCase):
    def test_three_pinned_ir_models(self):
        self.assertEqual(len({p[1] for p in PROFILES.values()}),3)
        self.assertTrue(all(len(p[2])==40 for p in PROFILES.values()))
        self.assertEqual({p[1] for p in PROFILES.values()},{
            'HarmenWessels/granite-4.1-3b-int4-cw-code-ov',
            'HarmenWessels/SmolLM3-3B-int4-symg128-ov',
            'OpenVINO/Qwen3-4B-int4-ov'})
        self.assertEqual(MODEL_SET_DIR,'triad-openvino-compact-v1')
        self.assertTrue(all(model_path(r).parent.name==MODEL_SET_DIR for r in PROFILES))
        self.assertTrue(all('triad-openvino' not in model_path(r).parts for r in PROFILES))
        self.assertEqual(len({model_path(r) for r in PROFILES}),3)
        self.assertEqual(model_path('janus').name,'janus-smollm3')
        self.assertEqual(model_path('implementation').name,'implementation')
        self.assertEqual(model_path('sentinel').name,'sentinel-qwen3-4b')
        self.assertEqual(PROFILES['sentinel'][2],'b467368d16b75df14055562fe927ae8e1f15f7ef')
    def test_routing(self):
        self.assertEqual(role_for_council('SENTINEL_SPEC_0'),'sentinel')
        self.assertEqual(role_for_council('JANUS_WORKFLOW'),'janus')
        for role in PROFILES:
            body={'model':MODEL_ID,'triad_role':role,'messages':[{'role':'user','content':'test'}]}
            self.assertEqual(validate(body,'implementation')[0],role)
            argv=command(role,12345,'test')
            self.assertEqual(argv[1],'-I')
            self.assertTrue(argv[2].endswith('triad_openvino_worker.py'))
            self.assertEqual(argv[3],role)
            self.assertNotIn('llama-server',str(argv))
    def test_invalid_request(self):
        with self.assertRaises(ValueError):validate({'triad_role':'other'},'janus')
    def test_combined_admission(self):
        with self.assertRaises(RuntimeError):admission(8_000_000_000,30_000_000_000,40_000_000_000,7_580_000_000)
        admission(12_000_000_000,30_000_000_000,40_000_000_000,7_580_000_000)
    def test_all_models_required(self):
        p=Pool();p.ready=True
        p.children={r:(10,'secret',i+10,lambda:True) for i,r in enumerate(PROFILES)}
        self.assertTrue(p.healthy())
        h=p.status(False)
        self.assertEqual(h['backend'],'native-openvino-ir-cpu')
        self.assertEqual(set(resident_roles(h,h['pid'])),set(PROFILES))
        h['models']['sentinel']['pid']=h['models']['janus']['pid']
        with self.assertRaises(ValueError):resident_roles(h,h['pid'])
        p.children['sentinel']=(10,'secret',3,lambda:False)
        self.assertFalse(p.healthy())
        with self.assertRaises(RuntimeError):p.infer('janus',[],2)
    def test_current_manifest(self):
        from deepthort_local.latest_acceptance import load_test
        m=load_test(Path(__file__).resolve().parents[1]/'LATEST_TEST.json')
        self.assertEqual(m['checks'],["shared_cap","triad_residency","janus_core","task_memory","memory_governance","portable_skills","portable_procedures","local_mcp","mcp_calls","task_mcp","mcp_stdio","live_memory"])
