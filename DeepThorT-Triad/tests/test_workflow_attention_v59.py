"""Separate permanent society reasoning while software work is active."""
import json
import unittest
from deepthort_local.janus_counsel import LocalCounsel
from deepthort_local.workflow_attention import choose,finish,advice,run_once
import test_memory_duty_v47 as previous

def response(finding='Ownership can be lost during deserialization.'):
    return json.dumps({'kind':'advice','finding':finding,'guidance':'Check the actual saved owner field against the approved requirement.'})

class AttentionTests(unittest.TestCase):
    def setUp(self):
        self.f=previous.MemoryDutyTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.jobs.change(self.f.job,'running','Working on the approved code')
    def test_separate_role_leases(self):
        c=LocalCounsel(self.f.root/'janus-counsel.sqlite3')
        self.assertTrue(c._acquire('janus:1'))
        self.assertTrue(c._acquire('sentinel:1'))
        self.assertFalse(c._acquire('janus:2'))
        c._release('janus:1')
        self.assertTrue(c._acquire('janus:2'))
        self.assertFalse(c._acquire('sentinel:2'))
    def test_both_societies_work_independently_during_production(self):
        calls=[]
        class Counsel:
            def request(self,**kw):
                calls.append(kw);return response()
        c=Counsel()
        one=run_once(self.f.jobs.path,'janus',c,lambda:False)
        two=run_once(self.f.jobs.path,'sentinel',c,lambda:False)
        self.assertEqual(one['key'],two['key'])
        self.assertFalse(one['authority']);self.assertFalse(two['verified'])
        self.assertEqual([x['society'] for x in calls],['janus','sentinel'])
        self.assertTrue(all(x['initiative'] for x in calls))
        self.assertIn(self.f.original,calls[0]['evidence'])
        self.assertIn('Independent peer findings',calls[1]['evidence'])
        self.assertIn('Ownership can be lost',calls[1]['evidence'])
        self.assertIsNone(choose(self.f.jobs.path,'janus'))
        self.assertIsNone(choose(self.f.jobs.path,'sentinel'))
        focus=one['identity']['focus']
        args=(self.f.jobs.path,self.f.job,self.f.original,focus)
        self.assertIn('JANUS independent',advice(*args,budget=1200))
        self.assertIn('SENTINEL independent',advice(*args,budget=1200))
        self.assertNotIn('SENTINEL independent',advice(*args,recipient='sentinel'))
        self.assertEqual(self.f.jobs.get(self.f.job)['state'],'running')
        self.f.jobs.set_step(self.f.jobs.steps(self.f.job)[0]['id'],'saved','Produced')
        self.assertEqual(advice(*args),'')
        self.assertIsNotNone(choose(self.f.jobs.path,'janus'))
    def test_no_finding_and_stale_or_cancelled_scope(self):
        packet=choose(self.f.jobs.path,'janus')
        empty=json.dumps({'kind':'none','finding':'','guidance':''})
        result=finish(self.f.jobs.path,'janus',packet,empty)
        self.assertIsNotNone(result)
        self.assertIsNone(choose(self.f.jobs.path,'janus'))
        self.assertEqual(advice(self.f.jobs.path,self.f.job,self.f.original,packet['focus']),'')
        self.f.jobs.cancel(self.f.job)
        self.assertIsNone(finish(self.f.jobs.path,'sentinel',packet,response()))
        self.assertIsNone(choose(self.f.jobs.path,'sentinel'))
if __name__=='__main__':unittest.main()
