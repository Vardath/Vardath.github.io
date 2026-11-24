import tempfile
import unittest
from pathlib import Path
from deepthort_local.reasoning_council import ReasoningCouncil
from deepthort_local.recovery_council import reframe, select_source_section, append_guidance


class FakeModel:
    def __init__(self,answers):
        self.answers=iter(answers)
        self.calls=[]
    def chat(self,session,prompt,max_tokens):
        self.calls.append((session,prompt))
        return next(self.answers)


class RecoveryCouncilTests(unittest.TestCase):
    def test_retranslation_review_cache_and_changed_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            council=ReasoningCouncil(Path(t)/'council.sqlite')
            original='Keep the original hull. Verify clearance and docking.'
            args=dict(session='work',project=t,original=original,
                      source_section=original,focus='docking',
                      observed='geometry saved, docking untested',feedback='collision',revision=1)
            model=FakeModel(['Inspect docking clearance without changing hull. Test landing.',
                             'ACCEPT\nPreserves hull and requests a test.'])
            review=reframe(council,model,**args)
            self.assertTrue(review['accepted'])
            self.assertFalse(review['verified'])
            self.assertEqual(len(model.calls),2)
            self.assertIn(original,model.calls[0][1])
            self.assertIn(original,model.calls[1][1])
            self.assertIn('geometry saved',model.calls[1][1])
            cached=FakeModel([])
            self.assertEqual(review,reframe(council,cached,**args))
            self.assertEqual(cached.calls,[])
            rejected=reframe(council,FakeModel(['Delete the hull','REJECT\nScope drift']),
                              **dict(args,revision=2))
            self.assertFalse(rejected['accepted'])
            self.assertNotEqual(rejected['evidence_sha'],review['evidence_sha'])
            self.assertEqual(append_guidance('original prompt',rejected,7500),'original prompt')
            self.assertIn(review['janus'],append_guidance('original prompt',review,7500))
            self.assertEqual(append_guidance('original prompt',review,30),'original prompt')

    def test_section_selection_preserves_exact_text(self):
        source='first feature\n'*400+'docking clearance must remain unobstructed\n'*10
        selected=select_source_section(source,'docking clearance')
        self.assertIn(selected,source)
        self.assertLessEqual(len(selected),3200)
        self.assertIn('docking clearance',selected)

    def test_malformed_sentinel_cannot_accept(self):
        with tempfile.TemporaryDirectory() as t:
            council=ReasoningCouncil(Path(t)/'c.sqlite')
            result=reframe(council,FakeModel(['Implement check','I think ACCEPT is appropriate']),
                session='x',project=t,original='Verify output',source_section='Verify output',
                focus='output',observed='test failed',feedback='wrong result',revision=0)
            self.assertFalse(result['accepted'])


if __name__=='__main__':
    unittest.main()
