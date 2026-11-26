"""V68: actual stored obligations and recipe selections; scripted VLM only."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.gemma_preparation import candidate,make_packet,parse_reply,run_once,available,stored
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.roadmap_runs import RoadmapRuns
from deepthort_local.mixed_roadmap import MixedRoadmaps
from deepthort_local.workflow_design import design

class GemmaPreparationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.db=self.root/'drafts.sqlite'
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.runs=RoadmapRuns(self.root/'roadmaps.sqlite3')
        self.mixed=MixedRoadmaps(self.root/'mixed.sqlite3')
        self.items=[];self.inputs=[]
        for name,output in [('mesh','mesh.obj'),('texture','texture.png')]:
            project=self.root/name;project.mkdir()
            ident=self.chats.submit(name,str(project),'draft_plan','Create the required '+name)
            self.chats.change(ident,'responded','Plan ready',response='Ready')
            req=self.chats.get(ident)
            task={'id':name,'after':0,'goal':'Create '+name,'output':output}
            plan={'request_id':ident,'code_sha':'a'*64,'tasks':[task]}
            self.mixed.save(plan);plan=self.mixed.get(ident,'a'*64)
            self.runs.approve({'request_id':ident,'project':str(project),'chat_id':name,
                'manifest_sha256':'a'*64,'mixed_sha':plan['sha']})
            recipes=[{'recipe_id':ident,'tool':'fixture','output':output,'input_required':False}]
            self.inputs.append((req,task,recipes,[]))
            self.items.append(candidate(self.runs.get(ident),plan,req,task,recipes,[]))
    def reply(self,index=1):
        recipe=self.inputs[index][2][0]['recipe_id']
        return json.dumps({'option':index,'proposal':{'stages':[{'recipe_id':recipe,'input':''}],'missing':[]}})
    def test_selection_persistence_and_no_execution(self):
        def generate(folder,stopped,notify):
            packet=json.loads((folder/'request.json').read_text('utf-8'))
            self.assertEqual(packet,make_packet([x['option'] for x in self.items]))
            return self.reply(),42
        body=run_once(self.db,lambda:iter(self.items),lambda:False,root=self.root,generate=generate)
        self.assertEqual(body['identity'],self.items[1]['identity'])
        self.assertFalse(body['authority']);self.assertFalse(body['verified']);self.assertFalse(body['native_inference_verified'])
        self.assertIsNone(stored(self.db,self.items[0]))
        req,task,recipes,files=self.inputs[1]
        self.assertEqual(available(self.db,self.runs,self.chats,self.mixed,req,task,recipes,files),body['proposal'])
        self.assertFalse((Path(req['project'])/task['output']).exists())
        self.assertIsNone(available(self.db,self.runs,self.chats,self.mixed,req,task,[],files))
        self.runs.change(req['id'],'paused','User paused')
        self.assertIsNone(available(self.db,self.runs,self.chats,self.mixed,req,task,recipes,files))
    def test_mixed_store_releases_database_handles(self):
        # Windows refuses to rename an open SQLite database. All store methods
        # must commit and close, not merely leave a connection context.
        renamed=self.root/'mixed-renamed.sqlite3'
        self.mixed.path.rename(renamed)
        renamed.rename(self.mixed.path)
    def test_invalid_choice_and_stale_scope(self):
        options=[x['option'] for x in self.items]
        with self.assertRaises(ValueError):
            parse_reply(self.reply().replace('"option": 1','"option": 9'),options)
        wrong=json.loads(self.reply());wrong['proposal']['stages'][0]['recipe_id']=999
        with self.assertRaises(ValueError):
            parse_reply(json.dumps(wrong),options)
        def generate(folder,stopped,notify):
            self.items.pop()
            return self.reply(),42
        self.assertIsNone(run_once(self.db,lambda:iter(self.items),lambda:False,root=self.root,generate=generate))
        self.assertFalse(self.db.exists())
    def test_prepared_draft_still_requires_review_and_falls_back(self):
        req,task,recipes,files=self.inputs[1]
        proposal=json.loads(self.reply())['proposal']
        class Acquisition:
            def enrolled(self):return []
            def tool(self,name):raise ValueError('not installed')
        calls=[]
        class Council:
            def _run(self,client,**kw):
                calls.append(kw['role'])
                return json.dumps(proposal)
        reviews=[]
        def review(text,kind):
            reviews.append(text)
            if len(reviews)==1:raise ValueError('Independent reviewer requires another draft')
        with patch('deepthort_local.workflow_design.inventory',return_value=(recipes,files)),patch(
            'deepthort_local.workflow_design.freeze',return_value={'stages':[{'output':task['output']}]}):
            result,manifest=design(Acquisition(),Council(),object(),request=req,goal=task['goal'],review=review,
                mixed_task=task,creative_provider=lambda *args:proposal)
        self.assertEqual(result,proposal)
        self.assertEqual(calls,['JANUS_WORKFLOW_0'])
        self.assertEqual(len(reviews),2)
        self.assertEqual(manifest['mixed_task'],task)
if __name__=='__main__':unittest.main()
