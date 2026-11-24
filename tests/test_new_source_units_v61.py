import unittest
from deepthort_local.staged_source import stage_new_python,StageError,sha

class Council:
    def __init__(self,answers):self.answers=iter(answers)
    def _run(self,client,**kw):return next(self.answers)

class Model:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def chat(self,session,prompt,max_tokens):
        self.prompts.append(prompt)
        return next(self.answers)

class NewUnitTests(unittest.TestCase):
    def args(self,model,council,review):
        return dict(client=model,council=council,advisor=model,session='build',
                    path='map.py',goal='Implement sectors and count them',
                    scope='Space game with sectors.',master_sha=sha('master'),review=review)

    def test_assembled_units_observe_prior_interface(self):
        m=Model(['def sectors():\n    return [1,2]','def count():\n    return len(sectors())'])
        c=Council(['{"units":["Implement sectors","Count sectors"]}'])
        reviews=[]
        result=stage_new_python(**self.args(m,c,lambda p,k:reviews.append(k)))
        self.assertIn('def sectors():',m.prompts[1])
        self.assertEqual(result['before_sha256'],None)
        self.assertIn('def count():',result['source'])
        self.assertEqual(reviews,['plan','code','code','code'])
        self.assertEqual(result['after_sha256'],sha(result['source']))

    def test_duplicate_binding_is_corrected(self):
        m=Model(['def sectors():\n    return [1,2]',
                 'def sectors():\n    return 0',
                 'def count():\n    return len(sectors())'])
        c=Council(['{"units":["Implement sectors","Count sectors"]}'])
        result=stage_new_python(**self.args(m,c,lambda p,k:None))
        self.assertEqual(result['source'].count('def sectors()'),1)
        self.assertIn('redefines prior',m.prompts[2])

    def test_incomplete_unit_is_not_returned(self):
        m=Model(['def sectors():\n    return [1,2]','def count(', 'def count('])
        c=Council(['{"units":["Implement sectors","Count sectors"]}'])
        with self.assertRaises(StageError):
            stage_new_python(**self.args(m,c,lambda p,k:None))

if __name__=='__main__':unittest.main()
