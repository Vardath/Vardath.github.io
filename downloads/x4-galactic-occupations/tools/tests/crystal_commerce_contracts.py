#!/usr/bin/env python3
"""Execute stock, yield-conversion and settlement XML with mocked native actions.

This small interpreter is intentionally not an X4 runtime or expression parser.
It exercises the shipped XML's accounting/control flow with rejected and partial
native actions. Navigation, region streaming and engine payments need live tests.
"""
from pathlib import Path
import copy
import re
import unittest
import xml.etree.ElementTree as E
from unittest.mock import patch

MOD=Path(__file__).resolve().parents[2]/'vardath_galactic_occupations'
S='player.entity.$vgo_objects.{this.ship}'
WARES=[f'inv_crystal_0{i}' for i in range(1,6)]
PRICES=dict(zip(WARES,[100000,1000000,1500000,2000000,12500000])) # raw hundredths of Cr

class Obj:
    def __init__(self,name,**attrs):self.name=name;self.__dict__.update(attrs)
    def __getattr__(self,key):return False
    def __repr__(self):return self.name
    def __deepcopy__(self,memo):return self

PLAYER=Obj('player',dock_ok=True,hostile=False)
OWNERLESS=Obj('ownerless',dock_ok=False,hostile=False)
FACTION=Obj('argon',dock_ok=True,hostile=False)
SECTOR=Obj('field',owner=FACTION,exists=True)
BUYER=Obj('buyer',owner=FACTION,sector=SECTOR,isoperational=True,isplayerowned=False,exists=True)
NULL=Obj('null',exists=False,isoperational=False,isplayerowned=False,owner=OWNERLESS,sector=SECTOR)
CAPTAIN=Obj('captain',exists=True)
ENTITY=Obj('entity',exists=True)

class Returned(Exception):pass
class Continued(Exception):pass
class Broken(Exception):pass

def xml(name):return E.parse(MOD/'aiscripts'/f'{name}.xml').getroot()

class VM:
    def __init__(self,stock=None):
        self.state={'vgo_crystal_stock':dict(stock or {}),'vgo_crystal_sale_station':BUYER,
                    'vgo_risk':1,'vgo_serial':0}
        self.vars={'source':CAPTAIN,'limits':None}
        self.inventories={CAPTAIN:{},ENTITY:{}}
        self.money=10000000;self.age=1000;self.owned=True;self.direct=False
        self.occupied=False;self.docked=BUYER;self.can_dock=True;self.departed=True
        self.in_scope=True;self.credit_limit=None;self.remove_limit=None
        self.resource=100000;self.rolls=[1];self.roll_index=0
        self.receipts=[];self.reward_requests=[];self.reputation=[];self.outcomes=[]
        self.rep_times={};self.interrupt_on_wait=False
        self.station_candidates=[BUYER]

    def get(self,key,index=None):
        value=self.state.get(key,NULL if key.endswith('_station') else 0)
        return value.get(index,0) if index is not None else value

    def expr(self,text):
        text=text.strip()
        # The conditional forms used by these helpers are at expression start.
        if text.startswith('if '):
            depth=0;quote=False;then=otherwise=None;i=3
            while i<len(text):
                ch=text[i]
                if ch=="'":quote=not quote
                if not quote:
                    if ch in '([':depth+=1
                    elif ch in ')]':depth-=1
                    if depth==0 and text.startswith(' then ',i) and then is None:then=i;i+=5
                    elif depth==0 and text.startswith(' else ',i):otherwise=i;break
                i+=1
            condition=text[3:then];yes=text[then+6:otherwise];no=text[otherwise+6:]
            chosen=yes if self.expr(condition) else no
            if chosen.startswith('(') and chosen.endswith(')'):chosen=chosen[1:-1]
            return self.expr(chosen)
        t=text
        t=re.sub(r'\(([^()]*)\)i',r'int(\1)',t)
        t=t.replace('this.ship.order != this.ship.defaultorder','direct')
        t=t.replace("this.ship.order.id != 'VGO_crystal'",'direct')
        t=t.replace('this.ship == player.occupiedship','occupied')
        t=t.replace('@this.ship.dock.container','docked').replace('this.ship.dock.container','docked')
        t=t.replace('this.ship.isplayerowned','owned').replace('this.ship.pilot','captain')
        t=t.replace('this.ship.sector','ship_sector')
        t=t.replace('player.entity.inventory.{$ware}.count',"inv(entity,v('ware'))")
        t=t.replace('$source.inventory.{$ware}.count',"inv(v('source'),v('ware'))")
        t=t.replace('player.entity', 'entity') if '$vgo_objects' not in t and '$vgo_rep_times' not in t else t
        t=t.replace('$ware.averageprice',"price(v('ware'))")
        t=t.replace('$buyer.owner.hasrelation.dock.{faction.player}',"v('buyer').owner.dock_ok")
        t=t.replace('$buyer.sector.owner.hasrelation.enemy.{faction.player}',"v('buyer').sector.owner.hostile")
        t=t.replace('$station.owner.hasrelation.dock.{faction.player}',"v('station').owner.dock_ok")
        t=t.replace('$station.sector.owner.hasrelation.enemy.{faction.player}',"v('station').sector.owner.hostile")
        t=t.replace('$faction.hasrelation.dock.{faction.player}',"v('faction').dock_ok")
        t=t.replace(S+'.$vgo_scope.indexof.{$buyer.sector}','in_scope')
        t=t.replace('player.entity.$vgo_rep_times.{$faction}?','rep_present')
        t=t.replace('player.entity.$vgo_rep_times.{$faction}',"rep_time()")
        t=t.replace('player.entity.$vgo_rep_times?','True')
        t=t.replace('player.money','money').replace('player.age','age')
        pattern=r'@?'+re.escape(S)+r'\.\$(\w+)(?:\.\{\$(\w+)\})?(\?)?'
        def state(m):
            if m[3]:return 'present('+repr(m[1])+')'
            return 'st('+repr(m[1])+(','+"v("+repr(m[2])+")" if m[2] else '')+')'
        t=re.sub(pattern,state,t)
        t=re.sub(r'@?\$limits\.\{\$ware\}',"at(v('limits'),v('ware'))",t)
        t=re.sub(r'\$(\w+)',lambda m:'v('+repr(m[1])+')',t)
        t=t.replace('faction.player','player_faction').replace('faction.ownerless','ownerless')
        t=t.replace('table[]','{}')
        for token,value in [('true','True'),('false','False'),('null','None'),('le','<='),('lt','<'),('ge','>='),('gt','>')]:t=re.sub(r'\b'+token+r'\b',value,t)
        t=re.sub(r'(\d+)Cr',lambda m:str(int(m[1])*100),t)
        t=re.sub(r'(\d+)min',lambda m:str(int(m[1])*60),t)
        t=re.sub(r'(\d+)s',lambda m:m[1],t)
        t=re.sub(r'ware\.(inv_crystal_0[1-5])',lambda m:repr(m[1]),t)
        # integer casts in the depleted-yield calculation (not rounded stock).
        t=re.sub(r'\(([^()]*)\)i',r'int(\1)',t)
        while re.search(r'\[([^\[\]]*)\]\.(min|max)',t):t=re.sub(r'\[([^\[\]]*)\]\.(min|max)',lambda m:m[2]+'('+m[1]+')',t)
        return eval(t,{'__builtins__':{}},{'v':lambda n:self.vars.get(n,0),'st':self.get,
            'present':lambda k:k in self.state,'at':lambda d,k:d.get(k,0),
            'min':min,'max':max,'int':int,'price':lambda w:PRICES[w],
            'inv':lambda o,w:self.inventories[o].get(w,0),'owned':self.owned,
            'direct':self.direct,'occupied':self.occupied,'docked':self.docked,
            'in_scope':self.in_scope,'money':self.money,'age':self.age,
            'captain':CAPTAIN,'entity':ENTITY,'player_faction':PLAYER,'ownerless':OWNERLESS,'ship_sector':SECTOR,
            'rep_present':self.vars.get('faction') in self.rep_times,
            'rep_time':lambda:self.rep_times.get(self.vars.get('faction'),0)})

    def assign(self,name,value,remove=False):
        if name=='$buyer' and value is None:value=NULL
        if name=='player.entity.$vgo_rep_times.{$faction}':self.rep_times[self.vars['faction']]=value;return
        if name.startswith(S+'.$'):
            tail=name[len(S)+2:];m=re.fullmatch(r'(\w+)\.\{\$(\w+)\}',tail)
            if m:self.state.setdefault(m[1],{})[self.vars[m[2]]]=value
            elif remove:self.state.pop(tail,None)
            else:self.state[tail]=value
        elif name.startswith('$'):
            self.vars[name[1:]]=value
        else:raise AssertionError('Unknown assignment '+name)

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
                for value in self.expr(n.get('in')):
                    self.vars[n.get('name')[1:]]=value
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif tag=='do_all':
                for _ in range(self.expr(n.get('exact'))):self.execute(n)
            elif tag=='set_value':
                if n.get('name').endswith(('.$vgo_status','.$vgo_result')):self.assign(n.get('name'),n.get('exact'));continue
                if n.get('name')=='$roll':value=self.rolls[self.roll_index%len(self.rolls)];self.roll_index+=1
                else:value=self.expr(n.get('exact'))
                self.assign(n.get('name'),value)
            elif tag=='remove_value':self.assign(n.get('name'),None,remove=True)
            elif tag=='remove_inventory':
                owner=self.expr(n.get('entity'));ware=self.expr(n.get('ware'));request=self.expr(n.get('exact'))
                amount=min(request,self.inventories[owner].get(ware,0))
                if self.remove_limit is not None:amount=min(amount,self.remove_limit)
                self.inventories[owner][ware]=self.inventories[owner].get(ware,0)-amount
            elif tag=='deplete_yield':
                requested=self.expr(n.get('amount'));actual=min(requested,self.resource)
                self.resource-=actual;self.assign(n.get('amount'),actual)
            elif tag=='reward_player':
                amount=self.expr(n.get('money'));self.reward_requests.append(amount)
                self.money+=amount if self.credit_limit is None else min(amount,self.credit_limit)
            elif tag=='run_script':
                name=n.get('name').strip("'");params={p.get('name'):p.get('value') for p in n}
                value=None
                if name=='vardath.go.recordpayment':self.receipts.append(self.expr(params['amount']))
                elif name=='vardath.go.recordresult':self.outcomes.append(params['outcome'])
                elif name=='vardath.go.depart':value=self.departed
                elif name=='move.generic':pass
                elif name=='vardath.go.dock':
                    self.docked=self.vars['buyer'] if self.can_dock else NULL
                    value=self.can_dock
                else:raise AssertionError('Unknown native/script mock '+name)
                if n.get('result'):self.assign(n.get('result'),value)
            elif tag=='find_station':self.assign(n.get('name'),self.station_candidates)
            elif tag=='wait':
                self.age+=self.expr(n.get('exact'))
                if self.interrupt_on_wait:self.direct=True;self.docked=NULL
            elif tag=='add_faction_relation':self.reputation.append(float(n.get('value')))
            elif tag=='return':raise Returned(self.expr(n.get('value')))
            elif tag=='continue':raise Continued()
            elif tag=='break':raise Broken()
            elif tag in ['debug_text','write_to_logbook','set_command_action']:pass
            else:raise AssertionError('Unmodelled action '+tag)

    def run(self,name):
        try:self.execute(xml(name).find('attention/actions'))
        except Returned as result:return result.args[0]

    def mine_tail(self,items=24):
        self.state.update(vgo_crystal_work_items=items,vgo_crystal_work_elapsed=300)
        self.vars.update(sector=SECTOR,pos='field-position',ore=Obj('ore'))
        actions=list(xml('vardath.go.crystal.simulation').find('attention/actions'))
        start=next(i for i,n in enumerate(actions) if n.tag=='set_value' and n.get('name')=='$drained')
        try:self.execute(actions[start:])
        except Returned as result:return result.args[0]

class CommerceAccounting(unittest.TestCase):
    def test_full_batch_requires_actual_yield_depletion(self):
        v=VM();self.assertEqual(v.mine_tail(),2);self.assertEqual(v.resource,97600)
        self.assertEqual(sum(v.get('vgo_crystal_stock').values()),24)
        self.assertEqual(v.money,10000000);self.assertEqual(v.inventories[ENTITY],{})
    def test_depleted_and_partial_fields_never_credit_requested_stock(self):
        for available,expected in [(0,0),(99,0),(100,1),(299,2),(2400,24)]:
            with self.subTest(available=available):
                v=VM();v.resource=available;v.mine_tail()
                self.assertEqual(sum(v.get('vgo_crystal_stock').values()),expected)
                self.assertEqual(v.reward_requests,[])
    def test_all_five_grade_branches_use_existing_native_crystal_wares(self):
        v=VM();v.rolls=[1,851,971,996,1000];v.mine_tail(5)
        self.assertEqual(v.get('vgo_crystal_stock'),{w:1 for w in WARES})
    def test_stock_contains_only_observed_captain_withdrawals(self):
        v=VM();v.inventories[CAPTAIN]={WARES[0]:5,'parts':19};v.remove_limit=2
        self.assertEqual(v.run('vardath.go.crystal.stock'),2)
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],2)
        self.assertEqual(v.inventories[CAPTAIN],{WARES[0]:3,'parts':19})
        self.assertEqual(v.inventories[ENTITY],{})
    def test_rejected_real_item_removal_produces_no_stock(self):
        v=VM();v.inventories[CAPTAIN]={WARES[0]:5};v.remove_limit=0
        self.assertEqual(v.run('vardath.go.crystal.stock'),0)
        self.assertEqual(sum(v.get('vgo_crystal_stock').values()),0)
    def test_existing_player_inventory_cannot_be_swept_without_attributed_limits(self):
        v=VM();v.vars['source']=ENTITY;v.inventories[ENTITY]={WARES[0]:99}
        self.assertEqual(v.run('vardath.go.crystal.stock'),0)
        self.assertEqual(v.inventories[ENTITY][WARES[0]],99)
    def test_direct_native_pickup_stashes_only_drop_attributed_delta(self):
        v=VM();v.vars.update(source=ENTITY,limits={WARES[0]:3})
        v.inventories[ENTITY]={WARES[0]:102,WARES[1]:50}
        self.assertEqual(v.run('vardath.go.crystal.stock'),3)
        self.assertEqual(v.inventories[ENTITY],{WARES[0]:99,WARES[1]:50})
    def test_sale_uses_native_average_prices_and_only_observed_money(self):
        v=VM({WARES[0]:4,WARES[1]:2});before=v.money
        self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.money-before,2400000);self.assertEqual(v.receipts,[2400000])
        self.assertEqual(v.get('vgo_crystal_sold'),6);self.assertEqual(v.reputation,[0.00002])
        self.assertEqual(sum(v.get('vgo_crystal_stock').values()),0)
    def test_completed_sale_cannot_pay_or_grant_reputation_twice(self):
        v=VM({WARES[0]:4});self.assertTrue(v.run('vardath.go.sellcrystals'));paid=v.money
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.money,paid)
        self.assertEqual(len(v.receipts),1);self.assertEqual(len(v.reputation),1)
    def test_partial_credit_retries_only_unpaid_remainder_after_serialized_reload(self):
        v=VM({WARES[0]:4});v.credit_limit=150000
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.get('vgo_crystal_sale_due'),250000)
        self.assertEqual(v.get('vgo_crystal_sold'),0);self.assertEqual(v.reputation,[])
        recovered=copy.deepcopy(v);recovered.credit_limit=None
        self.assertTrue(recovered.run('vardath.go.sellcrystals'))
        self.assertEqual(recovered.reward_requests,[400000,250000])
        self.assertEqual(sum(recovered.receipts),400000);self.assertEqual(recovered.get('vgo_crystal_sold'),4)
    def test_rejected_payment_keeps_unpaid_claim_and_does_not_create_receipt(self):
        v=VM({WARES[0]:4});v.credit_limit=0
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.receipts,[])
        self.assertEqual(v.get('vgo_crystal_sale_due'),400000);self.assertEqual(v.get('vgo_crystal_sale_units'),4)
        self.assertEqual(v.reputation,[])
    def test_failed_docking_never_consumes_stock_or_issues_payment(self):
        v=VM({WARES[0]:4});v.docked=NULL;v.can_dock=False
        self.assertFalse(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4);self.assertEqual(v.reward_requests,[])
    def test_player_order_during_sale_wait_prevents_payment(self):
        v=VM({WARES[0]:4});v.interrupt_on_wait=True
        self.assertFalse(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4);self.assertEqual(v.reward_requests,[])
    def test_shared_faction_cooldown_limits_reputation_across_batches(self):
        v=VM({WARES[0]:4});self.assertTrue(v.run('vardath.go.sellcrystals'))
        v.state['vgo_crystal_stock']={WARES[0]:1};v.state['vgo_crystal_sale_station']=BUYER
        self.assertTrue(v.run('vardath.go.sellcrystals'));self.assertEqual(len(v.reputation),1)
    def test_zero_price_override_retains_stock_and_grants_nothing(self):
        v=VM({WARES[0]:4})
        with patch.dict(PRICES,{WARES[0]:0}):self.assertFalse(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
        self.assertEqual(v.reward_requests,[]);self.assertEqual(v.reputation,[])
    def test_two_miners_share_only_actual_remaining_region_yield(self):
        first=VM();first.resource=3500;first.mine_tail()
        second=VM();second.resource=first.resource;second.mine_tail()
        self.assertEqual(first.get('vgo_crystal_simulated'),24)
        self.assertEqual(second.get('vgo_crystal_simulated'),11)
        self.assertEqual(second.resource,0)

class CommerceSafetyContracts(unittest.TestCase):
    def test_no_follow_player_destination_or_physical_object_creation(self):
        r=xml('vardath.go.crystal.simulation');text=E.tostring(r,encoding='unicode')
        self.assertNotIn('exact="player.sector"',text);self.assertNotIn('player.entity.relativeposition',text)
        for tag in ['create_drop','add_inventory','create_object','reward_player']:self.assertEqual(len(list(r.iter(tag))),0)
        self.assertIn('this.ship.sector == player.sector',text)
    def test_mining_elapsed_time_is_bounded_per_active_tick_and_persistent(self):
        r=xml('vardath.go.crystal.simulation');loop=r.find('.//do_while')
        wait=loop.find('wait');self.assertEqual(wait.get('exact'),'10s')
        nodes=list(loop);wi=nodes.index(wait)
        self.assertIn('this.ship.order != this.ship.defaultorder',nodes[wi+1].get('value'))
        elapsed=loop.find("set_value[@name='"+S+".$vgo_crystal_work_elapsed']").get('exact')
        self.assertIn('[player.age - $tick,10s].min',elapsed)
        self.assertIn(S+'.$vgo_crystal_work_goal',elapsed)
        v=VM();v.state.update(vgo_crystal_work_elapsed=100,vgo_crystal_work_goal=300)
        v.vars['tick']=0;v.age=100000
        self.assertEqual(v.expr(elapsed),110) # no catch-up income from hours of other orders
    def test_native_depletion_is_inout_and_does_not_need_mineral_cargo(self):
        n=xml('vardath.go.crystal.simulation').find('.//deplete_yield')
        self.assertEqual(n.get('amount'),'$drained');self.assertNotIn('container',n.attrib)
        self.assertEqual(n.find('position').get('value'),'$pos')
    def test_new_payments_match_native_script_add_records(self):
        r=xml('vardath.go.recordpayment');entry=r.find(".//append_to_list[@name='player.entity.$vardath_income']")
        self.assertTrue(entry.get('exact').endswith("'script_add']"))
        self.assertNotIn("then 'transfer'",entry.get('exact'))
    def test_13_roles_and_configurable_batch_values_survive_upgrade(self):
        r=xml('order.vardath.go.crystal')
        for name in ['miningtime','batchsize']:
            self.assertIsNotNone(r.find("order/params/param[@name='"+name+"']"))
            self.assertIsNotNone(r.find("patch[@sinceversion='10']/do_if[@value='not $"+name+"?']"))
        recovery=E.parse(MOD/'md/VGO_State.xml').find(".//cue[@name='RecoverOrdersV34']")
        text=E.tostring(recovery,encoding='unicode');self.assertIn('order == $ship.defaultorder',text)
        startup=next(n.get('exact') for n in xml('vardath.go.worker').findall('attention/actions/set_value') if n.get('name')==S+'.$vgo_runtime')
        self.assertIn('$vgo_runtime != '+startup,text)

if __name__=='__main__':unittest.main(verbosity=2)
