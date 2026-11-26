"""Separate resident-role calls across the real recursive society topology."""
import json
import unittest
from deepthort_local.core_deliberation import ORDER,step,choose,snapshot,_bounded_input
from deepthort_local.janus_cognition import SPECIALISTS,process_society,SenseFrame
import test_workflow_attention_v59 as previous

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.f=previous.AttentionTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.jobs=self.f.f.jobs
    def test_context_keeps_all_peer_conclusions_under_escaped_input_pressure(self):
        peers={n:{'conclusion':'x'*180,'check':'y'*120,'faculties':{}} for n in SPECIALISTS}
        raw=_bounded_input({'observed':'"\\'*3000,'peers':peers})
        self.assertLessEqual(len(raw),4200)
        self.assertEqual(set(json.loads(raw)['peers']),set(SPECIALISTS))
        self.assertEqual(json.loads(raw)['peers']['Evidence']['conclusion'],'x'*180)
    def test_independent_conclusions_revision_and_front_only_expression(self):
        class Counsel:
            def __init__(self):self.calls=[]
            def request(self,**kw):
                self.calls.append(kw);core=kw['core_name']
                if core in ('Front','Interface'):
                    return json.dumps({'kind':'advice','finding':'Check the recorded interface','guidance':'Verify exact source before integration'})
                return json.dumps({'faculties':{str(n):core+' reading' for n in range(1,8)},
                    'conclusion':core+' '+kw['core_phase']+' conclusion','check':'Check actual source'})
        c=Counsel();result=None
        self.assertIsNotNone(choose(self.jobs.path,'janus'), 'Fresh ledger must admit a first core turn')
        for i in range(len(ORDER)):
            result=step(self.jobs.path,'janus',c,lambda:False)
            self.assertEqual(snapshot(self.jobs.path,'janus').get('turn_count'),i+1, f'Core turn {i+1} must persist')
            if i<len(ORDER)-1:self.assertIsNone(result)
        self.assertIsNotNone(result)
        self.assertEqual([(x['core_name'],x['core_phase']) for x in c.calls],list(ORDER))
        for i,call in enumerate(c.calls[:7]):
            self.assertEqual(set(json.loads(call['evidence'])),{'observed'})
        for call in c.calls[7:14]:
            data=json.loads(call['evidence'])
            self.assertEqual(set(data['peers']),set(SPECIALISTS)-{call['core_name']})
            self.assertIn('own_prior',data)
        for call in c.calls[14:16]:self.assertEqual(set(json.loads(call['evidence'])['peers']),set(SPECIALISTS))
        self.assertEqual(set(json.loads(c.calls[16]['evidence'])['peers']),{'Left','Right'})
        self.assertEqual(set(json.loads(c.calls[17]['evidence'])),{'Front'})
        self.assertIsNone(choose(self.jobs.path,'janus'))
        snap=snapshot(self.jobs.path,'janus');self.assertTrue(snap['complete'])
        self.assertEqual(len(snap['cores']),11)
        state=process_society(society='janus',observation={},frames=[SenseFrame('runtime','test','Observed')],
            focus='test',decision='observe',neural=snap)
        self.assertEqual(state['cores']['Logic']['neural_readout']['phase'],'revise')
        self.assertEqual(state['cores']['Interface']['input_sources'],['Front'])
        self.assertFalse(snapshot(self.jobs.path,'sentinel'))
        step(self.jobs.path,'sentinel',c,lambda:False)
        self.assertEqual(snapshot(self.jobs.path,'sentinel')['turn_count'],1)
        self.jobs.cancel(self.f.f.job)
        self.assertFalse(snapshot(self.jobs.path,'janus'))
        self.assertIsNone(choose(self.jobs.path,'sentinel'))
if __name__=='__main__':unittest.main()
