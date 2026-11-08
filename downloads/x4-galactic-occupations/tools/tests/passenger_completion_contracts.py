#!/usr/bin/env python3
"""Execute shipped departure and fare XML with mocked rooms, rosters and credits.

These checks exercise interruption/accounting failures. They do not run X4,
prove native NPC pathfinding, or validate the installed merged game schema.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from crystal_commerce_contracts import VM as BaseVM, Obj, NULL, FACTION, PLAYER, S, Returned, Continued, Broken, MOD, xml

MD='player.entity.$vgo_objects.{$ship}'
class Seq(list):
    @property
    def count(self):return len(self)
    @property
    def clone(self):return Seq(self)
    @property
    def random(self):return self[0] if self else NULL

class PassengerVM(BaseVM):
    def __init__(self,job=2,count=2):
        super().__init__()
        self.ship=Obj('ship',exists=True,knownname='Taxi',isplayerowned=True)
        self.station=Obj('station',exists=True,knownname='Destination',isoperational=True)
        self.shiproom=Obj('shiproom',exists=True,context=self.ship)
        self.stationroom=Obj('stationroom',exists=True,context=self.station)
        self.exit=Obj('exit',component=self.stationroom)
        self.seat=Obj('seat',component=self.shiproom)
        self.roster=set(range(1,count+1));self.actors=[]
        entries=Seq()
        for i in range(1,count+1):
            actor=Obj('pax'+str(i),exists=True,room=self.shiproom,iswalking=False,walkspeed=1)
            entries.append({'template':i,'actor':actor,'boarded':True,'delivered':False})
            self.actors.append(actor)
        self.state.update(vgo_job=job,vgo_passenger_service=job,vgo_passengers=entries,
            vgo_taxi_booked_destination=self.station,
            vgo_taxi_boarded=True,vgo_taxi_contract_id=7,vgo_taxi_completed_id=0,
            vgo_taxi_phase='disembarking',vgo_taxi_faction=FACTION,vgo_taxi_dest=self.station,
            vgo_taxi_pickup=self.station,vgo_tour_booked_fee=50000000,vgo_tour_booked_stops=10,
            vgo_tour_trip=Seq(range(10)),vgo_tour_minsectors=3,vgo_tour_sectors=Seq(range(3)))
        self.vars.update(ship=self.ship,station=self.station)
        self.visible=True;self.pier=True;self.available_exits=True
        self.native_walk_arrives=True;self.place_succeeds=True;self.release_succeeds=True
        self.placement_misreports=False
        self.signals=[];self.placements=[];self.removed=[];self.ordering=[]

    def get(self,key,index=None):
        if index is not None and isinstance(self.state.get(key),list):
            return self.state[key][index-1]
        value=super().get(key,index)
        if key in ['vgo_passengers','vgo_tour_trip','vgo_tour_sectors'] and not isinstance(value,Seq):
            return Seq(value or [])
        return value

    def expr(self,text):
        text=text.replace(MD,S)
        text=text.replace('player.entity.$vgo_objects?','true').replace(S+'?','true')
        def saved_entry(match):
            index=self.vars.get(match[1],1)-1
            entry=self.state.get('vgo_passengers',[])[index]
            key='saved_entry_'+match[2]
            self.vars[key]=entry.get(match[2],0)
            return '$'+key
        text=re.sub(r'@?'+re.escape(S)+r'\.\$vgo_passengers\.\{\$(\w+)\}\.\$(\w+)',saved_entry,text)
        entry=self.vars.get('entry',{})
        actor=self.vars.get('actor',NULL)
        point=self.vars.get('exitpoint',NULL)
        self.vars.update(mock_roster=entry.get('template') in self.roster,
            mock_actor_station=actor.exists and getattr(actor.room,'context',None) is self.station,
            mock_actor_ship=actor.exists and getattr(actor.room,'context',None) is self.ship,
            mock_actor_class=actor in self.actors,
            mock_point_station=getattr(point.component,'context',None) is self.station,
            mock_point_ship=getattr(point.component,'context',None) is self.ship,
            mock_exit_exists=getattr(entry.get('exit',NULL).component,'exists',False),
            mock_pier=self.pier,mock_attention=1 if self.visible else 0)
        replacements={
            '@$ship.people.{$entry.$template}.exists':'$mock_roster',
            '$actor.room.hascontext.{$station}':'$mock_actor_station',
            '$actor.room.hascontext.{$ship}':'$mock_actor_ship',
            '$actor.isclass.npc':'$mock_actor_class',
            '@$ship.dock.container':'$mock_dockcontainer',
            '$exitpoint.component.hascontext.{$station}':'$mock_point_station',
            '$exitpoint.component.hascontext.{$ship}':'$mock_point_ship',
            '@$entry.$exit.component.exists':'$mock_exit_exists',
            '@$ship.dock.walkablemodule.haswalkableroom':'$mock_pier',
            '$ship.dock.walkablemodule':'$mock_module',
            '$ship.attention':'$mock_attention','attention.visible':'1'}
        for old,new in replacements.items():text=text.replace(old,new)
        self.vars['mock_dockcontainer']=self.station
        for prop in re.findall(r'\$entry\.\$(\w+)\?',text):
            text=text.replace('$entry.$'+prop+'?','true' if prop in entry else 'false')
        for prop in re.findall(r'\$entry\.\$(\w+)',text):
            self.vars['entry_'+prop]=entry.get(prop,NULL if prop in ['actor','exit','exitstation'] else 0)
            text=text.replace('$entry.$'+prop,'$entry_'+prop)
        # Base interpreter models optional state reads; optional local table reads
        # above are already converted to explicit mock values.
        text=re.sub(r'@(?=\$(?:entry_|mock_))','',text)
        return super().expr(text)

    def assign(self,name,value,remove=False):
        name=name.replace(MD,S)
        if isinstance(value,list) and not isinstance(value,Seq):value=Seq(value)
        m=re.fullmatch(re.escape(S)+r'\.\$vgo_passengers\.\{\$i\}\.\$(\w+)',name)
        if m:
            entry=self.state['vgo_passengers'][self.vars['i']-1]
            if remove:entry.pop(m[1],None)
            else:entry[m[1]]=value
        else:super().assign(name,value,remove)

    def execute(self,nodes):
        previous=False
        for n in nodes:
            tag=n.tag
            if tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif tag=='do_for_each':
                entries=list(enumerate(self.expr(n.get('in')),1))
                if n.get('reverse')=='true':entries.reverse()
                for index,value in entries:
                    self.vars[n.get('name')[1:]]=value
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=index
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif tag=='include_actions':
                if n.get('ref')=='PassengerRoomPointsV32':
                    self.vars['pointlist']=Seq([self.seat] if self.vars['pointcontainer'] is self.ship else [self.exit] if self.available_exits else [])
                else:raise AssertionError('Unexpected library '+n.get('ref'))
            elif tag=='find_npc_waypoint':
                self.assign(n.get('name'),Seq([self.exit] if self.available_exits else []))
            elif tag=='remove_npc_template':
                template=self.vars['entry']['template'];self.ordering.append(('release',template))
                if self.release_succeeds:self.roster.discard(template)
            elif tag=='add_actor_to_room':
                actor=self.expr(n.get('actor'));slot=self.expr(n.get('slot'))
                placed=self.place_succeeds
                if placed and not self.placement_misreports:actor.exists=True;actor.room=slot.component
                self.placements.append((actor,slot,placed));self.assign(n.get('result'),placed)
            elif tag=='remove_actor_from_room':
                actor=self.expr(n.get('actor'));self.removed.append(actor);actor.exists=False
            elif tag=='signal_objects':
                actor=self.expr(n.get('object'));self.signals.append(actor)
                self.ordering.append(('walk',self.vars['entry']['template']))
                if self.native_walk_arrives:actor.room=self.stationroom
            elif tag in ['set_entity_role','set_entity_role_object','set_entity_traits','clear_actor_roomslot']:pass
            elif tag=='run_script' and n.get('name')=="'vardath.go.passengers.pay'":
                result=self.run('vardath.go.passengers.pay')
                if n.get('result'):self.assign(n.get('result'),result)
            else:super().execute([n])

    def transfer(self):
        root=E.parse(MOD/'md/VGO_State.xml').getroot()
        self.execute(root.find(".//library[@name='PassengerDisembarkV35']/actions"))

    def complete(self):
        self.transfer();self.age+=2;self.transfer();self.age+=5;self.transfer()
        return self.state.get('vgo_taxi_delivered',False)

class PassengerCompletion(unittest.TestCase):
    def test_taxi_releases_only_booked_templates_before_native_walking(self):
        v=PassengerVM();v.roster.add(999)
        self.assertTrue(v.complete());self.assertEqual(v.roster,{999})
        for i in [1,2]:self.assertLess(v.ordering.index(('release',i)),v.ordering.index(('walk',i)))
        self.assertEqual(v.money,10000000);self.assertEqual(v.state['vgo_taxi_delivered_count'],2)
    def test_tour_has_the_same_real_departure_path_after_full_itinerary(self):
        v=PassengerVM(job=5,count=10);self.assertTrue(v.complete())
        self.assertEqual(len(v.removed),10);self.assertEqual(v.state['vgo_taxi_completed_service'],5)
    def test_tour_cannot_disembark_or_charge_before_all_sites_and_sectors(self):
        for sites,sectors in [(9,3),(10,2)]:
            v=PassengerVM(job=5);v.state['vgo_tour_trip']=Seq(range(sites));v.state['vgo_tour_sectors']=Seq(range(sectors))
            self.assertFalse(v.complete());self.assertEqual(v.roster,{1,2});self.assertEqual(v.signals,[])
    def test_partial_exit_never_completes_or_pays_entire_group(self):
        v=PassengerVM();v.native_walk_arrives=False;v.transfer()
        v.actors[0].room=v.stationroom;v.age+=5;v.transfer();v.age+=5;v.transfer()
        self.assertEqual(v.vars['completed'],1);self.assertFalse(v.state.get('vgo_taxi_delivered',False))
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
    def test_releasing_roster_is_not_delivery(self):
        v=PassengerVM();v.native_walk_arrives=False;v.transfer()
        self.assertEqual(v.roster,set());self.assertFalse(v.state.get('vgo_taxi_delivered',False))
        self.assertEqual(len(v.state['vgo_passengers']),2);self.assertEqual(v.removed,[])
    def test_false_arrival_flag_cannot_replace_actual_station_room(self):
        v=PassengerVM();v.native_walk_arrives=False
        for e in v.state['vgo_passengers']:e['arrived']=True
        self.assertFalse(v.complete());self.assertEqual(v.removed,[])
    def test_visible_blocked_walk_recovers_same_actor_only_after_two_minutes(self):
        v=PassengerVM();v.native_walk_arrives=False;original=list(v.actors);v.transfer()
        v.age+=119;v.transfer();self.assertEqual(v.placements,[])
        v.age+=1;v.transfer();self.assertEqual([x[0] for x in v.placements],original)
        self.assertFalse(v.state.get('vgo_taxi_delivered',False));v.age+=5;v.transfer()
        self.assertTrue(v.state['vgo_taxi_delivered']);self.assertEqual(v.actors,original)
    def test_offscreen_transfer_uses_same_actor_and_observes_actual_room(self):
        v=PassengerVM();v.visible=False;original=list(v.actors)
        self.assertTrue(v.complete());self.assertEqual([p[0] for p in v.placements],original)
        self.assertEqual(v.signals,[])
    def test_rejected_native_transfer_never_delivers_or_pays(self):
        v=PassengerVM();v.visible=False;v.place_succeeds=False
        self.assertFalse(v.complete());self.assertEqual(v.removed,[])
        self.assertTrue(all(e['released'] for e in v.state['vgo_passengers']))
        self.assertFalse(v.run('vardath.go.passengers.pay'))
    def test_native_true_without_actual_room_change_is_not_departure(self):
        v=PassengerVM();v.visible=False;v.placement_misreports=True
        self.assertFalse(v.complete());self.assertEqual(v.removed,[])
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
    def test_disconnected_cue_actor_is_reconnected_without_creating_a_new_npc(self):
        v=PassengerVM();original=list(v.actors);v.actors[0].exists=False
        self.assertTrue(v.complete());self.assertEqual(v.actors,original)
        self.assertIn(original[0],[p[0] for p in v.placements])
    def test_non_walkable_pier_can_use_real_station_transport_point(self):
        v=PassengerVM();v.pier=False;v.visible=False;self.assertTrue(v.complete())
    def test_absent_station_points_keep_roster_manifest_and_fare_unpaid(self):
        v=PassengerVM();v.available_exits=False;self.assertFalse(v.complete())
        self.assertEqual(v.roster,{1,2});self.assertEqual(v.placements,[]);self.assertEqual(v.money,10000000)
    def test_failed_template_release_does_not_walk_or_complete(self):
        v=PassengerVM();v.release_succeeds=False;self.assertFalse(v.complete())
        self.assertEqual(v.signals,[]);self.assertEqual(v.roster,{1,2})
    def test_save_reload_style_retry_keeps_per_npc_departure_deadline(self):
        v=PassengerVM();v.native_walk_arrives=False;v.transfer()
        started=[e['exitstarted'] for e in v.state['vgo_passengers']]
        v.state=copy.deepcopy(v.state);v.vars={"ship":v.ship,"station":v.station};v.age+=125;v.transfer()
        self.assertEqual([e['exitstarted'] for e in v.state['vgo_passengers']],started)
        v.age+=5;v.transfer();self.assertTrue(v.state['vgo_taxi_delivered'])

class PassengerFares(unittest.TestCase):
    def delivered(self,job=2):
        v=PassengerVM(job=job);self.assertTrue(v.complete());return v
    def test_taxi_fare_is_8000_per_delivered_npc_and_cannot_duplicate(self):
        v=self.delivered();before=v.money;self.assertTrue(v.run('vardath.go.passengers.pay'))
        self.assertEqual(v.money-before,1600000);self.assertEqual(v.receipts,[1600000]);self.assertEqual(v.state['vgo_taxi_paid_id'],7)
        v.run('vardath.go.passengers.pay');self.assertEqual(v.money-before,1600000)
    def test_full_luxury_fare_and_native_receipt_follow_actual_departure(self):
        v=self.delivered(job=5);before=v.money;self.assertTrue(v.run('vardath.go.passengers.pay'))
        self.assertEqual(v.money-before,100000000);self.assertEqual(v.receipts,[100000000])
    def test_player_station_or_relation_change_cannot_erase_booked_fare(self):
        for faction in [PLAYER,Obj('changed',dock_ok=False)]:
            v=self.delivered();v.state['vgo_taxi_faction']=faction;before=v.money
            self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.money-before,1600000)
            self.assertEqual(v.reputation,[])
    def test_zero_credit_is_not_marked_paid_and_can_retry(self):
        v=self.delivered();v.credit_limit=0;self.assertFalse(v.run('vardath.go.passengers.pay'))
        self.assertNotIn('vgo_taxi_paid_id',v.state);self.assertTrue(v.state['vgo_taxi_delivered']);self.assertEqual(v.receipts,[])
        v.credit_limit=None;v.age+=60;self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.receipts,[1600000])
    def test_partial_credit_save_retry_requests_only_unpaid_balance(self):
        v=self.delivered();v.credit_limit=600000;self.assertFalse(v.run('vardath.go.passengers.pay'))
        self.assertEqual(v.state['vgo_taxi_fare_received'],600000);self.assertNotIn('vgo_taxi_paid_id',v.state)
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(len(v.reward_requests),1)
        v.state=copy.deepcopy(v.state);v.credit_limit=None;v.age+=60
        self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[1600000,1000000])
        self.assertEqual(sum(v.receipts),1600000);self.assertEqual(v.outcomes,["'completed'"])
    def test_fare_survives_minimum_reward_change_after_booking(self):
        v=self.delivered();v.state['vgo_minreward']=999999999
        self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.state['vgo_taxi_fare_received'],1600000)
    def test_paid_or_wrong_service_contract_never_rewards(self):
        v=self.delivered();v.state['vgo_taxi_paid_id']=7;self.assertTrue(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
        v=self.delivered();v.state['vgo_taxi_completed_service']=5;self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
    def test_a_live_manifest_or_incomplete_tour_can_never_collect_a_fare(self):
        v=PassengerVM();v.state.update(vgo_taxi_completed_id=7,vgo_taxi_delivered=True,vgo_taxi_delivered_count=2,vgo_taxi_completed_service=2)
        self.assertFalse(v.run('vardath.go.passengers.pay'));self.assertEqual(v.reward_requests,[])
        v=self.delivered(job=5);v.state['vgo_tour_trip']=Seq(range(9));self.assertFalse(v.run('vardath.go.passengers.pay'))
    def test_generic_reward_delegates_to_observed_passenger_accounting(self):
        v=self.delivered();self.assertTrue(v.run('vardath.go.reward'));self.assertEqual(v.receipts,[1600000])
    def test_repeat_disabled_waits_for_settlement_in_worker(self):
        r=xml('vardath.go.worker');b=r.find(".//do_if[@value='$success']/do_if")
        self.assertIsNotNone(b.find("run_script[@result='$done'][@name=\"'vardath.go.reward'\"]"))
        self.assertIsNone(b.find("set_value[@name='$done'][@exact='true']"))

if __name__=='__main__':unittest.main(verbosity=2)
