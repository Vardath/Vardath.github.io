import io,json,queue,threading,unittest
from deepthort_local import headless_client as c,openai_gateway as g
from deepthort_local.triad_profiles import MODEL_ID
KEY='fixture_only_123456789012345678901234'

class HeadlessTests(unittest.TestCase):
    def test_real_local_session(self):
        ports=queue.Queue();cancel=threading.Event()
        def run():
            g.serve(KEY,lambda p:('fixture answer','stop'),ports.put,cancel.is_set,approved=True,seconds=10,
                    status_reader=lambda:{'schema':'janus-local-status-v1','mutated':False,'jobs':{'rows':[]}})
        t=threading.Thread(target=run,daemon=True);t.start()
        try:
            port=ports.get(timeout=4)
            for operation in ('models','status','chat'):
                out=io.StringIO();err=io.StringIO()
                rc=c.main(['--port',str(port),operation],stdin=io.BytesIO(b'fixture prompt'),stdout=out,stderr=err,env={'JANUS_DEVELOPER_KEY':KEY})
                self.assertEqual(rc,0,err.getvalue());self.assertNotIn(KEY,out.getvalue())
                value=json.loads(out.getvalue())
                if operation=='chat':self.assertEqual(value['choices'][0]['message']['content'],'fixture answer')
        finally:cancel.set();t.join(4)
        self.assertFalse(t.is_alive())
    def test_protected_port_and_input_bounds(self):
        for port in (8765,8766,80):
            with self.assertRaises(ValueError):c.validate_port(port)
        for data in (b'',b'x'*32001,b'x'*8001,b'\xff'):
            calls=[];out=io.StringIO();err=io.StringIO()
            rc=c.main(['--port','18888','chat'],stdin=io.BytesIO(data),stdout=out,stderr=err,env={'JANUS_DEVELOPER_KEY':KEY},transport=lambda *a:calls.append(a))
            self.assertEqual(rc,1);self.assertEqual(calls,[]);self.assertEqual(out.getvalue(),'');self.assertNotIn(KEY,err.getvalue())
    def test_secret_not_echoed_and_no_retry(self):
        calls=[]
        def failed(*args):
            calls.append(args);raise ValueError(KEY)
        err=io.StringIO()
        rc=c.main(['--port','18888','models'],stdout=io.StringIO(),stderr=err,env={},key_reader=lambda _:KEY,transport=failed)
        self.assertEqual(rc,1);self.assertEqual(len(calls),1);self.assertNotIn(KEY,err.getvalue())
