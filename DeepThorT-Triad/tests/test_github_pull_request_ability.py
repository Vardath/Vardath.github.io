import json
import unittest
from email.message import Message
from deepthort_local.github_pull_request import create,checked
S={'repository':'Owner/Repo','head':'feature','base':'main','title':'Draft','body':'Review this change.'}
class Response:
    status=201
    def __init__(self):
        self.raw=json.dumps({'number':12,'draft':True,'head':{'ref':'feature','repo':{'full_name':'Owner/Repo'}},'base':{'ref':'main','repo':{'full_name':'Owner/Repo'}}}).encode()
        self.headers=Message();self.headers['Content-Type']='application/json'
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):part,self.raw=self.raw[:n],self.raw[n:];return part
class Connection:
    def __init__(self,host,ip):self.host=host;self.ip=ip;self.sent=None
    def request(self,method,path,body,headers):self.sent=(method,path,json.loads(body),headers)
    def getresponse(self):return Response()
    def close(self):pass
class PullRequestTests(unittest.TestCase):
    def test_fixed_approved_post_and_receipt(self):
        instances=[]
        def conn(h,i):
            c=Connection(h,i);instances.append(c);return c
        def resolve(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
        r=create(S,'fixture_token',approved=True,resolver=resolve,connection=conn)
        self.assertEqual(r['number'],12);self.assertTrue(r['draft']);self.assertFalse(r['merged'])
        c=instances[0];self.assertEqual(c.host,'api.github.com')
        self.assertEqual(c.sent[:2],('POST','/repos/Owner/Repo/pulls'))
        self.assertTrue(c.sent[2]['draft']);self.assertNotIn('fixture_token',json.dumps(r))
    def test_approval_and_invalid_target(self):
        with self.assertRaises(ValueError):create(S,'fixture_token')
        for change in ({'repository':'https://example.invalid'},{'head':'../main'},{'head':'main'}):
            with self.assertRaises(ValueError):checked(dict(S,**change))
    def test_wrong_receipt_is_not_claimed(self):
        class Bad(Connection):
            def getresponse(self):
                r=Response();r.raw=b'{"number":12,"draft":false}';return r
        def resolve(*a,**k):return [(2,1,6,'',('8.8.8.8',443))]
        with self.assertRaises(ValueError):create(S,'fixture_token',approved=True,resolver=resolve,connection=Bad)
