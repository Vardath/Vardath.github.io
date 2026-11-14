#!/usr/bin/env python3
"""Execute shipped recovery/braking XML against refused and interrupted native actions.

Checks control-flow boundaries only; engine camera, teleport and collision behaviour
must be checked in X4 with the installed spacesuit mods.
"""
import copy
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E

TOP=Path(__file__).resolve().parents[2]
SUIT=E.parse(TOP/'vardath_galactic_occupations/md/VGO_Spacesuit.xml').getroot()
BRAKE=E.parse(TOP.parent/'x4-kopis-production-cheat/vardath_kopis_production_cheat/md/vardath_astrid_tours.xml').getroot()

class Object:
    def __init__(self,**values):self.__dict__.update(values)
    def __getattr__(self,key):return NONE
    def __bool__(self):return bool(self.__dict__.get('exists',False))
    def __deepcopy__(self,memo):return self
NONE=Object(exists=False)

class BoundaryVM:
    def __init__(self,root=SUIT):
        self.root=root;self.state={};self.local={};self.calls=[];self.logs=[]
        self.accept=True;self.anchor_accept=True;self.anchor_event=True;self.signals=[];self.native={};self.eventroom=NONE
        self.sector=Object(exists=True);self.zone=Object(exists=True,sector=self.sector,isclass=Object(zone=True))
        # Class flags are booleans even though component references are objects.
        self.zone.isclass.zone=True
        self.source=Object(exists=True,sector=self.sector,isplayerowned=True,
            isclass=Object(ship=True,spacesuit=False),dock=Object(container=NONE),
            macro='astrid',speed=10000,travel=Object(active=True),boost=Object(active=False))
        self.room=Object(exists=True,context=self.source)
        self.suit=Object(exists=True,isclass=Object(ship=True,spacesuit=True),sector=self.sector)
        flight=Object(throttle=0,horizontal=0,vertical=0,pitch=0,yaw=0,roll=0,matchspeed=False)
        self.player=Object(exists=True,age=100,sector=self.sector,room=self.room,ship=self.source,
            occupiedship=NONE,spacesuit=NONE,controlled=NONE,entity=Object(controlled=NONE,isintransit=False),
            isinconversation=False,teleport_permission=True,flightassist=True,autopilottarget=NONE,input=Object(flight=flight))
        self.event=[self.source,self.zone]
        self.initializing='Init' if root is SUIT else 'BrakeStateV116'
        self.actions(root.find(".//cue[@name='Init']/actions") if root is SUIT else root.find(".//cue[@name='BrakeStateV116']/actions"))
        self.initializing=None
    def expr(self,value):
        t=value
        t=re.sub(r'event\.param3\.\{(\d+)\}',lambda m:'event['+str(int(m[1])-1)+']',t)
        t=re.sub(r'\bevent\.param\b','eventroom',t)
        t=re.sub(r'player\.canforceteleportto\.\{[^}]+\}','player.teleport_permission',t)
        t=re.sub(r'\b(Init|BrakeStateV116)\.\$(\w+)',lambda m:'state.get('+repr(m[1]+'.'+m[2])+', NONE)',t)
        t=re.sub(r'([\w.]+)\.hascontext\.\{([^}]+)\}',r'context(\1,\2)',t)
        t=re.sub(r'\$(\w+)',lambda m:'local.get('+repr(m[1])+', NONE)',t)
        t=t.replace('macro.ship_vardath_astrid_tours_macro',repr('astrid'))
        t=t.replace('@','')
        t=re.sub(r'([0-9]+(?:\.[0-9]+)?)ms\b',lambda m:str(float(m[1])/1000),t)
        t=re.sub(r'([0-9]+(?:\.[0-9]+)?)[sm]\b',r'\1',t)
        for a,b in [('true','True'),('false','False'),('null','NONE'),('ge','>='),('gt','>'),('le','<='),('lt','<')]:t=re.sub(r'\b'+a+r'\b',b,t)
        env={'state':self.state,'local':self.local,'player':self.player,'NONE':NONE,'event':self.event,
             'context':lambda a,b:a.exists and a.context is b,'eventroom':self.eventroom}
        try:return eval(t,{'__builtins__':{}},env)
        except Exception as e:raise AssertionError(value+' => '+t) from e
    def actions(self,nodes):
        if nodes is None:return
        previous=False
        for n in nodes:
            if n.tag in ['do_if','do_elseif']:
                if n.tag=='do_elseif' and previous:continue
                previous=bool(self.expr(n.get('value')))
                if previous:self.actions(n)
            elif n.tag=='do_else':
                if not previous:self.actions(n)
                previous=False
            elif n.tag=='set_value':
                name=n.get('name');v=self.expr(n.get('exact'))
                if name.startswith('$') and self.initializing:self.state[self.initializing+'.'+name[1:]]=v
                elif name.startswith('$'):self.local[name[1:]]=v
                else:self.state[name.replace('.$','.')]=v
            elif n.tag=='include_actions':self.actions(self.root.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif n.tag=='teleport_player_to_spacesuit':
                self.calls.append(dict(n.attrib))
                # Phase is committed before calling native code; refusal cannot repeat the exit.
                assert self.state['Init.Stage']==2
                if self.accept:self.healthy()
            elif n.tag=='teleport_player':
                self.calls.append(('teleport',dict(n.attrib)))
                assert self.state['Init.Stage'] in [1,3]
                if self.anchor_accept:
                    self.player.room=Object(exists=True,context=self.source)
                    self.player.controlled=NONE;self.player.entity.controlled=NONE
                    self.player.spacesuit=NONE;self.player.occupiedship=NONE
                    self.player.ship=self.source;self.player.entity.isintransit=False
                    if self.anchor_event:
                        self.eventroom=self.player.room;self.cue('ShipResetObservedV46')
            elif n.tag=='set_object_velocity':
                ship=self.expr(n.get('object'));self.calls.append(('velocity',ship));ship.speed=0
            elif n.tag=='disable_travel_mode':
                ship=self.expr(n.get('ship'));self.calls.append(('travel',ship));ship.travel.active=False
            elif n.tag=='set_playership_throttle':self.player.input.flight.throttle=self.expr(n.get('value'))
            elif n.tag=='signal_cue':self.signals.append(n.get('cue'))
            elif n.tag=='write_to_logbook':self.logs.append(n.get('title'))
            elif n.tag=='debug_text':pass
            else:raise AssertionError('Unhandled shipped command '+n.tag)
    def cue(self,name):
        cue=self.root.find(".//cue[@name='"+name+"']")
        for n in cue.findall('./conditions/check_value'):
            if not self.expr(n.get('value')):return
        self.actions(cue.find('actions'))
    def watch(self):
        if self.state.get('Init.Pending'):self.actions(SUIT.find(".//library[@name='Watch']/actions"))
    def healthy(self):
        self.player.controlled=self.suit;self.player.entity.controlled=self.suit
        self.player.spacesuit=self.suit;self.player.ship=self.suit;self.player.room=NONE
        self.player.entity.isintransit=False
    def tick(self):self.cue('BrakeAssist_v112')

class SpacesuitRedockingSafety(unittest.TestCase):
    """Prevent any delayed teleport/eject from ordinary transporter use."""
    def test_legacy_cues_preserved_for_save_import(self):
        expected={'Init','Confirmed','ShipResetObservedV46','Poll','Verify','Loaded','UpgradeV46'}
        self.assertTrue(expected.issubset({c.get('name') for c in SUIT.findall('.//cue')}))
        for name in ('Clear','Healthy','SnapshotV46','ReturnToShipV46','Watch'):
            self.assertIsNotNone(SUIT.find(".//library[@name='"+name+"']"))

    def test_legacy_cues_have_no_forced_player_movement(self):
        # No movement anywhere in an automatic, saved or legacy v46 path.
        automatic=('Init','Confirmed','ShipResetObservedV46','Poll','Verify',
                   'Loaded','UpgradeV46')
        forbidden=('teleport_player','teleport_player_to_spacesuit',
                  'set_player_entity_position','set_entity_controlpost',
                  'create_ship','destroy_object')
        for cue in automatic:
            actions=SUIT.find(".//cue[@name='"+cue+"']/actions")
            for name in forbidden:
                self.assertEqual(list(actions.iter(name)),[],(cue,name))
        for name in ('Clear','Healthy','SnapshotV46','ReturnToShipV46','Watch'):
            actions=SUIT.find(".//library[@name='"+name+"']/actions")
            for cmd in forbidden:
                self.assertEqual(list(actions.iter(cmd)),[],(name,cmd))
        self.assertFalse(SUIT.find(".//cue[@name='Confirmed']/actions").findall("set_value"))

    def test_manual_eva_and_board_are_explicit_and_native_bounded(self):
        eva=SUIT.find(".//cue[@name='ManualSafeEVAV56']")
        board=SUIT.find(".//cue[@name='ManualBoardV56']")
        recovery=SUIT.find(".//cue[@name='ManualInputRecoveryV56']")
        self.assertIsNotNone(eva);self.assertIsNotNone(board);self.assertIsNotNone(recovery)
        self.assertEqual(eva.find('./conditions/event_ui_triggered').get('control'),"'safe_eva'")
        self.assertEqual(board.find('./conditions/event_ui_triggered').get('control'),"'recover_board'")
        self.assertEqual(eva.find('./conditions/event_ui_triggered').get('screen'),"'VGO.Spacesuit'")
        self.assertEqual(board.find('./conditions/event_ui_triggered').get('screen'),"'VGO.Spacesuit'")
        eva_guard=eva.find('./actions/do_if')
        board_guard=board.find('./actions/do_if')
        for token in ('@$Target.isclass.ship','@$Target.isplayerowned',
                      '@player.room.context == $Target','not @player.spacesuit',
                      'not @player.entity.isintransit','not @$Target.isdocked'):
            self.assertIn(token,eva_guard.get('value'))
        for token in ('@$Target.isclass.ship','@$Target.isplayerowned',
                      '@player.spacesuit.isclass.spacesuit',
                      'not @player.entity.isintransit','@$Target.sector == player.sector',
                      '@$Target.distanceto.{player.spacesuit} le 2km'):
            self.assertIn(token,board_guard.get('value'))
        native_exit=eva_guard.find('teleport_player_to_spacesuit')
        self.assertEqual(native_exit.get('emergency'),'true')
        self.assertEqual(native_exit.get('instant'),'true')
        self.assertEqual(native_exit.get('allowinhighway'),'false')
        native_board=board_guard.find('teleport_player')
        self.assertEqual(native_board.get('object'),'$Target')
        self.assertEqual(native_board.get('control'),'false')
        self.assertEqual(native_board.get('instant'),'true')
        self.assertEqual(native_board.get('force'),'true')
        self.assertEqual(len(list(SUIT.iter('teleport_player'))),1)
        self.assertEqual(len(list(SUIT.iter('teleport_player_to_spacesuit'))),1)
        self.assertEqual(recovery.find('./conditions/event_cue_signalled').attrib,{})
        self.assertEqual(recovery.find('./delay').get('exact'),'2s')
        self.assertEqual(len(list(SUIT.iter('unlock_all_flight_input'))),1)
        self.assertEqual(len(list(SUIT.iter('unlock_all_shooting_input'))),1)
        self.assertEqual(len(list(recovery.iter('teleport_player'))),0)
        self.assertEqual(len(list(recovery.iter('teleport_player_to_spacesuit'))),0)

    def test_confirmed_event_is_now_inert(self):
        v=BoundaryVM()
        original=v.state.copy()
        for _ in range(5):
            v.cue('Confirmed');v.watch();v.player.age+=20
        self.assertEqual(v.calls,[])
        self.assertFalse(v.state.get('Init.Pending'))
        self.assertEqual(v.state.get('Init.Serial'),original.get('Init.Serial'))
        self.assertEqual(v.player.ship,v.source)

    def test_loaded_pending_v46_request_is_disarmed_immediately(self):
        v=BoundaryVM()
        v.state.update({'Init.Pending':True,'Init.Source':v.source,
                        'Init.Stage':1,'Init.Due':v.player.age-12})
        v.cue('Poll')
        self.assertFalse(v.state['Init.Pending'])
        self.assertEqual(v.calls,[])

    def test_all_legacy_recovery_library_paths_cannot_move_player(self):
        v=BoundaryVM()
        v.state['Init.Pending']=True
        for name in ('ReturnToShipV46','Watch'):
            v.actions(SUIT.find(".//library[@name='"+name+"']/actions"))
        self.assertFalse(v.state['Init.Pending'])
        self.assertEqual(v.calls,[])

    def test_teleport_event_does_not_trigger_another_teleport(self):
        v=BoundaryVM()
        v.state['Init.Pending']=True
        v.cue('ShipResetObservedV46')
        self.assertFalse(v.state['Init.Pending'])
        self.assertEqual(v.calls,[])

    def test_new_game_and_upgrade_clear_old_requests(self):
        for cue in ('Loaded','UpgradeV46'):
            v=BoundaryVM();v.state['Init.Pending']=True
            v.cue(cue)
            self.assertFalse(v.state['Init.Pending'])
            self.assertEqual(v.calls,[])

    def test_poll_stays_bounded_and_clearing_only(self):
        poll=SUIT.find(".//cue[@name='Poll']")
        self.assertEqual(poll.get('checkinterval'),'1s')
        self.assertEqual(len(poll.findall('./actions/include_actions[@ref="Clear"]')),1)
        self.assertEqual(list(poll.iter('wait')),[])

class AstridBrakeBoundary(unittest.TestCase):
    def vm(self):
        v=BoundaryVM(BRAKE);v.player.occupiedship=v.source
        v.player.controlled=v.source;v.player.entity.controlled=v.source;return v
    def test_release_at_full_travel_stops_in_two_and_half_seconds(self):
        v=self.vm();v.tick();self.assertEqual(v.state['BrakeStateV116.Due'],102.5)
        v.player.age=102.4;v.tick();self.assertEqual(v.source.speed,10000)
        v.player.age=102.5;v.tick();self.assertEqual(v.source.speed,0)
        self.assertEqual(v.calls,[('travel',v.source),('velocity',v.source)])
    def test_any_input_autopilot_boost_or_flight_assist_off_cancels_brake(self):
        for reason in ['throttle','horizontal','vertical','pitch','yaw','roll','matchspeed','autopilot','boost','assist']:
            with self.subTest(reason=reason):
                v=self.vm();v.tick()
                if reason in ['throttle','horizontal','vertical','pitch','yaw','roll']:setattr(v.player.input.flight,reason,0.5)
                elif reason=='matchspeed':v.player.input.flight.matchspeed=True
                elif reason=='autopilot':v.player.autopilottarget=Object(exists=True)
                elif reason=='boost':v.source.boost.active=True
                else:v.player.flightassist=False
                v.player.age+=2.5;v.tick();self.assertEqual(v.source.speed,10000)
                self.assertEqual(v.state['BrakeStateV116.Due'],0)
    def test_spacesuit_transition_walking_or_another_hull_cannot_be_braked(self):
        for reason in ['walking','suit','other hull','other owner']:
            with self.subTest(reason=reason):
                v=self.vm();v.tick()
                if reason=='walking':v.player.occupiedship=NONE
                elif reason=='suit':v.player.occupiedship=v.suit
                elif reason=='other hull':v.source.macro='vanilla'
                else:v.source.isplayerowned=False
                v.player.age+=2.5;v.tick();self.assertEqual(v.source.speed,10000)
                self.assertEqual(v.state['BrakeStateV116.Due'],0)
    def test_stationary_astrid_never_clears_a_nonexistent_component_blackboard(self):
        v=self.vm();v.source.speed=0;v.source.travel.active=False
        for i in range(100):v.tick()
        self.assertEqual(v.calls,[]);self.assertEqual(v.state['BrakeStateV116.Due'],0)
        self.assertNotIn('$Ship.$vardath_tours_stopdeadline',E.tostring(BRAKE,encoding='unicode'))
    def test_return_from_suit_starts_a_fresh_brake_deadline(self):
        v=self.vm();v.tick();v.player.occupiedship=NONE;v.player.age+=1;v.tick()
        v.player.occupiedship=v.source;v.player.age+=1;v.tick();self.assertEqual(v.state['BrakeStateV116.Due'],104.5)
    def test_stale_occupied_ship_during_split_control_or_native_transit_is_not_braked(self):
        for reason in ['control','suit','transit']:
            with self.subTest(reason=reason):
                v=self.vm();v.tick()
                if reason=='control':v.player.controlled=v.suit
                if reason=='suit':v.player.spacesuit=v.suit
                if reason=='transit':v.player.entity.isintransit=True
                v.player.age+=2.5;v.tick();self.assertEqual(v.source.speed,10000)
                self.assertEqual(v.state['BrakeStateV116.Due'],0)
    def test_tours_only_brake_change_leaves_forge_weapon_files_untouched(self):
        self.assertEqual(list(BRAKE.iter('set_entity_role_object')),[])
        self.assertEqual(list(BRAKE.iter('equip_weapon')),[])

class LiteralRoleValidation(unittest.TestCase):
    def test_role_set_uses_native_roles_and_does_not_invent_pilot_role(self):
        data=json.loads((TOP/'tools/api_contracts.json').read_text())
        roles=data['literal_expression_enums']['entityrole'];self.assertNotIn('pilot',roles)
        for p in (TOP/'vardath_galactic_occupations').rglob('*.xml'):
            for n in E.parse(p).iter():
                for v in n.attrib.values():
                    for role in re.findall(r'\bentityrole\.(\w+)',v):self.assertIn(role,roles,str(p))
    def test_command_is_verified_nine_zero_native_action(self):
        data=json.loads((TOP/'tools/api_contracts.json').read_text())
        spec=data['commands']['teleport_player_to_spacesuit']
        self.assertIn('md',spec['contexts'])
        self.assertEqual(set(spec['attributes']),{'instant','emergency','launch','allowinhighway'})

if __name__=='__main__':unittest.main()
