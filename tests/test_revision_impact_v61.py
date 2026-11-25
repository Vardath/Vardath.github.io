import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.revision_impact import revision_delta,dependency_evidence
from deepthort_local.reasoning_council import sha

class RevisionImpactTests(unittest.TestCase):
    def test_delta_reconstructs_all_new_amendment_text(self):
        with tempfile.TemporaryDirectory() as t:
            store=ConversationStore(Path(t)/'conversations.sqlite3')
            first=store.submit('chat',t,'draft_plan','Space game. '+'a'*4000)
            second=store.amend_project('chat',t,'Change sectors')
            text='Change diplomacy. '+'b'*4000
            third=store.amend_project('chat',t,text)
            result=revision_delta(store,third,second)
            self.assertEqual(''.join(x['text'] for x in result['sections']),text)
            self.assertTrue(all(x['ordinal']==2 for x in result['sections']))
            self.assertIsNone(revision_delta(store,second,third))

    def test_transitive_dependency_change_blocks_retention(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            plan=[{'path':'core.py','description':'Core'},
                  {'path':'map.py','description':'Map; depends-on: core.py'},
                  {'path':'ui.py','description':'UI; depends-on: map.py'}]
            files={'core.py':'core','map.py':'map'}
            for name,content in files.items():(root/name).write_text(content,encoding='utf-8')
            snapshot={'files':{k:sha(v) for k,v in files.items()}}
            stages=[dict(x,state='saved') for x in plan]
            self.assertEqual(dependency_evidence(root,'ui.py',plan,plan,snapshot,stages),snapshot['files'])
            (root/'core.py').write_text('changed',encoding='utf-8')
            self.assertIsNone(dependency_evidence(root,'ui.py',plan,plan,snapshot,stages))

    def test_pending_dependency_cannot_be_certified(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'a.py').write_text('a',encoding='utf-8')
            plan=[{'path':'a.py','description':'A'},{'path':'b.py','description':'B; depends-on: a.py'}]
            snapshot={'files':{'a.py':sha('a')}}
            self.assertIsNone(dependency_evidence(root,'b.py',plan,plan,snapshot,[dict(plan[0],state='planned')]))

if __name__=='__main__':unittest.main()
