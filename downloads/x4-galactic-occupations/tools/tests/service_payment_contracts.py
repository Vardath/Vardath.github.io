#!/usr/bin/env python3
"""Execute real service-invoice XML with refused/partial mocked native credits."""
import copy
import unittest
from crystal_commerce_contracts import VM, FACTION, PLAYER, S, xml

class ServiceVM(VM):
    def __init__(self,job=1):
        super().__init__()
        self.state.update(vgo_job=job,vgo_serial=17,vgo_verified=True,
                          vgo_reward=1200000 if job==1 else 800000,vgo_rewardfaction=FACTION)
    def expr(self,text):
        text=text.replace('player.entity.$vgo_objects?','true').replace(S+'?','true')
        return super().expr(text)

class ServicePayments(unittest.TestCase):
    def test_verified_escort_and_patrol_pay_exactly_once(self):
        for job,amount in [(1,1200000),(12,800000)]:
            v=ServiceVM(job);before=v.money
            self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.money-before,amount)
            self.assertEqual(v.receipts,[amount]);self.assertEqual(v.get('vgo_paid'),17)
            self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.money-before,amount)
            self.assertEqual(len(v.reputation),1)
    def test_rejected_payment_keeps_claim_without_paid_marker_or_receipt(self):
        v=ServiceVM();v.credit_limit=0
        self.assertFalse(v.run('vardath.go.reward'));self.assertEqual(v.get('vgo_service_due'),1200000)
        self.assertNotIn('vgo_paid',v.state);self.assertEqual(v.receipts,[]);self.assertEqual(v.reputation,[])
    def test_partial_payment_reload_retries_only_the_unpaid_balance(self):
        v=ServiceVM();v.credit_limit=300000
        self.assertFalse(v.run('vardath.go.reward'));self.assertEqual(v.get('vgo_service_due'),900000)
        v.state=copy.deepcopy(v.state);v.credit_limit=None;v.age+=60
        self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.reward_requests,[1200000,900000])
        self.assertEqual(sum(v.receipts),1200000);self.assertEqual(v.get('vgo_paid'),17)
    def test_failed_payment_retries_are_throttled(self):
        v=ServiceVM();v.credit_limit=0;self.assertFalse(v.run('vardath.go.reward'))
        self.assertFalse(v.run('vardath.go.reward'));self.assertEqual(len(v.reward_requests),1)
    def test_changed_minimum_does_not_erase_an_already_earned_claim(self):
        v=ServiceVM();v.credit_limit=0;v.run('vardath.go.reward')
        v.state.update(vgo_minreward=999999999,vgo_reward=0,vgo_verified=False)
        v.age+=60;v.credit_limit=None
        self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.receipts,[1200000])
    def test_direct_orders_or_lost_ownership_cannot_settle_or_erase_claim(self):
        for attr in ['direct','occupied','owned']:
            v=ServiceVM();v.credit_limit=0;v.run('vardath.go.reward');v.age+=60
            setattr(v,attr,False if attr=='owned' else True);v.credit_limit=None
            self.assertFalse(v.run('vardath.go.reward'));self.assertEqual(v.get('vgo_service_due'),1200000)
            self.assertEqual(v.receipts,[])
    def test_unverified_work_never_creates_payment_or_reputation(self):
        v=ServiceVM();v.state['vgo_verified']=False
        self.assertFalse(v.run('vardath.go.reward'));self.assertEqual(v.reward_requests,[]);self.assertEqual(v.reputation,[])
    def test_successful_morale_improvement_grants_small_rep_and_no_invented_fee(self):
        v=ServiceVM(9);v.state['vgo_reward']=0
        self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.reward_requests,[])
        self.assertEqual(v.reputation,[0.0001]);v.run('vardath.go.reward');self.assertEqual(v.reputation,[0.0001])
    def test_existing_claim_retry_precedes_worker_standby_and_new_work(self):
        actions=list(xml('vardath.go.worker').find('attention/actions'))
        claim=next(i for i,n in enumerate(actions) if n.tag=='do_if' and 'service_due gt' in n.get('value',''))
        standby=next(i for i,n in enumerate(actions) if n.tag=='do_if' and '$done and not $repeat' in n.get('value',''))
        self.assertLess(claim,standby)
        self.assertIsNotNone(actions[claim].find("run_script[@result='$settled']"))

if __name__=='__main__':unittest.main(verbosity=2)
