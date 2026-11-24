"""Regression: new user instructions must never interrupt or authorize work."""
import tempfile
import unittest
from pathlib import Path
from deepthort_local.instruction_inbox import InstructionInbox, InstructionError


class InstructionInboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=str(self.root/'x4mods')
        self.store=InstructionInbox(self.root/'state'/'janus.sqlite3')

    def test_enqueue_claim_persist_original_exact_and_handoff(self):
        original='Please add docking collisions; do not interrupt the current weapon file.\n'*100
        ident=self.store.enqueue(self.project,'chatA',original)
        row=self.store.claim()
        self.assertEqual((row['id'],row['original'],row['state']),(ident,original,'pending'))
        self.assertTrue(self.store.finish(ident,'JANUS interpretation','Sentinel critique',
            'Review station docking entry locations','Verify PE elevator access'))
        store=InstructionInbox(self.store.path)
        self.assertEqual(store.list(self.project)[0]['original'],original)
        text=store.next_guidance(self.project,'chatA')
        self.assertIn('Review station docking',text)
        self.assertIn('JANUS NEXT-ACTION TRANSLATION',text)
        self.assertNotIn('Please add docking collisions',text)
        self.assertEqual(store.next_guidance(self.project,'chatA'),'')
        self.assertEqual(store.list(self.project)[0]['state'],'handed_to_planner')

    def test_project_chat_scoping_and_single_delivery(self):
        ident=self.store.enqueue(self.project,'a','Add an analysis step')
        self.store.claim();self.store.finish(ident,'a','b','Look up PE component','Confirm references')
        self.assertEqual(self.store.next_guidance(self.project,'b'),'')
        self.assertEqual(self.store.next_guidance(str(self.root/'other'),'a'),'')
        self.assertTrue(self.store.next_guidance(self.project,'a'))
        self.assertEqual(self.store.next_guidance(self.project,'a'),'')

    def test_interrupted_inference_is_safe_to_reinterpret(self):
        ident=self.store.enqueue(self.project,'a','Make one plan revision')
        self.assertEqual(self.store.claim()['id'],ident)
        self.assertEqual(self.store.claim(),None)
        recovered=InstructionInbox(self.store.path)
        self.assertEqual(recovered.claim()['id'],ident)

    def test_scope_changes_need_review_and_are_not_preapproved(self):
        ident=self.store.enqueue(self.project,'a','Change every approved ship file')
        self.store.claim();self.store.finish(ident,'j','s','Replace turret design','Check player approval',needs_review=True)
        self.assertEqual(self.store.next_guidance(self.project,'a'),'')
        self.assertTrue(self.store.review(ident,allow_planning=True))
        self.assertTrue(self.store.next_guidance(self.project,'a'))
        self.assertFalse(self.store.review(ident,allow_planning=True))

    def test_invalid_and_cancelled_instructions(self):
        with self.assertRaises(InstructionError):self.store.enqueue('', 'a','b')
        with self.assertRaises(InstructionError):self.store.enqueue(self.project,'','b')
        with self.assertRaises(InstructionError):self.store.enqueue(self.project,'a','')
        ident=self.store.enqueue(self.project,'a','Do not install anything')
        self.assertTrue(self.store.dismiss(ident))
        self.assertIsNone(self.store.claim())
        self.assertEqual(self.store.list(self.project)[0]['state'],'dismissed')

    def test_failed_inference_keeps_original_visible(self):
        ident=self.store.enqueue(self.project,'chat','New requirement')
        self.store.claim();self.assertTrue(self.store.fail(ident,'Worker reset'))
        row=self.store.list(self.project)[0]
        self.assertEqual((row['original'],row['state']),('New requirement','needs_review'))
        self.assertEqual(self.store.next_guidance(self.project,'chat'),'')
        self.assertFalse(self.store.review(ident,allow_planning=True))
        self.assertTrue(self.store.retry_interpretation(ident))
        self.assertEqual(self.store.claim()['id'],ident)

if __name__=='__main__':unittest.main()
