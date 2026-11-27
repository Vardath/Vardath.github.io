import json
import tempfile
import unittest
from pathlib import Path
from email.message import Message
import io
import socket
from deepthort_local.image_discovery import discover,review,execute
from deepthort_local.public_json import retrieve

SPEC={'query':'quartz landscape','count':3}
def page(n,license='CC BY 4.0'):
    return {'pageid':n,'index':n,'title':f'File:Quartz{n}.png','imageinfo':[{
        'mime':'image/png','size':1200,'width':100,'height':100,'sha1':'a'*40,
        'descriptionurl':f'https://commons.wikimedia.org/wiki/File:Quartz{n}.png',
        'url':f'https://upload.wikimedia.org/wikipedia/commons/a/ab/Quartz{n}.png',
        'extmetadata':{'LicenseShortName':{'value':license},
                       'LicenseUrl':{'value':'https://creativecommons.org/licenses/by/4.0/'},
                       'Artist':{'value':'Fixture author'}}}]}
DATA={'query':{'pages':{'1':page(1),'2':page(2,'All rights reserved')}}}
def transport(host,path,**kw):
    return DATA,json.dumps(DATA).encode()
class Response:
    def __init__(self,status=200):
        self.status=status;raw=json.dumps(DATA).encode();self.body=io.BytesIO(raw);self.headers=Message()
        self.headers['Content-Type']='application/json';self.headers['Content-Length']=str(len(raw))
    def getheader(self,k,default=None):return self.headers.get(k,default)
    def read1(self,n):return self.body.read(n)
class Conn:
    def __init__(self,status):self.response=Response(status);self.closed=False
    def request(self,*a,**kw):self.requested=(a,kw)
    def getresponse(self):return self.response
    def close(self):self.closed=True
def dns(*args):return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
class ImageDiscoveryTests(unittest.TestCase):
    def test_provider_candidates_and_rights(self):
        def capture(host,path,**kw):
            self.assertEqual(host,'commons.wikimedia.org');self.assertIn('gsrsearch=quartz+landscape',path)
            return transport(host,path,**kw)
        r=discover(SPEC,approved=True,transport=capture)
        self.assertEqual(len(r['candidates']),1);self.assertEqual(r['candidates'][0]['creator'],'Fixture author')
        self.assertTrue(r['candidates'][0]['attribution_required']);self.assertFalse(r['image_downloaded'])
        self.assertFalse(r['license_independently_verified'])
    def test_consent_error_and_no_results(self):
        with self.assertRaises(ValueError):discover(SPEC,transport=lambda *_:self.fail('network'))
        with self.assertRaises(ValueError):discover(SPEC,approved=True,transport=lambda *a,**k:({'error':{}},b'{}'))
        self.assertEqual(discover(SPEC,approved=True,transport=lambda *a,**k:({'batchcomplete':''},b'{}'))['candidates'],[])
    def test_transport_origin_and_redirect(self):
        c=Conn(200)
        data,_=retrieve('commons.wikimedia.org','/w/api.php?x=1',resolver=dns,connection=lambda *_:c)
        self.assertEqual(data,DATA);self.assertTrue(c.closed)
        with self.assertRaises(ValueError):retrieve('example.org','/',resolver=lambda *_:self.fail('network'))
        c=Conn(302)
        with self.assertRaises(ValueError):retrieve('commons.wikimedia.org','/w/api.php',resolver=dns,connection=lambda *_:c)
        self.assertTrue(c.closed)
    def test_review_publication_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','images.json')
            def search(s,approved):return discover(s,approved=approved,transport=transport)
            r=execute(root,plan,search=search);self.assertEqual(r['candidate_count'],1)
            with self.assertRaises(ValueError):execute(root,plan,search=search)
            (root/'images.json').unlink();p.write_text(json.dumps(dict(SPEC,count=1)))
            with self.assertRaises(ValueError):execute(root,plan,search=search)
