import hashlib
import io
from email.message import Message
import socket
import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.website_monitor import checked_url,resolve_public,fetch,WebsiteMonitors,MAX_BODY

def dns(host,port,family,kind):
    return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
class Response:
    def __init__(self,body,status=200,encoding='identity'):
        self.status=status;self.body=io.BytesIO(body);self.headers=Message()
        self.headers['Content-Type']='text/html';self.headers['Content-Length']=str(len(body))
        self.headers['Content-Encoding']=encoding
    def getheader(self,key,default=None):return self.headers.get(key,default)
    def read1(self,n):return self.body.read(n)
class Connection:
    def __init__(self,response):self.response=response;self.closed=False
    def request(self,*args,**kwargs):self.requested=(args,kwargs)
    def getresponse(self):return self.response
    def close(self):self.closed=True
class MonitorTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.c=ConversationStore(Path(tmp.name)/'c.db');self.m=WebsiteMonitors(self.c)
    def test_public_only_and_pinned_request(self):
        for url in ('http://example.org/','https://127.0.0.1/','https://localhost/','https://example.org:443/',
                    'https://user@example.org/','https://example.org/?token=x','https://example.org/#a','https://a.local/'):
            with self.assertRaises(ValueError):checked_url(url)
        def private(*args):return dns(*args)+[(socket.AF_INET,socket.SOCK_STREAM,6,'',('10.0.0.1',443))]
        with self.assertRaises(ValueError):resolve_public('example.org',private)
        conn=Connection(Response(b'hello'))
        def factory(host,ip):
            self.assertEqual((host,ip),('example.org','93.184.216.34'));return conn
        r=fetch('https://example.org/page',resolver=dns,connection=factory)
        self.assertEqual(r['sha256'],hashlib.sha256(b'hello').hexdigest())
        self.assertEqual(conn.requested[0],('GET','/page'));self.assertTrue(conn.closed)
    def test_reject_redirect_size_compression(self):
        for response in (Response(b'',302),Response(b'x'*(MAX_BODY+1)),Response(b'abc',encoding='gzip')):
            conn=Connection(response)
            with self.assertRaises(ValueError):fetch('https://example.org/',resolver=dns,connection=lambda *_:conn)
            self.assertTrue(conn.closed)
    def test_durable_baseline_error_change_and_no_duplicate(self):
        n=self.m.create('p','c','https://example.org/',900,4,approved=True,now=100)
        a={'sha256':'a'*64,'bytes':4,'mime':'text/html'};b=dict(a,sha256='b'*64)
        self.assertIsNone(self.m.due('p',['other'],now=100))
        s=self.m.due('p',['c'],now=100)
        self.assertEqual(self.m.finish(s,a,now=100)['status'],'baseline')
        self.assertIsNone(self.m.finish(s,b,now=100))
        self.assertIsNone(self.m.due('p',['c'],now=999))
        self.m=WebsiteMonitors(ConversationStore(self.c.path))
        self.assertEqual(self.m.finish(self.m.due('p',['c'],now=1000),None,now=1000)['status'],'error')
        self.assertEqual(self.m.finish(self.m.due('p',['c'],now=1900),a,now=1900)['status'],'unchanged')
        self.assertEqual(self.m.finish(self.m.due('p',['c'],now=5000),b,now=5000)['status'],'changed')
        self.assertEqual(self.m.rows('p','c')[0]['state'],'finished')
        self.assertEqual(len(self.m.history(n,'p','c')),4)
        self.assertEqual(self.c.thread('c'),[])
    def test_consent_scope_and_cancel(self):
        with self.assertRaises(ValueError):self.m.create('p','c','https://example.org/',900,3)
        n=self.m.create('p','c','https://example.org/',900,3,approved=True,now=100)
        s=self.m.due('p',['c'],now=100)
        self.assertFalse(self.m.cancel(n,'q','c'));self.assertTrue(self.m.cancel(n,'p','c'))
        self.assertIsNone(self.m.finish(s,None,now=100))
        self.assertEqual(self.m.history(n,'p','c'),[])
