import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import gpu_text_inference as m

SPEC={'role':'memory','device':'GPU.0','prompt':'Answer 2 + 2.','max_tokens':16}
def result(s):
    return {'device':s['device'],'device_name':'fixture device','total_device_memory_bytes':8*m.GIB,
            'text':'4','load_seconds':1.,'generation_seconds':.2,'runtime':m.RUNTIME_VERSION,
            'role':s['role'],'max_tokens':s['max_tokens']}

class GPUTextTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        (self.root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
        p=patch.object(m,'inventory',return_value={'revision':'fixture'});self.inv=p.start();self.addCleanup(p.stop)
    def plan(self):return m.review(self.root,'spec.json','out.json')[0]
    def test_exact_gpu_result(self):
        r=m.execute(self.root,self.plan(),backend=lambda s,_:result(s))
        self.assertEqual(r['backend'],'injected_fixture')
        self.assertEqual(r['text'],'4')
        self.assertFalse(r['gpu_memory_limit_enforced'])
        self.assertFalse(r['speedup_verified'])
        self.assertFalse(r['production_backend_changed'])
    def test_fallback_and_wrong_device_refused(self):
        for name in ('CPU','AUTO','GPU','MULTI:GPU,CPU'):
            with self.assertRaises(ValueError):m.checked(dict(SPEC,device=name))
        with self.assertRaises(ValueError):m.execute(self.root,self.plan(),backend=lambda s,_:dict(result(s),device='CPU'))
        self.assertFalse((self.root/'out.json').exists())
    def test_stale_model_and_empty_result_refused(self):
        plan=self.plan()
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda s,_:dict(result(s),text=''))
        self.inv.return_value={}
        with self.assertRaises(ValueError):m.execute(self.root,plan,backend=lambda *_:self.fail('stale model'))
        self.assertFalse((self.root/'out.json').exists())
if __name__=='__main__':unittest.main()
