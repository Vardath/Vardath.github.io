"""v55 regression: an open inbox is not proof of neural handoff."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.dual_onnx import _object, deliberate_instruction
from deepthort_local.instruction_inbox import InstructionInbox, inbox_acceptance


class StrictNeuralTranslationTests(unittest.TestCase):
    def test_json_fence_allowed_but_prose_refused(self):
        self.assertEqual(_object('```json\n{"test":"yes"}\n```')['test'],'yes')
        for bad in ('Here is {"test":"yes"}', '```python\n{"test":"yes"}\n```',
                    'not JSON', '[{"test":"yes"}]'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):_object(bad)

    def test_janus_invalid_reply_is_retried_once_then_sentinel_checks(self):
        outputs=iter([
            'Certainly! This is your next step:',
            json.dumps({'next_action':'Inspect verified PE connection refs','verification':'Confirm real macro ids',
                        'scope_change':False,'reason':'Read-only preparation'}),
            json.dumps({'risk':'Low','test':'Compare exact XML macro names','requires_review':False})])
        history=[]
        def fake(messages,tokens):
            history.append((messages,tokens));return next(outputs)
        out=deliberate_instruction('Check game files',project='C:/x4mods',asker=fake)
        self.assertEqual(len(history),3)
        self.assertIn('required JSON schema',history[1][0][-1]['content'])
        self.assertIn('Inspect verified PE',out['next_action'])
        self.assertEqual(out['verification'],'Compare exact XML macro names')
        self.assertFalse(out['needs_review'])

    def test_sentinel_format_retry_is_non_authorizing(self):
        outputs=iter([
            json.dumps({'next_action':'Inspect PE weapons','verification':'Check tags','scope_change':False,'reason':'test'}),
            'The test is inspect files',
            json.dumps({'risk':'Unverified data','test':'Reject nonexistent macro','requires_review':True})])
        result=deliberate_instruction('Inspect references',project='C:/x4mods',asker=lambda m,t:next(outputs))
        self.assertTrue(result['needs_review'])

    def test_repeated_invalid_model_output_never_becomes_action(self):
        answers=[]
        def bad(messages,tokens):
            answers.append(messages);return 'not valid'
        with self.assertRaisesRegex(ValueError,'could not provide valid structured advice'):
            deliberate_instruction('Inspect references',project='C:/x4mods',asker=bad)
        self.assertEqual(len(answers),2)


class ReadonlyHandoffStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=InstructionInbox(Path(self.tmp.name)/'inbox.sqlite3')
        self.project=str(Path(self.tmp.name)/'output')

    def health(self):return inbox_acceptance(self.db.list(None))

    def test_empty_inbox_not_proof_of_handoff(self):
        self.assertEqual(self.health()['status'],'inconclusive')

    def test_real_failed_neural_reply_blocks_handoff(self):
        ident=self.db.enqueue(self.project,'chat','Private user instruction')
        self.db.claim();self.db.fail(ident,'Expecting value: line 1 column 1')
        result=self.health()
        self.assertEqual(result['status'],'blocked')
        self.assertEqual(result['evidence']['state_counts'],{'needs_review':1})
        self.assertNotIn('Private user instruction',str(result))
        self.assertNotIn('Expecting value',str(result))

    def test_completed_advice_is_not_mistaken_for_handoff(self):
        ident=self.db.enqueue(self.project,'chat','New requirement')
        self.db.claim();self.db.finish(ident,'JANUS','Sentinel','Inspect verified data','Check result')
        self.assertEqual(self.health()['status'],'inconclusive')
        self.assertEqual(self.db.next_guidance(self.project,'other'), '')
        self.assertEqual(self.health()['status'],'inconclusive')
        checkpoint=self.db.planning_checkpoint(self.project,'chat')
        prompt, offered=checkpoint.attach('Plan the next file',7500)
        self.assertEqual(self.health()['status'],'inconclusive')
        checkpoint.received(offered,'example-session',prompt,'A model reply')
        self.assertEqual(self.health()['status'],'passed')

    def test_review_and_pending_are_reported_without_false_success(self):
        ident=self.db.enqueue(self.project,'chat','Replace approved data')
        self.db.claim();self.db.finish(ident,'j','s','Require plan revision','User review',needs_review=True)
        self.assertEqual(self.health()['status'],'inconclusive')
        self.assertTrue(self.db.review(ident,allow_planning=True))
        self.assertEqual(self.health()['status'],'inconclusive')
        self.db.enqueue(self.project,'chat','Another request')
        self.assertEqual(self.health()['status'],'inconclusive')

if __name__=='__main__':unittest.main()
