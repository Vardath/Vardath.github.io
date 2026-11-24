import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.amendment_context import historical_context,attach_history,predecessor_steps

class NoHierarchy:
    def has_roadmap(self,ident):return False
class NoIndex:
    def merged_steps(self,*args):raise ValueError('No index')

class AmendmentContextTests(unittest.TestCase):
    def test_carry_forward_does_not_inherit_approval(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            store=ConversationStore(root/'conversations.sqlite3')
            first=store.submit('chat',t,'draft_plan','Build a space game with mining.')
            store.change(first,'running','planning')
            steps=[{'path':'game.py','description':'Space sectors and mining'}]
            store.save_draft(first,steps)
            store.change(first,'responded','draft ready')
            second=store.amend_project('chat',t,'Add diplomacy')
            third=store.amend_project('chat',t,'Add trade')
            self.assertEqual(predecessor_steps(store,NoIndex(),NoHierarchy(),third),steps)
            self.assertIsNone(store.latest_draft('chat',t))
            self.assertEqual(store.get(first)['prompt'],'Build a space game with mining.')
            (root/'game.py').write_text('existing game code',encoding='utf-8')
            context=historical_context(t,steps,'mining')
            self.assertIn('exists sha256=',context)
            self.assertIn('Space sectors and mining',context)
            self.assertIn('not approval',context)
            self.assertEqual(attach_history('full specification',t,steps,max_chars=30),'full specification')

    def test_attachment_history_is_cumulative(self):
        with tempfile.TemporaryDirectory() as t:
            store=ConversationStore(Path(t)/'conversations.sqlite3')
            first=store.submit('chat',t,'draft_plan','Game',attachments=['a.txt'])
            second=store.amend_project('chat',t,'Add features',attachments=['b.txt'])
            third=store.amend_project('chat',t,'Change count',attachments=['b.txt','c.txt'])
            import json
            self.assertEqual(json.loads(store.get(third)['attachments']),['a.txt','b.txt','c.txt'])

    def test_revision_context_has_latest_correction_and_relevant_prior(self):
        from deepthort_local.specification_amendments import render_revision,sha,revision_matches,PRECEDENCE,PRECEDENCE_CHECKPOINT
        from deepthort_local.amendment_context import revision_context,attach_revision_context
        original='Build space game with mining.'
        amendments=['Change mining equipment.', 'Add pirate factions.', 'Increase sectors to 200.']
        effective=render_revision(original,amendments)
        history=[{'ordinal':n,'amendment':a,'amendment_sha256':sha(a)}
                 for n,a in enumerate(amendments,1)]
        note=revision_context(effective,history,'mining sectors',max_chars=500)
        self.assertIn('Increase sectors to 200.',note)
        self.assertIn('Change mining equipment.',note)
        self.assertLess(note.index('Amendment 1'),note.index('Amendment 3'))
        self.assertTrue(revision_matches(effective.replace(PRECEDENCE,PRECEDENCE_CHECKPOINT,1),original,amendments))
        self.assertEqual(attach_revision_context('unchanged source',effective,history,max_chars=30),'unchanged source')
        history[-1]['amendment_sha256']='corrupt'
        with self.assertRaises(ValueError):revision_context(effective,history)

if __name__=='__main__':unittest.main()
