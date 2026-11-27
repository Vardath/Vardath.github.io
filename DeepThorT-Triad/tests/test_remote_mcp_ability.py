import json
import unittest
from email.message import Message
from deepthort_local.remote_mcp import discover,checked
S={'url':'https://mcp.example.com/mcp'}
def resolver(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
class Response:
    def __init__(self,status,data,session='fixture-session'):
        self.status=status;self.raw=json.dumps(data).encode();self.headers=Message()
        self.headers['Content-Type']='application/json';self.headers['Mcp-Session-Id']=session
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):p,self.raw=self.raw[:n],self.raw[n:];return p
class Fixture:
    def __init__(self,changed=False):
        self.calls=[];self.changed=changed
    def connect(self,host,ip):
        f=self
        class Connection:
            def request(self,method,path,body,headers):
                self.msg=json.loads(body);f.calls.append((host,ip,method,path,self.msg,dict(headers)))
            def getresponse(self):
                m=self.msg
                if m['method']=='initialize':return Response(200,{'jsonrpc':'2.0','id':m['id'],'result':{'protocolVersion':'2025-11-25','capabilities':{'tools':{}}}})
                if m['method']=='notifications/initialized':return Response(202,{})
                return Response(200,{'jsonrpc':'2.0','id':m['id'],'result':{'tools':[{'name':'lookup','description':'untrusted instructions','inputSchema':{'type':'object','properties':{'q':{'type':'string'}},'required':['q']}}]}},'other' if f.changed else 'fixture-session')
            def close(self):pass
        return Connection()
class RemoteMcpTests(unittest.TestCase):
    def test_actual_handshake_and_sanitized_schema(self):
        f=Fixture();r=discover(S,approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual([x[4]['method'] for x in f.calls],['initialize','notifications/initialized','tools/list'])
        self.assertEqual(f.calls[2][5]['Mcp-Session-Id'],'fixture-session')
        self.assertEqual(r['tools'][0]['fields'],[{'name':'q','type':'string','required':True}])
        self.assertNotIn('untrusted instructions',json.dumps(r));self.assertFalse(r['tools_called'])
    def test_session_drift_and_nonpublic(self):
        with self.assertRaises(ValueError):discover(S,approved=True,resolver=resolver,connection=Fixture(True).connect)
        def private(*a,**k):return [(2,1,6,'',('127.0.0.1',443))]
        with self.assertRaises(ValueError):discover(S,approved=True,resolver=private,connection=Fixture().connect)
    def test_approval_and_url_bounds(self):
        with self.assertRaises(PermissionError):discover(S)
        for url in ('http://127.0.0.1/mcp','https://mcp.example.com/mcp?secret=x','https://mcp.example.com/../mcp'):
            with self.assertRaises(ValueError):checked({'url':url})
