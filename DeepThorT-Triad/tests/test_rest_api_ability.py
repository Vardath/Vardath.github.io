import json
import unittest
from email.message import Message
from deepthort_local.rest_api import request,checked
S={'url':'https://api.example.com/items','method':'GET','query':{'q':'a b'},'body':None}
def resolver(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
class Response:
    def __init__(self,status=200):
        self.status=status;self.raw=b'{"ok":true}';self.headers=Message()
        self.headers['Content-Type']='application/json';self.headers['Content-Length']=str(len(self.raw))
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):p,self.raw=self.raw[:n],self.raw[n:];return p
class Fixture:
    def __init__(self,status=200):self.status=status;self.calls=[]
    def connect(self,host,ip):
        f=self
        class Connection:
            def request(self,method,path,body,headers):f.calls.append((host,ip,method,path,body,headers))
            def getresponse(self):return Response(f.status)
            def close(self):pass
        return Connection()
class RestTests(unittest.TestCase):
    def test_exact_get_and_json(self):
        f=Fixture();r=request(S,approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual(f.calls[0][:5],('api.example.com','8.8.8.8','GET','/items?q=a+b',None))
        self.assertEqual(r['json'],{'ok':True});self.assertTrue(r['http_success'])
    def test_post_and_no_redirect_retry(self):
        f=Fixture(302);s=dict(S,method='POST',query={},body={'name':'example'})
        r=request(s,approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual(len(f.calls),1);self.assertEqual(json.loads(f.calls[0][4]),{'name':'example'})
        self.assertFalse(r['redirect_followed']);self.assertFalse(r['http_success']);self.assertFalse(r['json_included'])
    def test_rejected_credentials_and_nonpublic(self):
        with self.assertRaises(PermissionError):request(S)
        for change in ({'query':{'api_key':'example'}},{'method':'DELETE'},{'url':'https://api.example.com/../secret'},
                       {'method':'POST','body':{'auth':{'password':'example'}}}):
            with self.assertRaises(ValueError):checked(dict(S,**change))
        def private(*a,**k):return [(2,1,6,'',('127.0.0.1',443))]
        with self.assertRaises(ValueError):request(S,approved=True,resolver=private,connection=Fixture().connect)
