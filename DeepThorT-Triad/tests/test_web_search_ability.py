from email.message import Message
import hashlib
import io
import json
import socket
import unittest
from deepthort_local.web_search import search,normalize,HOST,ENDPOINT,MAX_RESPONSE

RAW=json.dumps({'type':'search','web':{'type':'search','results':[
    {'title':'<strong>Quartz</strong> engine','url':'https://example.org/manual','description':'Calibration <b>reference</b>'},
    {'title':'unsafe','url':'javascript:alert(1)','description':'bad'}]}}).encode()
def dns(host,port,family,kind):
    return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
class Response:
    def __init__(self,raw=RAW,status=200):
        self.status=status;self.body=io.BytesIO(raw);self.headers=Message()
        self.headers['Content-Type']='application/json';self.headers['Content-Length']=str(len(raw))
    def getheader(self,k,default=None):return self.headers.get(k,default)
    def read1(self,n):return self.body.read(n)
class Connection:
    def __init__(self,response):self.response=response;self.closed=False
    def request(self,*args,**kw):self.requested=(args,kw)
    def getresponse(self):return self.response
    def close(self):self.closed=True
class WebSearchTests(unittest.TestCase):
    def test_fixed_provider_request_and_redacted_output(self):
        c=Connection(Response())
        def factory(host,ip):
            self.assertEqual((host,ip),(HOST,'93.184.216.34'));return c
        r=search('quartz calibration',10,'example-token',approved=True,resolver=dns,connection=factory)
        self.assertEqual(c.requested[0][0],'GET');self.assertTrue(c.requested[0][1].startswith(ENDPOINT+'?'))
        self.assertIn('q=quartz+calibration',c.requested[0][1])
        self.assertEqual(c.requested[1]['headers']['X-Subscription-Token'],'example-token')
        self.assertNotIn('example-token',json.dumps(r));self.assertTrue(c.closed)
        self.assertEqual(r['supplied_results']['results'][0]['title'],'Quartz engine')
        self.assertEqual(r['interpretation']['provider_response_sha256'],hashlib.sha256(RAW).hexdigest())
        self.assertEqual(r['interpretation']['provider_rows_omitted'],1)
        self.assertFalse(r['interpretation']['claims_verified'])
    def test_no_consent_or_invalid_key(self):
        def fail(*a):self.fail('Network should not be invoked')
        with self.assertRaises(ValueError):search('quartz',10,'example-token',resolver=fail)
        with self.assertRaises(ValueError):search('quartz',10,'bad\nheader',approved=True,resolver=fail)
        with self.assertRaises(ValueError):search('quartz',21,'example-token',approved=True,resolver=fail)
    def test_redirect_and_oversize(self):
        for response in (Response(status=302),Response(b'x'*(MAX_RESPONSE+1))):
            c=Connection(response)
            with self.assertRaises(ValueError):search('quartz',10,'example-token',approved=True,resolver=dns,connection=lambda *_:c)
            self.assertTrue(c.closed)
    def test_empty_and_invalid_provider_response(self):
        r=normalize('quartz',10,b'{"type":"search"}')
        self.assertEqual(r['supplied_results']['results'],[])
        for raw in (b'{"type":"error"}',b'{"type":"search","web":{"type":"search","results":[{}]}}',b'{"type":"search","type":"search"}'):
            with self.assertRaises(ValueError):normalize('quartz',10,raw)
