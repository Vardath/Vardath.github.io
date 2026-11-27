from email.message import Message
import hashlib
import io
import json
import socket
import tempfile
import unittest
from pathlib import Path
from deepthort_local.webpage_retrieval import extract,fetch_page,review,execute,MAX_BODY

URL='https://example.org/manual'
RAW=b'<html><head><title>Quartz manual</title><script>hidden()</script></head><body><h1>Engine</h1><p>Calibrate &amp; inspect.</p><script>bad instructions</script><a href="/next">Next</a><a href="javascript:bad()">Ignore</a></body></html>'
def dns(host,port,family,kind):
    return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
class Response:
    def __init__(self,body=RAW,status=200,mime='text/html; charset=utf-8'):
        self.status=status;self.body=io.BytesIO(body);self.headers=Message()
        self.headers['Content-Type']=mime;self.headers['Content-Length']=str(len(body))
    def getheader(self,k,default=None):return self.headers.get(k,default)
    def read1(self,n):return self.body.read(n)
class Connection:
    def __init__(self,response):self.response=response;self.closed=False
    def request(self,*args,**kw):self.requested=(args,kw)
    def getresponse(self):return self.response
    def close(self):self.closed=True
class WebpageTests(unittest.TestCase):
    def test_static_extraction_and_links(self):
        r=extract(URL,RAW,'text/html','utf-8')
        self.assertEqual(r['title'],'Quartz manual');self.assertIn('Calibrate & inspect.',r['text'])
        self.assertNotIn('bad instructions',r['text']);self.assertNotIn('hidden()',r['text'])
        self.assertEqual(r['discovered_links'],['https://example.org/next'])
        self.assertFalse(r['links_followed']);self.assertFalse(r['content_verified_as_factual'])
        self.assertEqual(r['response_sha256'],hashlib.sha256(RAW).hexdigest())
    def test_pinned_network_and_approval(self):
        c=Connection(Response())
        def factory(host,ip):
            self.assertEqual((host,ip),('example.org','93.184.216.34'));return c
        with self.assertRaises(ValueError):fetch_page(URL,resolver=lambda *_:self.fail('unapproved network'))
        r=fetch_page(URL,approved=True,resolver=dns,connection=factory)
        self.assertEqual(r['url'],URL);self.assertEqual(c.requested[0],('GET','/manual'));self.assertTrue(c.closed)
    def test_redirect_nontext_and_size_refused(self):
        for response in (Response(status=302),Response(mime='application/pdf'),Response(b'x'*(MAX_BODY+1))):
            c=Connection(response)
            with self.assertRaises(ValueError):fetch_page(URL,approved=True,resolver=dns,connection=lambda *_:c)
            self.assertTrue(c.closed)
        with self.assertRaises(ValueError):extract(URL,b'abc','text/plain','utf-16')
    def test_review_publish_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'spec.json';p.write_text(json.dumps({'url':URL}))
            plan,preview=review(root,'spec.json','page.json');self.assertEqual(preview['url'],URL)
            def retrieve(url,approved):
                self.assertTrue(approved);return extract(url,RAW,'text/html','utf-8')
            r=execute(root,plan,retrieve=retrieve)
            self.assertEqual(json.loads((root/'page.json').read_text())['response_sha256'],r['response_sha256'])
            with self.assertRaises(ValueError):execute(root,plan,retrieve=lambda *_:self.fail('output already exists'))
            (root/'page.json').unlink();p.write_text(json.dumps({'url':'https://example.net/'}))
            with self.assertRaises(ValueError):execute(root,plan,retrieve=lambda *_:self.fail('source changed'))
