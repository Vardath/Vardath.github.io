import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from deepthort_local.application_monitoring import checked,observe,review,execute
S={'port':8080,'path':'/health','expected_status':200,'json_fields':{'ready':True},
   'samples':3,'interval_seconds':1,'max_latency_ms':100}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        body=b'{"ready":true}'
        self.send_response(200);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
class MonitorTests(unittest.TestCase):
    def test_health_and_latency_distinctions(self):
        results=iter([{'passed':True,'status':200,'elapsed_ms':5},
                      {'passed':True,'status':200,'elapsed_ms':150},
                      {'passed':False,'error_type':'TimeoutError'}])
        waits=[]
        r=observe(S,sample=lambda s:{'cases':[next(results)]},sleep=waits.append)
        self.assertEqual(waits,[1,1]);self.assertEqual(r['healthy_samples'],1)
        self.assertEqual(r['unhealthy_samples'],2);self.assertFalse(r['all_healthy'])
        self.assertEqual(r['median_response_latency_ms'],77.5)
    def test_partial_deadline(self):
        ticks=iter([0,0,0,46])
        r=observe(S,sample=lambda s:{'cases':[{'passed':True,'status':200,'elapsed_ms':1}]},
                  sleep=lambda n:None,clock=lambda:next(ticks))
        self.assertFalse(r['complete']);self.assertFalse(r['all_healthy']);self.assertTrue(r['deadline_reached'])
        with self.assertRaises(ValueError):checked(dict(S,samples=999))
    def test_live_health_and_exact_approval(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);s=dict(S,port=server.server_port,samples=2,max_latency_ms=5000)
                source=root/'spec.json';source.write_text(json.dumps(s),encoding='utf-8')
                plan,_=review(root,'spec.json','health.json')
                result=execute(root,plan);self.assertTrue(result['all_healthy'])
                self.assertEqual(json.loads((root/'health.json').read_text())['completed_samples'],2)
                plan,_=review(root,'spec.json','later.json')
                source.write_text(json.dumps(dict(s,expected_status=201)),encoding='utf-8')
                with self.assertRaises(ValueError):execute(root,plan)
        finally:server.shutdown();t.join(3);server.server_close()
