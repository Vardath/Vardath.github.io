#!/usr/bin/env python3
"""Execute the shipped delayed lifecycle XML with mocked native queues/rosters.

This is fault/boundary testing, not native X4 walking, teleport or save testing.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from crystal_commerce_contracts import Obj, NULL, S, MOD, xml
from passenger_completion_contracts import PassengerVM, Seq
from log12_return_contracts import ReturnVM
from log11_service_contracts import NativePassengers, STATE
from crystal_retail_contracts import MISSING_CLOCK

ROOT=E.parse(MOD/'md/VGO_Recovery.xml').getroot()
MD='player.entity.$vgo_objects.{$ship}'

class LifecycleVM(PassengerVM):
    def __init__(self,job=2,count=2):
        super().__init__(job,count)
        self.own=Obj('service',exists=True,id='VGO_tour' if job==5 else 'VGO_taxi')
        self.otherorder=Obj('manual',exists=True,id='MoveWait')
        self.ship.order=self.own;self.ship.defaultorder=self.own;self.ship.orders=Seq()
        self.ship.isclass=Obj('class',ship=True);self.ship.attention=1
        self.state.update(vgo_order=self.own,vgo_taxi_phase='aboard',vgo_tour_booked_stops=20)
        self.registry=Seq([self.ship]);self.knownships=Seq([self.ship])
        self.crew=Obj('existing crew',exists=True,npctemplate=999,room=self.stationroom,
            role='service',roleobject=self.ship,controlpost='engineer',iswalking=False,
            hasbody=True,istransferscheduled=False,isclass=Obj('npc class',npc=True))
        self.roles={i:'passenger' for i in self.roster};self.roles[999]='service';self.roster.add(999)
        for i,a in enumerate(self.actors,1):a.role='passenger';a.roleobject=self.ship;a.npctemplate=i
        self.logs=[];self.post_calls=[];self.native_post_accepts=True;self.post_instantiates=True
        self.body_removal_accepts=True;self.actualdock=self.station
        self.state['vgo_taxi_phase']='aboard'
    def expr(self,text):
        entry=self.vars.get('entry',{});actor=self.vars.get('actor',NULL)
        self.ship.isplayerowned=self.owned
        self.vars.update(registry=self.registry,knownships=self.knownships,
            lifecycle_occupied=self.ship if self.occupied else NULL,
            template_role=self.roles.get(entry.get('template'),'passenger'),
            native_crew_template=getattr(actor,'npctemplate',NULL) in self.roster,
            lifecycle_dock=self.actualdock)
        self.vars['recovery_npc']=bool(getattr(getattr(actor,'isclass',NULL),'npc',False))
        text=text.replace('$actor.isclass.npc','$recovery_npc')
        text=text.replace('player.entity.$vgo_objects.keys.list','$knownships')
        text=text.replace('Init.$Ships.indexof.{$ship}','true' if self.ship in self.registry else 'false')
        text=text.replace('Init.$Ships','$registry')
        text=text.replace('player.occupiedship','$lifecycle_occupied')
        text=text.replace('@$ship.dock.container','$lifecycle_dock')
        text=text.replace('@$ship.defaultorder','$ship.defaultorder').replace('@$ship.order','$ship.order')
        text=text.replace('$ship.people.{$entry.$template}.role','$template_role')
        text=text.replace('@$ship.people.{$actor.npctemplate}.exists','$native_crew_template')
        self.vars['origin_exists']=bool(getattr(getattr(self.vars.get('origin',NULL),'component',NULL),'exists',False))
        text=text.replace('@$origin.component.exists','$origin_exists')
        text=text.replace('$origin.component.hascontext.{$ship}','true' if self.vars.get('origin',NULL) is self.seat else 'false')
        for role in ['service','marine']:text=text.replace('entityrole.'+role,repr(role))
        text=re.sub(r'(\d+)h\b',lambda m:str(int(m[1])*3600),text)
        return super().expr(text)
    def assign(self,name,value,remove=False):
        if name=='Init.$Ships':self.registry=Seq(value);return
        if name=='Init.$Ships.{$shipindex}':self.registry.pop(self.vars['shipindex']-1);return
        m=re.fullmatch(r'\$actor\.\$(\w+)',name)
        if m:
            actor=self.vars['actor']
            if remove:actor.__dict__.pop(m[1],None)
            else:setattr(actor,m[1],value)
            return
        super().assign(name,value,remove)
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
            elif n.tag=='include_actions' and ROOT.find(".//library[@name='"+n.get('ref')+"']") is not None:
                self.execute(ROOT.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif n.tag=='append_to_list' and n.get('name')=='Init.$Ships':self.registry.append(self.expr(n.get('exact')))
            elif n.tag=='add_actor_to_post_location':
                actor=self.expr(n.get('actor'));self.post_calls.append(actor)
                if self.native_post_accepts:
                    actor.room=self.shiproom if self.post_instantiates else NULL
                    actor.hasbody=self.post_instantiates;actor.iswalking=False
            elif n.tag=='remove_actor_from_room' and not self.body_removal_accepts:pass
            elif n.tag=='write_to_logbook':self.logs.append(n.get('title'))
            else:super().execute([n])
    def library(self,name):self.execute(ROOT.find(".//library[@name='"+name+"']/actions"))
    def cancel(self):self.ship.defaultorder=self.otherorder;self.ship.order=self.otherorder
    def passengers(self):self.library('PassengerLifecycle')
    def crew_visit(self,kind='Crystal'):
        pfx='vgo_crystal_shop' if kind=='Crystal' else 'vgo_hack'
        self.state.update({pfx+'_deployed':True,pfx+'_actor':self.crew,
            pfx+'_station':self.station,pfx+'_origin':self.seat,pfx+'_phase':'returning'})
        self.actualdock=NULL;return pfx

class CancellationGrace(unittest.TestCase):
    def test_taxi_departs_at_thirty_minutes_without_fare_or_other_crew_loss(self):
        v=LifecycleVM();v.cancel();v.passengers();start=v.age
        self.assertEqual(v.get('vgo_passenger_cancel_due'),start+1800)
        v.age+=1799;v.passengers();self.assertEqual(v.roster,{1,2,999})
        v.age+=1;v.passengers();self.assertEqual(v.roster,{999})
        self.assertEqual(v.get('vgo_passengers'),[]);self.assertEqual(len(v.removed),2)
        self.assertEqual(v.get('vgo_taxi_cancelled_id'),7)
        self.assertFalse(v.get('vgo_taxi_delivered'));self.assertEqual(v.reward_requests,[])
        self.assertEqual(v.reputation,[]);self.assertEqual(v.crew.controlpost,'engineer')
    def test_cancelled_tour_has_at_least_two_game_hours(self):
        v=LifecycleVM(job=5);v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due'),v.age+7200)
        v.age+=7199;v.passengers();self.assertEqual(v.roster,{1,2,999})
        v.age+=1;v.passengers();self.assertEqual(v.roster,{999});self.assertEqual(v.reward_requests,[])
    def test_twenty_stop_estimate_extends_slow_cruise_grace(self):
        v=LifecycleVM(job=5);v.state.update(vgo_tour_trip=Seq(range(4)),vgo_tour_active_elapsed=3600)
        v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,19800)
    def test_last_completed_cruise_scales_to_current_booked_route(self):
        v=LifecycleVM(job=5);v.state.update(vgo_tour_last_duration=5400,vgo_tour_last_stops=10)
        v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,10800)
    def test_unmoving_zero_stop_tour_cannot_inflate_deadline_from_idle_time(self):
        v=LifecycleVM(job=5);v.state.update(vgo_tour_trip=Seq(),vgo_tour_active_elapsed=86400)
        v.cancel();v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,7200)
    def test_combat_lockbox_and_manual_control_with_retained_default_never_cancel(self):
        for job in [2,5]:
            for action in ['Attack','CollectLockbox','MoveWait']:
                with self.subTest(job=job,action=action):
                    v=LifecycleVM(job);v.ship.order=Obj(action,exists=True,id=action)
                    v.occupied=True;v.age+=86400;v.passengers()
                    self.assertNotIn('vgo_passenger_cancel_since',v.state)
                    self.assertEqual(v.roster,{1,2,999});self.assertEqual(v.logs,[])
    def test_queued_original_service_protects_party_after_default_change(self):
        v=LifecycleVM();v.cancel();v.ship.orders=Seq([v.own]);v.passengers()
        v.age+=4000;v.passengers();self.assertEqual(v.roster,{1,2,999})
        self.assertNotIn('vgo_passenger_cancel_due',v.state)
    def test_finished_missing_order_does_not_protect_cancelled_party(self):
        v=LifecycleVM();v.cancel();v.ship.orders=Seq([Obj('old',exists=False,id='VGO_taxi')])
        v.passengers();self.assertIn('vgo_passenger_cancel_due',v.state)
    def test_resuming_before_deadline_keeps_same_party_booked_destination_and_itinerary(self):
        v=LifecycleVM(job=5);original=list(v.actors);v.cancel();v.passengers();v.age+=7190
        v.ship.defaultorder=v.own;v.ship.order=v.own;v.passengers()
        self.assertNotIn('vgo_passenger_cancel_due',v.state);self.assertEqual(v.actors,original)
        self.assertIs(v.get('vgo_taxi_booked_destination'),v.station)
        self.assertEqual(len(v.get('vgo_tour_trip')),10);self.assertEqual(v.removed,[])
    def test_cancel_again_starts_a_new_grace_after_successful_resume(self):
        v=LifecycleVM();v.cancel();v.passengers();first=v.get('vgo_passenger_cancel_due')
        v.age+=1000;v.ship.defaultorder=v.own;v.passengers();v.cancel();v.passengers()
        self.assertEqual(v.get('vgo_passenger_cancel_due'),first+1000)
    def test_deadline_is_saved_and_does_not_slide_on_repeated_checks(self):
        v=LifecycleVM();v.cancel();v.passengers();due=v.get('vgo_passenger_cancel_due')
        v.state=copy.deepcopy(v.state)
        for _ in range(10):v.age+=30;v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due'),due)
        self.assertEqual(v.logs.count("'Galactic Occupations: passenger cancellation grace'"),1)
    def test_service_change_uses_original_contract_kind_and_preserves_other_job_state(self):
        v=LifecycleVM();v.state.update(vgo_job=5,vgo_verified=True,vgo_reward=12345)
        v.ship.defaultorder=Obj('tour',exists=True,id='VGO_tour');v.ship.order=v.ship.defaultorder
        v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due')-v.age,1800)
        v.age+=1800;v.passengers();self.assertEqual(v.get('vgo_reward'),12345);self.assertTrue(v.get('vgo_verified'))
    def test_pause_uses_game_time_and_ten_seta_minutes_are_still_six_hundred_seconds(self):
        v=LifecycleVM();v.cancel();v.passengers()
        for _ in range(20):v.passengers()
        self.assertEqual(v.roster,{1,2,999})
        v.age+=600;v.passengers();self.assertEqual(v.roster,{1,2,999})
        v.age+=1200;v.passengers();self.assertEqual(v.roster,{999})
    def test_legacy_missing_numeric_contract_is_normalised_without_a_sliding_deadline(self):
        class Legacy(LifecycleVM):
            def get(self,key,index=None):
                if key=='vgo_taxi_contract_id' and key not in self.state:return MISSING_CLOCK
                return super().get(key,index)
        v=Legacy();v.state.pop('vgo_taxi_contract_id');v.cancel();v.passengers()
        due=v.get('vgo_passenger_cancel_due');self.assertEqual(v.get('vgo_passenger_cancel_contract'),0)
        v.age+=600;v.passengers();self.assertEqual(v.get('vgo_passenger_cancel_due'),due)
        v.age+=1200;v.passengers();self.assertEqual(v.roster,{999})
        self.assertTrue(v.get('vgo_void_passenger_contracts')[0]);self.assertEqual(v.reward_requests,[])

class EvacuationAccounting(unittest.TestCase):
    def expired(self):
        v=LifecycleVM();v.cancel();v.passengers();v.age+=1800;return v
    def test_rejected_template_removal_retries_without_claiming_departure(self):
        v=self.expired();v.release_succeeds=False;v.passengers()
        self.assertTrue(v.get('vgo_passenger_disposing'));self.assertEqual(v.removed,[])
        self.assertEqual(v.roster,{1,2,999});v.release_succeeds=True;v.age+=30;v.passengers()
        self.assertEqual(v.roster,{999});self.assertEqual(v.reward_requests,[])
    def test_rejected_body_removal_is_not_evacuated_and_can_retry(self):
        v=self.expired();v.body_removal_accepts=False;v.passengers()
        self.assertTrue(v.get('vgo_passenger_disposing'));self.assertEqual(v.roster,{999})
        self.assertEqual(v.removed,[]);v.body_removal_accepts=True;v.age+=30;v.passengers()
        self.assertEqual(len(v.removed),2);self.assertEqual(v.get('vgo_passengers'),[])
    def test_recruited_passenger_is_kept_as_crew_with_native_roster_intact(self):
        v=self.expired();v.roles[1]='service';v.actors[0].role='service';v.actors[0].vgo_taxi_ship=v.ship;v.passengers()
        self.assertEqual(v.roster,{1,999});self.assertTrue(v.actors[0].exists)
        self.assertNotIn(v.actors[0],v.removed);self.assertFalse(v.get('vgo_passenger_disposing'))
        self.assertNotIn('vgo_taxi_ship',v.actors[0].__dict__)
    def test_role_conversion_is_checked_before_removing_even_stale_passenger_template(self):
        v=self.expired();v.actors[0].role='marine';v.passengers()
        self.assertEqual(v.roster,{1,999});self.assertTrue(v.actors[0].exists)
    def test_promoted_captain_is_retained_using_actual_pilot_identity(self):
        v=self.expired();v.actors[0].role='unassigned';v.ship.pilot=v.actors[0]
        v.passengers();self.assertEqual(v.roster,{1,999})
        self.assertTrue(v.actors[0].exists);self.assertNotIn(v.actors[0],v.removed)
    def test_cancellation_cannot_forge_completed_paid_contract_after_cleanup(self):
        v=self.expired();v.passengers()
        v.state.update(vgo_taxi_delivered=True,vgo_taxi_completed_service=2,vgo_taxi_completed_id=7,vgo_taxi_delivered_count=2)
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
    def test_expired_partial_eviction_cannot_be_resumed_or_board_new_people(self):
        v=self.expired();v.release_succeeds=False;v.passengers();v.ship.defaultorder=v.own;v.ship.order=v.own
        v.passengers();self.assertTrue(v.get('vgo_passenger_disposing'))
        self.assertFalse(v.run('vardath.go.passengers.board'))
        self.assertFalse(v.run('vardath.go.passengers.destination'));self.assertEqual(v.reward_requests,[])
    def test_normal_earned_unpaid_fare_without_manifest_is_not_voided(self):
        v=LifecycleVM();self.assertTrue(v.complete());v.cancel();v.passengers()
        self.assertNotIn('vgo_taxi_cancelled_id',v.state)
        self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.receipts,[1600000])
    def test_newer_contract_can_settle_after_older_cancelled_id(self):
        v=LifecycleVM();v.state['vgo_taxi_cancelled_id']=6;v.state['vgo_void_passenger_contracts']={6:True};self.assertTrue(v.complete())
        self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.receipts,[1600000])
    def test_void_history_rejects_an_older_cancelled_contract_after_another_cancellation(self):
        v=self.expired();v.passengers();self.assertTrue(v.get('vgo_void_passenger_contracts')[7])
        v.state.update(vgo_taxi_cancelled_id=8,vgo_taxi_delivered=True,vgo_taxi_completed_service=2,vgo_taxi_completed_id=7,vgo_taxi_delivered_count=2)
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])

class MeasuredTourClock(unittest.TestCase):
    def test_clock_counts_own_work_and_docking_but_excludes_interruption_and_control(self):
        v=LifecycleVM(job=5);v.library('TourClock');v.age+=30;v.library('TourClock')
        self.assertEqual(v.get('vgo_tour_active_elapsed'),30)
        v.ship.order=v.otherorder;v.age+=30;v.library('TourClock');v.age+=3600;v.library('TourClock')
        self.assertEqual(v.get('vgo_tour_active_elapsed'),30)
        v.ship.order=v.own;v.library('TourClock');v.age+=30;v.library('TourClock')
        self.assertEqual(v.get('vgo_tour_active_elapsed'),60)
        dock=Obj('dock',exists=True,id='DockAt');v.state['vgo_dock_order']=dock;v.ship.order=dock
        v.age+=30;v.library('TourClock');self.assertEqual(v.get('vgo_tour_active_elapsed'),90)
        v.occupied=True;v.age+=600;v.library('TourClock');self.assertEqual(v.get('vgo_tour_active_elapsed'),90)
    def test_long_gap_is_bounded_instead_of_becoming_hours_of_unobserved_work(self):
        v=LifecycleVM(job=5);v.library('TourClock');v.age+=86400;v.library('TourClock')
        self.assertEqual(v.get('vgo_tour_active_elapsed'),60)
    def test_completed_tour_records_actual_clock_only_after_full_departure(self):
        v=LifecycleVM(job=5);v.state.update(vgo_tour_trip=Seq(range(20)),vgo_tour_active_elapsed=10800)
        self.assertTrue(v.complete());self.assertEqual(v.get('vgo_tour_last_duration'),10800)
        self.assertEqual(v.get('vgo_tour_last_stops'),20)
    def test_unfinished_itinerary_cannot_record_completed_duration(self):
        v=LifecycleVM(job=5);v.state['vgo_tour_active_elapsed']=10000
        self.assertFalse(v.complete());self.assertNotIn('vgo_tour_last_duration',v.state)

class StrandedCrewRecall(unittest.TestCase):
    def test_crystal_and_hacker_recall_same_npc_after_twenty_minutes_away(self):
        for kind in ['Crystal','Hacker']:
            with self.subTest(kind=kind):
                v=LifecycleVM();pfx=v.crew_visit(kind);actor=v.crew;role=actor.role;post=actor.controlpost
                v.library('Recall'+kind);v.age+=1199;v.library('Recall'+kind)
                self.assertEqual(v.placements,[]);self.assertIs(actor.room,v.stationroom)
                v.age+=1;v.library('Recall'+kind)
                self.assertIs(actor.room,v.shiproom);self.assertIs(actor,v.crew)
                self.assertEqual((actor.role,actor.controlpost),(role,post));self.assertIn(999,v.roster)
                self.assertTrue(v.get(pfx+'_recalled'));self.assertEqual(v.get(pfx+'_phase'),'returning')
                self.assertEqual(v.reward_requests,[])
    def test_redocking_resets_away_timer_and_does_not_teleport_early(self):
        v=LifecycleVM();p=v.crew_visit();v.library('RecallCrystal');v.age+=1100
        v.actualdock=v.station;v.library('RecallCrystal');self.assertNotIn(p+'_away_since',v.state)
        v.actualdock=NULL;v.library('RecallCrystal');v.age+=1199;v.library('RecallCrystal')
        self.assertEqual(v.placements,[])
    def test_timer_and_actor_identity_survive_saved_state_retry(self):
        v=LifecycleVM();p=v.crew_visit();v.library('RecallCrystal');start=v.get(p+'_away_since')
        v.state=copy.deepcopy(v.state);v.age+=1200;v.library('RecallCrystal')
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.get(p+'_phase'),'returning')
        self.assertEqual(v.logs.count("'Galactic Occupations: stranded crew recalled'"),1)
    def test_missing_room_uses_native_original_post_without_creating_a_replacement(self):
        v=LifecycleVM();p=v.crew_visit();v.state[p+'_origin']=NULL
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
        self.assertEqual(v.post_calls,[v.crew]);self.assertIs(v.crew.room,v.shiproom)
        self.assertEqual(v.placements,[]);self.assertEqual(v.roster,{1,2,999})
    def test_unloaded_ship_can_confirm_existing_roster_post_return_without_body(self):
        v=LifecycleVM();p=v.crew_visit();v.state[p+'_origin']=NULL
        v.visible=False;v.player_sector=Obj('elsewhere',exists=True);v.post_instantiates=False
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
        self.assertTrue(v.get(p+'_recalled'));self.assertFalse(v.crew.room.exists)
        self.assertEqual(v.crew.roleobject,v.ship);self.assertIn(999,v.roster)
    def test_native_post_failure_is_not_claimed_recalled_and_retries_are_throttled(self):
        v=LifecycleVM();p=v.crew_visit();v.state[p+'_origin']=NULL;v.native_post_accepts=False
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal');v.library('RecallCrystal')
        self.assertFalse(v.get(p+'_recalled'));self.assertEqual(v.post_calls,[v.crew])
        v.age+=30;v.native_post_accepts=True;v.library('RecallCrystal');self.assertTrue(v.get(p+'_recalled'))
    def test_does_not_reclaim_manually_transferred_dead_or_scheduled_crew(self):
        for reason in ['roster','roleobject','dead','scheduled','ownership']:
            with self.subTest(reason=reason):
                v=LifecycleVM();p=v.crew_visit()
                if reason=='roster':v.roster.remove(999)
                elif reason=='roleobject':v.crew.roleobject=Obj('another ship',exists=True)
                elif reason=='dead':v.crew.exists=False;v.crew.isclass.npc=False;v.roster.remove(999)
                elif reason=='scheduled':v.crew.istransferscheduled=True
                else:v.owned=False
                v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
                self.assertFalse(v.get(p+'_recalled'));self.assertEqual(v.placements,[])
    def test_player_control_and_new_orders_are_preserved_during_recall(self):
        v=LifecycleVM();v.crew_visit();v.occupied=True;v.ship.order=v.otherorder
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
        self.assertIs(v.ship.order,v.otherorder);self.assertTrue(v.occupied)
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.reward_requests,[])
    def test_disconnected_existing_crew_still_recalls_to_native_roster_post(self):
        v=LifecycleVM();p=v.crew_visit();v.crew.exists=False;v.crew.hasbody=False;v.crew.room=NULL
        v.state[p+'_origin']=NULL;v.post_instantiates=False;v.visible=False;v.player_sector=Obj('elsewhere',exists=True)
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
        self.assertTrue(v.get(p+'_recalled'));self.assertIs(v.post_calls[0],v.crew)
        self.assertIn(999,v.roster);self.assertEqual(v.crew.controlpost,'engineer')

class RegistryAndSource(unittest.TestCase):
    def test_registry_recovers_only_mod_payloads_from_saved_keys(self):
        v=LifecycleVM();v.registry=Seq();v.execute(ROOT.find(".//cue[@name='BootstrapV40']/actions"))
        self.assertEqual(v.registry,[v.ship]);v.execute(ROOT.find(".//cue[@name='BootstrapV40']/actions"))
        self.assertEqual(v.registry,[v.ship])
    def test_empty_payload_is_pruned_after_unpaid_departure(self):
        v=LifecycleVM();v.cancel();v.passengers();v.age+=1800;v.passengers()
        v.execute(ROOT.find(".//cue[@name='Operations']/actions"));self.assertEqual(v.registry,[])
    def test_native_registry_and_post_properties_are_supported_and_no_money_or_crew_creation(self):
        for tag in ['reward_player','add_faction_relation','add_inventory','create_npc_template','create_cue_actor','create_order','cancel_order','set_entity_controlpost','set_entity_role_object']:
            self.assertEqual(list(ROOT.iter(tag)),[])
        self.assertEqual(ROOT.find(".//cue[@name='Operations']").get('checkinterval'),'30s')
        self.assertEqual(ROOT.find(".//cue[@name='RecoverRegistry']").get('checkinterval'),'5min')
    def test_twenty_stop_default_does_not_rewrite_existing_booked_stops(self):
        r=xml('order.vardath.go.tour');p=r.find("order/params/param[@name='stops']")
        self.assertEqual(p.get('default'),'20')
        self.assertFalse(any(n.tag=='set_value' and n.get('name','').endswith('.$vgo_tour_booked_stops') for n in r.iter()))
        task=xml('vardath.go.task.tour')
        booking=next(n for n in task.iter('do_if') if n.get('value')=='not @'+S+'.$vgo_passengers.count')
        setting=booking.find("do_if/set_value[@name='"+S+".$vgo_tour_stops']")
        self.assertEqual(setting.get('exact'),'this.ship.order.$stops')

class RetailRecallVM(ReturnVM):
    def __init__(self):super().__init__();self.uninstanced_post=False
    def expr(self,text):
        actor=self.vars.get('actor',NULL)
        text=text.replace('$actor.isclass.npc','true' if actor is self.crew else 'false')
        return super().expr(text)
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
            elif n.tag=='include_actions' and ROOT.find(".//library[@name='"+n.get('ref')+"']") is not None:
                self.execute(ROOT.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif n.tag=='add_actor_to_post_location' and self.uninstanced_post:
                actor=self.expr(n.get('actor'));actor.room=NULL;actor.hasbody=False
            else:super().execute([n])
    def recall(self):self.execute(ROOT.find(".//library[@name='RecallCrystal']/actions"))

class IntegratedRecovery(unittest.TestCase):
    def paid_away(self):
        v=RetailRecallVM();self.assertTrue(v.reach_counter());self.assertTrue(v.run('vardath.go.crystal.settle'))
        v.docked=NULL;return v
    def test_paid_crew_recall_finishes_existing_controller_and_restores_flags_once(self):
        v=self.paid_away();actor=v.crew;cash=v.money;v.recall();v.age+=1200;v.recall();v.tick()
        self.assertIs(v.crew,actor);self.assertIs(actor.room,v.shiproom)
        self.assertFalse(v.get('vgo_crystal_shop_deployed'));self.assertFalse(actor.isbusy)
        self.assertTrue(actor.istemporary);self.assertNotIn('Stay',actor.__dict__)
        self.assertEqual(actor.controlpost,'engineer');self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
        self.assertEqual(v.run('vardath.go.crystal.commercial'),1)
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[400000])
    def test_unloaded_roster_recall_also_finishes_existing_return_controller(self):
        v=self.paid_away();actor=v.crew;v.state['vgo_crystal_shop_origin']=NULL
        v.ship.attention=0;v.player_sector=Obj('elsewhere',exists=True);v.uninstanced_post=True
        v.recall();v.age+=1200;v.recall();self.assertFalse(actor.room.exists)
        v.tick();self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
        self.assertFalse(v.get('vgo_crystal_shop_deployed'));self.assertFalse(actor.isbusy)
        self.assertIn(actor.npctemplate,v.crew_roster);self.assertEqual(v.reward_requests,[400000])
    def test_disconnected_paid_representative_finishes_and_restores_flags_without_second_payment(self):
        v=self.paid_away();actor=v.crew;cash=v.money
        actor.exists=False;actor.hasbody=False;actor.room=NULL
        v.state['vgo_crystal_shop_origin']=NULL;v.ship.attention=0;v.player_sector=Obj('elsewhere',exists=True);v.uninstanced_post=True
        v.recall();v.age+=1200;v.recall();v.tick()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
        self.assertFalse(actor.isbusy);self.assertTrue(actor.istemporary)
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[400000])
    def test_changed_service_cannot_deliver_previous_party_through_normal_transfer_cue(self):
        v=NativePassengers();v.state['vgo_taxi_phase']='disembarking';v.state['vgo_taxi_boarded']=True
        for e in v.state['vgo_passengers']:e['boarded']=True
        tour=Obj('new tour',exists=True,id='VGO_tour');v.ship.order=tour;v.ship.defaultorder=tour;v.state['vgo_order']=tour
        v.execute(STATE.find(".//cue[@name='PassengerTransfersV2']/actions"));v.age+=10
        v.execute(STATE.find(".//cue[@name='PassengerTransfersV2']/actions"))
        self.assertEqual(v.roster,{1,2});self.assertEqual(v.removed,[])
        self.assertFalse(v.state.get('vgo_taxi_delivered',False))
    def test_empty_old_service_does_not_block_the_next_kinds_booking(self):
        v=NativePassengers(count=0);v.state['vgo_taxi_phase']='boarding'
        tour=Obj('next tour',exists=True,id='VGO_tour');v.ship.order=tour;v.ship.defaultorder=tour;v.state['vgo_order']=tour
        v.vars.pop('station',None)
        v.execute(STATE.find(".//cue[@name='PassengerTransfersV2']/actions"))
        self.assertIs(v.vars.get('station'),v.station)
    def test_hacker_recall_preserves_tool_loans_until_existing_return_accounting(self):
        v=LifecycleVM();v.crew_visit('Hacker');loan=Seq([{'ware':'security_tool','count':1}])
        v.state['vgo_hack_loans']=loan;v.library('RecallHacker');v.age+=1200;v.library('RecallHacker')
        self.assertIs(v.get('vgo_hack_loans'),loan);self.assertEqual(v.get('vgo_hack_phase'),'returning')
        h=E.parse(MOD/'md/VGO_Hacker.xml')
        gates=[n for n in h.iter('do_if') if '$vgo_hack_recalled' in n.get('value','')]
        self.assertEqual(len(gates),1);self.assertIn('not player.entity.$vgo_objects.{$ship}.$vgo_hack_loans.count',gates[0].get('value'))
        self.assertIsNotNone(h.find(".//include_actions[@ref='ReturnTools']"))

if __name__=='__main__':unittest.main(verbosity=2)
