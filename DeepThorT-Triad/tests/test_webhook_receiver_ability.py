import hashlib,hmac,http.client,json,queue,threading,unittest,uuid
from deepthort_local import webhook_receiver as w
SECRET='fixture_only_123456789'
BODY=b'{"example":"unretained payload"}'
def send(port,secret,event='push'):
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=4)
    try:
        conn.request('POST','/webhook',BODY,headers={'Content-Type':'application/json','X-GitHub-Event':event,'X-GitHub-Delivery':str(uuid.uuid4()),'X-Hub-Signature-256':'sha256='+hmac.new(secret.encode(),BODY,hashlib.sha256).hexdigest()})
        response=conn.getresponse();response.read();return response.status
    finally:conn.close()

class WebhookTests(unittest.TestCase):
    def launch(self):
        ports=queue.Queue();results=queue.Queue();cancel=threading.Event()
        def run():
            try:results.put(w.listen('push',SECRET,10,ports.put,cancel.is_set,approved=True))
            except Exception as exc:results.put(exc)
        t=threading.Thread(target=run,daemon=True);t.start()
        self.addCleanup(lambda:(cancel.set(),t.join(4)))
        return ports.get(timeout=4),results,cancel,t
    def test_signed_real_loopback_delivery(self):
        port,q,c,t=self.launch()
        self.assertEqual(send(port,'wrong_fixture_123456'),400)
        self.assertEqual(send(port,SECRET,'ping'),400)
        self.assertEqual(send(port,SECRET),200)
        result=q.get(timeout=4);t.join(4)
        self.assertEqual(result['body_sha256'],hashlib.sha256(BODY).hexdigest())
        self.assertFalse(result['task_submitted']);self.assertFalse(result['payload_retained'])
        self.assertNotIn('unretained payload',json.dumps(result))
        self.assertFalse(t.is_alive())
    def test_wrong_event_consumes_split_bounded_body(self):
        from unittest.mock import Mock
        head=('POST /webhook HTTP/1.1\r\nContent-Type: application/json\r\n'
              'X-GitHub-Event: ping\r\nX-GitHub-Delivery: '+str(uuid.uuid4())+
              '\r\nContent-Length: '+str(len(BODY))+'\r\n\r\n').encode('ascii')
        conn=Mock()
        conn.recv.side_effect=[head,BODY]
        with self.assertRaisesRegex(ValueError,'Unexpected event'):
            w.parse(conn,'push',SECRET.encode(),None,float('inf'))
        self.assertEqual(conn.recv.call_count,2)
    def test_cancel_and_no_approval(self):
        with self.assertRaises(PermissionError):w.listen('push',SECRET,5,lambda p:None)
        port,q,c,t=self.launch();c.set()
        self.assertIsInstance(q.get(timeout=4),TimeoutError);t.join(4);self.assertFalse(t.is_alive())
    def test_invalid_parameters(self):
        for args in (('push','short',5),('push',SECRET,91),('bad/name',SECRET,5)):
            with self.assertRaises(ValueError):w.checked(*args)
