import json,tempfile,unittest
from pathlib import Path
from email.message import Message
from deepthort_local import cross_device_notification as n
from deepthort_local.job_queue import JobStore
TOPIC='fixture_private_topic'
KEY='tk_fixture_token_123456789'
def resolver(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
class Response:
    status=200
    def __init__(self,row):
        self.raw=json.dumps(row).encode();self.headers=Message();self.headers['Content-Type']='application/json'
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,size):p,self.raw=self.raw[:size],self.raw[size:];return p
class NotifyTests(unittest.TestCase):
    def test_fixed_provider_payload(self):
        calls=[]
        class Conn:
            def __init__(self,host,ip):self.host=host
            def request(self,method,path,body,headers):calls.append((self.host,method,path,json.loads(body),headers))
            def getresponse(self):return Response({'event':'message','topic':TOPIC,'message':'JANUS job status: complete.','id':'fixtureid'})
            def close(self):pass
        result=n.publish(TOPIC,KEY,'job','complete',approved=True,resolver=resolver,connection=Conn)
        self.assertEqual(calls[0][:4],('ntfy.sh','POST','/',{'topic':TOPIC,'title':'JANUS status','message':'JANUS job status: complete.'}))
        self.assertEqual(calls[0][4]['Authorization'],'Bearer '+KEY)
        self.assertFalse(result['device_delivery_verified']);self.assertNotIn(KEY,str(result))
        with self.assertRaises(PermissionError):n.publish(TOPIC,KEY,'job','complete')
    def test_exact_scope_and_finite_watch(self):
        with tempfile.TemporaryDirectory() as td:
            store=JobStore(Path(td)/'jobs.sqlite3');ident=store.submit('project','chat','chat','private fixture')
            self.assertEqual(n.selected_state(store.path,'job',ident,'project','chat'),'queued')
            with self.assertRaises(ValueError):n.selected_state(store.path,'job',ident,'other','chat')
            tick=[0];calls=[]
            def wait(t):
                tick[0]+=t
                store.change(ident,'responded','fixture',allowed=('queued',))
            def sender(*args,**kw):calls.append(args);return {'status':'provider_accepted'}
            r=n.watch(lambda:n.selected_state(store.path,'job',ident,'project','chat'),'job',TOPIC,KEY,lambda:False,approved=True,seconds=9,clock=lambda:tick[0],wait=wait,sender=sender)
            self.assertEqual(r['status'],'provider_accepted');self.assertEqual(len(calls),1);self.assertEqual(calls[0][3],'responded')
    def test_expiry_and_cancel(self):
        t=[0]
        def sender(*a,**k):self.fail('Unexpected notification')
        r=n.watch(lambda:'queued','job',TOPIC,KEY,lambda:False,approved=True,seconds=6,clock=lambda:t[0],wait=lambda v:t.__setitem__(0,t[0]+v),sender=sender)
        self.assertEqual(r['status'],'watch_expired')
        with self.assertRaises(TimeoutError):n.watch(lambda:'complete','job',TOPIC,KEY,lambda:True,approved=True,sender=sender)
