import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch
from deepthort_local.triad_collaboration import collaboration,EXPECTED,decode
from deepthort_local.triad_profiles import PROFILES,MODEL_ID
from deepthort_local.janus_counsel import LocalCounsel

def health():
    return {"pid":100,"ready":True,"offline":True,"backend":"native-openvino-ir-cpu",
            "model":MODEL_ID,"serial_memory_mode":False,"memory_retries":0,
            "models":{r:{"name":p[0],"resident":True,"busy":False,"pid":101+i}
                      for i,(r,p) in enumerate(PROFILES.items())}}

class CollaborationTests(unittest.TestCase):
    def test_role_handoffs_and_independent_verification(self):
        calls=[]
        replies=[EXPECTED,{"verdict":"reject","fields":["owner","speed"]},EXPECTED,{"verdict":"accept","fields":[]}]
        def ask(role,prompt,tokens):
            calls.append((role,prompt,tokens))
            return json.dumps(replies[len(calls)-1])
        result=collaboration(health,ask,100,threading.Event())
        self.assertEqual(result["status"],"passed")
        self.assertEqual([c[0] for c in calls],["janus","sentinel","implementation","sentinel"])
        self.assertIn("Amendment",calls[-1][1])
        self.assertIn("Sentinel review",calls[2][1])
        self.assertEqual(len(result["evidence"]["artifact_sha256"]),64)
    def test_bad_repair_and_false_approval_do_not_pass(self):
        for replies in ([EXPECTED,{"verdict":"accept","fields":[]}],
                        [EXPECTED,{"verdict":"reject","fields":["owner","speed"]},dict(EXPECTED,owner="npc")],
                        [dict(EXPECTED,speed=True)]):
            answers=iter(replies)
            result=collaboration(health,lambda *args:json.dumps(next(answers,{})),100,threading.Event())
            self.assertEqual(result["status"],"failed")
    def test_review_evidence_distinguishes_semantics_and_format(self):
        replies=iter([json.dumps(EXPECTED),json.dumps({"verdict":"reject","fields":["owner"]})])
        result=collaboration(health,lambda *a:next(replies,"{}"),100,threading.Event())
        self.assertEqual(result["status"],"failed")
        review=result["evidence"]["collaboration_stages"]["reject_defect"]
        self.assertEqual(review["reported_fields"],["owner"])
        self.assertEqual(review["verdict"],"reject")
        self.assertTrue(review["valid_review_shape"])
        replies=iter([json.dumps(EXPECTED),"not JSON"])
        result=collaboration(health,lambda *a:next(replies,"{}"),100,threading.Event())
        review=result["evidence"]["collaboration_stages"]["reject_defect"]
        self.assertEqual(review["reason"],"invalid structured reply")
        self.assertNotIn("not JSON",json.dumps(result))
    def test_unknown_model_text_not_exported(self):
        replies=iter([json.dumps(EXPECTED),json.dumps({"verdict":"private text","fields":["owner","private text"]})])
        result=collaboration(health,lambda *a:next(replies,"{}"),100,threading.Event())
        review=result["evidence"]["collaboration_stages"]["reject_defect"]
        self.assertEqual(review["reported_fields"],["owner"])
        self.assertEqual(review["verdict"],"invalid")
        self.assertFalse(review["valid_review_shape"])
        self.assertNotIn("private text",json.dumps(result))
    def test_field_recovery_preserves_holistic_failure_and_checks_all_fields(self):
        from deepthort_local.triad_collaboration import BAD
        replies=[EXPECTED,{"verdict":"accept","fields":[]}]
        for k,v in EXPECTED.items():
            replies.append({"required":v,"verdict":"match" if BAD[k]==v else "mismatch"})
        replies.extend([EXPECTED,{"verdict":"accept","fields":[]}])
        answers=iter(replies);calls=[]
        def ask(role,prompt,tokens):
            calls.append((role,prompt))
            return json.dumps(next(answers))
        result=collaboration(health,ask,100,threading.Event())
        self.assertEqual(result["status"],"passed")
        stages=result["evidence"]["collaboration_stages"]
        self.assertEqual(stages["reject_defect"]["status"],"failed")
        self.assertEqual(stages["reject_defect"]["recovery_status"],"passed")
        self.assertEqual(set(stages["reject_defect"]["aggregate_fields"]),{"speed","owner"})
        self.assertEqual(len(calls),9)
        self.assertTrue(all(stages["reject_defect_"+k]["status"]=="passed" for k in EXPECTED))
    def test_field_recovery_never_trusts_false_judgment(self):
        replies=iter([EXPECTED,{"verdict":"accept","fields":[]},
                      {"required":"demo_pe","verdict":"match"},
                      {"required":480,"verdict":"match"}])
        result=collaboration(health,lambda *a:json.dumps(next(replies)),100,threading.Event())
        self.assertEqual(result["status"],"failed")
        self.assertEqual(result["evidence"]["collaboration_stages"]["reject_defect_speed"]["status"],"failed")
        self.assertNotIn("repair",result["evidence"]["collaboration_stages"])
    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):decode('{"speed":360,"speed":480}')
    def test_cancelled_and_serial_do_not_pass(self):
        stop=threading.Event();stop.set()
        self.assertEqual(collaboration(health,lambda *a:self.fail("called"),100,stop)["status"],"cancelled")
        self.assertEqual(collaboration(lambda:dict(health(),serial_memory_mode=True),lambda *a:self.fail("called"),100,threading.Event())["status"],"inconclusive")
    def test_background_counsel_auth_and_role(self):
        from io import BytesIO
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{"DEEPTHORT_TRIAD_TOKEN":"t"*64}):
            for role in ("janus","sentinel"):
                with patch("deepthort_local.janus_counsel.urllib.request.build_opener") as build:
                    requests=[]
                    def open_(req,timeout):
                        requests.append(req)
                        return BytesIO(json.dumps(health() if len(requests)==1 else {"triad_role":role,"choices":[{"message":{"content":"advice"}}]}).encode())
                    build.return_value.open.side_effect=open_
                    self.assertEqual(LocalCounsel(os.path.join(td,"lease.db")).request(society=role,goal="g",problem="p",evidence="e"),"advice")
                    self.assertEqual(requests[0].get_header("Authorization"),"Bearer "+"t"*64)
                    self.assertEqual(json.loads(requests[1].data)["triad_role"],role)
                    self.assertIn(":8766/",requests[1].full_url)
