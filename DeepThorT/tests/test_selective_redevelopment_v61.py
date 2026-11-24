import tempfile
import unittest
from pathlib import Path
from deepthort_local.reasoning_council import ReasoningCouncil,sha
from deepthort_local.selective_redevelopment import review_retention

class Model:
    def __init__(self,response):self.response=response;self.prompts=[]
    def chat(self,session,prompt,max_tokens):
        self.prompts.append(prompt);return self.response

class RetentionTests(unittest.TestCase):
    def test_keep_requires_explicit_verdict_and_binds_current_spec(self):
        with tempfile.TemporaryDirectory() as t:
            c=ReasoningCouncil(Path(t)/'c.sqlite')
            step={'path':'mining.py','description':'Mine ore'}
            source='def mine(): return "ore"'
            candidate={'code':source,'source_sha256':sha(source),'prior_job_id':1,
                       'prior_step_id':2,'path':'mining.py'}
            args=dict(project=t,session='build',step=step,candidate=candidate)
            m=Model('KEEP\nMining unchanged')
            result=review_retention(c,m,original='Space game. Change sector count.',**args)
            self.assertEqual(result['source_sha256'],sha(source))
            self.assertIn(source,m.prompts[0])
            self.assertIn('Change sector count',m.prompts[0])
            m2=Model('REVISE\nMining removed')
            self.assertIsNone(review_retention(c,m2,original='Space game. Remove mining.',**args))
            self.assertEqual(len(m2.prompts),1)
            self.assertIsNone(review_retention(c,Model('Maybe KEEP'),original='Space game. Change mining.',**args))

    def test_incomplete_context_or_changed_source_cannot_certify_reuse(self):
        with tempfile.TemporaryDirectory() as t:
            c=ReasoningCouncil(Path(t)/'c.sqlite')
            m=Model('KEEP')
            args=dict(project=t,session='build',step={'path':'a.py','description':'Feature'},
                candidate={'code':'x','source_sha256':sha('x'),'prior_job_id':1,'prior_step_id':2,'path':'a.py'})
            self.assertIsNone(review_retention(c,m,original='a'*3001,**args))
            args['candidate']['code']='changed'
            self.assertIsNone(review_retention(c,m,original='Feature',**args))
            self.assertEqual(m.prompts,[])

if __name__=='__main__':unittest.main()
