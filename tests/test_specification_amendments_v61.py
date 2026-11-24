import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.specification_amendments import job_is_superseded,render_revision

class AmendmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=ConversationStore(Path(self.temp.name)/'conversations.sqlite3')
        self.project=self.temp.name
        self.original='Build a space game with 100 sectors, diplomacy and mining.'
        self.root=self.store.submit('chat',self.project,'draft_plan',self.original)

    def test_amendments_are_ordered_immutable_and_preserve_original(self):
        first=self.store.amend_project('chat',self.project,'Change sector count to 200.')
        second=self.store.amend_project('chat',self.project,'Change sector count to 300.')
        self.assertEqual(self.store.get(self.root)['prompt'],self.original)
        self.assertIn('200',self.store.get(first)['prompt'])
        revised=self.store.get(second)['prompt']
        self.assertEqual(revised,render_revision(self.original,['Change sector count to 200.','Change sector count to 300.']))
        self.assertEqual([x['ordinal'] for x in self.store.amendment_history(second)],[1,2])
        self.assertEqual(self.store.get(self.root)['state'],'cancelled')
        self.assertEqual(self.store.get(first)['state'],'cancelled')
        self.assertEqual(self.store.get(second)['state'],'pending')

    def test_old_approved_milestone_is_superseded_only_in_same_project_chat(self):
        job={'mode':'build','approval_key':f'milestone:{self.root}:1:0123456789abcdef',
             'chat_id':'chat','project':self.project}
        self.assertFalse(job_is_superseded(job,self.store))
        revised=self.store.amend_project('chat',self.project,'200 sectors')
        self.assertTrue(job_is_superseded(job,self.store))
        self.assertFalse(job_is_superseded(dict(job,chat_id='other'),self.store))
        self.assertFalse(job_is_superseded(dict(job,approval_key=f'milestone:{revised}:1:0123456789abcdef'),self.store))

    def test_ordinary_chat_does_not_revise_requirements(self):
        self.store.submit('chat',self.project,'chat','What if we had 200 sectors?')
        self.assertFalse(self.store.amendment_supersedes(self.root,'chat',self.project))
        self.assertEqual(self.store.amendment_history(self.root),[])

if __name__=='__main__':unittest.main()
