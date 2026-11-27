import json
import unittest
from email.message import Message
from deepthort_local.github_oauth import connect,Session,VERIFY
def resolver(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
class Response:
    status=200
    def __init__(self,data):
        self.raw=json.dumps(data).encode();self.headers=Message();self.headers['Content-Type']='application/json'
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):p,self.raw=self.raw[:n],self.raw[n:];return p
class Fixture:
    def __init__(self,scope='read:user'):
        self.scope=scope;self.now=0;self.waits=[];self.codes=[];self.calls=[];self.polls=0
    def clock(self):return self.now
    def wait(self,t):self.waits.append(t);self.now+=t
    def connection(self,host,ip):
        f=self
        class Connection:
            def request(self,method,path,body,headers):self.path=path;f.calls.append((host,method,path))
            def getresponse(self):
                if self.path=='/login/device/code':return Response({'device_code':'fixture_device','user_code':'ABCD-1234','verification_uri':VERIFY,'interval':5,'expires_in':900})
                if self.path=='/user':return Response({'login':'example','id':42})
                f.polls+=1
                if f.polls==1:return Response({'error':'authorization_pending'})
                if f.polls==2:return Response({'error':'slow_down'})
                return Response({'access_token':'fixture_token','token_type':'bearer','scope':f.scope})
            def close(self):pass
        return Connection()
    def run(self):
        return connect('fixture_client'.replace('_',''),self.codes.append,lambda:False,approved=True,resolver=resolver,connection=self.connection,clock=self.clock,wait=self.wait)
class OAuthTests(unittest.TestCase):
    def test_polling_pacing_identity_and_expiry(self):
        f=Fixture();s=f.run()
        self.assertEqual(f.waits,[5,5,10]);self.assertEqual(f.codes,['ABCD-1234'])
        self.assertEqual(s.login,'example');self.assertEqual(s.token(f.now),'fixture_token')
        self.assertNotIn('fixture_token',repr(s));self.assertEqual(f.calls[-1],('api.github.com','GET','/user'))
        with self.assertRaises(ValueError):s.token(f.now+901)
    def test_excess_scope_refused(self):
        f=Fixture('read:user,repo')
        with self.assertRaises(ValueError):f.run()
        self.assertNotIn(('api.github.com','GET','/user'),f.calls)
    def test_no_approval_and_disconnect(self):
        with self.assertRaises(PermissionError):connect('fixtureclient',lambda x:None,lambda:False)
        s=Session('example',1,900,'fixture_token');s.disconnect()
        with self.assertRaises(ValueError):s.token(0)
