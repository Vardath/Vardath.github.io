#!/usr/bin/env python3
"""Execute station survey XML with native objects/actions mocked, not an X4 runtime."""
import copy
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E
from crystal_commerce_contracts import VM,Obj,NULL,S,SECTOR,Returned,Continued,Broken,MOD,xml
from passenger_completion_contracts import Seq
from log11_service_contracts import NativePassengers,RoomPointsVM,STATE

SURVEY=E.parse(MOD/'md/VGO_Survey.xml').getroot()

class SurveyVM(VM):
    def __init__(self):
        super().__init__();self.other=Obj('remote sector',exists=True)
        self.order=Obj('survey order',exists=True,id='VGO_scanner',scanleaks=True,simulatescans=True)
        self.ship=Obj('survey ship',exists=True,isplayerowned=True,order=self.order,size=50,sector=SECTOR,attention=0,maxscanlevel=2)
        self.station=Obj('station',exists=True,isoperational=True,isplayerowned=False,hostile=False,
            sector=SECTOR,size=1000,attention=0,dock_ok=True,knownname='Actual station',isclass=Obj('class',station=True),controlentity=NULL)
        self.module=Obj('module',exists=True,isoperational=True,isphysicsready=False,sector=SECTOR,size=200,
            revealedpercentage=0,scannedlevel=0)
        self.leak=Obj('leak',exists=True,container=self.station,type='data',islocked=False,size=1,
            isclass=Obj('leak class',signalleak=True),object=self.module)
        self.state.update(vgo_order=self.order)
        self.component_states={self.ship:self.state,self.station:{},self.leak:{}}
        self.native_offers=Seq();self.generic=Seq();self.slots=Seq(['actual leak slot'])
        self.native_leaks=Seq();self.native_calls=[];self.distance=1000;self.scan_accepts=True
        self.player_sector=self.other;self.vars.update(ship=self.ship,station=self.station,module=self.module,leak=self.leak)
        self.after_wait=None;self.waits=0;self.gm_enabled=True;self.market=NULL;self.approach_accepts=True;self.los=True;self.player_cap=2
        self.work(virtual=True)
    def work(self,virtual=True):
        self.state['vgo_leak_work']={'station':self.station,'leak':self.station if virtual else self.leak,
            'started':self.age-15,'finished':self.age,'virtual':virtual}
    def expr(self,text):
        if text.startswith('table[') and text!='table[]':
            return {k.strip()[1:]:self.expr(v.strip()) for k,v in (part.split('=',1) for part in text[6:-1].split(','))}
        t=text.replace(S,'_STATE_').replace('player.entity.$vgo_objects.{$ship}','_STATE_')
        self.vars.update(survey_ship=self.ship,player_sector=self.player_sector,occupied_ship=self.ship if self.occupied else NULL,
            native_offers=self.native_offers,gm_cues=self.generic,gm_disabled=not self.gm_enabled,market=self.market)
        t=t.replace('Init.$Offers','$native_offers')
        t=t.replace('event.param2','$survey_ship')
        t=t.replace('this.ship','$survey_ship').replace('player.occupiedship','$occupied_ship').replace('player.sector','$player_sector')
        t=t.replace('player.maxscanlevel',str(self.player_cap))
        for flag in ['scanleaks','simulatescans']:
            self.vars['option_'+flag]=getattr(self.ship.order,flag,True)
            t=t.replace('$survey_ship.order.$'+flag+'?','true' if flag in self.ship.order.__dict__ else 'false')
            t=t.replace('$survey_ship.order.$'+flag,'$option_'+flag)
        for var,obj in [('station',self.vars.get('station',self.station)),('leak',self.vars.get('leak',self.leak)),('module',self.vars.get('module',self.module))]:
            prefix='player.entity.$vgo_objects.{$'+var+'}'
            for key in re.findall(re.escape(prefix)+r'\.\$(\w+)',t):
                k=var+'_state_'+key;self.vars[k]=self.component_states.setdefault(obj,{}).get(key,NULL if key.endswith('_offer') else 0)
                t=t.replace(prefix+'.$'+key,'$'+k)
            t=t.replace(prefix+'?','true')
        t=t.replace('_STATE_',S)
        # Resolve a witnessed nested record before the base interpreter handles state.
        for key in re.findall(re.escape(S)+r'\.\$vgo_leak_work\.\$(\w+)',t):
            k='proof_'+key;self.vars[k]=self.state.get('vgo_leak_work',{}).get(key,NULL)
            t=t.replace(S+'.$vgo_leak_work.$'+key,'$'+k)
        t=t.replace('md.GenericMissions.Manager.$MissionCues?','true').replace('md.GenericMissions.Manager.$MissionCues','$gm_cues')
        t=t.replace('md.GenericMissions.Manager.$DefaultExcludedOfferFactions?','true')
        t=re.sub(r'md\.GenericMissions\.Manager\.\$DefaultExcludedOfferFactions\.indexof\.\{[^}]+\}','false',t)
        t=re.sub(r'md\.GenericMissions\.Manager\.\$ExcludedOfferObjects\.indexof\.\{[^}]+\}','false',t)
        t=t.replace('md.GenericMissions.Manager.$Disabled','$gm_disabled').replace('md.GenericMissions.Manager.$SectorLimit','7').replace('md.$TutorialActive','false')
        t=t.replace('$station.controlentity.{controlpost.shadyguy}','$market')
        t=t.replace('$market.isclass.npc','false' if self.market is NULL else 'true')
        t=t.replace('$station.ishostileto.{$survey_ship}','$station.hostile').replace('$station.ishostileto.{$ship}','$station.hostile')
        t=t.replace('$station.hasrelation.dock.{faction.player}','$station.dock_ok')
        t=re.sub(r'\$(?:survey_ship|ship)\.distanceto\.\{[^}]+\}',str(self.distance),t)
        t=t.replace('signalleaktype.data',repr('data')).replace('signalleaktype.voice',repr('voice'))
        t=t.replace('player.galaxy',repr('galaxy'))
        t=t.replace('attention.visible','1')
        t=re.sub(r'\$row\.\{(\d+)\}',lambda m:'$row_'+m[1],t)
        if 'row' in self.vars:
            for i,v in enumerate(self.vars['row'],1):self.vars['row_'+str(i)]=v
        # Native local table fields, including proof records, retain optional semantics.
        for var,key in re.findall(r'\$(\w+)\.\$(\w+)',t):
            obj=self.vars.get(var,{})
            val=obj.get(key,NULL) if isinstance(obj,dict) else getattr(obj,key,NULL)
            k='field_'+var+'_'+key;self.vars[k]=val;t=t.replace('$'+var+'.$'+key,'$'+k)
        t=re.sub(r'(\d+)h\b',lambda m:str(int(m[1])*3600),t)
        t=re.sub(r'(\d+)ms\b',lambda m:str(int(m[1])/1000),t)
        t=re.sub(r'(\d+)km\b',lambda m:str(int(m[1])*1000),t)
        t=re.sub(r'(\d+)m\b',lambda m:m[1],t)
        t=t.replace('(@$station_state_vgo_network_next','($station_state_vgo_network_next')
        t=t.replace('@','')
        while re.search(r'\(if [^()]+ then [^()]+ else [^()]+\)',t):
            t=re.sub(r'\((if [^()]+ then [^()]+ else [^()]+)\)',lambda m:str(self.expr(m[1])),t)
        try:return super().expr(t)
        except Exception as exc:raise AssertionError(text+' => '+t) from exc
    def assign(self,name,value,remove=False):
        if isinstance(value,list) and not isinstance(value,Seq):value=Seq(value)
        if name.startswith('player.entity.$vgo_objects.{$ship}'):
            tail=name[len('player.entity.$vgo_objects.{$ship}')+2:]
            if tail=='vgo_leak_work.$accepted':self.state['vgo_leak_work']['accepted']=value;return
            name=name.replace('player.entity.$vgo_objects.{$ship}',S)
        for var in ['station','leak','module']:
            prefix='player.entity.$vgo_objects.{$'+var+'}'
            if name.startswith(prefix):
                obj=self.vars[var];record=self.component_states.setdefault(obj,{})
                if name.endswith('.$vgo_network_next'):record['vgo_network_next']=value
                elif name.endswith('.$vgo_leak_scanned'):record['vgo_leak_scanned']=value
                elif name.endswith('.$vgo_survey_sample'):record['vgo_survey_sample']=value
                elif name==prefix:pass
                else:raise AssertionError(name)
                return
        if name.startswith('Init.$Offers.'):self.native_offers.pop(self.vars['oi']-1);return
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
            elif n.tag=='include_actions':self.execute(SURVEY.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif n.tag in ['set_known','add_player_discount','add_trade_subscription','update_offer','signal_cue_instantly','write_to_logbook','debug_text']:
                self.native_calls.append((n.tag,dict(n.attrib)))
            elif n.tag=='destroy_object':self.expr(n.get('object')).exists=False;self.native_calls.append(('destroy_object',dict(n.attrib)))
            elif n.tag=='set_object_scanned':
                if self.scan_accepts:self.module.scannedlevel=2;self.module.revealedpercentage=75
            elif n.tag=='find_object_component':self.assign(n.get('name'),Seq(self.native_leaks))
            elif n.tag=='find_signalleak_location':self.assign(n.get('name'),self.slots)
            elif n.tag=='append_to_list':self.expr(n.get('name')).append(self.expr(n.get('exact')))
            elif n.tag=='do_all':
                for i in range(self.expr(n.get('exact'))):
                    try:self.execute(n)
                    except Broken:break
            elif n.tag=='do_for_each':
                items=list(enumerate(self.expr(n.get('in')),1))
                if n.get('reverse')=='true':items.reverse()
                for index,value in items:
                    self.vars[n.get('name')[1:]]=value
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=index
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif n.tag=='run_script':
                name=n.get('name').strip("'")
                if name=='vardath.go.approach':result=self.approach_accepts
                elif name in ['vardath.go.scanleaks','vardath.go.survey.publish']:
                    saved=dict(self.vars);self.vars.update({p.get('name'):self.expr(p.get('value')) for p in n})
                    result=self.run(name);self.vars=saved
                else:raise AssertionError('Unexpected survey dependency '+name)
                self.assign(n.get('result'),result)
            elif n.tag=='signal_objects' and n.get('param')=="'vardath.go.survey.leak'":
                saved=dict(self.vars);self.decode();self.vars=saved
            elif n.tag=='signal_objects' and n.get('param')=="'vardath.go.survey.publish'":
                pass # This legacy VM refuses queue acknowledgement; PublicationVM executes it.
            elif n.tag=='check_line_of_sight':self.assign(n.get('name'),self.los)
            elif n.tag=='wait':
                self.waits+=1;super().execute([n])
                if self.after_wait:self.after_wait(self)
            else:super().execute([n])
    def decode(self):
        self.execute(SURVEY.find(".//cue[@name='Decode']/actions"))
        return bool(self.state['vgo_leak_work'].get('accepted'))

class RemoteComponentSurvey(unittest.TestCase):
    def test_actual_component_scan_changes_only_after_ten_active_samples(self):
        v=SurveyVM();self.assertTrue(v.run('vardath.go.survey.remote'));self.assertEqual(v.waits,10)
        self.assertEqual(v.module.scannedlevel,2);self.assertEqual(v.module.revealedpercentage,75)
    def test_rejected_native_scan_is_not_success(self):
        v=SurveyVM();v.scan_accepts=False;self.assertFalse(v.run('vardath.go.survey.remote'))
    def test_interruption_destruction_hostility_or_leaving_distance_cannot_scan(self):
        for cause in ['order','owner','occupied','destroyed','range','hostile','rendered']:
            with self.subTest(cause=cause):
                v=SurveyVM()
                def change(x):
                    if cause=='order':x.ship.order=Obj('manual',exists=True)
                    elif cause=='owner':x.ship.isplayerowned=False
                    elif cause=='occupied':x.occupied=True
                    elif cause=='destroyed':x.module.isoperational=False
                    elif cause=='range':x.distance=50000
                    elif cause=='hostile':x.station.hostile=True
                    else:x.module.isphysicsready=True;x.player_sector=SECTOR
                v.after_wait=change;self.assertFalse(v.run('vardath.go.survey.remote'));self.assertEqual(v.module.scannedlevel,0)

class LeakDiscovery(unittest.TestCase):
    def test_unloaded_native_signal_slots_supply_a_real_station_visit_target(self):
        v=SurveyVM();self.assertEqual(v.run('vardath.go.scanleaks'),[v.station])
    def test_no_slots_player_station_rendered_station_or_cooldown_gives_no_virtual_leak(self):
        for reason in ['slots','owned','visible','cooldown','disabled']:
            with self.subTest(reason=reason):
                v=SurveyVM()
                if reason=='slots':v.slots=Seq()
                elif reason=='owned':v.station.isplayerowned=True
                elif reason=='visible':v.station.attention=1;v.player_sector=SECTOR
                elif reason=='cooldown':v.component_states[v.station]['vgo_network_next']=v.age+100
                else:v.order.simulatescans=False
                self.assertEqual(v.run('vardath.go.scanleaks'),[])
    def test_actual_public_unlocked_leaks_are_found_and_plot_leaks_are_excluded(self):
        v=SurveyVM();v.native_leaks=Seq([v.leak]);v.slots=Seq();self.assertEqual(v.run('vardath.go.scanleaks'),[v.leak])
        for typ,locked in [('mission',False),('data',True)]:
            v.leak.type=typ;v.leak.islocked=locked;self.assertEqual(v.run('vardath.go.scanleaks'),[])
    def test_disabling_signal_leak_scan_is_a_functional_control(self):
        v=SurveyVM();v.order.scanleaks=False;self.assertEqual(v.run('vardath.go.scanleaks'),[])

class SignalSurveyEffects(unittest.TestCase):
    def test_actual_navigation_dwell_and_md_dispatch_form_a_complete_offscreen_scan(self):
        v=SurveyVM();self.assertEqual(v.run('vardath.go.task.leaks'),1)
        self.assertGreaterEqual(v.age,1015);self.assertTrue(v.state['vgo_leak_work']['accepted'])
        self.assertEqual(len([x for x in v.native_calls if x[0]=='add_player_discount']),1)
        self.assertEqual(v.run('vardath.go.task.leaks'),0)
    def test_failed_approach_cannot_make_an_offscreen_coupon(self):
        v=SurveyVM();v.approach_accepts=False;self.assertEqual(v.run('vardath.go.task.leaks'),0)
        self.assertEqual(v.native_calls,[])
    def test_player_arrival_or_direct_order_during_dwell_cannot_complete(self):
        for change in [lambda x:setattr(x.ship,'order',Obj('manual',exists=True)),lambda x:(setattr(x,'player_sector',SECTOR),setattr(x.station,'attention',1))]:
            v=SurveyVM();v.after_wait=change;self.assertEqual(v.run('vardath.go.task.leaks'),0)
            self.assertEqual(v.native_calls,[])
    def test_visible_obstructed_data_leak_does_not_get_decoded(self):
        v=SurveyVM();v.native_leaks=Seq([v.leak]);v.distance=600;v.ship.attention=1;v.module.isphysicsready=True;v.player_sector=SECTOR;v.los=False
        self.assertEqual(v.run('vardath.go.task.leaks'),0);self.assertTrue(v.leak.exists);self.assertEqual(v.native_calls,[])
    def test_offscreen_visit_publishes_station_scoped_real_native_effects_once(self):
        v=SurveyVM();self.assertTrue(v.decode())
        effects=[x for x in v.native_calls if x[0]=='add_player_discount'];self.assertEqual(len(effects),1)
        self.assertEqual(effects[0][1]['object'],'$station');self.assertEqual(effects[0][1]['amount'],'4')
        self.assertEqual(effects[0][1]['time'],'24h');self.assertEqual(v.component_states[v.station]['vgo_network_next'],v.age+86400)
        before=list(v.native_calls);self.assertTrue(v.decode());self.assertEqual(v.native_calls,before)
    def test_short_stale_remote_or_interrupted_proofs_get_no_benefit(self):
        for cause in ['duration','age','range','owner','hostile','order','occupied','ownedstation','rendered']:
            with self.subTest(cause=cause):
                v=SurveyVM()
                if cause=='duration':v.state['vgo_leak_work']['started']=v.age-14
                elif cause=='age':v.age+=6
                elif cause=='range':v.distance=50000
                elif cause=='owner':v.ship.isplayerowned=False
                elif cause=='hostile':v.station.hostile=True
                elif cause=='order':v.ship.order=Obj('manual',exists=True,id='MoveWait')
                elif cause=='occupied':v.occupied=True
                elif cause=='ownedstation':v.station.isplayerowned=True
                else:v.station.attention=1;v.player_sector=SECTOR
                self.assertFalse(v.decode());self.assertEqual(v.native_calls,[])
    def test_real_data_leak_is_consumed_voice_offer_is_kept_and_mission_leak_rejected(self):
        for typ in ['data','voice','mission']:
            with self.subTest(typ=typ):
                v=SurveyVM();v.work(False);v.leak.type=typ
                result=v.decode();self.assertEqual(result,typ!='mission')
                self.assertEqual(v.leak.exists,typ!='data')
    def test_station_cooldown_prevents_another_virtual_survey_after_reload(self):
        v=SurveyVM();self.assertTrue(v.decode());v.state['vgo_leak_work'].pop('accepted')
        v.component_states[v.station]=copy.deepcopy(v.component_states[v.station]);self.assertFalse(v.decode())
        self.assertEqual(len([x for x in v.native_calls if x[0]=='add_player_discount']),1)
    def test_attachment_slots_lost_during_work_invalidate_virtual_completion(self):
        v=SurveyVM();v.slots=Seq();self.assertFalse(v.decode());self.assertEqual(v.native_calls,[])
    def test_voice_offer_exposes_exact_native_cue_without_accepting_or_cutscene(self):
        v=SurveyVM();v.work(False);v.leak.type='voice'
        offer=Obj('native offer',exists=True,hasmissionoffer=True);v.native_offers=Seq([[offer,v.leak]])
        self.assertTrue(v.decode());self.assertEqual(len([x for x in v.native_calls if x[0]=='update_offer']),1)
        self.assertTrue(v.leak.exists)
        banned=['accept_offer','reward_player','create_mission','play_cutscene','set_entity_traits']
        for tag in banned:self.assertEqual(list(SURVEY.iter(tag)),[])
    def test_stale_offer_registry_entries_are_removed_before_exposure(self):
        v=SurveyVM();v.native_offers=Seq([[Obj('dead cue',exists=False),v.leak]])
        self.assertTrue(v.decode());self.assertEqual(v.native_offers,[])
        self.assertFalse(any(x[0]=='update_offer' for x in v.native_calls))
    def test_black_market_contact_requires_native_real_item_delivery_job(self):
        node=SURVEY.find(".//cue[@ref='md.GM_BringItems.Start']");params={p.get('name'):p.get('value') for p in node}
        self.assertEqual(params['DeliveryNPC'],'$contact');self.assertEqual(params['RewardObj'],'$contact')
        self.assertEqual(params['DeliveryStation'],'$station');self.assertEqual(params['BBSSpace'],'player.galaxy')
        self.assertNotIn('WithoutOffer',params);self.assertFalse(list(SURVEY.iter('accept_offer')))
        self.assertFalse(list(SURVEY.iter('add_inventory')));self.assertFalse(list(SURVEY.iter('unlock_achievement')))

class DisconnectedPassengerRecovery(unittest.TestCase):
    class Detached(NativePassengers):
        def execute(self,nodes):
            previous=False
            for n in nodes:
                if n.tag=='do_if':
                    previous=bool(self.expr(n.get('value')))
                    if previous:self.execute(n)
                elif n.tag=='do_else':
                    if not previous:self.execute(n)
                    previous=False
                elif n.tag=='remove_actor_from_room' and n.get('destroy')=='false':
                    super().execute([n]);a=self.expr(n.get('actor'));a.exists=False;a.roleobject=NULL
                else:super().execute([n])
    def test_disconnected_real_npcs_board_and_depart_on_same_native_roster(self):
        for job in [2,5]:
            with self.subTest(job=job):
                v=self.Detached(job);original=list(v.actors)
                for a in original:a.exists=False;a.room=NULL;a.hasbody=False
                self.assertTrue(v.board());self.assertTrue(all(a.roleobject is v.ship for a in original))
                v.state['vgo_taxi_phase']='disembarking';self.assertTrue(v.complete())
                self.assertEqual(v.roster,set());self.assertEqual(v.actors,original)
                self.assertTrue(all(a.roleobject is v.station for a in original))
                self.assertTrue(v.run('vardath.go.passengers.pay'))
    def test_same_sector_without_observed_interiors_does_not_require_a_body(self):
        v=self.Detached();v.player_sector=SECTOR;v.ship.attention=1;v.visible=True
        for a in v.actors:a.exists=False;a.room=NULL;a.hasbody=False
        self.assertTrue(v.board());self.assertTrue(all(e['native_abstract'] for e in v.state['vgo_passengers']))
    def test_disconnected_booked_identities_materialise_when_player_returns(self):
        v=self.Detached()
        for a in v.actors:a.exists=False;a.room=NULL;a.hasbody=False
        self.assertTrue(v.board());original=list(v.actors)
        v.visible=True;v.ship.attention=1;v.player_sector=SECTOR
        v.execute(STATE.find(".//cue[@name='PassengerBodiesV38']/actions"))
        self.assertTrue(all(a.exists and a.room is v.shiproom for a in original))
        self.assertEqual(v.actors,original);self.assertEqual(v.roster,{1,2})
    def test_visible_stalled_boarding_uses_same_actor_after_two_minutes_and_observes_room(self):
        v=NativePassengers();v.visible=True;v.observed_station=v.station;v.ship.attention=1
        v.native_walk_arrives=False;v.available_exits=False
        for a in v.actors:a.room=v.stationroom
        v.board();original=list(v.actors);self.assertFalse(v.state['vgo_taxi_boarded'])
        v.age+=119;v.board();self.assertFalse(v.state['vgo_taxi_boarded'])
        v.age+=1;v.board();v.board();self.assertTrue(v.state['vgo_taxi_boarded'])
        self.assertTrue(all(a.room is v.shiproom for a in original));self.assertEqual(v.actors,original)
        self.assertEqual(v.reward_requests,[])
    def test_visible_recovery_native_success_without_actual_room_cannot_acknowledge(self):
        v=NativePassengers();v.visible=True;v.observed_station=v.station;v.ship.attention=1
        v.native_walk_arrives=False;v.available_exits=False;v.placement_misreports=True
        for a in v.actors:a.room=v.stationroom
        v.board();v.age+=120;v.board();self.assertFalse(v.state['vgo_taxi_boarded'])
        self.assertEqual(v.reward_requests,[])

if __name__=='__main__':unittest.main()
