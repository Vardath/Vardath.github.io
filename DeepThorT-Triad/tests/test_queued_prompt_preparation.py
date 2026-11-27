import tempfile,unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local import queued_prompt_preparation as q
class Client:
    def __init__(self,callback=None):self.calls=[];self.callback=callback
    def chat_as(self,role,session,prompt,**kw):
        self.calls.append((role,prompt))
        if self.callback:self.callback()
        return '{"kind":"advice","finding":"Test a dependency","guidance":"Review acceptance first"}'
class QueueTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.path=Path(tmp.name)/'conversations.sqlite3';self.store=ConversationStore(self.path)
    def submit(self,chat,prompt):
        return self.store.submit(chat,'project','draft_plan',prompt,independent=True)
    def test_distinct_durable_fifo_tasks(self):
        a=self.submit('a','Make a game');b=self.submit('b','Make a music player')
        with self.assertRaises(ValueError):self.submit('a','Not an amendment')
        self.assertEqual([x['id'] for x in q.rows(self.path,'project')],[a,b])
        self.assertEqual(self.store.next_pending()['id'],a)
        self.store.change(a,'running','active',allowed=('pending',))
        self.assertEqual(self.store.next_pending()['id'],b)
        restored=ConversationStore(self.path)
        self.assertEqual(restored.get(a)['state'],'pending')
        self.assertEqual(restored.get(b)['prompt'],'Make a music player')
    def test_roles_prepare_and_consume_exactly(self):
        a=self.submit('a','First');b=self.submit('b','Second');client=Client()
        self.assertEqual(q.run_once(self.path,client,['sentinel'],lambda:False,exclude=(a,))['role'],'sentinel')
        self.assertIsNone(q.run_once(self.path,client,['sentinel'],lambda:False,exclude=(a,)))
        self.assertEqual(q.run_once(self.path,client,['implementation'],lambda:False,exclude=(a,))['role'],'implementation')
        self.assertEqual(q.advice(self.path,self.store.get(b)),'')
        self.store.change(b,'running','active',allowed=('pending',))
        req=self.store.get(b);self.assertIn('sentinel preparation',q.advice(self.path,req,1200))
        self.assertIn('implementation preparation',q.advice(self.path,req,1200))
        self.assertEqual(q.advice(self.path,dict(req,prompt='changed'),1200),'')
        self.assertEqual(len(client.calls),2);self.assertTrue(all('Second' in p for _,p in client.calls))
    def test_cancel_race_and_limits(self):
        a=self.submit('a','Cancel this')
        client=Client(lambda:self.store.cancel_chat_requests('a'))
        self.assertIsNone(q.run_once(self.path,client,['janus'],lambda:False))
        self.assertEqual(q.rows(self.path)[0]['prepared'],0)
        for i in range(32):self.submit(str(i),'Work')
        with self.assertRaises(ValueError):self.submit('overflow','Work')
        self.assertEqual(self.store.get(a)['state'],'cancelled')
    def test_invalid_reply_does_not_starve_next_prompt(self):
        a=self.submit('a','First');b=self.submit('b','Second')
        class Bad:
            def chat_as(self,*args,**kwargs):return 'not JSON'
        with self.assertRaises(ValueError):q.run_once(self.path,Bad(),['janus'],lambda:False)
        self.assertEqual(q.candidate(self.path,['janus'])[0]['id'],b)
        self.assertEqual(q.rows(self.path)[0]['prepared'],0)
    def test_admission(self):
        models={r:{'resident':True,'busy':False,'generating':False} for r in q.ROLES}
        health={'pid':1,'ready':True,'serial_memory_mode':False,'admission_waiting':0,'admission_slots':2,
                'models':models,'memory_model':{'generating':True}}
        self.assertEqual(q.available_roles(health,1),q.ROLES)
        models['janus']['generating']=True
        self.assertEqual(q.available_roles(health,1),())
        models['janus']['generating']=False
        self.assertEqual(q.available_roles(dict(health,admission_waiting=1),1),())
        self.assertEqual(q.available_roles(dict(health,serial_memory_mode=True),1),())
