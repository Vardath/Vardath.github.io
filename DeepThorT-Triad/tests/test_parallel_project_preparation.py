import tempfile,threading,unittest,time
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.project_queue import QueuePolicy
from deepthort_local import parallel_project_preparation as m

def health(slots=3):
    return {'pid':7,'ready':True,'serial_memory_mode':False,'admission_waiting':0,'admission_slots':slots,
            'models':{r:{'resident':True,'busy':False,'generating':False} for r in ('janus','sentinel','implementation')},
            'memory_model':{'resident':True,'generating':True}}
class ParallelTests(unittest.TestCase):
    def setup_inputs(self,td):
        root=Path(td).resolve();a=root/'a';b=root/'b';a.mkdir();b.mkdir()
        path=root/'conversations.sqlite3';store=ConversationStore(path);policy=QueuePolicy(root/'priority.sqlite3')
        first=store.submit('a',str(a),'draft_plan','First',independent=True)
        second=store.submit('b',str(b),'draft_plan','Second',independent=True)
        policy.sync([(str(a),'a'),(str(b),'b')])
        return path,store,policy,a,b,first,second
    def test_distinct_projects_and_slots(self):
        with tempfile.TemporaryDirectory() as td:
            path,store,p,a,b,first,second=self.setup_inputs(td)
            items=m.select(path,health(),7,('janus','sentinel'),priority=p.snapshot())
            self.assertEqual([(r['id'],role) for r,role in items],[(first,'janus'),(second,'sentinel')])
            self.assertEqual(len(m.select(path,health(2),7,('janus','sentinel'),priority=p.snapshot())),1)
            p.hold(str(a),held=True)
            self.assertEqual([r['id'] for r,_ in m.select(path,health(),7,('janus','sentinel'),priority=p.snapshot())],[second])
    def test_real_concurrent_preparation_and_no_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            path,store,p,a,b,first,second=self.setup_inputs(td)
            barrier=threading.Barrier(2,timeout=5)
            class Client:
                def chat_as(self,role,session,prompt,**kw):
                    barrier.wait()
                    return '{"kind":"advice","finding":"Evidence needed","guidance":"Review tests"}'
            errors=[]
            results=m.run(path,Client,('janus','sentinel'),lambda:False,health,7,p.snapshot,on_error=errors.append)
            self.assertEqual({r['role'] for r in results},{'janus','sentinel'},repr(errors))
            self.assertEqual(store.get(first)['state'],'pending');self.assertEqual(store.get(second)['state'],'pending')
    def test_short_competing_transaction_does_not_discard_advice(self):
        with tempfile.TemporaryDirectory() as td:
            path,store,p,a,b,first,second=self.setup_inputs(td)
            acquired=threading.Event();errors=[]
            def lock():
                from contextlib import closing
                with closing(m.q.connect(path)) as db,db:
                    db.execute('BEGIN IMMEDIATE');acquired.set();time.sleep(.25)
            thread=threading.Thread(target=lock)
            thread.start()
            try:
                self.assertTrue(acquired.wait(2))
                class Client:
                    def chat_as(self,*args,**kwargs):
                        return '{"kind":"advice","finding":"Finding","guidance":"Advice"}'
                results=m.run(path,Client,('janus','sentinel'),lambda:False,health,7,p.snapshot,on_error=errors.append)
                self.assertEqual({x['role'] for x in results},{'janus','sentinel'},repr(errors))
            finally:thread.join(3)
            self.assertEqual(store.get(first)['state'],'pending')
            self.assertEqual(store.get(second)['state'],'pending')
    def test_nested_workspaces_and_late_hold(self):
        with tempfile.TemporaryDirectory() as td:
            path,store,p,a,b,first,second=self.setup_inputs(td)
            p.hold(str(b),held=True);nested=a/'nested';nested.mkdir()
            store.submit('n',str(nested),'draft_plan','Nested',independent=True)
            p.sync([(str(nested),'n')])
            self.assertEqual(len(m.select(path,health(),7,('janus','sentinel'),priority=p.snapshot())),1)
            class Client:
                def chat_as(self,*args,**kwargs):
                    p.hold(str(a),held=True)
                    return '{"kind":"advice","finding":"Finding","guidance":"Advice"}'
            self.assertEqual(m.run(path,Client,('janus','sentinel'),lambda:False,health,7,p.snapshot),[])
            self.assertEqual(store.get(first)['state'],'pending')
if __name__=='__main__':unittest.main()
