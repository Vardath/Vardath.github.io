#!/usr/bin/env python3
"""Execute travel/docking recovery XML with native actions mocked.

The supplied log proves failed arrivals and an unsupported sector property.
These tests check the repaired control flow; they do not run X4 or prove pathing.
"""
from pathlib import Path
import copy
import re
import unittest
import xml.etree.ElementTree as E
from lxml import etree
from crystal_commerce_contracts import VM as BaseVM, Obj, NULL, BUYER, SECTOR, S, Returned, xml, MOD, WARES

class RecoveryVM(BaseVM):
    def __init__(self):
        super().__init__()
        self.default=Obj('default',id='VGO_taxi',state='started',exists=True,isoverride=False)
        self.current=self.default;self.queue=[];self.native_moves=[];self.new_orders=[]
        self.current_sector=SECTOR;self.moves_arrive=True
        self.docked=NULL;self.vars.update(destination=BUYER,position=None,radius=15000,waittime=300)
        self.state['vgo_order']=self.current
        self.state['vgo_dock_order']=NULL
        self.settings={'home':SECTOR,'range':99,'risk':1,'preferred':None,'repeat':False,'minreward':0,'debugchance':0}

    def expr(self,text):
        text=text.replace('this.ship.orders.clone','$mockqueue')
        for k,v in self.settings.items():
            self.vars['mockparam_'+k]=v
            text=text.replace('@this.ship.defaultorder.$'+k,'$mockparam_'+k)
            text=text.replace('this.ship.defaultorder.$'+k,'$mockparam_'+k)
        for k,v in self.vars.get('settings',{}).items():
            self.vars['mocksetting_'+k]=v
            text=text.replace('$settings.$'+k,'$mocksetting_'+k)
        text=text.replace('this.ship.defaultorder','$mockdefault').replace('this.ship.order','$mockorder')
        text=text.replace('this.ship.sector','$mocksector')
        text=text.replace('orderstate.critical',"'critical'").replace('orderstate.finish',"'finish'")
        text=text.replace('$destination.isclass.sector',"($destination == $mockdestinationsector)")
        text=text.replace('$destination.dockingallowed.{this.ship}','$mockdockallowed')
        text=text.replace('$destination.owner.hasrelation.enemy.{faction.player}','$mockhostile')
        text=text.replace(S+'.$vgo_scope.indexof.{$destination}','$mockscope')
        text=re.sub(r'this\.ship\.distanceto\.\[\$destination,\$position\]','$mockdistance',text)
        self.vars.update(mockqueue=list(self.queue),mockdefault=self.default,mockorder=self.current,
            mocksector=self.current_sector,mockdestinationsector=SECTOR,mockdockallowed=True,
            mockhostile=False,mockscope=self.in_scope,mockdistance=0)
        return super().expr(text)

    def assign(self,name,value,remove=False):
        if name.startswith('$settings.$'):
            self.vars.setdefault('settings',{})[name[len('$settings.$'):]]=value
        else:super().assign(name,value,remove)

    def execute(self,nodes):
        # Base interpreter handles branches/loops by calling this method again.
        previous=False
        for n in nodes:
            if n.tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag=='run_script':
                name=n.get('name').strip("'")
                if name=='move.generic':
                    pars={p.get('name'):self.expr(p.get('value')) for p in n}
                    self.native_moves.append(pars)
                    if self.moves_arrive:self.current_sector=pars['destination']
                    result=True # reproduce a native true result without arrival too
                elif name in ['vardath.go.travel','vardath.go.refreshdefault']:
                    old=self.vars.copy()
                    for p in n:self.vars[p.get('name')]=self.expr(p.get('value'))
                    result=self.run(name)
                    settings=self.vars.get('settings')
                    self.vars=old
                    if settings is not None:self.vars['settings']=settings
                elif name=='vardath.go.depart':result=self.departed
                else:raise AssertionError('Unexpected script '+name)
                if n.get('result'):self.assign(n.get('result'),result)
            elif n.tag=='create_order':
                ident=self.expr(n.get('id'));pars={p.get('name'):self.expr(p.get('value')) for p in n}
                order=Obj('created'+str(len(self.new_orders)),id=ident,state='ready',exists=True,isoverride=n.get('override')=='true',params=pars)
                self.new_orders.append(order)
                if n.get('default')=='true':self.default=order;self.current=order
                else:self.queue.insert(0,order)
                self.assign(n.get('name'),order)
            elif n.tag=='set_order_state':
                order=self.expr(n.get('order'));state=self.expr(n.get('state'))
                if state=='finish':self.assert_transition=order.state in ['critical','started'];assert self.assert_transition
                order.state=state
            elif n.tag=='wait' and 'exact' not in n.attrib:self.age+=10
            else:super().execute([n])

class ExecutedRecovery(unittest.TestCase):
    def test_sector_trip_does_not_accept_a_native_true_without_arrival(self):
        v=RecoveryVM();v.vars['destination']=Obj('remote',exists=True,owner=SECTOR.owner)
        # The test's supported sector reference is updated separately from location.
        # Use SECTOR as the destination and another sector as actual location.
        v.vars['destination']=SECTOR;v.current_sector=Obj('other',exists=True)
        v.moves_arrive=False
        self.assertFalse(v.run('vardath.go.travel'))
        self.assertEqual(len(v.native_moves),2)
        self.assertTrue(all(p['endintargetsector'] is False for p in v.native_moves))
    def test_actual_arrival_completes_trip_once(self):
        v=RecoveryVM();v.vars['destination']=SECTOR;v.current_sector=Obj('other',exists=True)
        self.assertTrue(v.run('vardath.go.travel'));self.assertEqual(len(v.native_moves),1)
    def test_out_of_scope_travel_never_starts(self):
        v=RecoveryVM();v.vars['destination']=SECTOR;v.in_scope=False
        self.assertFalse(v.run('vardath.go.travel'));self.assertEqual(v.native_moves,[])
    def test_direct_order_prevents_automatic_travel(self):
        v=RecoveryVM();v.vars['destination']=SECTOR;v.current_sector=Obj('other',exists=True)
        v.current=Obj('userorder',id='MoveWait',exists=True)
        self.assertFalse(v.run('vardath.go.travel'));self.assertEqual(v.native_moves,[])
    def test_docking_is_a_separate_finite_native_order_and_keeps_default(self):
        v=RecoveryVM();original=v.default
        self.assertFalse(v.run('vardath.go.dock'))
        self.assertIs(v.default,original);self.assertEqual(len(v.queue),1)
        self.assertEqual(v.queue[0].id,'DockAt');self.assertEqual(v.queue[0].params['destination'],BUYER)
        self.assertTrue(v.queue[0].isoverride)
        self.assertIs(v.state['vgo_dock_order'],v.queue[0])
    def test_pending_docking_does_not_create_duplicates(self):
        v=RecoveryVM();v.run('vardath.go.dock');v.run('vardath.go.dock')
        self.assertEqual(len(v.queue),1)
    def test_only_actual_docking_returns_success(self):
        v=RecoveryVM();v.run('vardath.go.dock');v.docked=BUYER
        self.assertTrue(v.run('vardath.go.dock'));self.assertEqual(len(v.new_orders),1)
    def test_critical_legacy_default_reconstruction_keeps_false_zero_and_all_settings(self):
        v=RecoveryVM();v.current.state='critical';before=dict(v.settings)
        v.state.update(vgo_passengers=['same-npc'],vgo_crystal_stock={'inv_crystal_01':9})
        self.assertTrue(v.run('vardath.go.refreshdefault'))
        self.assertEqual(v.default.id,'VGO_taxi');self.assertEqual(v.default.params,before)
        self.assertFalse(v.default.params['repeat']);self.assertEqual(v.default.params['minreward'],0)
        self.assertEqual(v.state['vgo_passengers'],['same-npc']);self.assertEqual(v.state['vgo_crystal_stock'],{'inv_crystal_01':9})
    def test_normal_or_user_default_is_never_reconstructed(self):
        v=RecoveryVM();self.assertFalse(v.run('vardath.go.refreshdefault'));self.assertEqual(v.new_orders,[])
        v.default.id='MoveWait';v.default.state='critical'
        self.assertFalse(v.run('vardath.go.refreshdefault'));self.assertEqual(v.new_orders,[])
    def test_deployed_hacker_prevents_default_reconstruction(self):
        v=RecoveryVM();v.default.state='critical';v.state['vgo_hack_deployed']=True
        self.assertFalse(v.run('vardath.go.refreshdefault'));self.assertEqual(v.new_orders,[])
    def test_failed_sale_dock_selects_another_real_buyer_with_same_stock(self):
        v=BaseVM({WARES[0]:3});other=Obj('otherbuyer',owner=BUYER.owner,sector=SECTOR,isoperational=True,isplayerowned=False,exists=True)
        v.state.update(vgo_crystal_sale_station=BUYER,vgo_dock_failed_target=BUYER,vgo_dock_retry=v.age+300)
        v.station_candidates=[BUYER,other];v.docked=NULL
        self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertIs(v.docked,other);self.assertEqual(v.get('vgo_crystal_sold'),3)

class SourceAndCompatibility(unittest.TestCase):
    def test_invalid_yield_property_and_sector_shortcut_are_absent(self):
        for p in (MOD/'aiscripts').glob('*.xml'):
            r=E.parse(p).getroot();self.assertNotIn('averagemaxyield',p.read_text())
            self.assertIsNone(r.find(".//param[@name='endintargetsector'][@value='true']"))
            self.assertIsNone(r.find(".//run_script[@name=\"'order.dock'\"]"))
    def test_every_refresh_branch_snapshots_exact_declared_settings(self):
        r=xml('vardath.go.refreshdefault')
        branches=[n for n in r.findall('attention/actions/do_if') if n.find('create_order') is not None]
        self.assertEqual(len(branches),13)
        for b in branches:
            new=b.find('create_order');ident=new.get('id').strip("'")
            wrapper=next(E.parse(p).getroot() for p in (MOD/'aiscripts').glob('order.vardath.go.*.xml') if E.parse(p).find('order').get('id')==ident)
            self.assertEqual({p.get('name') for p in new},{p.get('name') for p in wrapper.findall('order/params/param')})
            self.assertEqual(new.get('default'),'true');self.assertNotIn('immediate',new.attrib)
    def test_fare_still_requires_real_disembarkation_and_dock_adapter_success(self):
        r=xml('vardath.go.passengers.deliver');a=r.find('attention/actions')
        gate=next(i for i,n in enumerate(a) if n.tag=='run_script' and n.get('name')=="'vardath.go.dock'")
        self.assertEqual(a[gate+1].get('value'),'not $vgo_docked')
        self.assertIsNotNone(a[gate+1].find("return[@value='0']"))
        self.assertIn("$vgo_taxi_delivered",E.tostring(r,encoding='unicode'))
        self.assertIsNone(r.find('.//reward_player'));self.assertIsNone(r.find('.//remove_npc_template'))
    def test_morale_does_not_require_a_comms_actor_and_never_sets_hold(self):
        r=xml('vardath.go.task.morale');text=E.tostring(r,encoding='unicode')
        self.assertNotIn('iscommable',text);self.assertIsNotNone(r.find('.//add_skill'))
        self.assertIn('$target.pilot.isclass.npc',text)
        self.assertNotIn('MoveWait',text);self.assertIsNone(r.find('.//set_order_failed'))
    def test_remote_search_is_throttled_and_uses_active_trader_destination(self):
        r=xml('vardath.go.find');text=E.tostring(r,encoding='unicode')
        self.assertIn('player.age + 1min',text);self.assertIn('$galaxychecked',text)
        self.assertIsNotNone(r.find(".//find_ship[@space='"+S+".$vgo_scope'][@primarypurpose='purpose.trade']"))
        self.assertIsNotNone(r.find(".//run_script[@name=\"'vardath.go.destination'\"]"))
    def test_cancel_only_owned_docking_when_new_orders_arrive(self):
        r=E.parse(MOD/'md/VGO_State.xml').getroot();cue=r.find(".//cue[@name='DockOrdersV34']")
        text=E.tostring(cue,encoding='unicode')
        self.assertIn('$vgo_dock_previousorders.indexof.{$other}',text)
        guard=next(n for n in cue.iter('do_if') if n.find('cancel_order') is not None)
        self.assertIn("$dockorder.id == 'DockAt'",guard.get('value'));self.assertIn('$dockorder.isoverride',guard.get('value'))
        self.assertEqual(guard.find('cancel_order').get('order'),'$dockorder')
    def test_sector_explorer_patch_matches_the_exact_logged_input(self):
        p=MOD/'extensions/fs_exp/aiscripts/sectorexplorer.xml';op=etree.parse(str(p)).getroot()[0]
        old='not $fs_target.isblacklisted.{blacklisttype.travel}.{blacklistgroup.civilian}.{this.assignedcontrolled} and not $fs_target.isblacklisted.{blacklisttype.sectoractivity}.{blacklistgroup.civilian}.{this.assignedcontrolled}'
        target=etree.Element('aiscript');a=etree.SubElement(target,'attention');a=etree.SubElement(a,'actions');n=etree.SubElement(a,'do_if',value=old)
        matches=target.xpath(op.get('sel'));self.assertEqual(len(matches),1)
        matches[0].getparent().set('value',op.text)
        self.assertIn('blacklisttype.sectortravel',n.get('value'));self.assertNotIn('blacklisttype.travel}',n.get('value'))
    def test_subscription_patch_changes_only_undefined_faction_reference(self):
        p=MOD/'extensions/z_ram_autotradesubs/md/ramautosubs.xml';op=etree.parse(str(p)).getroot()[0]
        old='faction.player.canholdlicence.tradesubscription.{faction.alliance} and not faction.player.haslicence.tradesubscription.{alliance}'
        root=etree.Element('mdscript');a=etree.SubElement(root,'actions');n=etree.SubElement(a,'do_if',value=old)
        self.assertEqual(len(root.xpath(op.get('sel'))),1)
        self.assertEqual(op.text,old.replace('{alliance}','{faction.alliance}'))
        self.assertEqual(op.get('silent'),'true')
    def test_dead_invincibility_request_is_removed_without_reading_its_state(self):
        op=E.parse(MOD/'md/lib_generic.xml').getroot()[0]
        expression=op.text.replace('not $RequesterCue.exists','not exists').replace('$RequesterCue.state','state()').replace('cuestate.complete',"'complete'").replace('cuestate.active',"'active'")
        for exists,value,remove in [(False,None,True),(True,'active',False),(True,'complete',False),(True,'cancelled',True)]:
            def state():
                if not exists:raise AssertionError('Read a dead cue state')
                return value
            self.assertEqual(eval(expression,{'__builtins__':{}},{'exists':exists,'state':state}),remove)
    def test_missing_faction_equipment_selects_native_defaults_without_fabricating_table(self):
        root=E.parse(MOD/'md/finalisestations.xml').getroot()
        guards=[n for n in root if n.get('sel').endswith('/@value')]
        self.assertEqual(len(guards),2)
        for table,entry,allowed in [(False,None,False),(True,None,False),(True,['turret'],True)]:
            expression=guards[0].text.replace('md.$EquipmentTable?','present').replace('@md.$EquipmentTable.{$Station.owner}','entry').replace('null','None')
            self.assertEqual(eval(expression,{'__builtins__':{}},{'present':table,'entry':entry}),allowed)
        for op in root:
            if op.get('sel').endswith('/@wares'):
                condition,branches=op.text[3:].split(' then ');yes,no=branches.split(' else ')
                for wares in [[],['turret']]:
                    chosen=yes if len(wares) else no
                    self.assertEqual(wares if chosen=='$PossibleWares' else None,wares or None)
        self.assertTrue(all(n.tag=='replace' for n in root))

if __name__=='__main__':unittest.main(verbosity=2)
