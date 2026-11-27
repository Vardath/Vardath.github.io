import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from deepthort_local.api_testing import run,review,execute,checked
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','http://example.invalid/');self.end_headers();return
        raw=b'{"ready":true,"count":2}'
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.addCleanup(self.server.server_close)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join,3);self.addCleanup(self.server.shutdown)
        self.s={'port':self.server.server_port,'cases':[{'id':'ready','path':'/health','status':200,'json_fields':{'ready':True,'count':2}}]}
    def test_actual_requests_and_type_checks(self):
        self.assertTrue(run(self.s)['all_passed'])
        self.s['cases'][0]['json_fields']['ready']=1
        self.assertFalse(run(self.s)['all_passed'])
    def test_no_redirect_and_target_bounds(self):
        self.s['cases'][0].update(path='/redirect',status=302,json_fields={})
        self.assertTrue(run(self.s)['all_passed'])
        with self.assertRaises(ValueError):checked(dict(self.s,port=8765))
        self.s['cases'][0]['path']='//example.invalid/'
        with self.assertRaises(ValueError):checked(self.s)
    def test_review_publication_and_stale_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'spec.json';source.write_text(json.dumps(self.s),encoding='utf-8')
            plan,_=review(root,'spec.json','test.json')
            self.assertTrue(execute(root,plan)['all_passed'])
            self.assertNotIn('body',json.loads((root/'test.json').read_text())['cases'][0])
            plan,_=review(root,'spec.json','later.json')
            self.s['cases'][0]['status']=201;source.write_text(json.dumps(self.s),encoding='utf-8')
            with self.assertRaises(ValueError):execute(root,plan)
