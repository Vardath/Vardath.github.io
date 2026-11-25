import unittest
from deepthort_local.reviewed_generation import generate_reviewed
from deepthort_local.specification_guard import SpecificationRejected

class Model:
    def __init__(self,replies):
        self.replies=iter(replies)
        self.calls=[]
    def chat(self,session,prompt,max_tokens):
        self.calls.append((session,prompt))
        return next(self.replies)

class ReviewedGenerationTests(unittest.TestCase):
    def test_corrected_candidate_preserves_original_and_feedback(self):
        model=Model(['train game','space game'])
        checked=[]
        def review(text):
            checked.append(text)
            if text!='space game':raise SpecificationRejected('Railway substitution; implement sectors.')
        result=generate_reviewed(model,'world','Build a space game with sectors.',review)
        self.assertEqual(result,'space game')
        self.assertEqual(checked,['train game','space game'])
        self.assertIn('Build a space game with sectors.',model.calls[1][1])
        self.assertIn('Railway substitution',model.calls[1][1])
        self.assertNotEqual(model.calls[0][0],model.calls[1][0])

    def test_repeated_rejection_is_bounded(self):
        model=Model(['train','train','train'])
        checked=[]
        def review(text):
            checked.append(text)
            raise SpecificationRejected('Off task')
        with self.assertRaises(SpecificationRejected):
            generate_reviewed(model,'world','Build a space game.',review)
        self.assertEqual(len(model.calls),3)
        self.assertEqual(checked,['train'])

    def test_transport_failure_is_not_a_semantic_retry(self):
        model=Model(['space'])
        def review(text):raise OSError('Local worker disconnected')
        with self.assertRaises(OSError):
            generate_reviewed(model,'world','Build a space game.',review)
        self.assertEqual(len(model.calls),1)

    def test_context_is_never_truncated(self):
        model=Model(['train'])
        def review(text):raise SpecificationRejected('Off task')
        with self.assertRaisesRegex(SpecificationRejected,'context space'):
            generate_reviewed(model,'world','a'*7490,review)
        self.assertEqual(len(model.calls),1)

if __name__=='__main__':unittest.main()
