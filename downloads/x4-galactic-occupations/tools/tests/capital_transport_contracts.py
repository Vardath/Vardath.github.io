#!/usr/bin/env python3
"""Execute capital passenger XML with fault-injected native room/roster calls.

These are mocked boundary tests, not X4 transporter/pathfinding runtime tests.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from passenger_completion_contracts import PassengerVM, Seq, Obj, NULL, MOD
from crystal_commerce_contracts import Continued, Broken

ROOT=E.parse(MOD/'md/VGO_State.xml').getroot()
LIB=ROOT.find(".//library[@name='PassengerCapitalTransportV48']/actions")

class CapitalVM(PassengerVM):
    def __init__(self,phase='boarding',count=1):
        super().__init__(job=5,count=count)
        self.ship.isclass=Obj('large',ship_s=False,ship_m=False,ship_l=True,ship_xl=False)
        self.ship.isclass.ship=True;self.station.isclass=Obj('station class',ship=False,station=True)
        self.shiproom.container=self.ship;self.stationroom.container=self.station
        self.actualdock=self.station;self.distance=8;self.walk_arrives=True
        self.origin_points=True;self.arrival_points=True;self.transit=False;self.drop_body_on_release=False
        self.ship.people=NULL
        self.origin_point=self.exit if phase=='boarding' else self.seat
        self.arrival_point=self.seat if phase=='boarding' else self.exit
        self.vars.update(phase=phase,i=1,entry=self.state['vgo_passengers'][0],actor=self.actors[0])
        self.state['vgo_taxi_phase']=phase
        for a,e in zip(self.actors,self.state['vgo_passengers']):
            a.room=self.stationroom if phase=='boarding' else self.shiproom
            a.roleobject=self.ship;a.iswalking=False;e['boarded']=phase!='boarding'
        self.attempts=[]
    def expr(self,text):
        text=re.sub(r'\b(\d+)m\b',r'\1',text)
        actor=self.vars.get('actor',NULL);entry=self.vars.get('entry',{})
        origin=self.vars.get('origincontainer',NULL);arrival=self.vars.get('arrivalcontainer',NULL)
        def context(obj):return getattr(getattr(obj,'component',NULL),'context',None)
        def valid(obj):return bool(getattr(getattr(obj,'component',NULL),'exists',False))
        point=self.vars.get('transportpoint',NULL);container=self.vars.get('pointcontainer',NULL)
        oldorigin=entry.get('transport_origin',NULL);olddest=entry.get('transport_destination',NULL)
        to=self.vars.get('transportorigin',NULL);td=self.vars.get('transportdestination',NULL)
        fields={
            '@$ship.dock.container':self.actualdock,
            '@$ship.people.{$entry.$template}.isintransit':self.transit,
            '$actor.room.hascontext.{$arrivalcontainer}':actor.room.exists and getattr(actor.room,'context',None) is arrival,
            '$actor.room.hascontext.{$origincontainer}':actor.room.exists and getattr(actor.room,'context',None) is origin,
            '@$entry.$transport_origin.component.exists':valid(oldorigin),
            '@$entry.$transport_destination.component.exists':valid(olddest),
            '@$transportorigin.component.exists':valid(to),
            '@$transportdestination.component.exists':valid(td),
            '$transportorigin.component.hascontext.{$origincontainer}':context(to) is origin,
            '$transportdestination.component.hascontext.{$arrivalcontainer}':context(td) is arrival,
            '$transportdestination.component.hascontext.{$ship}':context(td) is self.ship,
            '$transportpoint.component.hascontext.{$pointcontainer}':context(point) is container,
            '$transportpoint.component.hascontext.{$ship}':context(point) is self.ship,
            '$actor.distanceto.{$transportorigin}':self.distance,
            '@$actor.room.container.isclass.ship':bool(getattr(getattr(getattr(actor.room,'container',NULL),'isclass',NULL),'ship',False)),
            '@$transportpoint.component.container.isclass.ship':bool(getattr(getattr(getattr(getattr(point,'component',NULL),'container',NULL),'isclass',NULL),'ship',False)),
            'RuntimeV21.$Passengers':Seq(self.actors),
        }
        for i,(old,value) in enumerate(sorted(fields.items(),key=lambda x:len(x[0]),reverse=True)):
            token='capital_mock_'+str(i);self.vars[token]=value;text=text.replace(old,'$'+token)
        return super().expr(text)
    def assign(self,name,value,remove=False):
        if name=='$actor.$vgo_taxi_ship':self.vars['actor'].taxi_ship=value;return
        if name=='$pointlist.{$j}' and remove:
            del self.vars['pointlist'][self.vars['j']-1];return
        super().assign(name,value,remove)
    def execute(self,nodes):
        previous=False
        for n in nodes:
            tag=n.tag
            if tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif tag=='do_elseif':
                if not previous:
                    previous=bool(self.expr(n.get('value')))
                    if previous:self.execute(n)
            elif tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif tag=='include_actions' and n.get('ref') in ('PassengerCapitalTransportV48','PassengerTransportPointsV48'):
                self.execute(ROOT.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif tag=='find_npc_waypoint':
                obj=self.expr(n.get('object'));point=self.seat if obj is self.ship else self.exit
                origin=self.vars.get('origincontainer')
                enabled=self.origin_points if obj is origin else self.arrival_points
                self.assign(n.get('name'),Seq([point] if enabled else []))
            elif tag=='find_room':self.assign(n.get('name'),Seq())
            elif tag=='do_for_each':
                items=list(enumerate(self.expr(n.get('in')),1))
                if n.get('reverse')=='true':items.reverse()
                for i,value in items:
                    self.vars[n.get('name')[1:]]=value
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif tag=='add_to_group':pass
            elif tag=='signal_objects':
                actor=self.expr(n.get('object'));param=n.get('param2','')
                point=self.vars['transportorigin'] if '$transportorigin' in param else self.vars['pointlist'].random
                self.signals.append((actor,point))
                if self.walk_arrives:actor.room=point.component;actor.iswalking=False;self.distance=0
            elif tag=='add_actor_to_room':
                actor=self.expr(n.get('actor'));point=self.expr(n.get('slot'));self.attempts.append((actor,point))
                self.vars[n.get('result')[1:]]=self.place_succeeds
                if self.place_succeeds and not self.placement_misreports:actor.room=point.component;actor.exists=True;actor.hasbody=True
            elif tag=='remove_npc_template':
                super().execute([n])
                if self.drop_body_on_release and self.vars['entry']['template'] not in self.roster:
                    self.vars['actor'].room=Obj('disconnected',exists=False);self.vars['actor'].exists=False
            else:super().execute([n])
    def tick(self,seconds=2):
        self.age+=seconds;self.execute(LIB)
    def arrive(self):
        for _ in range(5):self.tick()

class CapitalPassengerContracts(unittest.TestCase):
    def test_tour_menu_accepts_all_four_ship_sizes(self):
        r=E.parse(MOD/'aiscripts/order.vardath.go.tour.xml').getroot()
        self.assertIsNotNone(r.find("./order/requires/match[@class='[class.ship_s, class.ship_m, class.ship_l, class.ship_xl]']"))
    def test_real_l_and_xl_actor_walks_to_transporter_then_boards(self):
        for size in ('ship_l','ship_xl'):
            v=CapitalVM();v.ship.isclass.ship_l=size=='ship_l';v.ship.isclass.ship_xl=size=='ship_xl';actor=v.actors[0]
            v.tick();self.assertFalse(v.state['vgo_passengers'][0]['boarded']);self.assertEqual(v.attempts,[])
            v.arrive();self.assertTrue(v.state['vgo_passengers'][0]['boarded'])
            self.assertIs(actor.room,v.shiproom);self.assertIs(v.attempts[0][0],actor);self.assertEqual(v.roster,{1})
            self.assertEqual(v.reward_requests,[])
    def test_far_or_still_walking_actor_cannot_teleport(self):
        v=CapitalVM();v.walk_arrives=False
        for _ in range(20):v.tick()
        self.assertEqual(v.attempts,[]);self.assertFalse(v.state['vgo_passengers'][0]['boarded'])
        v.distance=0;v.actors[0].iswalking=True;v.arrive();self.assertEqual(v.attempts,[])
    def test_missing_source_or_receiver_preserves_npc_booking_and_money(self):
        for field in ('origin_points','arrival_points'):
            v=CapitalVM();setattr(v,field,False);v.arrive()
            self.assertEqual(v.roster,{1});self.assertEqual(v.attempts,[]);self.assertEqual(v.reward_requests,[])
            self.assertFalse(v.state['vgo_passengers'][0]['boarded'])
    def test_undocking_prevents_transfer_and_release(self):
        for phase in ('boarding','disembarking'):
            v=CapitalVM(phase);v.actualdock=NULL;v.arrive()
            self.assertEqual(v.roster,{1});self.assertEqual(v.attempts,[])
    def test_failed_or_false_positive_native_transfer_is_not_boarding(self):
        for field,value in [('place_succeeds',False),('placement_misreports',True)]:
            v=CapitalVM();setattr(v,field,value);v.arrive()
            self.assertFalse(v.state['vgo_passengers'][0]['boarded']);self.assertIs(v.actors[0].room,v.stationroom)
            self.assertEqual(v.roster,{1});self.assertEqual(v.reward_requests,[])
    def test_transit_flag_prevents_early_board_ack(self):
        v=CapitalVM();v.transit=True;v.arrive();self.assertIs(v.actors[0].room,v.shiproom)
        self.assertFalse(v.state['vgo_passengers'][0]['boarded']);v.transit=False;v.tick();self.assertTrue(v.state['vgo_passengers'][0]['boarded'])
    def test_departure_keeps_same_actor_and_requires_actual_station_arrival(self):
        v=CapitalVM('disembarking');actor=v.actors[0];v.arrive()
        self.assertEqual(v.roster,set());self.assertIs(actor.room,v.stationroom);self.assertIs(actor.roleobject,v.station)
        self.assertTrue(v.state['vgo_passengers'][0]['arrived']);self.assertEqual(v.reward_requests,[])
    def test_roster_refusal_or_station_placement_refusal_never_earns_fare(self):
        for field in ('release_succeeds','place_succeeds'):
            v=CapitalVM('disembarking');setattr(v,field,False);v.arrive()
            self.assertNotIn('arrived',v.state['vgo_passengers'][0]);self.assertIs(v.actors[0].room,v.shiproom)
            self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
    def test_native_template_removal_can_disconnect_body_then_same_actor_reappears(self):
        v=CapitalVM('disembarking');v.drop_body_on_release=True;actor=v.actors[0];v.arrive()
        self.assertTrue(actor.exists);self.assertIs(actor.room,v.stationroom);self.assertTrue(v.state['vgo_passengers'][0]['arrived'])
    def test_saved_pending_transfer_resumes_without_replacing_actor(self):
        v=CapitalVM();v.tick();v.tick();saved=copy.deepcopy(v.state);actor=v.actors[0]
        v.state=saved;v.vars['entry']=saved['vgo_passengers'][0];v.arrive()
        self.assertTrue(v.state['vgo_passengers'][0]['boarded']);self.assertIs(v.state['vgo_passengers'][0]['actor'],actor)
    def test_changed_station_invalidates_saved_transport_pair(self):
        v=CapitalVM();v.tick();e=v.vars['entry'];e['transport_station']=Obj('old station',exists=True);e['transport_destination']=Obj('stale point',component=v.stationroom)
        v.arrive();self.assertIs(e['transport_station'],v.station);self.assertIs(v.actors[0].room,v.shiproom)
    def test_ten_capital_passengers_complete_real_departure_and_pay_once(self):
        v=CapitalVM('disembarking',10);original=list(v.actors)
        for _ in range(16):
            v.transfer();v.age+=2
            if v.state.get('vgo_taxi_delivered'):break
        self.assertTrue(v.state['vgo_taxi_delivered']);self.assertEqual(v.state['vgo_taxi_delivered_count'],10)
        self.assertEqual(v.roster,set());self.assertEqual(len(v.removed),10);self.assertEqual(v.actors,original)
        self.assertTrue(all(any(a is actor and point is v.exit for actor,point in v.attempts) for a in original))
        before=v.money;self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertGreater(v.money,before)
        paid=v.money;v.run('vardath.go.passengers.pay');self.assertEqual(v.money,paid)
    def test_capital_arrival_clock_is_not_restarted_by_repeated_checks(self):
        v=CapitalVM('disembarking');v.arrive();e=v.state['vgo_passengers'][0];clock=e['stationarrival']
        for _ in range(4):v.tick()
        self.assertEqual(e['stationarrival'],clock)
    def test_other_docked_ships_bridge_cannot_count_as_station_departure(self):
        v=CapitalVM('disembarking');foreign=Obj('other docked ship',isclass=Obj('ship class',ship=True))
        v.stationroom.container=foreign
        v.arrive();self.assertEqual(v.attempts,[]);self.assertEqual(v.roster,{1})
        self.assertNotIn('arrived',v.state['vgo_passengers'][0]);self.assertEqual(v.reward_requests,[])
    def test_captain_or_crew_member_is_never_moved_by_passenger_transport(self):
        v=CapitalVM('disembarking');v.actors[0].role='pilot';v.arrive()
        self.assertEqual(v.attempts,[]);self.assertEqual(v.roster,{1});self.assertIs(v.actors[0].room,v.shiproom)
    def test_capital_path_has_no_rewards_inventory_grants_or_new_passenger_identity(self):
        for tag in ('reward_player','add_money','add_inventory','create_cue_actor','create_npc_template','destroy_object'):
            self.assertEqual(list(LIB.iter(tag)),[])
        points=ROOT.find(".//library[@name='PassengerTransportPointsV48']")
        self.assertTrue(all(n.get('tags')=='tag.npctransport' for n in points.iter('find_npc_waypoint')))

class ScannerPhysicsContracts(unittest.TestCase):
    def test_every_surface_query_is_preceded_by_visible_physics_and_sector_checks(self):
        r=E.parse(MOD/'aiscripts/vardath.go.task.scanner.xml').getroot()
        attempt=r.find(".//do_all[@counter='$attempt']")
        guard=attempt.find('do_if').get('value')
        self.assertIn('not $module.isphysicsready',guard);self.assertIn('$module.attention lt attention.visible',guard);self.assertIn('$module.sector != player.sector',guard)
        for ready,visible,same,allowed in [(True,True,True,True),(True,False,True,False),(False,True,True,False),(True,True,False,False)]:
            expr=guard.replace('not $module.isoperational','False').replace('$module.isphysicsready',str(ready)).replace('$module.attention lt attention.visible',str(not visible)).replace('$module.sector != player.sector',str(not same)).replace('$target.ishostileto.{this.ship}','False')
            self.assertEqual(not eval(expr,{'__builtins__':{}}),allowed)
        self.assertEqual(len(list(attempt.iter('find_object_surface'))),2)
    def test_loaded_but_inactive_geometry_uses_existing_remote_survey(self):
        r=E.parse(MOD/'aiscripts/vardath.go.task.scanner.xml').getroot()
        remote=r.find(".//run_script[@name=\"'vardath.go.survey.remote'\"]")
        parents={c:p for p in r.iter() for c in p};guard=parents[remote]
        self.assertIn('$module.attention lt attention.visible',guard.get('value'))

if __name__=='__main__':unittest.main()
