#!/usr/bin/env python3
"""Exercise the native dispatch boundary and shipped passenger work with mocks.

The log shows DockAt -> Undock, a boundary omitted by earlier isolated tests.
This model evaluates the actual shipped native patch before executing delivery
XML. It is not X4 and cannot establish runtime/load-order or NPC pathfinding.
"""
import re
import unittest
import xml.etree.ElementTree as E
from lxml import etree
from crystal_commerce_contracts import Obj, NULL, BUYER, SECTOR, S, Returned, Continued, Broken, WARES, VM as BaseVM
from log8_recovery_contracts import RecoveryVM
from passenger_completion_contracts import PassengerVM, Seq, MOD, xml

O='player.entity.$vgo_objects.{$object}'
class DockBoundary(RecoveryVM):
    def __init__(self,role='taxi'):
        super().__init__();self.current.id='VGO_'+role;self.state['vgo_runtime']=36
        self.vars.update(mockisclass=True,mockdock=False,mockpark=False)
    def expr(self,text):
        text=text.replace(O,S)
        text=text.replace('this.isplayerowned','this.ship.isplayerowned')
        text=text.replace('$object.isclass.ship','$mockisclass')
        text=text.replace('$object.isplayerowned','this.ship.isplayerowned')
        text=text.replace('@$object.dock.container','@this.ship.dock.container')
        text=text.replace('$object.order','this.ship.order')
        text=text.replace('$object.dock','$mockdock').replace('$object.parkedat','$mockpark')
        self.vars.update(mockdock=self.docked is not NULL)
        return super().expr(text)
    def native_prestart_undocks(self,patched=True):
        n=E.parse(MOD/'aiscripts/orders.base.xml').getroot()[0]
        condition=n.text if patched else n.text.split(' and not (',1)[0]
        # VGO orders are absent from the native allowed-docked ID list, so entering
        # this guard is sufficient for this named role to take its catch-all Undock.
        return bool(self.expr(condition))
    def complete_native_dock(self,patched=True):
        self.docked=BUYER;self.current=self.default
        return 'Undock' if self.native_prestart_undocks(patched) else self.default.id

class HandoffVM(PassengerVM):
    def __init__(self,role='taxi'):
        super().__init__(job=2 if role=='taxi' else 5)
        self.station=BUYER;self.stationroom.context=BUYER;self.vars['station']=BUYER
        self.state.update(vgo_taxi_dest=BUYER,vgo_taxi_pickup=BUYER,vgo_taxi_booked_destination=BUYER)
        self.own=Obj('worker',id='VGO_'+role,exists=True);self.current=self.own
        self.state['vgo_order']=self.own;self.docked=BUYER
        self.departures=0;self.dockcalls=0;self.ticks=0
    def expr(self,text):
        self.vars['mockcurrent']=self.current
        text=text.replace('this.ship.order','$mockcurrent')
        text=text.replace('$'+ 'station.dockingallowed.{this.ship}','true')
        text=text.replace('@'+S+'.$vgo_taxi_dest.dockingallowed.{this.ship}','true')
        text=text.replace(S+'.$vgo_taxi_dest.dockingallowed.{this.ship}','true')
        return super().expr(text)
    def execute(self,nodes):
        # Mirror the base model's branch handling so nested waits execute this hook.
        prev=False
        for n in nodes:
            if n.tag=='do_if':
                prev=bool(self.expr(n.get('value')))
                if prev:self.execute(n)
            elif n.tag=='do_else':
                if not prev:self.execute(n)
                prev=False
            elif n.tag=='run_script':
                name=n.get('name').strip("'")
                if name=='vardath.go.passengers.destination':result=self.run(name)
                elif name=='vardath.go.dock':self.dockcalls+=1;result=self.docked is BUYER
                elif name=='vardath.go.depart':self.departures+=1;self.docked=NULL;result=True
                elif name=='vardath.go.travel':raise AssertionError('Already docked; must not navigate')
                else:raise AssertionError('Unexpected helper '+name)
                if n.get('result'):self.assign(n.get('result'),result)
            elif n.tag=='do_while':
                while self.expr(n.get('value')):
                    self.ticks+=1
                    if self.ticks>50:raise AssertionError('Unbounded handoff loop')
                    self.execute(n)
            elif n.tag=='wait':self.age+=self.expr(n.get('exact'));self.transfer()
            else:super().execute([n])

class GalaxyVM(DockBoundary):
    def __init__(self,role='morale'):
        super().__init__(role);self.vars['distance']=3000
        self.remote=Obj('remote',exists=True,owner=SECTOR.owner,knownname='Remote')
        self.current_sector=SECTOR
        self.target=Obj('friendly',exists=True,isoperational=True,sector=self.remote,size=100,
                        knownname='Freighter',owner=BUYER.owner,pilot=Obj('computer',exists=False))
        self.vars.update(target=self.target,destination=self.remote)
        self.people={1:5,2:15};self.target_state={};self.skill_changes=[]
    def expr(self,text):
        text=text.replace('player.entity.$vgo_objects?','true').replace(S+'?','true')
        text=text.replace('$destination.isclass.sector','true')
        text=re.sub(r'(\d+)km',lambda m:str(int(m[1])*1000),text)
        text=text.replace('player.entity.$vgo_objects.{$target}.$vgo_cooldowns?', 'true' if 'cooldowns' in self.target_state else 'false')
        text=text.replace('player.entity.$vgo_objects.{$target}?','true')
        text=text.replace('$target.ishostileto.{this.ship}','false')
        text=text.replace('$target.people.list','$mockpeople')
        text=text.replace('$target.people.{$person}.exists','$mockpersonexists')
        text=text.replace('$target.people.{$person}.role',"'crew'")
        text=text.replace('$target.people.{$person}.skill.morale','$mockmorale')
        text=text.replace('entityrole.passenger',"'passenger'")
        text=text.replace('this.ship.distanceto.{$target}','$mocktargetdistance')
        text=text.replace('$sector.owner.hasrelation.enemy.{faction.player}','false')
        text=text.replace(S+'.$vgo_scope.indexof.{$sector}','true')
        text=text.replace('@$target','$target').replace('100ms','0.1')
        self.vars.update(mockpeople=list(self.people),mockpersonexists=self.vars.get('person') in self.people,
            mockmorale=self.people.get(self.vars.get('person'),0),
            mocktargetdistance=0 if self.current_sector is self.remote else 100000)
        return super().expr(text)
    def assign(self,name,value,remove=False):
        if name.startswith('player.entity.$vgo_objects.{$target}'):
            if name.endswith('.$vgo_cooldowns'):self.target_state['cooldowns']=value
            elif name.endswith('.{9}'):self.target_state['cooldown9']=value
            return
        super().assign(name,value,remove)
    def execute(self,nodes):
        previous=False
        for n in nodes:
            if n.tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag=='do_all':
                for i in range(int(self.expr(n.get('exact')))):
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i+1
                    try:self.execute(n)
                    except Broken:break
            elif n.tag=='do_for_each':
                for i,p in enumerate(self.expr(n.get('in')),1):
                    self.vars[n.get('name')[1:]]=p
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif n.tag=='run_script' and n.get('name')=="'move.generic'":
                self.vars['useknownpath']=self.expr(n.find("param[@name='useknownpath']").get('value'))
                expression=E.parse(MOD/'aiscripts/move.generic.xml').getroot()[0].text
                self.moves_arrive=not self.expr(expression)
                super().execute([n])
            elif n.tag=='run_script' and n.get('name')=="'vardath.go.approach'":
                for p in n:self.vars[p.get('name')]=self.expr(p.get('value'))
                result=self.run('vardath.go.approach');self.assign(n.get('result'),result)
            elif n.tag=='get_safe_pos':self.assign(n.get('result'),'safe-offset')
            elif n.tag=='add_skill':
                person=self.vars['person'];before=self.people[person]
                self.people[person]=min(15,before+int(n.get('exact')))
                self.skill_changes.append((person,before,self.people[person]))
            else:super().execute([n])

class NativeDockingBoundary(unittest.TestCase):
    def test_unpatched_native_rule_reproduces_dock_then_undock(self):
        v=DockBoundary();v.run('vardath.go.dock')
        self.assertEqual(v.complete_native_dock(patched=False),'Undock')
    def test_same_boundary_now_resumes_each_docking_service_at_its_station(self):
        for role in ['taxi','tour','crystal','hacker','hackonce']:
            v=DockBoundary(role);v.run('vardath.go.dock')
            self.assertEqual(v.complete_native_dock(),'VGO_'+role)
            self.assertEqual(len(v.queue),1)
    def test_service_dock_is_saved_before_native_order_is_queued(self):
        v=DockBoundary();v.run('vardath.go.dock')
        self.assertIs(v.state['vgo_service_dock'],BUYER)
        self.assertEqual(v.state['vgo_service_dock_until'],1000+1800)
        self.assertIs(v.state['vgo_dock_target'],BUYER)
    def test_wrong_station_expired_lease_player_order_and_other_roles_keep_native_rules(self):
        for case in ['wrongstation','expired','playerorder','otherrole','ownership','nottracked']:
            v=DockBoundary();v.run('vardath.go.dock');v.docked=BUYER
            if case=='wrongstation':v.docked=Obj('other',isoperational=True)
            elif case=='expired':v.age=v.state['vgo_service_dock_until']+1
            elif case=='playerorder':v.current=Obj('manual',id='MoveWait',exists=True)
            elif case=='otherrole':v.current.id='VGO_morale'
            elif case=='ownership':v.owned=False
            else:v.state['vgo_order']=NULL
            self.assertTrue(v.native_prestart_undocks(),case)
    def test_new_worker_keeps_existing_party_until_actual_destination_departure(self):
        for role in ['taxi','tour']:
            boundary=DockBoundary(role);boundary.run('vardath.go.dock')
            self.assertEqual(boundary.complete_native_dock(),'VGO_'+role)
            p=HandoffVM(role);original=list(p.actors)
            self.assertEqual(p.run('vardath.go.passengers.deliver'),2)
            self.assertEqual(p.departures,0);self.assertEqual(p.dockcalls,1)
            self.assertEqual(p.actors,original);self.assertTrue(p.state['vgo_taxi_delivered'])
    def test_dispatcher_started_undock_cannot_be_overridden_by_delivery(self):
        p=HandoffVM();p.current=Obj('nativeUndock',id='Undock',exists=True)
        self.assertEqual(p.run('vardath.go.passengers.deliver'),0)
        self.assertEqual(p.dockcalls,0);self.assertEqual(p.departures,0);self.assertEqual(p.removed,[])
    def test_crystal_sale_can_settle_real_stock_after_docked_handoff(self):
        b=DockBoundary('crystal');b.run('vardath.go.dock');self.assertEqual(b.complete_native_dock(),'VGO_crystal')
        v=BaseVM({WARES[0]:4});v.state.update(vgo_service_dock=BUYER,vgo_service_dock_until=b.state['vgo_service_dock_until'])
        self.assertTrue(v.run('vardath.go.sellcrystals'));self.assertEqual(v.get('vgo_crystal_sold'),4)
    def test_explicit_departure_releases_the_service_lease_before_movement(self):
        r=xml('vardath.go.depart');a=list(r.find('attention/actions'))
        cleared=[i for i,n in enumerate(a) if n.tag=='remove_value' and 'vgo_service_dock' in n.get('name','')]
        move=next(i for i,n in enumerate(a) if n.tag=='run_script' and n.get('name')=="'move.undock'")
        self.assertEqual(len(cleared),2);self.assertLess(max(cleared),move)
    def test_dock_monitor_keeps_the_handoff_when_finite_dockat_finishes(self):
        r=E.parse(MOD/'md/VGO_State.xml').find(".//cue[@name='DockOrdersV34']")
        self.assertFalse(any('vgo_service_dock' in n.get('name','') for n in r.iter('remove_value')))

class BookedDestination(unittest.TestCase):
    def test_taxi_locks_existing_booked_station(self):
        v=HandoffVM();self.assertTrue(v.run('vardath.go.passengers.destination'))
        other=Obj('other',exists=True,isoperational=True);v.state['vgo_taxi_dest']=other
        self.assertTrue(v.run('vardath.go.passengers.destination'));self.assertIs(v.state['vgo_taxi_dest'],BUYER)
    def test_legacy_tour_restores_original_pickup_station(self):
        v=HandoffVM('tour');v.state.pop('vgo_taxi_booked_destination')
        v.state['vgo_taxi_dest']=Obj('oldalternate',exists=True,isoperational=True)
        self.assertTrue(v.run('vardath.go.passengers.destination'))
        self.assertIs(v.state['vgo_taxi_dest'],BUYER);self.assertIs(v.state['vgo_taxi_booked_destination'],BUYER)
    def test_unavailable_booked_station_preserves_passengers_and_cannot_pay(self):
        v=HandoffVM();v.state['vgo_taxi_booked_destination']=NULL
        v.state['vgo_taxi_dest']=NULL
        self.assertFalse(v.run('vardath.go.passengers.destination'))
        self.assertEqual(len(v.state['vgo_passengers']),2);self.assertEqual(v.reward_requests,[])
    def test_departure_at_different_station_cannot_release_or_pay_passengers(self):
        v=PassengerVM();v.state['vgo_taxi_booked_destination']=Obj('original',exists=True)
        self.assertFalse(v.complete());self.assertEqual(v.roster,{1,2});self.assertEqual(v.placements,[])
    def test_no_alternate_station_search_once_manifest_is_booked(self):
        find=xml('vardath.go.find');self.assertIsNone(find.find(".//find_station[@name='$alternates']"))
        task=xml('vardath.go.task.taxi')
        gate=next(n for n in task.iter('do_if') if n.find("set_value[@name='$sectors']") is not None)
        self.assertIn('not @'+S+'.$vgo_passengers.count',gate.get('value'))
        self.assertIn('not @'+S+'.$vgo_taxi_boarded',gate.get('value'))

class NativeRouteAndLog(unittest.TestCase):
    def test_all_thirteen_roles_can_take_the_shared_route_to_an_unmapped_sector(self):
        roles=['escort','taxi','scanner','mapper','tour','crystal','lure','demolition','morale','inspection','recruit','patrol','hacker']
        for role in roles:
            v=GalaxyVM(role);self.assertTrue(v.run('vardath.go.travel'),role)
            self.assertIs(v.current_sector,v.remote);self.assertEqual(len(v.native_moves),1)
    def test_morale_moves_to_remote_target_before_observed_crew_improvement(self):
        v=GalaxyVM();v.state['vgo_cooldown']=3600;before=v.age
        self.assertTrue(v.run('vardath.go.task.morale'))
        self.assertIs(v.current_sector,v.remote);self.assertTrue(v.native_moves)
        self.assertEqual(v.people,{1:6,2:15});self.assertEqual(v.skill_changes,[(1,5,6)])
        self.assertGreaterEqual(v.age-before,30);self.assertTrue(v.state['vgo_verified'])
        self.assertGreater(v.target_state['cooldown9'],v.age)
    def test_scoped_jump_discovery_honours_requested_known_path_setting(self):
        ops=E.parse(MOD/'aiscripts/move.generic.xml').getroot();self.assertEqual(len(ops),4)
        v=DockBoundary();v.vars['useknownpath']=False
        for op in ops:
            self.assertFalse(v.expr(op.text))
            v.state['vgo_runtime']=35;self.assertTrue(v.expr(op.text));v.state['vgo_runtime']=36
            v.current=Obj('manual',id='MoveWait',exists=True);self.assertTrue(v.expr(op.text));v.current=v.default
            v.vars['useknownpath']=True;self.assertTrue(v.expr(op.text));v.vars['useknownpath']=False
    def test_crystal_search_has_no_time_remainder_and_alternates_ore_and_silicon(self):
        r=xml('vardath.go.crystal.simulation');loop=r.find(".//do_for_each[@name='$tryware']")
        expression=loop.get('in');self.assertNotIn('%',expression)
        v=BaseVM();expression=expression.replace('ware.ore',"'ore'").replace('ware.silicon',"'silicon'")
        self.assertEqual(v.expr(expression),['ore','silicon'])
        toggle=next(n for n in r.iter('set_value') if n.get('name')==S+'.$vgo_crystal_silicon_next')
        v.execute([toggle]);self.assertEqual(v.expr(expression),['silicon','ore'])
    def test_new_native_diffs_use_valid_attribute_only_grammar(self):
        for name in ['orders.base.xml','move.generic.xml']:
            r=E.parse(MOD/'aiscripts'/name).getroot()
            self.assertTrue(all(n.tag=='replace' and not len(n) and n.get('sel').endswith(('/@value','/@useknownpath')) for n in r))

if __name__=='__main__':unittest.main(verbosity=2)
