import tempfile
import unittest
from pathlib import Path
from deepthort_local.reasoning_council import ReasoningCouncil
from deepthort_local.specification_guard import inspect_proposal,review_source
from deepthort_local.agent_plan import PlanError

class Model:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def chat(self,session,prompt,max_tokens):
        self.prompts.append(prompt)
        return next(self.answers)

class SpecificationGuardTests(unittest.TestCase):
    def test_domain_substitution_and_legitimate_infrastructure(self):
        with tempfile.TemporaryDirectory() as t:
            c=ReasoningCouncil(Path(t)/'c.sqlite')
            original='Build a space game with sectors and space stations.'
            args=dict(original=original,project=t,session='game',focus='World map')
            m=Model(['REJECT\nRailway game changes the requested domain.'])
            result=inspect_proposal(c,m,proposal='Design railway routes and train stations',**args)
            self.assertFalse(result['accepted'])
            self.assertIn(original,m.prompts[0])
            self.assertIn('railway routes',m.prompts[0])
            m2=Model(['ACCEPT\nSpace station docking fits the requested game.'])
            result=inspect_proposal(c,m2,proposal='Implement docking at space stations',**args)
            self.assertTrue(result['accepted'])
            self.assertFalse(result['verified'])
            cached=Model([])
            self.assertEqual(result,inspect_proposal(c,cached,proposal='Implement docking at space stations',**args))
            self.assertEqual(cached.prompts,[])

    def test_long_original_root_and_relevant_requirement(self):
        original='Create a space strategy game.\n'+('economic rule\n'*400)+'Alien diplomacy and docking.'
        text=review_source(original,'docking','Alien diplomacy and docking.')
        self.assertIn('Create a space strategy game.',text)
        self.assertIn('Alien diplomacy and docking.',text)
        with self.assertRaises(PlanError):
            review_source(original,'docking','Invented requirement')

    def test_every_proposal_chunk_and_ambiguous_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            c=ReasoningCouncil(Path(t)/'c.sqlite')
            m=Model(['ACCEPT','Possibly acceptable'])
            result=inspect_proposal(c,m,original='Build a space game',project=t,session='code',
                focus='Game logic',proposal='a'*2200+'railway logic',kind='code')
            self.assertFalse(result['accepted'])
            self.assertEqual(len(m.prompts),2)
            self.assertIn('railway logic',m.prompts[1])

if __name__=='__main__':
    unittest.main()
