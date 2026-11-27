import json,tempfile,unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local import queued_prompt_preparation as q
from deepthort_local import specialist_agents as m

PROFILE={'host':'implementation','name':'Build specialist','focus':'Inspect build dependency requirements','deliverable':'List likely verification steps'}
class Client:
    def __init__(self):self.calls=[]
    def chat_as(self,role,session,prompt,**kw):
        self.calls.append((role,prompt))
        body={'kind':'advice','finding':'Review scope','guidance':'Do not invent evidence'}
        if role=='janus':body['specialist']=PROFILE
        return json.dumps(body)

class SpecialistTests(unittest.TestCase):
    def test_live_queue_configuration_and_host_use(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'conversations.sqlite3';store=ConversationStore(path)
            ident=store.submit('a','project','draft_plan','Build a local utility',independent=True)
            c=Client();r=q.run_once(path,c,['janus'],lambda:False)
            self.assertEqual(r['specialist_config']['profile'],PROFILE)
            self.assertFalse(r['specialist_config']['authority'])
            q.run_once(path,c,['sentinel'],lambda:False)
            self.assertNotIn('Build specialist',c.calls[-1][1])
            q.run_once(path,c,['implementation'],lambda:False)
            self.assertIn('Build specialist',c.calls[-1][1])
            self.assertIn('Build a local utility',c.calls[-1][1])
            self.assertIn('permanent role',c.calls[-1][1])
            store.change(ident,'running','active',allowed=('pending',))
            self.assertIn('Build specialist',q.advice(path,store.get(ident),2000))
    def test_scope_and_authority(self):
        a='a'*64;b='b'*64;c=m.configure(PROFILE,a)
        self.assertEqual(m.guidance(c,a,'sentinel'),'')
        with self.assertRaises(ValueError):m.validate(c,b)
        with self.assertRaises(ValueError):m.validate(dict(c,tools_granted=True),a)
        for bad in (dict(PROFILE,host='janus'),dict(PROFILE,host='memory'),dict(PROFILE,focus='')):
            with self.assertRaises(ValueError):m.configure(bad,a)
        with self.assertRaises(ValueError):q.checked({'kind':'advice','finding':'f','guidance':'g','specialist':PROFILE},'sentinel')
    def test_cancelled_and_cross_task_never_consumed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'conversations.sqlite3';store=ConversationStore(path)
            a=store.submit('a','project','draft_plan','First',independent=True)
            b=store.submit('b','project','draft_plan','Second',independent=True)
            c=Client();q.run_once(path,c,['janus'],lambda:False)
            store.cancel_chat_requests('a')
            self.assertIsNone(q.specialist_for(path,store.get(a),'implementation'))
            q.run_once(path,c,['implementation'],lambda:False)
            self.assertIn('Second',c.calls[-1][1]);self.assertNotIn('Build specialist',c.calls[-1][1])
if __name__=='__main__':unittest.main()
