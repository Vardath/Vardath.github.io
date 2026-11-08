#!/usr/bin/env python3
"""Execute paid-visit recovery without depending on the AI caller receiving a return.

Native NPC movement and room placement remain mocked; this is not live X4.
"""
import copy
import re
import unittest
from crystal_commerce_contracts import Obj, NULL, BUYER, S, WARES, MOD, xml
from crystal_retail_contracts import RetailVM, ROOT
from passenger_completion_contracts import Seq

class ReturnVM(RetailVM):
    def __init__(self,stock=None):
        super().__init__(stock);self.saved_registry=Seq([self.ship]);self.drop_result=False
    def expr(self,text):
        text=text.replace('md.VGO_State.Init.$Ships','$saved_registry')
        self.vars['saved_registry']=self.saved_registry
        text=text.replace('Init.$Ships.indexof.{$ship}','true' if self.ship in self.registry else 'false')
        return super().expr(text)
    def run(self,name):
        result=super().run(name)
        return False if self.drop_result and name=='vardath.go.crystal.exchange' else result
    def execute(self,nodes):
        previous=False
        for n in nodes:
            if n.tag in ['do_if','do_elseif']:
                if n.tag=='do_elseif' and previous:continue
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag=='append_to_list' and n.get('name')=='Init.$Ships':self.registry.append(self.expr(n.get('exact')))
            else:super().execute([n])
    def recover_registry(self):self.execute(ROOT.find(".//cue[@name='RecoverVisitsV39']/actions"))
    def legacy_paid(self):
        # Exact logical state shown for AKD-700: paid 7,000 Cr, sold 7, at desk,
        # no completion/crew return. No call to a financial helper in this fixture.
        self.state.update(vgo_crystal_shop_phase='atcounter',vgo_crystal_shop_deployed=True,
            vgo_crystal_shop_station=BUYER,vgo_crystal_shop_actor=self.crew,
            vgo_crystal_shop_trader=self.merchant,vgo_crystal_shop_origin=self.seat,
            vgo_crystal_shop_temporary=True,vgo_crystal_shop_setbusy=True,
            vgo_crystal_shop_hadstay=False,vgo_crystal_shop_manifest={WARES[0]:7},
            vgo_crystal_shop_walkstart=self.age-191,vgo_crystal_shop_step=self.age-191,
            vgo_crystal_shop_success=False,vgo_crystal_stock={WARES[0]:0},
            vgo_crystal_sale_mode='counter',vgo_crystal_sale_id=1,
            vgo_crystal_sale_completed=1,vgo_crystal_sale_due=0,vgo_crystal_sale_units=0,
            vgo_crystal_sold=7,vgo_result='Sold 7 finite crystal items for 7,000')
        self.crew.room=self.shoproom;self.crew.isbusy=True;self.crew.istemporary=False
        self.crew.Stay=True;self.crew.vgo_sale_ship=self.ship
        self.other[self.merchant]={'vgo_shop_owner':self.ship,'vgo_shop_expires':self.age+900}
        self.registry=Seq([self.ship]);self.money+=700000
        return self

class PaidCrewReturn(unittest.TestCase):
    def test_financial_commit_sets_saved_return_state_before_caller_resumes(self):
        v=ReturnVM({WARES[0]:7});self.assertTrue(v.reach_counter());before=v.money
        self.assertTrue(v.run('vardath.go.crystal.settle'))
        self.assertEqual(v.money-before,700000)
        self.assertTrue(v.get('vgo_crystal_shop_success'))
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returning')
        self.assertEqual(v.get('vgo_crystal_shop_invoice'),v.get('vgo_crystal_sale_completed'))
        # No crystal.shop caller is run: the independent MD must return the NPC.
        v.age+=21;v.tick();v.tick()
        self.assertIs(v.crew.room,v.shiproom);self.assertFalse(v.crew.isbusy)
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
        self.assertEqual(v.reward_requests,[700000])
    def test_lost_ai_return_result_does_not_leave_paid_actor_at_desk(self):
        v=ReturnVM();v.drop_result=True
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.receipts,[400000])
        self.assertEqual(v.get('vgo_crystal_sold'),4);self.assertEqual(len(v.goods_transfers),1)
    def test_supplied_legacy_seven_item_state_returns_without_a_second_payment(self):
        v=ReturnVM().legacy_paid();actor=v.crew;cash=v.money;v.tick();v.tick()
        self.assertIs(v.crew,actor);self.assertIs(v.crew.room,v.shiproom)
        self.assertTrue(v.get('vgo_crystal_shop_success'));self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
        self.assertEqual(v.get('vgo_crystal_shop_invoice'),1);self.assertEqual(v.get('vgo_crystal_sold'),7)
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[]);self.assertEqual(v.goods_transfers,[])
        self.assertEqual(v.run('vardath.go.crystal.commercial'),1)
        self.assertTrue(v.run('vardath.go.depart'));self.assertIs(v.docked,NULL)
        self.assertEqual(v.money,cash)
    def test_legacy_return_recovery_works_while_ai_is_paused_by_player_order(self):
        v=ReturnVM().legacy_paid();v.direct=True;v.tick();v.tick()
        self.assertIs(v.crew.room,v.shiproom);self.assertTrue(v.get('vgo_crystal_shop_success'))
        self.assertTrue(v.direct);self.assertEqual(v.reward_requests,[])
    def test_legacy_nonmatching_or_unpaid_state_cannot_claim_paid_success(self):
        for change in ['claim','due','id','broker','stock','manifest','newvisit']:
            with self.subTest(change=change):
                v=ReturnVM().legacy_paid()
                if change=='claim':v.state['vgo_crystal_sale_units']=7
                elif change=='due':v.state['vgo_crystal_sale_due']=100
                elif change=='id':v.state['vgo_crystal_sale_completed']=0
                elif change=='broker':v.state['vgo_crystal_sale_mode']='off-screen broker'
                elif change=='stock':v.state['vgo_crystal_stock'][WARES[0]]=4
                elif change=='manifest':v.state['vgo_crystal_shop_manifest']={}
                else:v.state['vgo_crystal_shop_invoice_baseline']=1
                v.tick();self.assertFalse(v.get('vgo_crystal_shop_success'))
                self.assertEqual(v.get('vgo_crystal_shop_phase'),'atcounter')
                self.assertEqual(v.reward_requests,[])
    def test_exact_paid_visit_can_return_after_partial_merchant_acceptance(self):
        v=ReturnVM();self.assertTrue(v.reach_counter());v.accept_limit=2
        self.assertTrue(v.run('vardath.go.crystal.settle'));self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],2)
        v.state['vgo_crystal_shop_phase']='atcounter';v.state['vgo_crystal_shop_success']=False
        v.tick();v.age+=21;v.tick();v.tick()
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.receipts,[200000])
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],2)
    def test_saved_mid_return_keeps_identity_and_has_bounded_blocked_path_recovery(self):
        v=ReturnVM().legacy_paid();v.native_arrives=False;actor=v.crew;v.tick()
        self.assertTrue(actor.iswalking);start=v.get('vgo_crystal_shop_return_started')
        v.state=copy.deepcopy(v.state);v.age+=119;v.tick();self.assertIs(actor.room,v.shoproom)
        v.age+=1;v.tick();v.tick()
        self.assertEqual(v.get('vgo_crystal_shop_return_started'),start)
        self.assertIs(v.crew,actor);self.assertIs(actor.room,v.shiproom)
        self.assertFalse(actor.isbusy);self.assertTrue(actor.istemporary)
        self.assertNotIn('Stay',actor.__dict__);self.assertEqual(actor.controlpost,'engineer')
        self.assertEqual(v.reward_requests,[])
    def test_manual_departure_away_from_station_never_teleports_crew_or_cancels_order(self):
        v=ReturnVM().legacy_paid();v.direct=True;v.docked=NULL;v.tick();v.age+=300;v.tick()
        self.assertIs(v.crew.room,v.shoproom);self.assertEqual(v.reward_requests,[])
        self.assertFalse(any(e[0] in ['reconnect','post'] for e in v.events));self.assertTrue(v.direct)
    def test_registry_rebuild_recovers_saved_visit_without_search_or_duplicate(self):
        v=ReturnVM().legacy_paid();v.registry=Seq();v.recover_registry();v.recover_registry()
        self.assertEqual(v.registry,[v.ship]);v.tick();v.tick();self.assertIs(v.crew.room,v.shiproom)
        self.assertEqual(v.reward_requests,[])
    def test_finished_visit_is_not_reregistered(self):
        v=ReturnVM().legacy_paid();v.registry=Seq();v.state['vgo_crystal_shop_phase']='returned'
        v.recover_registry();self.assertEqual(v.registry,[])

class UpgradeAndBlockerRecovery(unittest.TestCase):
    def test_all_crystal_parameter_migrations_guard_unset_lookups(self):
        r=xml('order.vardath.go.crystal')
        for p in r.findall('order/params/param/patch'):
            condition=p.get('condition');self.assertIn('?',condition);self.assertIn('@$',condition)
        p=r.find("order/params/param[@name='simulatesales']/patch")
        self.assertEqual(p.get('sinceversion'),'13')
    def test_newly_inserted_blockers_have_import_version_metadata(self):
        r=xml('vardath.go.crystal.shop')
        for n in r.findall('.//run_script'):
            if '.remote' in n.get('name'):self.assertEqual(n.get('sinceversion'),'3')
        r=xml('vardath.go.crystal.settle')
        self.assertEqual(r.find(".//run_script[@name=\"'vardath.go.crystal.exchange'\"]").get('sinceversion'),'2')
        for name in ['vardath.go.crystal.shop','vardath.go.crystal.settle']:
            self.assertIsNone(xml(name).find('.//return[@value="$sold"]'))
    def test_own_md_controls_return_without_creating_removing_or_reassigning_crew(self):
        for tag in ['create_npc','create_cue_actor','remove_npc_template','remove_actor_from_room','set_owner','set_entity_role','set_entity_controlpost']:
            self.assertEqual(list(ROOT.iter(tag)),[])
        c=ROOT.find(".//cue[@name='RecoverVisitsV39']")
        self.assertEqual(c.get('checkinterval'),'5s');self.assertEqual(list(c.iter('find_ship')),[])

if __name__=='__main__':unittest.main(verbosity=2)
