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

    def test_large_revision_requires_every_delta_verdict(self):
        with tempfile.TemporaryDirectory() as t:
            c=ReasoningCouncil(Path(t)/'c.sqlite')
            original='Build a space game. '+'a'*3500+' Change sectors. Remove mining.'
            code='def mine(): return 1'
            delta={'current_spec_sha256':sha(original),'prior_spec_sha256':sha('old'),
                   'sections':[{'ordinal':1,'part':1,'parts':1,'text':'Change sectors.','sha256':sha('Change sectors.')},
                               {'ordinal':2,'part':1,'parts':1,'text':'Remove mining.','sha256':sha('Remove mining.')}]}
            class Sequence:
                def __init__(self):self.prompts=[]
                def chat(self,session,prompt,max_tokens):
                    self.prompts.append(prompt)
                    return 'KEEP' if len(self.prompts)==1 else 'REVISE'
            m=Sequence()
            args=dict(project=t,session='build',step={'path':'mining.py','description':'Mining'},
                candidate={'code':code,'source_sha256':sha(code),'prior_job_id':1,'prior_step_id':2,
                           'path':'mining.py','delta':delta})
            self.assertIsNone(review_retention(c,m,original=original,**args))
            self.assertEqual(len(m.prompts),2)
            self.assertIn('Remove mining.',m.prompts[1])
            self.assertIn(code,m.prompts[1])

if __name__=='__main__':unittest.main()
