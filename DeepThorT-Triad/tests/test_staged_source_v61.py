import unittest
from deepthort_local.staged_source import stage_existing,source_ranges,validate_source,StageError,sha

class Council:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def _run(self,client,**kw):
        self.prompts.append(kw['prompt'])
        return next(self.answers)

class Model:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def chat(self,session,prompt,max_tokens):
        self.prompts.append(prompt)
        return next(self.answers)

class StagedSourceTests(unittest.TestCase):
    def test_preserves_exact_unselected_ranges(self):
        source='sectors = 100\r\n'+'# unchanged\r\n'*112
        spans=source_ranges(source)
        self.assertGreater(len(spans),1)
        model=Model([spans[0][2].replace('100','200')])
        council=Council(['EDIT\nIncrease sector count']+['KEEP']*(len(spans)-1))
        reviewed=[]
        result=stage_existing(model,council,model,session='build',path='map.py',
            goal='Increase sectors to 200',scope='Space game with mining and 200 sectors.',
            master_sha=sha('master'),source=source,review=lambda p,k:reviewed.append((p,k)))
        self.assertEqual(result['source'],source.replace('100','200'))
        self.assertEqual(result['before_sha256'],sha(source))
        self.assertEqual(result['changed_ranges'],1)
        self.assertEqual([kind for _,kind in reviewed],['plan','code'])
        self.assertIn('200',reviewed[-1][0])

    def test_rejected_change_retries_without_accepting_bad_source(self):
        model=Model(['sectors = 50','sectors = 200'])
        council=Council(['EDIT\nSet 200 sectors'])
        def review(proposal,kind):
            if kind=='code' and '+sectors = 50' in proposal:raise ValueError('Wrong count')
        result=stage_existing(model,council,model,session='build',path='map.py',
            goal='Increase sectors to 200',scope='Space game.',master_sha=sha('master'),
            source='sectors = 100\n',review=review)
        self.assertEqual(result['source'],'sectors = 200\n')
        self.assertIn('Wrong count',model.prompts[1])

    def test_noop_and_invalid_syntax_do_not_complete(self):
        for decision,answers in [('KEEP',[]),('EDIT\nFix count',['sectors = ('])]:
            model=Model(answers)
            with self.assertRaises(StageError):
                stage_existing(model,Council([decision]),model,session='build',path='map.py',
                    goal='Change count',scope='Space game.',master_sha=sha('master'),
                    source='sectors = 100\n',review=lambda p,k:None)

    def test_long_line_and_invalid_xml_are_refused(self):
        with self.assertRaises(StageError):source_ranges('x'*1401)
        with self.assertRaises(StageError):validate_source('ship.xml','<ship>')
        self.assertTrue(validate_source('ship.xml','<ship/>'))

if __name__=='__main__':unittest.main()
