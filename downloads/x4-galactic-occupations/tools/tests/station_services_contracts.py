"""Execute real office-selection XML against fault-injected native room APIs.

Room assets, NPC pathing, panel effects and engine scheduling remain unverified.
"""
import re
import unittest
import xml.etree.ElementTree as E
from pathlib import Path
from survey_contracts import SurveyVM, SURVEY
from crystal_commerce_contracts import Obj, NULL as SURVEY_NULL

MOD=Path(__file__).resolve().parents[2]/'vardath_galactic_occupations'
HACK=E.parse(MOD/'md/VGO_Hacker.xml').getroot()
class Enum(str):
    @property
    def name(self):return str(self)
class Rows(list):
    @property
    def count(self):return len(self)
class O:
    def __init__(self,**attrs):self.__dict__.update(attrs)
    def __getattr__(self,key):return 0 if key=='count' else NONE
    def __bool__(self):return bool(self.__dict__.get('exists',False))
NONE=O(exists=False)
class ContinueLoop(Exception):pass
class BreakLoop(Exception):pass
class RoomVM:
    def __init__(self):
        self.age=1000;self.state={};self.records={};self.vars={};self.calls=[];self.rooms=[];self.occupants=[];self.ui=Rows()
        self.station=O(exists=True,isoperational=True,isplayerowned=False,canhavedynamicinterior=True,seed=91,
                       owner=O(exists=True,primaryrace=Enum('argon')),debugname='Actual station')
        self.ship=O(exists=True,dock=O(container=self.station));self.player=O(exists=True,context=NONE)
        self.security=O(exists=True,panels={'hack_storage','hack_all_turrets'})
        self.infrastructure=O(exists=True,panels={'hack_engineer','hack_discount'})
        self.corridor=O(exists=True);self.creation_accepts=True
        self.vars.update(station=self.station,ship=self.ship)
        types=HACK.find(".//cue[@name='Init']//set_value[@name='$Types']").get('exact')
        self.state.update(Types=self.expr(types),OwnedRoomsV47=Rows(),Ships=Rows([self.ship]))
        self.record(self.ship).update(vgo_hack_type=Enum('hack_storage'),vgo_hack_station=self.station,vgo_hack_phase='docked',vgo_hack_token=17)
    def record(self,obj):return self.records.setdefault(obj,{})
    def expr(self,text):
        if text is None:return NONE
        text=re.sub(r'\((if [^()]+ then [^()]+ else [^()]+)\)',lambda m:repr(self.expr(m[1])),text)
        if text.startswith('if '):
            m=re.match(r'if (.*?) then (.*?) else (.*)$',text)
            return self.expr(m[2] if self.expr(m[1]) else m[3])
        t=text.replace('table[]','{}')
        t=t.replace('player.entity.$vgo_objects?','True').replace('player.entity.$vgo_hack_catalogue_ui?','True').replace('player.entity.$vgo_hack_catalogue_ui','ui')
        def field(m):
            obj="v.get('"+m[1]+"',NONE)";key=m[2]
            if not key:return 'rec('+obj+')'
            return repr(key)+' in rec('+obj+')' if m[3] else 'rec('+obj+').get('+repr(key)+',NONE)'
        t=re.sub(r'@?player\.entity\.\$vgo_objects\.\{\$(\w+)\}(?:\.\$(\w+))?(\?)?',field,t)
        t=re.sub(r'Init\.\$(\w+)(\?)?',lambda m:repr(m[1])+' in state' if m[2] else 'state.get('+repr(m[1])+',NONE)',t)
        t=re.sub(r'\.\{(\d+)\}',lambda m:'['+str(int(m[1])-1)+']',t)
        t=t.replace('lookup.roomtype.list.indexof.{$definition[1]}',"(1 if $definition[1] == 'security' else 2)")
        t=t.replace('lookup.roomtype.list.indexof.{roomtype.security}','1').replace('lookup.roomtype.list.indexof.{roomtype.infrastructure}','2')
        for attr,fn in [('hascontrolpanel','panel'),('iscontrolpanelhacked','hacked'),('hascontext','within')]:
            t=re.sub(r'([\w$\[\].]+)\.'+attr+r'\.\{([^}]+)\}',lambda m:fn+'('+m[1]+','+m[2]+')',t)
        t=re.sub(r"\['done','aborted'\]\.indexof\.\{([^}]+)\}",r"(\1 in ['done','aborted'])",t)
        t=t.replace('player.entity','player').replace('player.age','age')
        t=re.sub(r'\b(controlpaneltype|roomtype|tag|faction)\.(\w+)',lambda m:'Enum('+repr(m[2])+')',t)
        t=re.sub(r'\$(\w+)',lambda m:'v.get('+repr(m[1])+',NONE)',t)
        t=t.replace('@','');t=re.sub(r'\)f',')',t)
        t=re.sub(r'(\d+)min\b',lambda m:str(int(m[1])*60),t);t=re.sub(r'(\d+)s\b',r'\1',t)
        for a,b in [('true','True'),('false','False'),('null','NONE'),('gt','>'),('ge','>='),('lt','<'),('le','<=')]:t=re.sub(r'\b'+a+r'\b',b,t)
        env=dict(v=self.vars,state=self.state,rec=self.record,age=self.age,player=self.player,NONE=NONE,Enum=Enum,ui=self.ui,
                 panel=lambda macro,typ:bool(macro) and str(typ) in macro.panels,
                 hacked=lambda station,typ:False,within=lambda actor,container:actor.context is container)
        try:return eval(t,{'__builtins__':{}},env)
        except Exception as e:raise AssertionError(text+' => '+t) from e
    def assign(self,name,value,remove=False):
        if isinstance(value,list) and not isinstance(value,Rows):value=Rows(value)
        m=re.fullmatch(r'player\.entity\.\$vgo_objects\.\{\$(\w+)\}\.\$(\w+)',name)
        if name=='player.entity.$vgo_hack_catalogue_ui':self.ui=value
        elif name.startswith('player.entity.$vgo_hack_catalogue_ui.{'):
            index=int(self.expr(name.split('.{')[-1][:-1]))-1
            if remove:self.ui.pop(index)
            else:self.ui[index]=value
        elif m:
            r=self.record(self.vars[m[1]])
            if remove:r.pop(m[2],None)
            else:r[m[2]]=value
        elif name.startswith('Init.$'):
            key=name[6:]
            if '.{' in key:
                base,index=key.split('.{');index=int(self.expr(index[:-1]))-1
                if remove:self.state[base].pop(index)
                else:self.state[base][index]=value
            else:self.state[key]=value
        else:self.vars[name[1:]]=value
    def execute(self,nodes):
        previous=False
        for n in nodes:
            tag=n.tag
            if tag in ['do_if','do_elseif']:
                if tag=='do_elseif' and previous:continue
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif tag=='set_value':self.assign(n.get('name'),self.expr(n.get('exact')))
            elif tag=='remove_value':self.assign(n.get('name'),None,True)
            elif tag=='include_actions':self.library(n.get('ref'))
            elif tag=='do_for_each':
                rows=list(enumerate(self.expr(n.get('in')),1))
                if n.get('reverse')=='true':rows.reverse()
                for i,item in rows:
                    self.vars[n.get('name')[1:]]=item
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i
                    try:self.execute(n)
                    except ContinueLoop:continue
                    except BreakLoop:break
            elif tag=='continue':raise ContinueLoop()
            elif tag=='break':raise BreakLoop()
            elif tag=='append_to_list':self.expr(n.get('name')).append(self.expr(n.get('exact')))
            elif tag=='do_while':
                for _ in range(300):
                    if not self.expr(n.get('value')):break
                    self.execute(n)
                else:raise AssertionError('Unbounded mock loop')
            elif tag=='get_room_definition':
                tags=str(self.expr(n.get('tags')))
                macro=self.security if tags=='security' else self.infrastructure if tags=='infrastructure' else self.corridor
                self.assign(n.get('macro'),macro)
            elif tag=='find_room':
                wanted=self.expr(n.get('hascontrolpanel'));self.assign(n.get('name'),Rows(r for r in self.rooms if r.exists and str(wanted) in r.panels))
            elif tag=='create_dynamic_interior':
                self.calls.append(('create',dict(n.attrib)))
                if self.creation_accepts:
                    interior=O(exists=True);room=O(exists=True,panels=set(self.expr(n.get('room')).panels),dynamicinterior=interior)
                    self.rooms.append(room);self.assign(n.get('interiorname'),interior);self.assign(n.get('roomname'),room);self.assign(n.get('corridorname'),self.corridor)
                else:
                    for a in ['interiorname','roomname','corridorname']:self.assign(n.get(a),NONE)
            elif tag=='find_object_component':self.assign(n.get('name'),Rows(self.occupants))
            elif tag=='set_dynamic_interior_persistent':self.calls.append(('persistent',self.expr(n.get('interior')),self.expr(n.get('persistent'))))
            elif tag=='remove_dynamic_interior':
                obj=self.expr(n.get('interior'));self.calls.append(('remove',obj));obj.exists=False
            elif tag in ['signal_objects','raise_lua_event']:self.calls.append((tag,dict(n.attrib)))
            elif tag in ['debug_text','write_to_logbook']:pass
            else:raise AssertionError('Unhandled native boundary '+tag)
    def library(self,name):self.execute(HACK.find(".//library[@name='"+name+"']/actions"))
    def cleanup(self):self.execute(HACK.find(".//cue[@name='CleanupRoomsV47']/actions"))
    def create(self):self.library('EnsureHackRoomV47')

class NativeOfficeDiscovery(unittest.TestCase):
    def test_only_existing_production_room_still_discovers_supported_native_offices(self):
        v=RoomVM();v.rooms=[O(exists=True,panels={'hack_production'})];v.library('Catalogue')
        entries=v.record(v.station)['vgo_hack_catalogue'];self.assertEqual({str(e[0]) for e in entries},{'hack_production','hack_storage','hack_all_turrets','hack_engineer','hack_discount'})
        self.assertFalse(any(c[0]=='create' for c in v.calls));self.assertEqual(v.record(v.station)['vgo_hack_instantiated_types'],1)
    def test_missing_installed_room_macros_do_not_invent_options(self):
        v=RoomVM();v.security=NONE;v.infrastructure=NONE;v.library('Catalogue');self.assertEqual(v.record(v.station)['vgo_hack_catalogue'],[])
    def test_station_without_dynamic_interior_capability_has_only_actual_panels(self):
        v=RoomVM();v.station.canhavedynamicinterior=False;v.rooms=[O(exists=True,panels={'hack_production'})];v.library('Catalogue')
        self.assertEqual(len(v.record(v.station)['vgo_hack_catalogue']),1)
    def test_old_partial_cache_is_replaced_even_before_its_old_expiry(self):
        v=RoomVM();v.record(v.station).update(vgo_hack_catalogue=[],vgo_hack_catalogue_until=99999,vgo_hack_catalogue_version=46)
        v.library('Catalogue');self.assertEqual(v.record(v.station)['vgo_hack_catalogue_version'],47);self.assertEqual(len(v.record(v.station)['vgo_hack_catalogue']),4)
    def test_delayed_md_reply_cannot_return_the_old_partial_ai_cache(self):
        v=RoomVM();h=E.parse(MOD/'aiscripts/vardath.go.hacker.catalogue.xml').getroot()
        result=h.find('attention/actions/return').get('value');ready=h.find('.//do_all/do_if').get('value')
        record=v.record(v.station);record.update(vgo_hack_catalogue=Rows(['production only']),vgo_hack_catalogue_until=99999,vgo_hack_catalogue_version=46)
        self.assertFalse(v.expr(ready));self.assertEqual(v.expr(result),[])
        record['vgo_hack_catalogue_version']=47;self.assertTrue(v.expr(ready));self.assertEqual(v.expr(result),record['vgo_hack_catalogue'])
        record['vgo_hack_catalogue_until']=v.age;self.assertFalse(v.expr(ready));self.assertEqual(v.expr(result),[])
    def test_docked_hacker_gets_one_real_office_and_fresh_room_reference(self):
        v=RoomVM();v.create();self.assertEqual(len(v.rooms),1);self.assertIn('hack_storage',v.rooms[0].panels)
        self.assertEqual(v.record(v.ship)['vgo_hack_rooms'],v.rooms);self.assertEqual(len(v.state['OwnedRoomsV47']),1)
        v.create();self.assertEqual(len([c for c in v.calls if c[0]=='create']),1)
    def test_existing_native_office_is_reused_without_ownership_or_persistence_changes(self):
        v=RoomVM();room=O(exists=True,panels={'hack_storage'});v.rooms=[room];v.create()
        self.assertEqual(v.record(v.ship)['vgo_hack_rooms'],[room]);self.assertEqual(v.calls,[]);self.assertEqual(v.state['OwnedRoomsV47'],[])
    def test_not_docked_cannot_create_station_rooms(self):
        v=RoomVM();v.ship.dock.container=NONE;v.create();self.assertEqual(v.rooms,[]);self.assertEqual(v.calls,[])
    def test_player_owned_or_ownerless_station_cannot_get_a_hacker_office(self):
        for owner in ['player','ownerless']:
            v=RoomVM()
            if owner=='player':v.station.isplayerowned=True
            else:v.station.owner=Enum('ownerless')
            v.create();self.assertEqual(v.calls,[])
    def test_unsupported_native_panel_cannot_create_an_unrelated_office(self):
        v=RoomVM();v.record(v.ship)['vgo_hack_type']=Enum('hack_radar');v.create();self.assertEqual(v.rooms,[])
    def test_missing_corridor_or_refused_creation_never_reports_a_room(self):
        for cause in ['corridor','native refusal']:
            v=RoomVM()
            if cause=='corridor':v.corridor=NONE
            else:v.creation_accepts=False
            v.create();self.assertEqual(v.record(v.ship)['vgo_hack_rooms'],[]);self.assertEqual(v.state['OwnedRoomsV47'],[])
    def test_refused_creation_is_bounded_per_visit_but_a_new_visit_can_retry(self):
        v=RoomVM();v.creation_accepts=False
        for _ in range(40):v.create()
        self.assertEqual(len([c for c in v.calls if c[0]=='create']),1)
        v.record(v.ship)['vgo_hack_token']+=1;v.creation_accepts=True;v.create()
        self.assertEqual(len([c for c in v.calls if c[0]=='create']),2);self.assertEqual(len(v.rooms),1)
    def test_active_hacker_keeps_its_office(self):
        v=RoomVM();v.create();v.calls=[];v.cleanup();self.assertFalse(v.calls);self.assertEqual(len(v.state['OwnedRoomsV47']),1)
    def test_player_in_office_prevents_cleanup(self):
        v=RoomVM();v.create();v.record(v.ship)['vgo_hack_phase']='done';v.player.context=v.state['OwnedRoomsV47'][0][1];v.calls=[];v.cleanup();self.assertEqual(v.calls,[])
    def test_empty_completed_owned_office_is_released_and_removed(self):
        v=RoomVM();v.create();v.record(v.ship)['vgo_hack_phase']='done';v.calls=[];v.cleanup()
        self.assertEqual([c[0] for c in v.calls],['persistent','remove']);self.assertEqual(v.state['OwnedRoomsV47'],[])
    def test_occupied_office_is_not_force_removed(self):
        v=RoomVM();v.create();v.record(v.ship)['vgo_hack_phase']='aborted';v.occupants=[O(exists=True)];v.calls=[];v.cleanup()
        self.assertEqual([c[0] for c in v.calls],['persistent']);self.assertEqual(len(v.state['OwnedRoomsV47']),1)
    def test_failed_station_or_removed_interior_drops_only_its_registry_reference(self):
        v=RoomVM();v.state['OwnedRoomsV47']=[(v.station,NONE)];v.cleanup();self.assertEqual(v.state['OwnedRoomsV47'],[]);self.assertEqual(v.calls,[])

class RemoteMarketContacts(unittest.TestCase):
    def contact(self):return Obj('actual native market',exists=True,isclass=Obj('npc',npc=True),isshadyguy=True,tradesvisible=False,knownname='Native broker')
    def test_assigned_contact_is_found_without_a_visible_body(self):
        v=SurveyVM();v.assigned_market=self.contact();self.assertTrue(v.decode());self.assertIs(v.vars['market'],v.assigned_market)
        self.assertTrue(any(n[0]=='signal_cue_instantly' and n[1]['cue']=='MarketOffer' for n in v.native_calls))
    def test_visible_contact_remains_a_fallback(self):
        v=SurveyVM();v.market=self.contact();v.decode();self.assertIs(v.vars['market'],v.market)
    def test_native_registry_recovers_a_real_contact_assigned_to_this_station(self):
        v=SurveyVM();contact=self.contact();v.market_map={contact:v.station};v.decode();self.assertIs(v.vars['market'],contact)
    def test_registry_contact_at_another_station_is_not_invented_here(self):
        v=SurveyVM();v.market_map={self.contact():Obj('other station',exists=True)};v.decode();self.assertIs(v.vars['market'],SURVEY_NULL)
        self.assertFalse(any(n[0]=='signal_cue_instantly' and n[1]['cue']=='MarketOffer' for n in v.native_calls))
    def test_unlocked_contact_does_not_get_another_unlock_job(self):
        v=SurveyVM();v.assigned_market=self.contact();v.assigned_market.tradesvisible=True;v.decode()
        self.assertFalse(any(n[0]=='signal_cue_instantly' and n[1]['cue']=='MarketOffer' for n in v.native_calls))
    def test_scanning_never_fabricates_a_trader_or_grants_market_access(self):
        for tag in ['create_cue_actor','set_entity_traits','accept_offer','reward_player','add_inventory']:
            self.assertEqual(list(SURVEY.iter(tag)),[])

class CrystalWorkerScheduling(unittest.TestCase):
    def test_fast_return_sale_bookkeeping_has_positive_versioned_yields(self):
        w=E.parse(MOD/'aiscripts/vardath.go.worker.xml').getroot();block=w.find(".//do_if[@value='$job == 6'][run_script]")
        # Select the commercial block, not the turret preflight block.
        block=next(n for n in w.iter('do_if') if n.find("run_script[@name=\"'vardath.go.crystal.commercial'\"]") is not None)
        nodes=list(block)
        for i,n in enumerate(nodes):
            if n.tag=='run_script' and n.get('name') in ["'vardath.go.crystal.commercial'","'vardath.go.recordresult'"]:
                self.assertEqual(nodes[i+1].tag,'wait');self.assertEqual(nodes[i+1].get('exact'),'1s');self.assertEqual(nodes[i+1].get('sinceversion'),'21')
        complete=block.find("do_if[@value='$crystalcycle == 1']");self.assertEqual(complete.find('wait').get('exact'),'1s')
    def test_new_iteration_yields_without_changing_runtime_or_existing_contracts(self):
        w=E.parse(MOD/'aiscripts/vardath.go.worker.xml').getroot();actions=list(w.find('attention/actions'));i=next(i for i,n in enumerate(actions) if n.tag=='label' and n.get('name')=='start')
        self.assertEqual(actions[i+1].tag,'do_if');self.assertEqual(actions[i+2].tag,'wait');self.assertEqual(actions[i+2].get('sinceversion'),'21')
        self.assertTrue(any(n.get('exact')=='42' for n in w.iter('set_value') if n.get('name','').endswith('.$vgo_runtime')))

if __name__=='__main__':unittest.main()
