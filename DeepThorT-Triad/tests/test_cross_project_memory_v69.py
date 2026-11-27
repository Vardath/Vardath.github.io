"""V69: cross-project history is labelled and never promoted to authority."""
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
import sqlite3
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.conversation_memory import run_once,advice,indexed_advice,_packet
from deepthort_local.specification_library import SpecificationIndex,sha
from deepthort_local.memory_governor import fit
from deepthort_local.memory_observer import ADVISORY_HEADER

class CrossProjectMemoryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.jobs=self.root/'jobs.sqlite3'
        self.chats=ConversationStore(self.root/'conversations.sqlite3')
        self.source=self.chats.submit('old','older','draft_plan','Preserve serialized vessel ownership using a regression test.')
        self.chats.change(self.source,'responded','Historical plan',response='Assistant claim is not evidence')
        self.ident=self.chats.submit('new','newer','draft_plan','Implement serialized vessel ownership with regression tests.')
    def select(self,key,prompt,tokens):
        return json.dumps({'keep':['X'+str(self.source)],'reason':'Transferable ownership regression test'})
    def test_cross_project_selected_and_labelled(self):
        for _ in range(4):
            run_once(self.jobs,self.select)
        req=self.chats.get(self.ident)
        result=advice(self.jobs,req)
        self.assertIn('cross_project_example_not_requirement',result)
        self.assertIn('serialized vessel ownership',result)
        self.assertNotIn('Assistant claim',result)
        with closing(sqlite3.connect(self.chats.path)) as db,db:
            db.execute('UPDATE conversation_requests SET prompt=? WHERE id=?',('Changed historical text',self.source))
        self.assertEqual(advice(self.jobs,req),'')
    def test_indexed_section_recall_and_bounded_fit(self):
        original='Unrelated background information. '*110+'\nImplement serialized vessel ownership with regression tests.'
        ident=self.chats.submit('new','newer','draft_plan',original)
        index=SpecificationIndex(self.root/'specification_index.sqlite3')
        index.index(ident,original)
        with closing(sqlite3.connect(index.path)) as db,db:
            db.execute("UPDATE specification_sections SET steps_json='[]' WHERE request_id=? AND ordinal=0",(ident,))
        row=index.next_section(ident,original)
        self.assertIsNotNone(row)
        packet=_packet(self.jobs,ident)
        self.assertEqual(packet['section_sha'],row['sha256'])
        for _ in range(4):run_once(self.jobs,self.select)
        req=self.chats.get(ident)
        scoped=ADVISORY_HEADER+json.dumps({'id':'local','observation':'Historical scoped test'})+'\n'
        context=indexed_advice(self.jobs,req,row['text'],scoped,budget=600)
        self.assertIn('cross_project_example_not_requirement',context)
        self.assertIn('Historical scoped test',context)
        self.assertEqual(fit(context,600),context)
        self.assertEqual(indexed_advice(self.jobs,req,'invented section'), '')
        self.assertEqual(indexed_advice(self.jobs,req,row['text'],budget=10),'')
        self.assertEqual(fit(scoped,600),scoped)
    def test_recall_deeper_exact_historical_excerpt(self):
        from deepthort_local.conversation_memory import _candidates, _scope
        historical='Unrelated background. '*40+'Preserve serialized vessel ownership using a regression test.'
        with closing(sqlite3.connect(self.chats.path)) as db,db:
            db.execute('UPDATE conversation_requests SET prompt=? WHERE id=?',(historical,self.source))
        row=_scope(self.jobs,self.ident)
        candidate=next(x for x in _candidates(self.jobs,row) if x['id']=='X'+str(self.source))
        self.assertGreater(candidate['source_offset'],0)
        start=candidate['source_offset']
        self.assertEqual(candidate['observation'],historical[start:start+400])
        for _ in range(4):run_once(self.jobs,self.select)
        self.assertIn('serialized vessel ownership',advice(self.jobs,self.chats.get(self.ident),budget=1000))
        with closing(sqlite3.connect(self.chats.path)) as db,db:
            db.execute('UPDATE conversation_requests SET prompt=? WHERE id=?',
                       (historical.replace('serialized vessel ownership','different unrelated subject'),self.source))
        self.assertEqual(advice(self.jobs,self.chats.get(self.ident),budget=1000),'')
    def test_cross_excerpt_bounds_and_ties(self):
        from deepthort_local.conversation_memory import _cross_excerpt, CROSS_SOURCE_CHARS
        words={'vessel','ownership'}
        self.assertIsNone(_cross_excerpt('x'*CROSS_SOURCE_CHARS+' vessel ownership',words))
        self.assertEqual(_cross_excerpt('vessel ownership '+'x '*300+' vessel ownership',words)[1],0)
    def test_general_and_non_planning_scope_not_expanded(self):
        from deepthort_local.conversation_memory import _candidates,_scope
        for project,mode in [('(general)','draft_plan'),('new','chat')]:
            ident=self.chats.submit('different-chat',project,mode,'serialized vessel ownership regression')
            self.assertFalse(any(x['id'].startswith('X') for x in _candidates(self.jobs,_scope(self.jobs,ident))))
if __name__=='__main__':unittest.main()

