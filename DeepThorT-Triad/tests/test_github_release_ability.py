import json
import unittest
from email.message import Message
from deepthort_local.github_release import create,checked
S={'repository':'Owner/Repo','tag':'v1.0','commit':'a'*40,'title':'Version 1','body':'Notes'}
def resolver(*args,**kwargs):return [(2,1,6,'',('8.8.8.8',443))]
class Response:
    def __init__(self,status,data):
        self.status=status;self.raw=json.dumps(data).encode();self.headers=Message();self.headers['Content-Type']='application/json'
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):part,self.raw=self.raw[:n],self.raw[n:];return part
class Fixture:
    def __init__(self,sha='a'*40):
        self.sha=sha;self.calls=[]
    def connect(self,host,ip):
        parent=self
        class Connection:
            def request(self,method,path,body,headers):self.method=method;parent.calls.append((host,method,path,json.loads(body) if body else None))
            def getresponse(self):
                if self.method=='GET':return Response(200,{'ref':'refs/tags/v1.0','object':{'type':'commit','sha':parent.sha}})
                return Response(201,{'id':42,'draft':True,'tag_name':'v1.0'})
            def close(self):pass
        return Connection()
class ReleaseTests(unittest.TestCase):
    def test_exact_tag_and_draft(self):
        f=Fixture();r=create(S,'fixture_token',approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual([x[1] for x in f.calls],['GET','POST'])
        self.assertEqual(f.calls[0][2],'/repos/Owner/Repo/git/ref/tags/v1.0')
        self.assertTrue(f.calls[1][3]['draft']);self.assertFalse(r['published']);self.assertEqual(r['release_id'],42)
    def test_changed_tag_no_post(self):
        f=Fixture('b'*40)
        with self.assertRaises(ValueError):create(S,'fixture_token',approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual(len(f.calls),1)
    def test_validation_and_no_approval(self):
        with self.assertRaises(ValueError):create(S,'fixture_token')
        for change in ({'tag':'../bad'},{'commit':'main'},{'repository':'https://invalid'}):
            with self.assertRaises(ValueError):checked(dict(S,**change))
