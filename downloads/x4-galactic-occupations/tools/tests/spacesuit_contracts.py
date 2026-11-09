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

class ConfirmedSpacesuitRecovery(unittest.TestCase):
    def reset(self,v):
        v.cue('Confirmed');v.player.age+=12;v.watch()
    def exit(self,v):
        self.reset(v);v.player.age+=2;v.watch()
    def test_no_explicit_exit_request_never_moves_player(self):
        v=BoundaryVM();v.player.age+=1000;v.watch();self.assertEqual(v.calls,[])
    def test_logged_null_suit_null_control_ship_room_is_reset_before_an_exit(self):
        v=BoundaryVM();v.cue('Confirmed');v.player.age+=11.9;v.watch();self.assertEqual(v.calls,[])
        v.player.age+=0.1;v.watch();self.assertEqual(v.calls,[('teleport',{'object':'Init.$Source','control':'false','instant':'true','force':'true'})])
        self.assertTrue(v.state['Init.ResetObserved']);self.assertEqual(v.state['Init.Stage'],1)
        v.player.age+=2;v.watch();self.assertEqual(v.calls[1],{'emergency':'true','instant':'true','allowinhighway':'false'})
        v.watch();self.assertFalse(v.state['Init.Pending']);self.assertEqual(len(v.calls),2)
        self.assertTrue(any('handoff verified' in l for l in v.logs))
    def test_successful_normal_exit_never_gets_repeated(self):
        v=BoundaryVM();v.cue('Confirmed');v.healthy();v.watch();v.player.age+=30;v.watch()
        self.assertFalse(v.state['Init.Pending']);self.assertEqual(v.calls,[])
    def test_already_healthy_on_event_delivery_does_not_arm(self):
        v=BoundaryVM();v.healthy();v.cue('Confirmed');self.assertFalse(v.state['Init.Pending'])
    def test_suit_cockpit_room_is_healthy_but_original_ship_room_is_not(self):
        v=BoundaryVM();v.healthy();v.player.room=Object(exists=True,context=v.suit)
        v.cue('Confirmed');self.assertFalse(v.state['Init.Pending'])
        v.player.room=v.room;v.cue('Confirmed');self.assertTrue(v.state['Init.Pending'])
    def test_existing_suit_with_original_room_and_split_controls_gets_reset(self):
        v=BoundaryVM();v.player.spacesuit=v.suit;v.player.controlled=v.suit;self.exit(v)
        v.watch();self.assertEqual(len(v.calls),2);self.assertFalse(v.state['Init.Pending'])
    def test_refused_suit_exit_returns_to_ship_once_then_stops(self):
        v=BoundaryVM();v.accept=False;self.exit(v)
        self.assertEqual(v.state['Init.Stage'],2);self.assertEqual(v.logs,[])
        v.player.age+=5;v.watch();self.assertEqual(v.state['Init.Stage'],3)
        for i in range(40):v.player.age+=1;v.watch()
        self.assertEqual(len(v.calls),3);self.assertFalse(v.state['Init.Pending'])
        self.assertEqual(sum(isinstance(c,dict) for c in v.calls),1)
        self.assertFalse(any('handoff verified' in l for l in v.logs))
    def test_room_without_actual_native_reset_event_cannot_start_an_exit(self):
        v=BoundaryVM();v.anchor_event=False;self.reset(v)
        for i in range(30):v.player.age+=1;v.watch()
        self.assertEqual(len(v.calls),1);self.assertFalse(v.state['Init.Pending'])
        self.assertFalse(v.state['Init.ResetObserved'])
    def test_wrong_room_teleport_event_cannot_unlock_the_reset(self):
        v=BoundaryVM();v.anchor_event=False;self.reset(v)
        v.eventroom=Object(exists=True,context=Object(exists=True));v.cue('ShipResetObservedV46')
        self.assertFalse(v.state['Init.ResetObserved']);v.player.age+=2;v.watch();self.assertEqual(len(v.calls),1)
    def test_refused_anchor_never_repeats_and_cannot_claim_a_successful_exit(self):
        v=BoundaryVM();v.anchor_accept=False;self.reset(v)
        for i in range(30):v.player.age+=1;v.watch()
        self.assertEqual(len(v.calls),1);self.assertFalse(v.state['Init.Pending'])
        self.assertFalse(any('handoff verified' in l for l in v.logs))
    def test_duplicate_confirmation_does_not_slide_the_recovery_clock(self):
        v=BoundaryVM();v.cue('Confirmed');due=v.state['Init.Due'];serial=v.state['Init.Serial']
        v.player.age+=7;v.cue('Confirmed');self.assertEqual(v.state['Init.Due'],due);self.assertEqual(v.state['Init.Serial'],serial)
    def test_player_reseating_changing_rooms_teleporting_or_docking_cancels(self):
        for reason in ['seat','room','ship','dock','sector','destroyed','remote control']:
            with self.subTest(reason=reason):
                v=BoundaryVM();v.cue('Confirmed')
                if reason=='seat':v.player.occupiedship=v.source
                if reason=='room':v.player.room=Object(exists=True,context=v.source)
                if reason=='ship':v.player.ship=Object(exists=True,isclass=Object(spacesuit=False))
                if reason=='dock':v.source.dock.container=Object(exists=True)
                if reason=='sector':v.source.sector=Object(exists=True)
                if reason=='destroyed':v.source.exists=False
                if reason=='remote control':v.player.controlled=v.source
                v.player.age+=12;v.watch();self.assertFalse(v.state['Init.Pending']);self.assertEqual(v.calls,[])
    def test_native_transit_is_allowed_to_finish_then_stale_transit_has_one_reset(self):
        v=BoundaryVM();v.cue('Confirmed');v.player.entity.isintransit=True
        v.player.age+=12;v.watch();self.assertEqual(v.calls,[]);self.assertTrue(v.state['Init.Pending'])
        v.player.age+=17;v.watch();self.assertEqual(v.calls,[])
        v.player.age+=1;v.watch();self.assertEqual(len(v.calls),1)
        self.assertFalse(v.player.entity.isintransit)
        v.player.age+=2;v.watch();self.assertEqual(len(v.calls),2)
    def test_suit_exit_stale_transit_also_gets_a_bounded_original_ship_return(self):
        v=BoundaryVM();v.accept=False;self.exit(v);v.player.entity.isintransit=True
        v.player.age+=5;v.watch();self.assertEqual(len(v.calls),2)
        v.player.age+=10;v.watch();self.assertEqual(len(v.calls),3)
        v.player.age+=3;v.watch();self.assertFalse(v.state['Init.Pending'])
    def test_conversation_and_expired_confirmation_cannot_force_any_movement(self):
        v=BoundaryVM();v.player.isinconversation=True;self.reset(v);self.assertEqual(v.calls,[])
        v.player.age+=34;v.watch();self.assertEqual(v.calls,[]);self.assertFalse(v.state['Init.Pending'])
    def test_native_permission_refusal_does_not_call_teleport(self):
        v=BoundaryVM();v.player.teleport_permission=False;self.reset(v)
        self.assertFalse(v.state['Init.Pending']);self.assertEqual(v.calls,[])
    def test_transit_finishes_before_expiry_then_single_context_reset(self):
        v=BoundaryVM();v.cue('Confirmed');v.player.entity.isintransit=True;v.player.age+=15;v.watch()
        v.player.entity.isintransit=False;v.watch();self.assertEqual(len(v.calls),1)
    def test_saving_loading_clears_pending_ejection_intent(self):
        v=BoundaryVM();v.cue('Confirmed');v.state=copy.deepcopy(v.state);v.cue('Loaded')
        v.player.age+=20;v.watch();self.assertEqual(v.calls,[])
    def test_upgrade_cannot_replay_a_saved_request_from_the_old_controller(self):
        v=BoundaryVM();v.cue('Confirmed');del v.state['Init.Stage']
        v.cue('UpgradeV46');v.player.age+=20;v.watch()
        self.assertEqual(v.calls,[]);self.assertFalse(v.state['Init.Pending'])
    def test_foreign_zone_docked_source_or_invalid_source_is_rejected(self):
        for reason in ['zone','dock','suit','dead']:
            with self.subTest(reason=reason):
                v=BoundaryVM()
                if reason=='zone':v.zone.sector=Object(exists=True)
                if reason=='dock':v.source.dock.container=Object(exists=True)
                if reason=='suit':v.source.isclass.spacesuit=True
                if reason=='dead':v.source.exists=False
                v.cue('Confirmed');v.player.age+=20;v.watch();self.assertEqual(v.calls,[])
    def test_reseating_between_reset_and_exit_cancels_ejection(self):
        v=BoundaryVM();self.reset(v);v.player.occupiedship=v.source
        v.player.age+=2;v.watch();self.assertEqual(len(v.calls),1);self.assertFalse(v.state['Init.Pending'])
    def test_recovery_changes_no_ship_rosters_equipment_orders_or_control_posts(self):
        banned=['create_ship','destroy_object','set_player_entity_position','set_entity_controlpost','set_object_velocity','create_order','cancel_order','set_owner']
        self.assertFalse(any(SUIT.find('.//'+tag) is not None for tag in banned))
        self.assertEqual(SUIT.find(".//cue[@name='Poll']").get('checkinterval'),'1s')
        for n in SUIT.iter('teleport_player'):
            self.assertEqual(n.get('object'),'Init.$Source');self.assertEqual(n.get('control'),'false')

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
