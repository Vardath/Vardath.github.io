#!/usr/bin/env python3
"""Execute the retail MD, counter guard and AI with mocked native room movement.

This exercises the shipped state machine and financial helpers, including native
action rejection. It does not prove X4 room streaming, pathfinding or animations.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from crystal_commerce_contracts import VM, Obj, NULL, BUYER, ENTITY, SECTOR, S, WARES, Returned, Continued, Broken, MOD, xml
from passenger_completion_contracts import Seq

MD='player.entity.$vgo_objects.{$ship}'
ROOT=E.parse(MOD/'md/VGO_CrystalShop.xml').getroot()

class MissingClock:
    """Absent optional game times are null, rather than a numeric zero clock."""
    def __bool__(self):return False
    def __lt__(self,other):return False
    def __le__(self,other):return False
    def __gt__(self,other):return False
    def __ge__(self,other):return False

MISSING_CLOCK=MissingClock()

class RetailVM(VM):
    def __init__(self,stock=None):
        super().__init__({WARES[0]:4} if stock is None else stock)
        self.order=Obj('order',id='VGO_crystal',exists=True)
        self.ship=Obj('ship',exists=True,isplayerowned=True,order=self.order,defaultorder=self.order)
        self.ship.sector=SECTOR;self.ship.attention=1;self.player_sector=SECTOR
        self.shiproom=Obj('shiproom',exists=True,context=self.ship)
        self.shoproom=Obj('shoproom',exists=True,context=BUYER)
        self.seat=Obj('seat',component=self.shiproom)
        self.counter=Obj('counter',component=self.shoproom,hastag=Obj('tags',itemtrader=True))
        self.customer=Obj('customer',component=self.shoproom)
        self.crew=Obj('crew',exists=True,hasbody=True,room=self.shiproom,roomslot=self.seat,
                      iswalking=False,role='service',istemporary=True,controlpost='engineer',isclass=Obj('class',npc=True))
        self.captain=Obj('captain',exists=True,isclass=Obj('class',npc=True),room=self.shiproom,
                         roomslot=self.seat,iswalking=False,role='unassigned',controlpost='aipilot')
        self.ship.pilot=self.captain
        self.crew.npctemplate=1000;self.captain.npctemplate=1001
        self.crew.roleobject=self.ship;self.captain.roleobject=self.ship
        self.crew_roster={1000,1001}
        self.merchant.type='trader';self.merchant.room=self.shoproom;self.merchant.roomslot=self.counter
        self.crewlist=Seq([self.crew]);self.traders=Seq([self.merchant]);self.registry=Seq()
        self.other={};self.events=[];self.pending={};self.native_arrives=True
        self.trader_population=True;self.counter_points=True;self.interaction_point=True
        self.offset=Obj('offset',exists=True);self.distance=2;self.population_calls=[]
        self.populate_merchants=False;self.counter_slots=True;self.payment_attempt_times=[]
        self.floor_checks=[];self.floor_results=None;self.native_slot_walkable=True
        self.state['vgo_order']=self.order;self.ticks=0
        self.vars.update(ship=self.ship,buyer=BUYER)

    def context(self,obj,target):return bool(obj and obj is not NULL and getattr(obj,'context',NULL) is target)
    def get(self,key,index=None):
        if key in ['vgo_crystal_shop_actor','vgo_crystal_shop_trader'] and key not in self.state:return NULL
        if key=='vgo_crystal_shop_nextpayment' and key not in self.state:return MISSING_CLOCK
        return super().get(key,index)
    def path(self,path):
        bits=path.lstrip('@$').split('.');v=self.vars.get(bits[0],NULL)
        for b in bits[1:]:v=getattr(v,b,False)
        return v
    def remembered(self,value):
        key='retail_mock_'+str(len(self.vars));self.vars[key]=value;return '$'+key

    def expr(self,text):
        text=text.replace('this.ship','$ship').replace(MD,S)
        self.ship.order=NULL if self.direct else self.order
        self.ship.isplayerowned=self.owned
        self.ship.dock=Obj('dock',container=self.docked) if self.docked is not NULL else NULL
        self.vars['registry']=self.registry
        if text.startswith('table[') and text!='table[]':
            return {k.strip().lstrip('$'):self.expr(v.strip()) for k,v in
                    (part.split('=',1) for part in text[6:-1].split(','))}
        text=text.replace('player.occupiedship',self.remembered(self.ship if self.occupied else NULL))
        text=text.replace('player.sector',self.remembered(self.player_sector)).replace('attention.visible','1')
        text=text.replace('$buyer.dockingallowed.{$ship}',self.remembered(self.can_dock))
        text=text.replace('@$origin.component.exists',self.remembered(bool(self.path('$origin.component.exists'))))
        actor=self.vars.get('actor',NULL)
        text=text.replace('@$ship.people.{$actor.npctemplate}.exists',self.remembered(getattr(actor,'npctemplate',NULL) in self.crew_roster))
        text=text.replace('Init.$Ships','$registry')
        text=re.sub(r'@?'+re.escape(S)+r'\.\$(\w+)\.clone',lambda m:self.remembered(copy.deepcopy(self.get(m[1]))),text)
        p=r'@?player\.entity\.\$vgo_objects\.\{\$(\w+)\}(?:\.\$(\w+))?(\?)?'
        def other(m):
            obj=self.vars.get(m[1],NULL);data=self.other.get(obj,{})
            return self.remembered((m[2] in data if m[2] else obj in self.other) if m[3]
                                   else data.get(m[2],NULL if m[2] and m[2].endswith('owner') else MISSING_CLOCK if m[2] and m[2].endswith('_after') else 0))
        text=re.sub(p,other,text)
        text=re.sub(r'@?(\$\w+(?:\.\w+)*)\.\$(\w+)(\?)?',lambda m:self.remembered(
            m[2] in self.path(m[1]).__dict__ if m[3] else self.path(m[1]).__dict__.get(m[2],NULL if m[2].endswith('_ship') else False)),text)
        text=re.sub(r'@?(\$\w+(?:\.\w+)*)\.hascontext\.\{(\$\w+)\}',
                    lambda m:self.remembered(self.context(self.path(m[1]),self.path(m[2]))),text)
        text=re.sub(r'@?(\$\w+(?:\.\w+)*)\.distanceto\.\{(\$\w+)\}',lambda m:self.remembered(self.distance),text)
        text=text.replace('md.NPC_Instantiation.PlaceItemTrader.exists','true')
        for token in ['service','marine']:text=text.replace('entityrole.'+token,repr(token))
        text=text.replace('entitytype.trader',"'trader'")
        text=re.sub(r'(\d+(?:\.\d+)?)m\b',r'\1',text)
        text=re.sub(r'@(?=\$)','',text)
        try:return super().expr(text)
        except (AttributeError,SyntaxError,TypeError) as error:raise AssertionError('Unmodelled retail expression '+text) from error

    def assign(self,name,value,remove=False):
        if name=='$trader' and value is None:value=NULL
        name=name.replace(MD,S)
        if name=='Init.$Ships.{$i}':self.registry.pop(self.vars['i']-1);return
        p=re.fullmatch(r'player\.entity\.\$vgo_objects\.\{\$(\w+)\}(?:\.\$(\w+))?',name)
        if p:
            obj=self.vars[p[1]]
            if not p[2]:self.other[obj]=value
            elif remove:self.other.setdefault(obj,{}).pop(p[2],None)
            else:self.other.setdefault(obj,{})[p[2]]=value
            return
        p=re.fullmatch(r'\$(\w+)\.\$(\w+)',name)
        if p:
            actor=self.vars[p[1]]
            if remove:actor.__dict__.pop(p[2],None)
            else:setattr(actor,p[2],value)
            return
        super().assign(name,value,remove)

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
            elif tag=='do_for_each':
                entries=list(enumerate(self.expr(n.get('in')),1))
                if n.get('reverse')=='true':entries.reverse()
                for i,value in entries:
                    self.vars[n.get('name')[1:]]=value
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif tag=='do_while':
                while self.expr(n.get('value')):
                    self.ticks+=1
                    if self.ticks>1000:raise AssertionError('Retail loop exceeded mock budget')
                    self.execute(n)
            elif tag=='do_all':
                for i in range(1,self.expr(n.get('exact'))+1):
                    if n.get('counter'):self.vars[n.get('counter')[1:]]=i
                    try:self.execute(n)
                    except Broken:break
            elif tag=='include_actions':self.execute(ROOT.find(".//library[@name='"+n.get('ref')+"']/actions"))
            elif tag=='find_object_component':self.assign(n.get('name'),self.traders if n.get('entitytype') else self.crewlist)
            elif tag=='find_npc_slot':
                if n.get('tags')=='tag.itemtrader':value=Seq([self.counter]) if self.counter_slots else Seq()
                else:value=Seq([self.customer]) if n.get('multiple') and self.counter_points else self.seat if not n.get('multiple') else Seq()
                self.assign(n.get('name'),value)
            elif tag=='find_actor_interaction_point':
                raise AssertionError('NPCs are not class.object; retail must use native room-path validation')
            elif tag=='find_npc_waypoint':
                points=Seq()
                if n.get('append')=='true':points=Seq(self.vars.get(n.get('name')[1:],[]))
                self.assign(n.get('name'),points)
            elif tag=='transform_position':
                p=n.find('position');coords={k:self.expr(p.get(k,'0m')) for k in ['x','y','z']}
                self.offset=Obj('floor_position',**coords);self.assign(n.get('name'),self.offset)
            elif tag=='check_walk_path':
                if n.find('end') is None:valid=self.native_slot_walkable
                else:
                    pos=self.expr(n.find('end').get('value'));self.floor_checks.append((pos.x,pos.y,pos.z))
                    valid=(self.floor_results.pop(0) if self.floor_results else self.interaction_point)
                self.assign(n.get('result'),valid)
            elif tag=='set_entity_traits':
                actor=self.expr(n.get('entity'))
                for key,value in n.attrib.items():
                    if key!='entity':setattr(actor,'is'+key,self.expr(value))
            elif tag=='add_actor_to_post_location':
                actor=self.expr(n.get('actor'));actor.hasbody=True;actor.room=self.shiproom;actor.roomslot=self.seat
                self.events.append(('post',actor))
            elif tag=='add_actor_to_room':
                actor=self.expr(n.get('actor'));slot=self.expr(n.get('slot'))
                actor.room=slot.component;actor.iswalking=False;self.pending.pop(actor,None)
                if n.get('result'):self.assign(n.get('result'),True)
                self.events.append(('reconnect',actor,actor.room))
            elif tag=='stop_actor_walk':
                actor=self.expr(n.get('actor'));actor.iswalking=False;self.pending.pop(actor,None)
                self.events.append(('stopwalk',actor))
            elif tag=='signal_objects':
                if n.get('param')=="'vardath.go.crystal.shop'":
                    if self.ship not in self.registry:self.registry.append(self.ship)
                elif n.get('param')=="'vardath.go.recovery.track'":pass # Independent lifecycle tested separately.
                else:
                    actor=self.expr(n.get('object'));movement=self.expr(n.get('param2'))
                    target=movement.get('slot',NULL)
                    room=target.component if target is not NULL and target else movement['room']
                    actor.iswalking=True;self.pending[actor]=room
                    self.events.append(('walk',actor,room))
            elif tag=='signal_cue_instantly':
                self.population_calls.append(self.age)
                if self.populate_merchants and self.counter_slots:self.traders=Seq([self.merchant])
            elif tag=='reward_player':
                self.payment_attempt_times.append(self.age);super().execute([n])
            elif tag=='run_script' and n.get('name').strip("'") in ['vardath.go.crystal.atcounter','vardath.go.crystal.settle','vardath.go.crystal.exchange','vardath.go.crystal.remote.allowed','vardath.go.crystal.remote','vardath.go.crystal.shop','vardath.go.sellcrystals']:
                name=n.get('name').strip("'");args={p.get('name'):self.expr(p.get('value')) for p in n}
                saved=dict(self.vars);self.vars.update(args);result=self.run(name);self.vars=saved
                if n.get('result'):self.assign(n.get('result'),result)
            elif tag=='run_script' and n.get('name').strip("'") in ['vardath.go.crystal.stock','vardath.go.depart']:
                name=n.get('name').strip("'");saved=dict(self.vars);result=self.run(name);self.vars=saved
                if n.get('result'):self.assign(n.get('result'),result)
            elif tag=='run_script' and n.get('name')=="'move.undock'":
                self.docked=NULL;self.events.append(('undock',self.ship))
            elif tag=='wait':
                self.age+=self.expr(n.get('exact'))
                if self.interrupt_on_wait:self.direct=True;self.docked=NULL
                self.tick()
            elif tag=='write_to_logbook':self.events.append(('log',n.get('title')))
            elif tag=='set_value' and n.get('name')=='$movement':self.assign('$movement',self.expr(n.get('exact')))
            else:super().execute([n])

    def tick(self):
        if self.native_arrives:
            for actor,room in list(self.pending.items()):actor.room=room;actor.iswalking=False;del self.pending[actor]
        saved=dict(self.vars)
        self.execute(ROOT.find(".//cue[@name='Operations']/actions"))
        self.vars=saved
    def start(self):
        self.state.update(vgo_crystal_shop_phase='prepare',vgo_crystal_shop_station=BUYER,
                          vgo_crystal_shop_started=self.age,vgo_crystal_shop_step=self.age)
        self.registry.append(self.ship);self.tick()
    def reach_counter(self):
        self.start();self.age+=2;self.tick();self.age+=5;self.tick()
        return self.get('vgo_crystal_shop_phase')=='atcounter'

class PhysicalRetail(unittest.TestCase):
    def test_same_existing_crew_visits_counter_sells_and_returns_before_success(self):
        v=RetailVM();original=v.crew;before=v.money
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.money-before,400000);self.assertEqual(v.inventories[v.merchant][WARES[0]],4)
        self.assertIs(v.crew,original);self.assertIs(v.crew.room,v.shiproom)
        self.assertEqual([e[2] for e in v.events if e[0]=='walk'],[v.shoproom,v.shiproom])
        self.assertEqual(v.crew.controlpost,'engineer');self.assertTrue(v.crew.istemporary)
        self.assertFalse(v.crew.isbusy);self.assertNotIn('Stay',v.crew.__dict__)
    def test_captain_fallback_retains_pilot_control_post_and_identity(self):
        v=RetailVM();v.crewlist=Seq()
        self.assertTrue(v.run('vardath.go.crystal.shop'));self.assertIs(v.ship.pilot,v.captain)
        self.assertEqual(v.captain.controlpost,'aipilot');self.assertIs(v.captain.room,v.shiproom)
    def test_preexisting_stay_value_and_temporary_flag_are_restored(self):
        v=RetailVM();v.crew.Stay=False;v.crew.istemporary=False
        self.assertTrue(v.run('vardath.go.crystal.shop'));self.assertIs(v.crew.Stay,False)
        self.assertIs(v.crew.istemporary,False)
    def test_busy_mission_transferring_or_hacking_crew_are_never_repurposed(self):
        for key in ['isbusy','ismissionactor','istransferscheduled','vgo_hack_ship','vgo_sale_ship']:
            with self.subTest(key=key):
                v=RetailVM();setattr(v.crew,key,v.ship if key.endswith('_ship') else True)
                v.ship.pilot=NULL;v.start();self.assertNotIn('vgo_crystal_shop_actor',v.state)
    def test_absent_real_trader_is_native_population_throttled_and_retains_stock(self):
        v=RetailVM();v.traders=Seq();v.start();self.assertEqual(v.population_calls,[1000])
        for _ in range(20):v.age+=2;v.tick()
        self.assertEqual(len(v.population_calls),1);self.assertEqual(v.goods_transfers,[])
        v.age+=30;v.tick();self.assertEqual(len(v.population_calls),2)
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
    def test_absent_customer_positions_cannot_start_sale(self):
        v=RetailVM();v.counter_points=False;v.interaction_point=False;v.start()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'prepare');self.assertEqual(v.pending,{})
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.reward_requests,[])
    def test_a_still_walking_or_shipboard_actor_cannot_invoice(self):
        v=RetailVM();v.native_arrives=False;v.start()
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.goods_transfers,[])
        v.state['vgo_crystal_shop_phase']='atcounter';v.crew.iswalking=False
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.reward_requests,[])
    def test_actual_counter_dwell_is_required_before_sale(self):
        v=RetailVM();v.start();v.age+=2;v.tick()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'walking')
        v.age+=4;v.tick();self.assertEqual(v.get('vgo_crystal_shop_phase'),'walking')
        v.age+=1;v.tick();self.assertEqual(v.get('vgo_crystal_shop_phase'),'atcounter')
    def test_lost_counter_reservation_blocks_transfer_and_cash(self):
        v=RetailVM();self.assertTrue(v.reach_counter());v.other[v.merchant]['vgo_shop_owner']=Obj('other ship',exists=True)
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.goods_transfers,[])
        self.assertEqual(v.reward_requests,[])
    def test_second_ship_cannot_claim_another_representatives_counter(self):
        v=RetailVM();v.other[v.merchant]={'vgo_shop_owner':Obj('other',exists=True),'vgo_shop_expires':v.age+600}
        v.start();self.assertEqual(v.get('vgo_crystal_shop_phase'),'prepare');self.assertEqual(v.events,[])
    def test_departure_helper_keeps_ship_docked_until_same_crew_returns(self):
        v=RetailVM();v.native_arrives=False;v.start();v.crew.room=v.shoproom
        self.assertFalse(v.run('vardath.go.depart'));self.assertIs(v.docked,BUYER)
    def test_interrupted_sale_preserves_stock_and_registry_for_same_crew_return(self):
        v=RetailVM();self.assertTrue(v.reach_counter());v.interrupt_on_wait=True
        self.assertFalse(v.run('vardath.go.crystal.shop'));self.assertEqual(v.goods_transfers,[])
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returning');self.assertIn(v.ship,v.registry)
        v.interrupt_on_wait=False;v.direct=False;v.docked=BUYER;v.age+=30;v.tick();v.tick()
        self.assertIs(v.crew.room,v.shiproom);self.assertFalse(v.crew.isbusy)
    def test_missing_trader_times_out_and_restores_crew_without_selling(self):
        v=RetailVM();v.traders=Seq();self.assertFalse(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4);self.assertEqual(v.reward_requests,[])
        self.assertNotIn('vgo_sale_ship',v.crew.__dict__);self.assertTrue(v.crew.istemporary)
    def test_destroyed_actor_fails_without_inventing_a_replacement_or_a_return_receipt(self):
        v=RetailVM();v.start();v.crew.exists=False;v.crew.isclass.npc=False;v.crew_roster.remove(v.crew.npctemplate);v.state['vgo_crystal_shop_phase']='returning';v.tick()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned');self.assertFalse(v.get('vgo_crystal_shop_success'))
        self.assertFalse(any(e[0]=='log' for e in v.events));self.assertEqual(v.goods_transfers,[])
    def test_saved_paid_visit_is_resumed_even_when_stock_is_empty(self):
        v=RetailVM();self.assertTrue(v.reach_counter());self.assertTrue(v.run('vardath.go.crystal.settle'))
        v.state.update(vgo_crystal_shop_success=True,vgo_crystal_shop_phase='returning')
        v.state=copy.deepcopy(v.state);v.age+=25
        self.assertEqual(v.run('vardath.go.crystal.commercial'),1)
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(len(v.reward_requests),1)
    def test_stalled_return_recovers_the_same_actor_to_its_docked_ship(self):
        v=RetailVM();self.assertTrue(v.reach_counter());v.native_arrives=False
        v.state['vgo_crystal_shop_phase']='returning';v.age+=25;v.tick()
        self.assertTrue(v.crew.iswalking);self.assertIs(v.crew.room,v.shoproom)
        v.age+=121;v.tick();self.assertTrue(any(e[0]=='stopwalk' for e in v.events))
        self.assertIs(v.crew.room,v.shiproom);self.assertFalse(v.crew.iswalking)
        self.assertTrue(any(e[0]=='reconnect' and e[1] is v.crew for e in v.events))
        v.tick()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'returned')
    def test_active_service_refreshes_dock_lease_during_a_long_return(self):
        v=RetailVM();self.assertTrue(v.reach_counter());v.native_arrives=False
        v.state['vgo_crystal_shop_phase']='returning';v.age+=1801;v.tick()
        self.assertEqual(v.get('vgo_service_dock_until'),v.age+1800)
        self.assertIs(v.get('vgo_service_dock'),BUYER)

class RetailAccounting(unittest.TestCase):
    def counter(self,stock=None):
        v=RetailVM(stock);self.assertTrue(v.reach_counter());return v
    def test_native_merchant_refusal_retains_all_goods_and_pays_nothing(self):
        v=self.counter();v.accept_limit=0
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
        self.assertEqual(v.receipts,[]);self.assertEqual(v.reputation,[])
    def test_partial_merchant_acceptance_only_consumes_and_pays_for_actual_goods(self):
        v=self.counter();v.accept_limit=2;before=v.money
        self.assertTrue(v.run('vardath.go.crystal.settle'));self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],2)
        self.assertEqual(v.inventories[v.merchant][WARES[0]],2);self.assertEqual(v.money-before,200000)
    def test_reloaded_partial_credit_never_transfers_the_goods_twice(self):
        v=self.counter();v.credit_limit=150000
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.get('vgo_crystal_sale_due'),250000)
        v.state=copy.deepcopy(v.state);v.credit_limit=None
        self.assertTrue(v.run('vardath.go.crystal.settle'));self.assertEqual(sum(v.receipts),400000)
        self.assertEqual(v.inventories[v.merchant][WARES[0]],4);self.assertEqual(len(v.goods_transfers),1)
    def test_stock_collected_after_representative_left_is_not_in_this_visit(self):
        v=self.counter();v.state['vgo_crystal_stock'][WARES[0]]+=3
        self.assertTrue(v.run('vardath.go.crystal.settle'));self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],3)
        self.assertEqual(v.inventories[v.merchant][WARES[0]],4)
    def test_moving_away_from_counter_during_work_prevents_stock_transfer(self):
        v=self.counter();v.distance=10
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.goods_transfers,[])
    def test_retail_has_no_crew_cloning_template_removal_or_ui_trade_simulation(self):
        roots=[ROOT,xml('vardath.go.crystal.shop'),xml('vardath.go.crystal.settle')]
        for root in roots:
            for tag in ['create_npc','remove_npc_template','remove_actor_from_room','set_owner','set_entity_controlpost']:
                self.assertEqual(list(root.iter(tag)),[])

class FirstUseAndBuyerRecovery(unittest.TestCase):
    def test_no_nearby_free_slot_uses_actual_merchant_interaction_point(self):
        v=RetailVM();v.counter_points=False
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.receipts,[400000]);self.assertIs(v.crew.room,v.shiproom)
    def test_native_population_reply_can_start_first_visit_with_both_clocks_missing(self):
        v=RetailVM();v.traders=Seq();v.populate_merchants=True
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertEqual(len(v.population_calls),1);self.assertEqual(v.receipts,[400000])
        self.assertIs(v.crew.room,v.shiproom)
    def test_no_actual_counter_cannot_be_populated_or_sold_at(self):
        v=RetailVM();v.traders=Seq();v.populate_merchants=True;v.counter_slots=False
        self.assertFalse(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.get('vgo_crystal_shop_counter_slots'),0)
        self.assertEqual(v.traders,[]);self.assertEqual(v.reward_requests,[])
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
    def test_existing_population_clock_remains_station_throttled(self):
        v=RetailVM();v.traders=Seq();v.other[BUYER]={'vgo_shop_population_after':v.age+60}
        v.start();self.assertEqual(v.population_calls,[])
        v.age+=60;v.tick();self.assertEqual(v.population_calls,[1060])
    def test_existing_payment_clock_is_respected_then_same_visit_settles(self):
        v=RetailVM();self.assertTrue(v.reach_counter());due=v.age+60
        v.state['vgo_crystal_shop_nextpayment']=due
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertEqual(len(v.payment_attempt_times),1);self.assertGreaterEqual(v.payment_attempt_times[0],due+10)
    def test_failed_buyers_keep_independent_retry_times(self):
        v=RetailVM();v.traders=Seq();self.assertFalse(v.run('vardath.go.crystal.shop'))
        first=v.get('vgo_crystal_sale_cooldowns')[BUYER]
        other=Obj('second',exists=True,isoperational=True)
        v.vars['buyer']=other;v.docked=other
        self.assertFalse(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.get('vgo_crystal_sale_cooldowns')[BUYER],first)
        self.assertGreater(v.get('vgo_crystal_sale_cooldowns')[other],first)
    def test_shot_deposit_listener_allows_destroyed_source_without_global_subscription(self):
        event=xml('vardath.go.task.crystal').find('.//event_object_dropped_objects')
        self.assertEqual(event.get('object'),'$target');self.assertEqual(event.get('check'),'false')
        scan=xml('vardath.go.task.crystal').find(".//run_script[@name=\"'vardath.go.crystaldrops'\"]")
        self.assertEqual(scan.find("param[@name='force']").get('value'),'true')

if __name__=='__main__':unittest.main(verbosity=2)
