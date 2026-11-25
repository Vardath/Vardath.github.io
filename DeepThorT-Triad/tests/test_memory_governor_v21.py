import unittest
from deepthort_local.memory_governor import parse_selection,fit,HEADER
from deepthort_local.memory_governor_probe import exercise
class MemoryGovernorTests(unittest.TestCase):
    def test_integration(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
    def test_exact_selection(self):
        self.assertEqual(parse_selection('{"keep":["N1"],"reason":"Relevant"}',{'N1'}),['N1'])
        for answer in ('{"keep":["N2"],"reason":"Invented"}','{"keep":["N1","N1"],"reason":"Duplicate"}',
                       '{"keep":["N1"],"reason":""}','{"keep":["N1"],"reason":"Fine","extra":"instruction"}'):
            with self.assertRaises(ValueError):parse_selection(answer,{'N1'})
    def test_complete_rows_only(self):
        text=HEADER+'{"id":"N1","observation":"first"}\n{"id":"N2","observation":"second"}\n'
        self.assertEqual(fit(text,len(HEADER)+35),HEADER+'{"id":"N1","observation":"first"}\n')
        self.assertEqual(fit(text,10),'')
