#!/usr/bin/env python3
"""Pinned-source, model/loadout, quest-route and spawn boundary validation.

No X4 engine is run. Native path results and ship creation are mocked; all XML
selectors and external component/macro names are checked against pinned data.
"""
import argparse,ast,copy,hashlib,json,re,tempfile,unittest,urllib.request
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

BASE=Path(__file__).resolve().parents[1]
MOD=BASE/'vardath_hyperion_ascendant'
SOURCES=json.loads((BASE/'tools/sources.json').read_text())
REFS={}
def normalize(b):return b.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
def references(cache):
    out={}
    for item in SOURCES:
        p=cache/(item['key']+'.xml')
        if not p.exists():
            req=urllib.request.Request(item['url'],headers={'User-Agent':'Vardath-X4-source-validation/1.0'})
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(urllib.request.urlopen(req,timeout=40).read())
        b=normalize(p.read_bytes())
        if hashlib.sha256(b).hexdigest()!=item['sha256_lf_finalnewline']:raise ValueError('Reference mismatch: '+item['key'])
        out[item['key']]=E.fromstring(b)
    return out
def canonical(x):
    x=copy.deepcopy(x)
    for n in x.iter():
        if n.text is not None and not n.text.strip():n.text=None
        if n.tail is not None and not n.tail.strip():n.tail=None
    return E.tostring(x,method='c14n')
def apply_story_patch(original):
    out=copy.deepcopy(original);patch=E.parse(str(MOD/'extensions/ego_dlc_mini_01/md/story_hyperion.xml')).getroot()
    for op in patch:
        if not isinstance(op.tag,str):continue
        found=out.xpath(op.get('sel'))
        if len(found)!=1:raise ValueError('Expected unique native story selector '+op.get('sel'))
        old=found[0];parent=old.getparent();index=parent.index(old)
        if op.tag=='replace':parent.remove(old)
        elif op.tag=='add' and op.get('pos')=='after':index+=1
        else:raise ValueError('Unexpected story operation')
        for child in op:parent.insert(index,copy.deepcopy(child));index+=1
    return out
def scalar(expr,values):
    bindings={}
    for i,key in enumerate(sorted(values,key=len,reverse=True)):
        expr=expr.replace(key,f'v{i}');bindings[f'v{i}']=values[key]
    expr=re.sub(r'\b(\d+)min\b',lambda m:str(int(m[1])*60),expr)
    expr=re.sub(r'\b(\d+)s\b',r'\1',expr)
    for a,b in [(' ge ',' >= '),(' le ',' <= '),(' gt ',' > '),(' lt ',' < ')]:expr=expr.replace(a,b)
    expr=re.sub(r'\bnull\b','None',expr);expr=re.sub(r'\btrue\b','True',expr);expr=re.sub(r'\bfalse\b','False',expr)
    tree=ast.parse(expr,mode='eval')
    types=(ast.Expression,ast.BoolOp,ast.And,ast.Or,ast.Compare,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Name,ast.Load,ast.Constant,ast.UnaryOp,ast.Not,ast.BinOp,ast.Add)
    if any(not isinstance(n,types) for n in ast.walk(tree)):raise ValueError('Unresolved source expression '+expr)
    return eval(compile(tree,'<native guard>','eval'),{'__builtins__':{}},bindings)

class ReturnValue(Exception):
    def __init__(self,value):self.value=value
class Gate:
    def __init__(self,name,sector,exit_sector=None,exists=True,is_gate=True):self.name=name;self.sector=sector;self.exit_sector=exit_sector;self.exists=exists;self.is_gate=is_gate
class RouteVM:
    """Execute the shipped resolver; get_jump_path is an explicit native stub."""
    def __init__(self,actual,path,sector='current',destination='home'):
        self.actual,self.path,self.sector,self.destination=actual,path,sector,destination;self.locals={};self.path_calls=0
    def expression(self,text):
        g=self.locals.get('Candidate');values={'$sector.exists':self.sector is not None,'$destination.exists':self.destination is not None,'$sector':self.sector,'$destination':self.destination,'$Path':self.locals.get('Path',[])}
        if g:values.update({'$Candidate.exists':g.exists,'$ActualGates.indexof.{$Candidate}':g in self.locals.get('ActualGates',[]),'$LiveGates.indexof.{$Candidate}':g in self.locals.get('LiveGates',[]),'$Candidate.isclass.gate':g.is_gate,'$Candidate.sector.exists':g.sector is not None,'$Candidate.sector':g.sector,'$Candidate.exit.exists':g.exit_sector is not None,'$Candidate.exit.sector.exists':g.exit_sector is not None,'$Candidate.exit.sector':g.exit_sector,'$Candidate':g})
        return scalar(text,values)
    def execute(self,nodes):
        for n in nodes:
            if not isinstance(n.tag,str):continue
            if n.tag=='do_if':
                if self.expression(n.get('value')):self.execute(n)
            elif n.tag=='find_gate':self.locals[n.get('name')[1:]]=[g for g in self.actual if g.sector==self.expression(n.get('space')) and g.is_gate]
            elif n.tag=='set_value':self.locals[n.get('name')[1:]]=[]
            elif n.tag=='get_jump_path':self.path_calls+=1;self.locals['Path']=self.path
            elif n.tag=='do_for_each':
                for item in self.expression(n.get('in')):self.locals[n.get('name')[1:]]=item;self.execute(n)
            elif n.tag=='return':raise ReturnValue(self.expression(n.get('value')))
            else:raise ValueError('Unexpected resolver action '+n.tag)
    def run(self):
        try:self.execute(E.parse(str(MOD/'md/VCF_HyperionRoute.xml')).find(".//library[@name='ResolveGate']/actions"))
        except ReturnValue as r:return r.value

class RecoveryDeliveryVM:
    """Run the shipped post-delay actions with explicit native event boundaries."""
    stage='md.Story_Hyperion.Ch1_3_Investigate_Gates.state'
    def __init__(self,changes=None):
        self.values={'$Prepared':True,'@$Story.hasmission':True,'$Story.$MissionAccepted?':True,'@$Story.$Sector_Investigation':'current','@$Story.$Sector_Next':'current','@$Story.$Sector_Hyperion.exists':True,'$Story.$Sector_Hyperion':'home','$Sector':'current',self.stage:'waiting','cuestate.waiting':'waiting','md.Story_Hyperion.Ch1_3_Hyperion_Sector.state':'waiting','@$Story.$HyperionCloneShip.exists':False,'$HadInvestigated':True,'$Investigated':7,'$Story.$SectorsInvestigated':7}
        self.values.update(changes or {});self.signals=[];self.reset=False
    def execute(self,nodes):
        for n in nodes:
            if not isinstance(n.tag,str):continue
            if n.tag=='do_if':
                if scalar(n.get('value'),self.values):self.execute(n)
            elif n.tag=='signal_cue_instantly':
                if self.values[self.stage]!='waiting':raise ValueError('No native listener')
                self.signals.append(scalar(n.get('param'),self.values));self.values[self.stage]='complete';self.values['$Story.$SectorsInvestigated']+=1
            elif n.tag=='set_value':self.values[n.get('name')]=scalar(n.get('exact'),self.values)
            elif n.tag=='reset_cue':
                if n.get('cue')!='this':raise ValueError('Unexpected deferred reset')
                self.reset=True
            elif n.tag!='debug_text':raise ValueError('Unexpected deferred action '+n.tag)
    def run(self):
        actions=E.parse(str(MOD/'md/VCF_HyperionRoute.xml')).find(".//cue[@name='RecoverCurrentInvestigation']").findall('actions')
        self.execute(actions[1]);return self

class Contracts(unittest.TestCase):
    def test_all_assets_and_external_connections_resolve(self):
        components=set(REFS['base_components'].xpath('//entry/@name'))|set(REFS['dlc_components'].xpath('//entry/@name'))
        external=set(REFS['base_macros'].xpath('//entry/@name'))|set(REFS['dlc_macros'].xpath('//entry/@name'))
        custom={x.get('name') for p in MOD.glob('assets/**/*.xml') for x in E.parse(str(p)).xpath('/macros/macro')}
        self.assertEqual(len(custom),7)
        for p in MOD.glob('assets/**/*.xml'):
            x=E.parse(str(p));m=x.find('macro');self.assertIn(m.find('component').get('ref'),components)
            for n in m.findall('./connections/connection/macro'):self.assertTrue(n.get('ref') in custom|external,n.get('ref'))
            for n in m.findall('./properties/bullet[@class]'):self.assertTrue(n.get('class') in custom|external,n.get('class'))
        index=E.parse(str(MOD/'index/macros.xml'))
        self.assertEqual(set(index.xpath('//entry/@name')),custom)
        for item in index.xpath('//entry'):
            path=item.get('value').replace('\\','/').removeprefix('extensions/'+MOD.name+'/')+'.xml'
            self.assertTrue((MOD/path).exists(),path)
    def test_native_hyperion_hardpoints_are_filled_and_preserved(self):
        native=REFS['loadouts'].xpath("//loadout[@id='story_hyperion_reward_special']")[0]
        own=E.parse(str(MOD/'libraries/loadouts.xml')).find('.//loadout')
        for kind in ('engine','weapon','shield'):
            self.assertEqual([n.get('path') for n in own.findall('./macros/'+kind)],[n.get('path') for n in native.findall('./macros/'+kind)])
        self.assertEqual(len(own.findall('./macros/weapon')),6)
        self.assertEqual(sum(int(n.get('exact','1')) for n in own.findall('./groups/turrets')),8)
        self.assertEqual([n.get('group') for n in own.findall('./groups/turrets')],[n.get('group') for n in native.findall('./groups/turrets')])
        self.assertTrue(all(n.get('macro')=='weapon_vardath_hyperion_ascendant_macro' for n in own.findall('./macros/weapon')))
        self.assertTrue(all(n.get('macro')=='turret_vardath_hyperion_ascendant_macro' for n in own.findall('./groups/turrets')))
    def test_only_custom_assets_are_modified_and_registered_as_wares(self):
        files=list(MOD.glob('assets/**/*.xml'))
        self.assertTrue(all('vardath_hyperion' in p.name for p in files))
        wares=E.parse(str(MOD/'libraries/wares.xml')).xpath('//ware')
        self.assertEqual(len(wares),5)
        self.assertTrue(all(w.find('owner') is None and w.find('production') is None for w in wares))
        self.assertTrue(all(w.find('component').get('ref').startswith(('ship_vardath_','engine_vardath_','shield_vardath_','weapon_vardath_','turret_vardath_')) for w in wares))
        manifest=E.parse(str(MOD/'content.xml'));ids=set(manifest.xpath('//dependency/@id'))
        self.assertTrue({'ego_dlc_mini_01','ego_dlc_terran'}<=ids);self.assertNotIn('vro',ids)
        self.assertFalse(list(MOD.glob('ui/**/*')))
    def test_normal_reverse_boost_and_travel_speed_factors_are_tripled_once(self):
        old=REFS['previous_engine'].find('.//properties');new=E.parse(str(MOD/'assets/props/engines/macros/engine_vardath_hyperion_ascendant_macro.xml')).find('.//properties')
        for axis in ('forward','reverse'):
            self.assertAlmostEqual(float(new.find('thrust').get(axis))/float(old.find('thrust').get(axis)),3)
        for mode in ('boost','travel'):
            self.assertEqual(new.find(mode).attrib,old.find(mode).attrib) # three times base force, not nine times mode force
            self.assertAlmostEqual(float(new.find('thrust').get('forward'))*float(new.find(mode).get('thrust'))/(float(old.find('thrust').get('forward'))*float(old.find(mode).get('thrust'))),3)
    def test_each_main_battery_and_beam_damage_meets_published_astrid(self):
        main=E.parse(str(MOD/'assets/fx/weaponfx/macros/bullet_vardath_hyperion_ascendant_macro.xml')).find('.//properties');other=REFS['astrid_laser'].find('.//properties')
        self.assertGreaterEqual(float(main.find('damage').get('value')),float(other.find('damage').get('value')))
        self.assertGreaterEqual(float(main.find('damage').get('value'))*float(main.find('reload').get('rate')),float(other.find('damage').get('value'))*float(other.find('reload').get('rate'))) # Astrid burst ceiling, before its magazine reload
        beam=E.parse(str(MOD/'assets/fx/weaponfx/macros/bullet_vardath_hyperion_ascendant_beam_macro.xml')).find('.//properties');other=REFS['astrid_beam'].find('.//properties')
        for channel in ('value','shield'):
            self.assertGreaterEqual(float(beam.find('damage').get(channel)),10*float(other.find('damage').get(channel,other.find('damage').get('value'))))
        self.assertGreaterEqual(float(beam.find('bullet').get('lifetime')),float(other.find('bullet').get('lifetime')))
        self.assertLessEqual(float(beam.find('reload').get('time')),float(other.find('reload').get('time')))
        turret=E.parse(str(MOD/'assets/props/weaponsystems/energy/macros/turret_vardath_hyperion_ascendant_macro.xml')).find('.//properties');other=REFS['astrid_turret'].find('.//properties')
        self.assertEqual(turret.find('reload').attrib,other.find('reload').attrib)
        for tag in ('rotationspeed','rotationacceleration'):self.assertGreaterEqual(float(turret.find(tag).get('max')),float(other.find(tag).get('max')))
    def test_equipment_wares_have_native_use_metadata_and_no_unused_blueprint_owners(self):
        wares=E.parse(str(MOD/'libraries/wares.xml')).xpath('//ware');native=REFS['wares'].xpath('/wares/ware[@id="engine_par_l_allround_01_mk1"]')[0]
        self.assertIsNotNone(native.find('restriction'));self.assertIsNotNone(native.find('use'))
        equipment=[w for w in wares if 'equipment' in w.get('tags','').split()];self.assertEqual(len(equipment),4)
        for w in equipment:self.assertEqual(w.find('use').get('threshold'),'0')
        self.assertFalse(any(w.find('owner') is not None for w in wares))
    def test_localized_ship_name_is_a_native_text_token_string(self):
        self.assertEqual(E.parse(str(MOD/'md/Vardath_Hyperion_Ascendant.xml')).find('.//set_object_name').get('name'),"'{995510,1}'")
    def test_native_reset_is_settled_before_signal_in_separate_action_block(self):
        cue=E.parse(str(MOD/'md/VCF_HyperionRoute.xml')).find(".//cue[@name='RecoverCurrentInvestigation']");blocks=cue.findall('actions')
        self.assertEqual(len(blocks),2);self.assertEqual(cue.find('delay').get('exact'),'1s')
        self.assertIsNotNone(blocks[0].find(".//reset_cue[@cue='md.Story_Hyperion.Ch1_3_Investigate_Gates']"));self.assertIsNone(blocks[0].find(".//signal_cue_instantly[@cue='md.Story_Hyperion.Ch1_3_Investigate_Gates']"))
        documentation=''.join(REFS['md_schema'].xpath('//*[local-name()="element"][@name="reset_cue"]//*[local-name()="documentation"]/text()'))
        self.assertIn('after the current cue actions',documentation)
        native=REFS['story'].xpath("//cue[@name='Ch1_3_Investigate_Gates_Next_Sector']")[0];self.assertEqual(cue.find('delay').attrib,native.find('delay').attrib)
    def test_post_reset_and_previous_failed_waiting_stage_start_once_without_counter_gain(self):
        # In both cases the real listener becomes/remains waiting after the delay.
        for starting_state in ('complete','waiting'):
            with self.subTest(starting_state=starting_state):
                cue=E.parse(str(MOD/'md/VCF_HyperionRoute.xml')).find(".//cue[@name='RecoverCurrentInvestigation']");self.assertIn('cuestate.'+starting_state,cue.find('actions/do_if/do_if').get('value'))
                vm=RecoveryDeliveryVM().run();self.assertEqual(vm.signals,['current']);self.assertEqual(vm.values['$Story.$SectorsInvestigated'],7);self.assertTrue(vm.reset)
                vm.run();self.assertEqual(vm.signals,['current']) # already consumed listener
    def test_deferred_recovery_does_not_replay_after_quest_or_sector_changes(self):
        for changes in ({'$Prepared':False},{'@$Story.hasmission':False},{'$Story.$MissionAccepted?':False},{'@$Story.$Sector_Investigation':'elsewhere'},{'@$Story.$Sector_Next':'elsewhere'},{'$Story.$Sector_Hyperion':'current'},{'@$Story.$HyperionCloneShip.exists':True},{RecoveryDeliveryVM.stage:'complete'},{'md.Story_Hyperion.Ch1_3_Hyperion_Sector.state':'complete'}):
            with self.subTest(changes=changes):
                vm=RecoveryDeliveryVM(changes).run();self.assertEqual(vm.signals,[]);self.assertEqual(vm.values['$Story.$SectorsInvestigated'],7);self.assertTrue(vm.reset)
    def test_spawn_is_player_owned_yaki_and_leaves_ten_passenger_berths(self):
        r=E.parse(str(MOD/'md/Vardath_Hyperion_Ascendant.xml'));cue=r.find(".//cue[@name='Maintain']")
        self.assertEqual(cue.get('checkinterval'),'1min')
        find=cue.find('.//find_ship_by_true_owner');self.assertEqual(find.get('space'),'player.galaxy');self.assertEqual(find.get('faction'),'faction.player');self.assertEqual(find.get('macro'),'macro.ship_vardath_hyperion_ascendant_macro')
        self.assertIsNotNone(cue.find(".//do_if[@value='not $Ships.count']/create_ship"))
        ship=cue.find('.//create_ship');self.assertEqual(ship.find('owner').get('exact'),'faction.player');self.assertEqual(ship.find('pilot/select').get('faction'),'faction.yaki')
        capacity=int(E.parse(str(MOD/'assets/units/size_l/macros/ship_vardath_hyperion_ascendant_macro.xml')).find('.//people').get('capacity'))
        fill=int(ship.find('people/fillpercent').get('exact'));self.assertGreaterEqual(capacity-(capacity*fill+99)//100-1,10)
        people=E.parse(str(MOD/'libraries/people.xml'));self.assertTrue(all(s.get('faction')=='yaki' for s in people.xpath('//select')))
        self.assertFalse(cue.xpath('.//set_owner|.//remove_npc_template|.//cancel_all_orders|.//add_inventory|.//remove_ship'))
    def test_spawn_guard_no_duplicate_for_owned_remote_or_docked_copy(self):
        r=E.parse(str(MOD/'md/Vardath_Hyperion_Ascendant.xml'));g=r.find(".//cue[@name='Maintain']/actions/do_if").get('value')
        for count,spawn in [(0,True),(1,False),(2,False)]:self.assertEqual(bool(scalar(g,{'$Ships.count':count})),spawn)
        self.assertEqual(len(r.findall('.//create_ship')),1) # one attempt per scheduled pass
        self.assertIsNotNone(r.find(".//do_if[@value='$Ship.exists']/set_object_name"))
    def test_brake_scope_excludes_other_ships_copiloting_and_spacesuits(self):
        r=E.parse(str(MOD/'md/Vardath_Hyperion_Ascendant.xml'));g=r.find(".//cue[@name='BrakeAssist']/actions/do_if").get('value')
        base={'$Ship.exists':True,'$Ship.isplayerowned':True,'$Ship.macro':'custom','macro.ship_vardath_hyperion_ascendant_macro':'custom','player.controlled':'ship','$Ship':'ship','player.spacesuit.exists':False,'player.entity.isintransit':False}
        self.assertFalse(scalar(g,base))
        for field,value in [('$Ship.exists',False),('$Ship.isplayerowned',False),('$Ship.macro','vanilla'),('player.controlled','copilot'),('player.spacesuit.exists',True),('player.entity.isintransit',True)]:
            values=dict(base);values[field]=value;self.assertTrue(scalar(g,values))
    def test_route_uses_actual_engine_path_after_sector_insertion(self):
        old=Gate('old','current','old-neighbour',exists=False);new=Gate('new','current','inserted-sector');exit=Gate('arrival','inserted-sector','current')
        vm=RouteVM([new],[old,new,exit]);self.assertIs(vm.run(),new);self.assertEqual(vm.path_calls,1)
        r=E.parse(str(MOD/'md/VCF_HyperionRoute.xml')).find('.//get_jump_path')
        self.assertIsNone(r.get('useknownpath')) # native default false; no missing refobject
        self.assertEqual([c.tag for c in r],['start','end'])
    def test_route_rejects_missing_inactive_wrong_sector_or_unconnected_gate(self):
        good=Gate('good','current','home');other=Gate('other','elsewhere','home');dead=Gate('dead','current','home',False);unlinked=Gate('unlinked','current',None);inactive=Gate('inactive','current','home')
        for path in ([],[dead],[unlinked],[inactive]):self.assertIsNone(RouteVM([good,other,dead,unlinked],path).run())
    def test_gate_free_sector_relocates_search_to_next_actual_gate_on_route(self):
        highway=Gate('highway entry','current','next-sector',is_gate=False);nextgate=Gate('next real jumpgate','next-sector','home')
        self.assertIs(RouteVM([nextgate],[highway,nextgate]).run(),nextgate)
        patched=apply_story_patch(REFS['story'])
        redirect=patched.xpath("//cue[@name='Ch1_3_Investigate_Gates_Next_Sector']/actions/do_if//set_value[@name='$Sector_Next'][@exact='this.$vcf_next_gate.sector']")
        self.assertEqual(len(redirect),1)
    def test_arrival_gate_in_home_sector_is_not_a_fake_scan_shortcut(self):
        arrival=Gate('home arrival','home','previous')
        self.assertIsNone(RouteVM([arrival],[arrival]).run())
    def test_route_supports_backtracking_and_accelerators_without_stale_cache(self):
        back=Gate('real route through former sector','current','previous')
        self.assertIs(RouteVM([back],[back]).run(),back)
        patched=apply_story_patch(REFS['story']);cue=patched.xpath("//cue[@name='Ch1_3_Investigate_Gates']")[0]
        self.assertEqual(len(cue.xpath("./actions/append_to_list[@name='$Gates_CurrentInvestigationSector'][@unique='true']")),0)
        self.assertEqual(len(cue.xpath("./actions/do_all/do_if/append_to_list[@name='$Gates_CurrentInvestigationSector'][@unique='true']")),1)
    def test_absent_or_completed_target_does_not_search_or_invent_a_gate(self):
        for sector,target in [(None,'home'),('current',None),('home','home')]:
            vm=RouteVM([],[],sector,target);self.assertIsNone(vm.run());self.assertEqual(vm.path_calls,0)
    def test_native_rewards_chapters_and_actors_are_untouched_by_story_patch(self):
        original=REFS['story'];patched=apply_story_patch(original)
        self.assertEqual(canonical(patched.xpath("//cue[@name='Ch2_Contact']")[0]),canonical(original.xpath("//cue[@name='Ch2_Contact']")[0]))
        for tag in ('create_cue_actor','create_mission','reward_player','transfer_money_to_player','set_owner','destroy_object'):
            self.assertEqual([canonical(x) for x in patched.xpath('//'+tag)],[canonical(x) for x in original.xpath('//'+tag)])
        self.assertEqual(len(patched.xpath("//cue[@name='Ch1_3_Investigate_Gates']/actions/do_for_each[@in='$WayHomeTable.{$Sector_Investigation}']")),0)
    def test_recovery_resets_only_current_scan_preserves_counter_and_has_no_payments(self):
        r=E.parse(str(MOD/'md/VCF_HyperionRoute.xml'));cue=r.find(".//cue[@name='RecoverCurrentInvestigation']")
        reset=[n.get('cue') for n in cue.iter('reset_cue')];self.assertEqual(reset,['md.Story_Hyperion.Ch1_3_Investigate_Gates','this'])
        self.assertIsNotNone(cue.find(".//set_value[@name='$Story.$SectorsInvestigated'][@exact='$Investigated']"))
        self.assertEqual(cue.find(".//signal_cue_instantly[@cue='md.Story_Hyperion.Ch1_3_Investigate_Gates']").get('param'),'$Sector')
        self.assertEqual(cue.find(".//signal_cue_instantly[@cue='md.Story_Hyperion.Ch1_3_Investigate_Gates_Next_Sector']").get('param'),'$Gate.sector')
        for token in ('Start.hasmission','Ch1_3_Investigate_Gates.state == cuestate.complete','Ch1_3_Hyperion_Sector.state == cuestate.waiting','not @$Story.$HyperionCloneShip.exists'):
            self.assertIn(token,E.tostring(cue,encoding='unicode'))
        for tag in ('reward_player','create_gate','create_mission','set_owner','teleport_player','set_object_position'):
            self.assertEqual(list(r.iter(tag)),[])
        self.assertIsNotNone(r.find(".//set_value[@name='RouteState.$NoRouteNotice'][@exact='player.age + 10min']"))
    def test_final_arrival_uses_actual_gate_exit(self):
        patched=apply_story_patch(REFS['story'])
        n=patched.xpath("//cue[@name='Ch1_3_Investigate_Gates_Next_Sector']/actions/do_if[@value='$Sector_Next == $Sector_Hyperion and @$Investigation_CorrectGate.exit.sector == $Sector_Hyperion']")
        self.assertEqual(len(n),1);self.assertEqual(n[0][0].get('exact'),'$Investigation_CorrectGate.exit')

def validate(cache,archive=None):
    global REFS
    REFS=references(cache)
    schema=E.XMLSchema(E.ElementTree(REFS['diff']))
    xmlfiles=list(MOD.rglob('*.xml'));diffs=0
    for p in xmlfiles:
        x=E.parse(str(p))
        if x.getroot().tag=='diff':schema.assertValid(x);diffs+=1
    apply_story_patch(REFS['story'])
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    if not result.wasSuccessful():raise ValueError('Hyperion source contracts failed')
    if archive:
        with ZipFile(archive) as z:
            expected={'extensions/'+MOD.name+'/'+p.relative_to(MOD).as_posix():p.read_bytes() for p in MOD.rglob('*') if p.is_file()}
            if z.testzip() or set(z.namelist())!=set(expected) or any(z.read(p)!=b for p,b in expected.items()):raise ValueError('Archive/source mismatch')
    return {'version':'1.0.1','result':'pass','reference_files':len(REFS),'xml_files':len(xmlfiles),'diffs':diffs,'native_story_selectors':2,'tests':result.testsRun,'runtime_tested':False,'limitations':['No X4 executable, user save or effective installed mod merge available.','Native pathfinding, physical ship/weapon/crew behavior and current-stage recovery require live acceptance.']}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-cache',type=Path);parser.add_argument('--zip',type=Path);parser.add_argument('--report',type=Path);a=parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:report=validate(a.source_cache or Path(tmp),a.zip)
    if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
