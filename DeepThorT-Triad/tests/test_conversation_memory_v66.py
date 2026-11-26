"""Independent Memory observes persisted conversations, including general chat."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.conversation_memory import run_once,advice,observations

class RecallTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.jobs=self.root/'jobs.sqlite3'
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
    def past(self,chat,project,text):
        ident=self.chats.submit(chat,project,'chat',text)
        self.chats.change(ident,'responded','Responded',response='Assistant claim not user evidence')
        return ident
    def test_general_chat_and_isolation(self):
        old=self.past('same','(general)','The synthesizer should use a triangle oscillator.')
        self.past('other','(general)','The synthesizer should use a saw oscillator.')
        self.past('same','project','The synthesizer should use a pulse oscillator.')
        ident=self.chats.submit('same','(general)','chat','Which oscillator should my synthesizer use?')
        calls=[]
        def select(key,prompt,tokens):
            calls.append(prompt)
            return json.dumps({'keep':['C'+str(old)],'reason':'Relevant prior preference'})
        for _ in range(8):
            run_once(self.jobs,select)
            if advice(self.jobs,self.chats.get(ident)):break
        result=advice(self.jobs,self.chats.get(ident))
        self.assertIn('triangle oscillator',result)
        self.assertNotIn('saw oscillator',result)
        self.assertNotIn('pulse oscillator',result)
        self.assertNotIn('Assistant claim',result)
        self.assertEqual(len(calls),1)
        self.assertEqual(observations(self.jobs)[0]['recipients'],['janus','sentinel'])
        self.assertNotIn('triangle',json.dumps(observations(self.jobs)))
        self.chats.submit('same','(general)','chat','A newer synthesizer request')
        self.assertEqual(advice(self.jobs,self.chats.get(ident)),'')
    def test_superseded_during_recall(self):
        old=self.past('same','(general)','Use triangle oscillator.')
        ident=self.chats.submit('same','(general)','chat','Choose oscillator.')
        def select(*args):
            self.chats.submit('same','(general)','chat','Use a different oscillator.')
            return json.dumps({'keep':['C'+str(old)],'reason':'Previous choice'})
        self.assertIsNone(run_once(self.jobs,select))
        self.assertEqual(advice(self.jobs,self.chats.get(ident)),'')
        self.assertEqual(observations(self.jobs),[])
if __name__=='__main__':unittest.main()
