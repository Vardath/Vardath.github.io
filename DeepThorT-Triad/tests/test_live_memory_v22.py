import unittest
import threading
import json
import io
from urllib.error import HTTPError
from deepthort_local.memory_governor import MEMORY_SELECTION_TOKENS
from triad_openvino_worker import thinking_enabled
from deepthort_local.live_memory_probe import exercise
from deepthort_local.triad_profiles import PROFILES
class Fixture:
    def __init__(self,path):pass
    def chat_as(self,role,session,prompt,max_tokens):
        if role!='sentinel':raise AssertionError('Wrong model role')
        if max_tokens!=MEMORY_SELECTION_TOKENS or thinking_enabled(role,max_tokens):raise AssertionError('Memory selection must use bounded direct mode')
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

    def test_classified_broker_failure_is_not_a_relevance_failure(self):
        from unittest.mock import patch
        class Blocked(Fixture):
            def chat_as(self,role,session,prompt,max_tokens):
                raise HTTPError('http://127.0.0.1',500,'failure',{},
                    io.BytesIO(b'{"code":"reasoning_budget","detail":"private text"}'))
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            result=exercise(health,123,threading.Event(),client_factory=Blocked)
        self.assertEqual(result['status'],'blocked',result)
        case=result['evidence']['memory_cases']['ownership']
        self.assertEqual(case['error_code'],'reasoning_budget')
        self.assertNotIn('private text',json.dumps(result))
        self.assertNotIn('selected_ids',case)
