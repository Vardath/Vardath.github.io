import tempfile
import unittest
import threading
from pathlib import Path
from unittest.mock import patch
from deepthort_local.reasoning_council import ReasoningCouncil
from deepthort_local.specification_guard import inspect_proposal
from deepthort_local.production_review_probe import exercise,BAD
from deepthort_local.triad_profiles import PROFILES,MODEL_ID

def health():
    return {'pid':100,'ready':True,'offline':True,'backend':'native-openvino-ir-cpu',
        'model':MODEL_ID,'serial_memory_mode':False,'memory_retries':0,
        'models':{r:{'name':p[0],'resident':True,'busy':False,'pid':101+i}
                  for i,(r,p) in enumerate(PROFILES.items())}}

class Model:
    def __init__(self,answers):self.answers=iter(answers);self.calls=[]
    def chat_as(self,role,session,prompt,max_tokens):
        self.calls.append((role,session,prompt,max_tokens))
        return next(self.answers)

class ProductionTests(unittest.TestCase):
    def test_production_gate_uses_thinking_and_new_model_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            council=ReasoningCouncil(Path(folder)/'test.sqlite')
            args=dict(original='Make a space game with sectors.',project=folder,
                session='source',focus='map.py',proposal='sectors = []',kind='code')
            client=Model(['ACCEPT\nSector structure matches.','REJECT\nMissing behavior.'])
            result=inspect_proposal(council,client,**args)
            self.assertTrue(result['accepted'])
            self.assertEqual(client.calls[0][0],'sentinel')
            self.assertEqual(client.calls[0][3],768)
            self.assertFalse(result['verified'])
            self.assertTrue(inspect_proposal(council,client,**args)['accepted'])
            self.assertEqual(len(client.calls),1)
            with patch.dict(PROFILES,{'sentinel':('other','repo','f'*40,1)}):
                self.assertFalse(inspect_proposal(council,client,**args)['accepted'])
            self.assertNotEqual(client.calls[0][1],client.calls[1][1])
    def test_bare_source_acceptance_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            result=inspect_proposal(ReasoningCouncil(Path(folder)/'test.sqlite'),Model(['ACCEPT']),
                original='Make a space game',project=folder,session='x',focus='source',proposal='source',kind='code')
            self.assertFalse(result['accepted'])
    def test_production_fixture_actual_helpers_and_role_order(self):
        model=Model(['REJECT\nWrong owner and speed.','<ship id="demo_pe" owner="player" speed="360"/>','ACCEPT\nAll attributes correct.'])
        result=exercise(health,100,threading.Event(),client_factory=lambda _:model)
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual([x[0] for x in model.calls],['sentinel','implementation','sentinel'])
        self.assertIn('Wrong owner and speed',model.calls[1][2])
        self.assertEqual(len(result['evidence']['artifact_sha256']),64)
    def test_false_acceptance_cannot_reach_implementation(self):
        model=Model(['ACCEPT\nLooks fine.'])
        result=exercise(health,100,threading.Event(),client_factory=lambda _:model)
        self.assertEqual(result['status'],'failed')
        self.assertEqual(len(model.calls),1)
    def test_client_rejects_wrong_role_before_persisting(self):
        from deepthort_local.client import LocalModelClient
        from io import BytesIO
        import json
        with tempfile.TemporaryDirectory() as folder:
            client=LocalModelClient(Path(folder)/'sessions.sqlite')
            with patch('deepthort_local.client.urllib.request.build_opener') as opener:
                opener.return_value.open.return_value=BytesIO(json.dumps({'model':MODEL_ID,'triad_role':'implementation','choices':[{'message':{'content':'ACCEPT'}}]}).encode())
                with self.assertRaisesRegex(ValueError,'unexpected model or role'):
                    client.chat_as('sentinel','role-check','review',max_tokens=768)
            self.assertEqual(client.history('role-check'),[])

    def test_ambiguous_seeded_review_is_not_successful_detection(self):
        model=Model(['Possibly acceptable'])
        result=exercise(health,100,threading.Event(),client_factory=lambda _:model)
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['evidence']['production_stages']['seeded_defect_review']['status'],'failed')
        self.assertEqual(len(model.calls),1)

    def test_structured_review_and_bounded_diagnostics(self):
        model=Model(['{"verdict":"REJECT","reason":"Wrong owner and speed."}',
                     '<ship id="demo_pe" owner="player" speed="360"/>',
                     '{"verdict":"ACCEPT","reason":"All attributes correct."}'])
        result=exercise(health,100,threading.Event(),client_factory=lambda _:model)
        self.assertEqual(result['status'],'passed',result)
        stages=result['evidence']['production_stages']
        self.assertEqual(stages['seeded_defect_review']['response_format'],'json')
        self.assertEqual(stages['seeded_defect_review']['mentioned_fields'],['owner','speed'])
        self.assertNotIn('Wrong owner and speed',str(result))
    def test_one_defect_only_does_not_pass(self):
        result=exercise(health,100,threading.Event(),client_factory=lambda _:Model(['REJECT\nWrong owner.']))
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['evidence']['production_stages']['seeded_defect_review']['mentioned_fields'],['owner'])
    def test_parser_rejects_ambiguous_duplicate_or_reasonless_output(self):
        from deepthort_local.specification_guard import parse_source_verdict
        for raw in ['ACCEPT','{"verdict":"ACCEPT","reason":""}',
                    '{"verdict":"REJECT","verdict":"ACCEPT","reason":"ok"}',
                    'Maybe acceptable']:
            self.assertEqual(parse_source_verdict(raw)[0],'INVALID')
