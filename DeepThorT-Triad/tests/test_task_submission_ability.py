import http.client,json,queue,threading,unittest,uuid
from deepthort_local import task_submission as s,openai_gateway as g
KEY='fixture_only_123456789012345678901234'
class SubmissionTests(unittest.TestCase):
    def test_real_authenticated_inbox_and_owner_review(self):
        inbox=s.Inbox('project','chat',approved=True);ports=queue.Queue();cancel=threading.Event();calls=[]
        t=threading.Thread(target=lambda:g.serve(KEY,lambda p:None,ports.put,cancel.is_set,approved=True,seconds=10,task_receiver=inbox.receive),daemon=True)
        t.start()
        def request(value,key=KEY):
            c=http.client.HTTPConnection('127.0.0.1',port,timeout=4)
            try:
                c.request('POST','/janus/v1/tasks',json.dumps(value).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                r=c.getresponse();return r.status,json.loads(r.read())
            finally:c.close()
        try:
            port=ports.get(timeout=4);v={'submission_id':str(uuid.uuid4()),'prompt':'Design a local fixture'}
            self.assertEqual(request(v,'wrong')[0],401);self.assertEqual(inbox.pending(),[])
            code,r=request(v);self.assertEqual(code,202);self.assertFalse(r['conversation_created'])
            self.assertEqual(request(v)[0],400)
            self.assertEqual(inbox.pending(),[(v['submission_id'],v['prompt'])])
            def submit(*args):calls.append(args);return 42
            with self.assertRaises(PermissionError):inbox.review(v['submission_id'],v['prompt'],'project','chat',submit)
            with self.assertRaises(ValueError):inbox.review(v['submission_id'],v['prompt'],'other','chat',submit,approved=True)
            self.assertEqual(calls,[])
            self.assertEqual(inbox.review(v['submission_id'],v['prompt'],'project','chat',submit,approved=True),42)
            self.assertEqual(calls,[('chat','project','chat',v['prompt'])])
            with self.assertRaises(ValueError):inbox.review(v['submission_id'],v['prompt'],'project','chat',submit,approved=True)
        finally:cancel.set();t.join(4)
    def test_limit_and_discard(self):
        box=s.Inbox('p','c',approved=True)
        for _ in range(2):box.receive({'submission_id':str(uuid.uuid4()),'prompt':'fixture'})
        with self.assertRaises(ValueError):box.receive({'submission_id':str(uuid.uuid4()),'prompt':'fixture'})
        box.discard();self.assertEqual(box.pending(),[])
        with self.assertRaises(ValueError):box.receive({'submission_id':str(uuid.uuid4()),'prompt':'fixture'})
    def test_invalid_submission(self):
        for value in ({'submission_id':'bad','prompt':'a'},{'submission_id':str(uuid.uuid4()),'prompt':'a','mode':'build'},{'submission_id':str(uuid.uuid4()),'prompt':'\x00'}):
            with self.assertRaises(ValueError):s.checked(value)
