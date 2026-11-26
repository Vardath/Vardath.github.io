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
        if 'SENTINEL MEMORY CHALLENGE.' in prompt:
            return json.dumps({'checks':[{'id':x['id'],
                'basis':'PROPOSAL' if 'suggestion:' in x['observation'] or 'proposal:' in x['observation'] else 'OBSERVATION',
                'direct':x['observation'].startswith('Regression:'),
                'compatible':True} for x in rows]})
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

    def test_challenge_rejects_overselection_without_relaxing_oracle(self):
        from unittest.mock import patch
        class OverselectThenReview(Fixture):
            def chat_as(self,role,session,prompt,max_tokens):
                if 'SENTINEL MEMORY CHALLENGE.' in prompt:
                    return super().chat_as(role,session,prompt,max_tokens)
                rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
                return json.dumps({'keep':[x['id'] for x in rows],'reason':'Overbroad initial selection'})
        class PersistentOverselection(OverselectThenReview):
            def chat_as(self,role,session,prompt,max_tokens):
                rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
                if 'SENTINEL MEMORY CHALLENGE.' in prompt:
                    return json.dumps({'checks':[dict(id=x['id'],basis='OBSERVATION',direct=True,compatible=True) for x in rows]})
                return json.dumps({'keep':[x['id'] for x in rows],'reason':'Overbroad selection'})
        class InvalidChallenge(Fixture):
            def chat_as(self,role,session,prompt,max_tokens):
                if 'SENTINEL MEMORY CHALLENGE.' in prompt:
                    return '{"keep":["N99999"],"reason":"Invented record"}'
                return super().chat_as(role,session,prompt,max_tokens)
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            good=exercise(health,123,threading.Event(),client_factory=OverselectThenReview)
            self.assertEqual(good['status'],'passed',good)
            for client in (PersistentOverselection,InvalidChallenge):
                bad=exercise(health,123,threading.Event(),client_factory=client)
                self.assertEqual(bad['status'],'failed',bad)
                self.assertEqual(bad['evidence']['memory_cases']['ownership']['status'],'failed')

    def test_proposal_veto_even_if_classified_direct_and_compatible(self):
        from unittest.mock import patch
        class ProposalMistakenForUseful(Fixture):
            def chat_as(self,role,session,prompt,max_tokens):
                rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
                if 'SENTINEL MEMORY CHALLENGE.' in prompt:
                    return json.dumps({'checks':[dict(id=x['id'],
                        basis='PROPOSAL' if 'proposal:' in x['observation'] or 'suggestion:' in x['observation'] else 'OBSERVATION',
                        direct=x['observation'].startswith('Regression:'),
                        compatible=True) for x in rows]})
                return json.dumps({'keep':[x['id'] for x in rows],'reason':'Overbroad selection'})
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            result=exercise(health,123,threading.Event(),client_factory=ProposalMistakenForUseful)
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(result['evidence']['memory_cases']['prices']['selected_ids'],[])

    def test_advisory_only_never_calls_model(self):
        from unittest.mock import patch
        class RejectAdviceExposure(Fixture):
            def chat_as(self,role,session,prompt,max_tokens):
                rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
                if any(x['kind'] in ('historical_janus','historical_implementation') for x in rows):
                    raise AssertionError('Advisory notes leaked into evidence review')
                return super().chat_as(role,session,prompt,max_tokens)
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            result=exercise(health,123,threading.Event(),client_factory=RejectAdviceExposure)
        self.assertEqual(result['status'],'passed',result)
        case=result['evidence']['memory_cases']['advice_only']
        self.assertEqual(case['selection_status'],'provenance_withheld')
        self.assertEqual(case['eligible_ids'],[])
        self.assertEqual(case['selected_ids'],[])

    def test_busy_models_drain_before_live_test(self):
        from unittest.mock import patch
        first=health();first['models']['sentinel']['busy']=True
        reports=iter([first,health(),health()])
        cancel=threading.Event()
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            result=exercise(lambda:next(reports),123,cancel,client_factory=Fixture,idle_wait_seconds=2)
        self.assertEqual(result['status'],'passed',result)

    def test_busy_timeout_and_worker_change_do_not_pass(self):
        from unittest.mock import patch
        busy=health();busy['models']['sentinel']['busy']=True
        changed=health();changed['models']['sentinel']['pid']=999
        with patch('deepthort_local.live_memory_probe.resident_roles',side_effect=lambda h,p:h['models']):
            result=exercise(lambda:busy,123,threading.Event(),client_factory=Fixture,idle_wait_seconds=0)
            self.assertEqual(result['status'],'inconclusive',result)
            self.assertEqual(result['evidence']['memory_cases'],{})
            reports=iter([busy,changed])
            result=exercise(lambda:next(reports),123,threading.Event(),client_factory=Fixture,idle_wait_seconds=2)
            self.assertEqual(result['status'],'inconclusive',result)
            cancel=threading.Event();cancel.set()
            result=exercise(lambda:busy,123,cancel,client_factory=Fixture,idle_wait_seconds=2)
            self.assertEqual(result['status'],'cancelled',result)
