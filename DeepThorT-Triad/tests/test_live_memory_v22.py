import unittest
import threading
import json
from deepthort_local.live_memory_probe import exercise
from deepthort_local.triad_profiles import PROFILES
class Fixture:
    def __init__(self,path):pass
    def chat_as(self,role,session,prompt,max_tokens):
        if role!='sentinel':raise AssertionError('Wrong model role')
        rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
        return json.dumps({'keep':[x['id'] for x in rows if x['observation'].startswith('Regression:')],'reason':'Fixture selector'})
class Bad(Fixture):
    def chat_as(self,role,session,prompt,max_tokens):
        return '{"keep":[],"reason":"Incorrectly omitted relevant record"}'
def health():
    # Match the production resident-role validator.
    return {'pid':123,'ready':True,'serial_memory_mode':False,'memory_retries':0,
            'models':{role:{'pid':124+i,'name':p[0],'ready':True,'busy':False} for i,(role,p) in enumerate(PROFILES.items())}}
class LiveMemoryHarnessTests(unittest.TestCase):
    def test_positive_and_negative_scoring(self):
        from unittest.mock import patch
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            good=exercise(health,123,threading.Event(),client_factory=Fixture)
            self.assertEqual(good['status'],'passed',good)
            bad=exercise(health,123,threading.Event(),client_factory=Bad)
            self.assertEqual(bad['status'],'failed',bad)
            self.assertEqual(bad['evidence']['memory_cases']['ownership']['status'],'failed')
