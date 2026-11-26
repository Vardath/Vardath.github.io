import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.triad_profiles import ALL_PROFILES, PROFILES, MEMORY_PROFILE, MODEL_ID, role_for_council
from deepthort_local.triad_job import memory_specialist_fits
from deepthort_local.multimedia_profile import install_plan
from deepthort_local.live_memory_probe import exercise as live_exercise
from deepthort_local.memory_core_probe import resident_memory, exercise
from triad_server import Pool, validate, command


def health():
    return {'pid':123,'ready':True,'offline':True,'backend':'native-openvino-ir-cpu',
            'serial_memory_mode':False,'memory_retries':0,
            'models':{role:{'pid':124+i,'name':p[0],'resident':True,'busy':False}
                      for i,(role,p) in enumerate(PROFILES.items())},
            'memory_model':{'pid':130,'name':MEMORY_PROFILE[0],'revision':MEMORY_PROFILE[2],
                            'resident':True,'busy':False}}


class Fixture:
    calls=[]
    def __init__(self,path):pass
    def chat_as(self,role,session,prompt,max_tokens):
        self.calls.append(role)
        rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
        if 'SENTINEL MEMORY CHALLENGE.' in prompt:
            if role!='sentinel':raise AssertionError('Independent Sentinel challenge required')
            return json.dumps({'checks':[{'id':x['id'],'basis':'OBSERVATION',
                'direct':x['observation'].startswith('Regression:'),'compatible':True} for x in rows]})
        return json.dumps({'keep':[x['id'] for x in rows if x['observation'].startswith('Regression:')],
                           'reason':'Fixture selection'})


class WrongMemory(Fixture):
    def chat_as(self,role,session,prompt,max_tokens):
        if role=='memory':
            self.calls.append(role)
            return '{"keep":[],"reason":"wrongly omitted"}'
        return super().chat_as(role,session,prompt,max_tokens)


class MemoryCoreTests(unittest.TestCase):
    def test_install_only_memory_when_everything_else_present(self):
        self.assertEqual(install_plan(role_ok=lambda role:True,runtime_ok=True,media_ok=True,
                         creative_ok=True,memory_ok=False)[0][:2],('download_model.py',('--role','memory')))
        self.assertEqual(install_plan(role_ok=lambda role:True,runtime_ok=True,media_ok=True,
                         creative_ok=True,memory_ok=True),[])

    def test_native_role_distinct_and_optional(self):
        self.assertEqual(set(ALL_PROFILES),set(PROFILES)|{'memory'})
        self.assertEqual(role_for_council('MEMORY_SELECT'),'memory')
        self.assertEqual(validate({'model':MODEL_ID,'triad_role':'memory',
            'messages':[{'role':'user','content':'recall'}]},'janus')[0],'memory')
        self.assertEqual(command('memory',12345,'test')[3],'memory')
        p=Pool();p.ready=True
        p.children={r:(10,'key',124+i,lambda:True) for i,r in enumerate(PROFILES)}
        self.assertTrue(p.healthy())
        self.assertFalse(p.status(False)['memory_model']['resident'])
        p.memory_child=(10,'key',130,lambda:True)
        self.assertEqual(resident_memory(p.status(False),p.status(False)['pid'])['pid'],130)
        p.memory_child=(10,'key',130,lambda:False)
        self.assertTrue(p.healthy())
        self.assertFalse(p.status(False)['memory_model']['resident'])

    def test_memory_admission_preserves_foreground_reserve(self):
        g=1024**3
        self.assertTrue(memory_specialist_fits(20*g,20*g,40*g,10*g))
        self.assertFalse(memory_specialist_fits(20*g,20*g,40*g,18*g))
        self.assertFalse(memory_specialist_fits(20*g,6*g,40*g,10*g))

    def test_identity_cannot_reuse_language_pid(self):
        h=health()
        h['memory_model']['pid']=h['models']['janus']['pid']
        with self.assertRaises(ValueError):resident_memory(h,123)

    def test_governed_memory_and_fifth_oracles(self):
        Fixture.calls=[]
        result=live_exercise(health,123,threading.Event(),client_factory=Fixture,use_memory_core=True)
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(Fixture.calls.count('memory'),2)
        self.assertIn('sentinel',Fixture.calls)
        self.assertEqual(exercise(health,123,result)['status'],'passed')

    def test_fallback_cannot_fake_fifth_accuracy(self):
        result=live_exercise(health,123,threading.Event(),client_factory=WrongMemory,use_memory_core=True)
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(exercise(health,123,result)['status'],'failed')


if __name__=='__main__':
    unittest.main()
