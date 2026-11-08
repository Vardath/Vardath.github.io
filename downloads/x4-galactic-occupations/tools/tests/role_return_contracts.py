#!/usr/bin/env python3
"""Execute changed-role travel and background return XML with native actions mocked.

These checks cross the old crew-lock/shared-depart/native-move boundary. They are
not an X4 runtime, NPC pathfinding test or engine save/load test.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from crystal_commerce_contracts import Obj, NULL, BUYER, SECTOR, S, MOD, xml
from crystal_retail_contracts import RetailVM
from log12_return_contracts import ReturnVM
from lifecycle_contracts import LifecycleVM

ROLES = ['escort','taxi','scanner','mapper','tour','crystal','lure',
         'demolition','morale','inspection','recruit','patrol','hacker']


class MotionVM(ReturnVM):
    def __init__(self, role='patrol'):
        super().__init__();self.legacy_paid();self.native_moves=[]
        self.docked=NULL;self.ship.parkedat=NULL;self.ship.size=50
        self.change_role(role)
        self.remote=Obj('remote sector',exists=True,knownname='Another sector')
        self.target=Obj('destination',exists=True,isoperational=True,sector=self.remote,size=100,knownname='Target')
        self.vars.update(target=self.target,distance=3000)
    def change_role(self, role):
        self.order=Obj('new '+role,exists=True,id='VGO_'+role)
        self.ship.defaultorder=self.order;self.state['vgo_order']=self.order
    def expr(self,text):
        actor=self.state.get('vgo_crystal_shop_actor',NULL)
        text=text.replace('@'+S+'.$vgo_crystal_shop_actor.isclass.npc',
            'true' if actor and getattr(getattr(actor,'isclass',NULL),'npc',False) else 'false')
        text=text.replace('player.entity.$vgo_objects?', 'true').replace(S+'?', 'true')
        text=text.replace(S+'.$vgo_scope.indexof.{$sector}','true')
        text=text.replace('$sector.owner.hasrelation.enemy.{faction.player}','false')
        text=text.replace('this.ship.distanceto.{$target}',self.remembered(0 if self.ship.sector is self.target.sector else 100000))
        text=re.sub(r'(\d+)km',lambda m:str(int(m[1])*1000),text)
        return super().expr(text)
    def execute(self,nodes):
        previous=False
        for n in nodes:
            if n.tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag=='get_safe_pos':self.assign(n.get('result'),'safe offset')
            elif n.tag=='run_script' and n.get('name')=="'move.generic'":
                args={p.get('name'):self.expr(p.get('value')) for p in n}
                self.native_moves.append(args);self.ship.sector=args['destination']
                self.assign(n.get('result'),True)
            elif n.tag=='wait':self.age+=self.expr(n.get('exact'))
            else:super().execute([n])


class ChangedRoleDeparture(unittest.TestCase):
    def test_all_thirteen_airborne_roles_cross_actual_depart_and_native_approach(self):
        for role in ROLES:
            with self.subTest(role=role):
                v=MotionVM(role);actor=v.crew;cash=v.money
                payload=copy.deepcopy(v.state)
                self.assertTrue(v.run('vardath.go.approach'))
                self.assertEqual(len(v.native_moves),1)
                self.assertIs(v.native_moves[0]['destination'],v.remote)
                self.assertFalse(v.native_moves[0]['useknownpath'])
                self.assertIs(actor.room,v.shoproom);self.assertIs(v.crew,actor)
                for key in payload:
                    if key.startswith('vgo_crystal_'):self.assertEqual(v.state[key],payload[key],key)
                self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[])
                self.assertFalse(any(e[0]=='undock' for e in v.events))
    def test_all_other_docked_roles_can_undock_with_old_representative_ashore(self):
        for role in ROLES:
            if role=='crystal':continue
            with self.subTest(role=role):
                v=MotionVM(role);v.docked=BUYER
                self.assertTrue(v.run('vardath.go.depart'));self.assertIs(v.docked,NULL)
                self.assertIs(v.crew.room,v.shoproom)
                self.assertEqual([e[0] for e in v.events],['undock'])
    def test_current_crystal_job_waits_only_at_its_actual_retail_dock(self):
        v=MotionVM('crystal');v.docked=BUYER
        self.assertFalse(v.run('vardath.go.depart'));self.assertIs(v.docked,BUYER)
        v.docked=Obj('another dock',exists=True)
        self.assertTrue(v.run('vardath.go.depart'));self.assertIs(v.docked,NULL)
    def test_stale_deployed_flag_without_a_real_npc_cannot_lock_departure(self):
        v=MotionVM('crystal');v.docked=BUYER;v.state['vgo_crystal_shop_actor']=NULL
        self.assertTrue(v.run('vardath.go.depart'))
    def test_existing_ashore_crew_does_not_override_direct_orders_or_player_control(self):
        for reason in ['direct','occupied','owner']:
            v=MotionVM();v.docked=BUYER
            if reason=='direct':v.direct=True
            elif reason=='occupied':v.occupied=True
            else:v.owned=False
            self.assertFalse(v.run('vardath.go.approach'))
            self.assertEqual(v.native_moves,[]);self.assertIs(v.docked,BUYER)
            self.assertIs(v.crew.room,v.shoproom)
    def test_background_shop_return_cannot_replace_new_foreground_job_status(self):
        v=MotionVM();v.state['vgo_status']='Patrolling a real trade route'
        cash=v.money;v.tick();v.age+=300;v.tick()
        self.assertEqual(v.state['vgo_status'],'Patrolling a real trade route')
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[])
        self.assertIs(v.crew.room,v.shoproom)
    def test_destroyed_or_absent_saved_worker_cannot_undock_a_later_direct_order(self):
        for tracked in [NULL,None]:
            v=MotionVM();v.docked=BUYER
            if tracked is None:v.state.pop('vgo_order')
            else:v.state['vgo_order']=tracked
            self.assertFalse(v.run('vardath.go.depart'))
            self.assertIs(v.docked,BUYER);self.assertEqual(v.events,[])
    def test_redock_returns_original_npc_without_clobbering_new_job_or_paying_twice(self):
        v=MotionVM();v.state['vgo_status']='Patrol suspended at dock';v.docked=BUYER
        cash=v.money;actor=v.crew;v.tick();v.tick()
        self.assertIs(v.crew,actor);self.assertIs(actor.room,v.shiproom)
        self.assertEqual(v.state['vgo_status'],'Patrol suspended at dock')
        self.assertEqual(v.money,cash);self.assertEqual(v.reward_requests,[])
        self.assertTrue(v.run('vardath.go.depart'))


class RecallAndUpgradeIsolation(unittest.TestCase):
    def test_repeated_role_changes_do_not_reset_twenty_minute_crew_recall(self):
        v=LifecycleVM();prefix=v.crew_visit();v.library('RecallCrystal')
        due=v.state[prefix+'_away_since']+1200
        for role in ROLES:
            v.ship.order=Obj(role,exists=True,id='VGO_'+role);v.ship.defaultorder=v.ship.order
            v.state['vgo_status']='New role '+role;v.age+=30;v.library('RecallCrystal')
            self.assertEqual(v.state[prefix+'_away_since']+1200,due)
            self.assertEqual(v.state['vgo_status'],'New role '+role)
        v.age=due-1;v.library('RecallCrystal');self.assertIs(v.crew.room,v.stationroom)
        v.age=due;v.library('RecallCrystal');self.assertIs(v.crew.room,v.shiproom)
        self.assertEqual(v.logs.count("'Galactic Occupations: background crew recovery'"),1)
        self.assertEqual(v.reward_requests,[])
    def test_captain_recall_defers_while_player_occupies_ship_then_uses_same_actor(self):
        v=LifecycleVM();prefix=v.crew_visit();v.crew.controlpost='aipilot';v.occupied=True
        v.library('RecallCrystal');v.age+=1200;v.library('RecallCrystal')
        self.assertIs(v.crew.room,v.stationroom);self.assertFalse(v.get(prefix+'_recalled'))
        v.occupied=False;v.age+=30;v.library('RecallCrystal')
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.crew.controlpost,'aipilot')
    def test_old_hacker_status_and_upgrade_guards_are_scoped_to_its_own_current_order(self):
        r=E.parse(MOD/'md/VGO_Hacker.xml').getroot()
        ops=r.find(".//cue[@name='Operations']/actions")
        for node in ops.iter('set_value'):
            if node.get('name','').endswith('.$vgo_status'):
                parents=[p for p in ops.iter() if node in list(p)]
                self.assertEqual(parents[0].get('value'),'$statusowned')
        w=xml('vardath.go.worker');patch=w.find("patch[@sinceversion='20']")
        self.assertIsNotNone(patch.find("signal_objects[@param=\"'vardath.go.restart42'\"]"))
        trigger=next(n for n in w.iter('handler') if n.find(".//event_object_signalled[@param=\"'vardath.go.restart42'\"]") is not None)
        condition=trigger.find('actions/do_if').get('value')
        self.assertIn('vgo_hack_deployed',condition);self.assertIn('vgo_hack_order',condition)
        self.assertIn('this.assignedcontrolled.order ==',condition)
    def test_worker_scanner_uses_assigned_ship_equipment_for_capital_and_small_ships(self):
        w=xml('vardath.go.worker');gate=next(n for n in w.iter('do_if') if '$job == 3 and' in n.get('value',''))
        self.assertEqual(gate.get('value'),'$job == 3 and this.ship.maxscanlevel le 0')


if __name__=='__main__':unittest.main(verbosity=2)
