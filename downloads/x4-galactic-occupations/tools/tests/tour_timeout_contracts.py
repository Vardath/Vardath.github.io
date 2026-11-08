#!/usr/bin/env python3
"""Execute real tour grace/budget XML with mocked native state and clocks.

This checks deadline accounting and interruption boundaries, not X4 pathfinding.
"""
import copy
import unittest
from lifecycle_contracts import LifecycleVM, ROOT
from log11_service_contracts import STATE
from crystal_commerce_contracts import Obj, NULL, xml
from passenger_completion_contracts import Seq


class TourBudgetVM(LifecycleVM):
    def __init__(self):
        super().__init__(job=5);self.state['vgo_passenger_service']=5
        self.state.update(vgo_deadline=self.age+1800,vgo_tour_booked_stops=20,vgo_dock_order=NULL)
    def budget(self):self.execute(STATE.find(".//library[@name='TourTimeoutBudgetV45']/actions"))


class ActiveTourBudget(unittest.TestCase):
    def test_already_expired_saved_budget_gets_one_hour_but_still_has_a_finite_end(self):
        v=TourBudgetVM();v.state['vgo_deadline']=v.age-30;v.budget()
        self.assertEqual(v.get('vgo_deadline'),v.age+3570)
        v.age+=3571;v.budget();self.assertLess(v.get('vgo_deadline'),v.age)
    def test_active_and_existing_saved_leg_get_exactly_one_additional_hour(self):
        v=TourBudgetVM();before=v.get('vgo_deadline');party=list(v.actors)
        v.budget();self.assertEqual(v.get('vgo_deadline'),before+3600)
        for _ in range(30):v.age+=2;v.budget()
        self.assertEqual(v.get('vgo_deadline'),before+3600);self.assertEqual(v.actors,party)
        v.state=copy.deepcopy(v.state);v.budget();self.assertEqual(v.get('vgo_deadline'),before+3600)
        self.assertEqual(v.reward_requests,[]);self.assertEqual(v.removed,[])
    def test_new_native_leg_gets_its_own_hour_without_reusing_or_sliding_old_budget(self):
        v=TourBudgetVM();v.budget();v.age+=60;nextdeadline=v.age+1800
        v.state['vgo_deadline']=nextdeadline;v.budget()
        self.assertEqual(v.get('vgo_deadline'),nextdeadline+3600);v.budget()
        self.assertEqual(v.get('vgo_deadline'),nextdeadline+3600)
    def test_owned_tour_dock_gets_one_hour_but_direct_orders_remain_current(self):
        v=TourBudgetVM();dock=Obj('native dock',exists=True,id='DockAt')
        v.state.update(vgo_dock_order=dock,vgo_dock_until=v.age+1800);v.ship.order=dock
        original=v.get('vgo_dock_until');v.budget();v.budget()
        self.assertEqual(v.get('vgo_dock_until'),original+3600);self.assertIs(v.ship.order,dock)
        v.ship.order=v.otherorder;v.age+=60;v.state['vgo_dock_until']=v.age+1800
        directdeadline=v.get('vgo_dock_until');v.budget()
        self.assertEqual(v.get('vgo_dock_until'),directdeadline);self.assertIs(v.ship.order,v.otherorder)
    def test_taxi_other_role_player_control_nonowner_and_disposing_are_unchanged(self):
        for why in ['taxi','otherrole','queued_other_role','occupied','owner','disposing','no_passengers']:
            with self.subTest(why=why):
                v=TourBudgetVM();before=v.get('vgo_deadline')
                if why=='taxi':v.state['vgo_passenger_service']=2;v.own.id='VGO_taxi'
                elif why=='otherrole':v.ship.order=v.otherorder
                elif why=='queued_other_role':
                    v.ship.order=Obj('morale',exists=True,id='VGO_morale');v.state['vgo_order']=v.ship.order
                elif why=='occupied':v.occupied=True
                elif why=='owner':v.owned=False
                elif why=='disposing':v.state['vgo_passenger_disposing']=True
                else:v.state['vgo_passengers']=Seq()
                v.budget();self.assertEqual(v.get('vgo_deadline'),before)
    def test_budget_is_applied_before_both_watchdog_and_dock_expiry_evaluations(self):
        watch=STATE.find(".//cue[@name='Watchdog']/actions/do_for_each")
        names=list(watch);hook=next(i for i,n in enumerate(names) if n.tag=='include_actions' and n.get('ref')=='TourTimeoutBudgetV45')
        expiry=next(i for i,n in enumerate(names) if n.tag=='do_elseif' and 'vgo_deadline lt player.age' in n.get('value',''))
        self.assertLess(hook,expiry)
        dock=list(STATE.find(".//cue[@name='DockOrdersV34']/actions/do_for_each"))
        hook=next(i for i,n in enumerate(dock) if n.tag=='include_actions' and n.get('ref')=='TourTimeoutBudgetV45')
        expiry=next(i for i,n in enumerate(dock) if n.tag=='set_value' and n.get('name')=='$cancel')
        self.assertLess(hook,expiry)


class CancellationExtension(unittest.TestCase):
    def test_new_cancelled_tour_gets_three_hours_and_preserves_booked_twenty_stops(self):
        v=TourBudgetVM();v.cancel();v.passengers();due=v.get('vgo_passenger_cancel_due')
        self.assertEqual(due,v.age+10800);self.assertEqual(v.get('vgo_tour_booked_stops'),20)
        v.age=due-1;v.passengers();self.assertEqual(v.roster,{1,2,999})
        v.age=due;v.passengers();self.assertEqual(v.roster,{999});self.assertEqual(v.reward_requests,[])
    def test_existing_cancellation_deadline_extends_once_even_after_reload_or_repeated_poll(self):
        v=TourBudgetVM();v.cancel();old=v.age+200
        v.state.update(vgo_passenger_cancel_since=v.age-7000,vgo_passenger_cancel_due=old,vgo_passenger_cancel_contract=7)
        v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due'),old+3600)
        v.state=copy.deepcopy(v.state)
        for _ in range(10):v.age+=30;v.passengers()
        self.assertEqual(v.get('vgo_passenger_cancel_due'),old+3600);self.assertEqual(v.roster,{1,2,999})
    def test_duration_estimate_receives_extra_hour_above_existing_scaled_budget(self):
        v=TourBudgetVM();v.state.update(vgo_tour_trip=Seq(range(4)),vgo_tour_active_elapsed=3600)
        v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,23400)
    def test_taxi_keeps_thirty_minutes_and_active_tour_never_begins_cancellation(self):
        v=LifecycleVM();v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,1800)
        t=TourBudgetVM();t.ship.order=t.otherorder;t.age+=20000;t.passengers()
        self.assertNotIn('vgo_passenger_cancel_due',t.state);self.assertEqual(t.roster,{1,2,999})
    def test_resuming_clears_extension_marker_then_another_real_cancellation_gets_new_grace(self):
        v=TourBudgetVM();v.cancel();v.passengers();first=v.get('vgo_passenger_cancel_due')
        v.age+=100;v.ship.defaultorder=v.own;v.ship.order=v.own;v.passengers()
        self.assertNotIn('vgo_tour_cancel_grace_v45',v.state)
        v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due'),first+100)
    def test_already_disposing_contract_is_not_resurrected_or_paid(self):
        v=TourBudgetVM();v.cancel();v.state.update(vgo_passenger_disposing=True,vgo_taxi_cancelled_id=7)
        v.passengers();self.assertEqual(v.roster,{999});self.assertFalse(v.run('vardath.go.passengers.pay'))


class NewTourDefault(unittest.TestCase):
    def test_new_default_ten_stops_keeps_editable_range_fare_and_existing_booking(self):
        r=xml('order.vardath.go.tour');p=r.find("order/params/param[@name='stops']")
        self.assertEqual(p.get('default'),'10')
        self.assertEqual(p.find("input_param[@name='min']").get('value'),'10')
        self.assertEqual(p.find("input_param[@name='max']").get('value'),'20')
        self.assertEqual(r.find("order/params/param[@name='ticketfee']").get('default'),'500000Cr')
        self.assertTrue(all(n.get('value')=='10' for n in p.findall('patch')))
        self.assertFalse(any(n.get('name','').endswith('.$vgo_tour_booked_stops') for n in r.iter('set_value')))


if __name__=='__main__':unittest.main(verbosity=2)
