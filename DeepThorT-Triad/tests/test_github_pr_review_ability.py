import json
import unittest
from email.message import Message
from deepthort_local.github_pr_review import inspect,checked
S={'repository':'Owner/Repo','number':7,'head_sha':'a'*40,'base_sha':'b'*40}
def resolver(*args,**kwargs):return [(2,1,6,'',('8.8.8.8',443))]
def meta(sha='a'*40):
    return {'number':7,'head':{'sha':sha},'base':{'sha':'b'*40,'repo':{'full_name':'Owner/Repo'}},'changed_files':2,'state':'open','draft':False}
class Response:
    status=200
    def __init__(self,data):
        self.raw=json.dumps(data).encode();self.headers=Message();self.headers['Content-Type']='application/json'
    def getheader(self,k,d=None):return self.headers.get(k,d)
    def read1(self,n):part,self.raw=self.raw[:n],self.raw[n:];return part
class Fixture:
    def __init__(self,changed=False,missing=False):
        self.calls=[];self.changed=changed;self.missing=missing
    def connect(self,host,ip):
        parent=self
        class Connection:
            def request(self,method,path,body,headers):parent.calls.append((method,path));self.path=path
            def getresponse(self):
                if '/files?' in self.path:
                    rows=[{'filename':'.github/workflows/test.yml','status':'modified','additions':1,'deletions':0,'patch':'@@ -1 +1,2 @@\n a\n+b'},
                          {'filename':'bin/app.exe','status':'added','additions':0,'deletions':0}]
                    return Response(rows[:1] if parent.missing else rows)
                return Response(meta('c'*40 if parent.changed and len(parent.calls)==3 else 'a'*40))
            def close(self):pass
        return Connection()
class ReviewTests(unittest.TestCase):
    def test_bounded_actual_request_sequence_and_evidence(self):
        f=Fixture();r=inspect(S,'fixture_token',approved=True,resolver=resolver,connection=f.connect)
        self.assertEqual([x[0] for x in f.calls],['GET','GET','GET'])
        self.assertEqual(r['summary']['patches_present'],1)
        self.assertIn('build_or_ci_configuration',r['files'][0]['review_indicators'])
        self.assertEqual(r['files'][1]['patch_omission_reason'],'provider_patch_missing')
        self.assertFalse(r['review_posted'])
    def test_drift_and_incomplete_rejected(self):
        for f in (Fixture(changed=True),Fixture(missing=True)):
            with self.assertRaises(ValueError):inspect(S,'fixture_token',approved=True,resolver=resolver,connection=f.connect)
    def test_no_authority_or_guessing(self):
        with self.assertRaises(ValueError):inspect(S,'fixture_token')
        with self.assertRaises(ValueError):checked(dict(S,head_sha='main'))
