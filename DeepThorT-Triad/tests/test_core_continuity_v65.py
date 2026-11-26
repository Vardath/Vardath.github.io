"""Progress changes preserve core thought, never stale outward acceptance."""
import json
import unittest
from deepthort_local.core_deliberation import ORDER,step,choose,snapshot,select_lane
from deepthort_local.workflow_attention import advice
import test_workflow_attention_v59 as prior

class Counsel:
    def __init__(self):self.calls=[]
    def request(self,**kw):
        self.calls.append(kw)
        core=kw['core_name']
        if core in ('Front','Interface'):
            return json.dumps({'kind':'advice','finding':'Check ownership','guidance':'Inspect actual saved owner field'})
        return json.dumps({'faculties':{str(n):core+' reading' for n in range(1,8)},
                           'conclusion':core+' independent reading','check':'Inspect actual source'})

class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.f=prior.AttentionTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.jobs=self.f.f.jobs;self.id=self.f.f.job;self.c=Counsel()
    def turn(self):return step(self.jobs.path,'janus',self.c,lambda:False)
    def progress(self):
        self.jobs.set_step(self.jobs.steps(self.id)[0]['id'],'saved','Produced')
    def test_live_advice_cannot_starve_core_opportunities(self):
        self.assertEqual(select_lane(True,True,''),'ordinary')
        self.assertEqual(select_lane(True,True,'ordinary'),'core')
        self.assertEqual(select_lane(True,True,'core'),'ordinary')
        self.assertEqual(select_lane(False,True,'core'),'core')
        self.assertEqual(select_lane(True,False,'ordinary'),'ordinary')
    def test_expired_round_can_restart(self):
        import sqlite3
        self.turn()
        before=snapshot(self.jobs.path,'janus')
        with sqlite3.connect(self.jobs.path.parent/'janus-counsel.sqlite3') as db:
            db.execute("UPDATE core_deliberation_v65 SET updated=0")
        self.assertIsNotNone(choose(self.jobs.path,'janus'))
        self.turn()
        after=snapshot(self.jobs.path,'janus')
        self.assertEqual(after['round_key'],before['round_key'])
        self.assertEqual(after['turn_count'],1)
    def test_progress_retains_initial_readings_then_fresh_revision(self):
        self.turn()
        before=snapshot(self.jobs.path,'janus')
        self.progress()
        after=snapshot(self.jobs.path,'janus')
        self.assertEqual(after['round_key'],before['round_key'])
        self.assertNotEqual(after['key'],before['key'])
        self.assertFalse(after['cores']['Evidence']['current'])
        for _ in range(len(ORDER)-2):self.assertIsNone(self.turn())
        final=self.turn()
        self.assertIsNotNone(final)
        self.assertTrue(snapshot(self.jobs.path,'janus')['current_complete'])
        packet=__import__('deepthort_local.workflow_attention',fromlist=['_scope'])._scope(self.jobs.path,self.id)
        self.assertIn('integrated core advisory',advice(self.jobs.path,self.id,self.f.f.original,packet['focus']))
    def test_mixed_revision_remains_internal_and_next_round_recalls(self):
        for _ in range(8):self.turn()
        old=snapshot(self.jobs.path,'janus')['round_key']
        self.progress()
        for _ in range(len(ORDER)-8):self.assertIsNone(self.turn())
        snap=snapshot(self.jobs.path,'janus')
        self.assertTrue(snap['complete']);self.assertFalse(snap['current_complete'])
        self.assertIsNotNone(choose(self.jobs.path,'janus'))
        self.turn()
        self.assertNotEqual(snapshot(self.jobs.path,'janus')['round_key'],old)
        prior=json.loads(self.c.calls[-1]['evidence'])['historical_hypothesis']
        self.assertEqual(prior['status'],'historical_hypothesis_not_current_evidence')
        self.jobs.cancel(self.id)
        self.assertFalse(snapshot(self.jobs.path,'janus'))
        self.assertIsNone(choose(self.jobs.path,'janus'))
if __name__=='__main__':unittest.main()
