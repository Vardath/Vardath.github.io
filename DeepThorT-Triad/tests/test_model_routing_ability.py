import tempfile,unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.project_queue import QueuePolicy
from deepthort_local import queued_prompt_preparation as q
from deepthort_local import model_routing as m
from deepthort_local.parallel_project_preparation import select

class RoutingTests(unittest.TestCase):
    def test_fixed_doctrine_and_availability(self):
        roles=m.ROLES
        self.assertEqual(m.rank('Implement code and fix bug',roles)[0][0],'implementation')
        self.assertEqual(m.rank('Audit security risk and validate acceptance',roles)[0][0],'sentinel')
        self.assertEqual(m.rank('Plan architecture and roadmap',roles)[0][0],'janus')
        self.assertEqual(m.rank('Fix bug',('janus','sentinel'))[0][0],'janus')
        self.assertEqual(m.rank('Fix bug',roles,preferred='sentinel')[0][0],'sentinel')
        r=m.receipt('Fix bug',roles,'implementation','a'*64)
        self.assertFalse(r['authority']);self.assertFalse(r['model_replaced'])
        with self.assertRaises(ValueError):m.receipt('Fix bug',('janus',),'implementation','a'*64)
    def test_real_scheduler_routes_and_preserves_priority(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();a=root/'a';b=root/'b';a.mkdir();b.mkdir()
            path=root/'c.sqlite3';store=ConversationStore(path);policy=QueuePolicy(root/'p.sqlite3')
            first=store.submit('a',str(a),'draft_plan','Implement code and fix bug',independent=True)
            second=store.submit('b',str(b),'draft_plan','Audit security risk',independent=True)
            policy.sync([(str(a),'a'),(str(b),'b')])
            h={'pid':1,'ready':True,'serial_memory_mode':False,'admission_waiting':0,'admission_slots':3,
               'models':{r:{'resident':True,'busy':False,'generating':False} for r in m.ROLES},
               'memory_model':{'resident':True,'generating':True}}
            items=select(path,h,1,m.ROLES,priority=policy.snapshot())
            self.assertEqual([(r['id'],role) for r,role in items],[(first,'implementation'),(second,'sentinel')])
            h['models']['implementation']['busy']=True
            self.assertEqual(select(path,h,1,m.ROLES,priority=policy.snapshot())[0][1],'janus')
    def test_exact_receipt_and_no_extra_grant(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'c.sqlite3';store=ConversationStore(path)
            ident=store.submit('a','project','draft_plan','Audit security risk',independent=True)
            class Client:
                def chat_as(self,role,session,prompt,**kw):
                    self.role=role
                    return '{"kind":"advice","finding":"Review scope","guidance":"Evidence needed"}'
            c=Client();r=q.run_once(path,c,m.ROLES,lambda:False,dynamic=True)
            self.assertEqual(c.role,'sentinel');self.assertEqual(r['route']['task_identity'],q.identity(store.get(ident)))
            self.assertFalse(r['route']['authority']);self.assertEqual(store.get(ident)['state'],'pending')
            self.assertEqual(q.candidate(path,m.ROLES,dynamic=True)[1],'janus')
if __name__=='__main__':unittest.main()
