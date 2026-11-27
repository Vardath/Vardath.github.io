import hashlib,http.client,json,queue,sqlite3,tempfile,threading,unittest
from contextlib import closing
from pathlib import Path
from deepthort_local import developer_status as s,openai_gateway as g
from deepthort_local.job_queue import JobStore
from deepthort_local.conversation_workflow import ConversationStore
KEY='fixture_only_123456789012345678901234'
class StatusTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);self.root=Path(d.name)
        self.jobs=JobStore(self.root/'jobs.sqlite3');self.requests=ConversationStore(self.root/'conversations.sqlite3')
        self.job=self.jobs.submit('project','chat','chat','private fixture prompt')
        self.jobs.submit('other','chat','chat','other project')
        self.jobs.submit('project','other','chat','other chat')
        self.req=self.requests.submit('chat','project','chat','private fixture request')
        self.requests.submit('other','project','chat','other chat')
    def read(self):return s.status(self.jobs.path,self.requests.path,'project','chat',approved=True)
    def test_exact_scope_and_no_recovery(self):
        with closing(sqlite3.connect(self.requests.path)) as db, db:
            db.execute("UPDATE conversation_requests SET state='running' WHERE id=?",(self.req,))
        before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.jobs.path,self.requests.path)]
        value=self.read();after=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.jobs.path,self.requests.path)]
        self.assertEqual(before,after)
        self.assertEqual(value['jobs']['rows'],[{'id':self.job,'mode':'chat','state':'queued'}])
        self.assertEqual(value['conversation_requests']['rows'],[{'id':self.req,'mode':'chat','state':'running'}])
        self.assertNotIn('private fixture',json.dumps(value))
        with self.assertRaises(PermissionError):s.status(self.jobs.path,self.requests.path,'project','chat')
    def test_optional_authenticated_endpoint(self):
        for enabled in (False,True):
            ports=queue.Queue();cancel=threading.Event()
            t=threading.Thread(target=lambda:g.serve(KEY,lambda p:None,ports.put,cancel.is_set,approved=True,seconds=5,status_reader=self.read if enabled else None),daemon=True);t.start()
            try:
                port=ports.get(timeout=4)
                for key,expected in [('incorrect',401),(KEY,200 if enabled else 400)]:
                    c=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                    try:
                        c.request('GET','/janus/v1/status',headers={'Authorization':'Bearer '+key})
                        r=c.getresponse();data=json.loads(r.read());self.assertEqual(r.status,expected)
                        if expected==200:self.assertEqual(data['jobs']['rows'][0]['id'],self.job)
                    finally:c.close()
            finally:cancel.set();t.join(4)
    def test_bounded_recent_rows(self):
        for _ in range(51):self.jobs.submit('project','chat','chat','fixture')
        value=self.read()['jobs'];self.assertEqual(len(value['rows']),50);self.assertTrue(value['more_omitted'])
