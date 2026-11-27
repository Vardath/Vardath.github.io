import http.client,json,queue,threading,unittest
from deepthort_local import openai_gateway as g
from deepthort_local.triad_profiles import MODEL_ID
KEY='fixture_only_123456789012345678901234'
BODY={'model':MODEL_ID,'messages':[{'role':'user','content':'fixture'}],'max_tokens':32}
def send(port,method,path,body=None,key=KEY):
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=4)
    try:
        conn.request(method,path,None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        r=conn.getresponse();return r.status,json.loads(r.read())
    finally:conn.close()
class GatewayTests(unittest.TestCase):
    def test_actual_local_gateway(self):
        ports=queue.Queue();results=queue.Queue();cancel=threading.Event();calls=[]
        def infer(p):calls.append(p);return 'fixture result','stop'
        def run():
            try:results.put(g.serve(KEY,infer,ports.put,cancel.is_set,approved=True,seconds=10))
            except Exception as e:results.put(e)
        t=threading.Thread(target=run,daemon=True);t.start()
        self.addCleanup(lambda:(cancel.set(),t.join(4)))
        p=ports.get(timeout=4)
        self.assertEqual(send(p,'GET','/v1/models',key='incorrect')[0],401)
        self.assertEqual(send(p,'GET','/v1/models')[1]['data'][0]['id'],MODEL_ID)
        self.assertEqual(send(p,'POST','/v1/chat/completions',dict(BODY,triad_role='sentinel'))[0],400)
        code,result=send(p,'POST','/v1/chat/completions',BODY)
        self.assertEqual(code,200);self.assertEqual(result['choices'][0]['message']['content'],'fixture result')
        self.assertNotIn('usage',result);self.assertEqual(calls[0]['triad_role'],'implementation')
        self.assertEqual(send(p,'POST','/v1/chat/completions',BODY)[0],200)
        self.assertEqual(results.get(timeout=4)['completion_attempts'],2);t.join(4);self.assertFalse(t.is_alive())
    def test_unsupported_options(self):
        for d in (dict(BODY,stream=True),dict(BODY,tools=[]),dict(BODY,max_tokens=769),dict(BODY,model='other'),dict(BODY,messages=[{'role':'assistant','content':'x'}])):
            with self.assertRaises(ValueError):g.checked(d)
    def test_no_approval(self):
        with self.assertRaises(PermissionError):g.serve(KEY,lambda p:None,lambda p:None)
