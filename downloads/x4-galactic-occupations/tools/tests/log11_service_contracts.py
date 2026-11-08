#!/usr/bin/env python3
"""Execute the log-11 recovery paths with mocked native results, not an X4 runtime.

The shipped AI/MD performs stock settlement and real passenger-roster handoffs.
Native rooms, role assignment, payment and navigation remain mocked boundaries.
"""
import copy
import re
import unittest
import xml.etree.ElementTree as E
from unittest.mock import patch
from crystal_commerce_contracts import Obj, NULL, BUYER, SECTOR, S, WARES, PRICES, MOD, xml
from crystal_retail_contracts import RetailVM, ROOT as SHOP, MISSING_CLOCK
from passenger_completion_contracts import PassengerVM, Seq

STATE=E.parse(MOD/'md/VGO_State.xml').getroot()

class RemoteVM(RetailVM):
    def __init__(self,stock=None):
        super().__init__(stock)
        self.ship.attention=0;self.player_sector=Obj('elsewhere',exists=True)
        self.counter_slots=False;self.counter_points=False;self.traders=Seq()
        self.after_wait=None
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
            elif n.tag=='wait' and self.after_wait:
                callback=self.after_wait;self.after_wait=None
                super().execute([n]);callback(self)
            else:super().execute([n])

class OffscreenSaleRecovery(unittest.TestCase):
    def test_actual_commercial_path_sells_saved_seven_without_counter_then_undocks(self):
        v=RemoteVM({WARES[0]:7});captain=v.ship.pilot;before=v.money
        self.assertEqual(v.run('vardath.go.crystal.commercial'),1)
        self.assertEqual(v.money-before,7*PRICES[WARES[0]])
        self.assertEqual(v.get('vgo_crystal_sold'),7);self.assertEqual(v.receipts,[700000])
        self.assertEqual(v.goods_transfers,[]);self.assertEqual(v.population_calls,[])
        self.assertIs(v.ship.pilot,captain);self.assertFalse(v.get('vgo_crystal_shop_deployed'))
        self.assertTrue(v.run('vardath.go.depart'));self.assertIs(v.docked,NULL)
        self.assertIn(('undock',v.ship),v.events)
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.money-before,700000)
    def test_all_grades_use_finite_native_prices_and_one_invoice(self):
        v=RemoteVM({w:2 for w in WARES});before=v.money
        self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.money-before,2*sum(PRICES.values()))
        self.assertEqual(v.get('vgo_crystal_sold'),10);self.assertEqual(v.reputation,[0.00002])
        self.assertEqual(v.get('vgo_crystal_sale_mode'),'off-screen broker')
    def test_remote_guard_rejects_observed_or_uncontrolled_or_invalid_docks(self):
        for reason in ['disabled','playersector','visible','direct','ownership','occupied','undocked','denied','deployed','untracked']:
            with self.subTest(reason=reason):
                v=RemoteVM();v.vars['buyer']=BUYER
                if reason=='disabled':v.state['vgo_simulatesales']=False
                elif reason=='playersector':v.player_sector=SECTOR
                elif reason=='visible':v.ship.attention=1
                elif reason=='direct':v.direct=True
                elif reason=='ownership':v.owned=False
                elif reason=='occupied':v.occupied=True
                elif reason=='undocked':v.docked=NULL
                elif reason=='denied':v.can_dock=False
                elif reason=='deployed':v.state['vgo_crystal_shop_deployed']=True
                else:v.state['vgo_order']=NULL
                self.assertFalse(v.run('vardath.go.crystal.remote'))
                self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
                self.assertEqual(v.reward_requests,[])
    def test_hostile_territory_requires_aggressive_setting(self):
        v=RemoteVM();v.vars['buyer']=BUYER
        with patch.object(BUYER.sector.owner,'hostile',True):
            self.assertFalse(v.run('vardath.go.crystal.remote.allowed'))
            v.state['vgo_risk']=2;self.assertTrue(v.run('vardath.go.crystal.remote.allowed'))
    def test_player_entering_or_new_order_during_work_preserves_all_stock(self):
        for change in [lambda v:setattr(v,'player_sector',SECTOR),lambda v:setattr(v,'direct',True)]:
            v=RemoteVM();v.vars['buyer']=BUYER;v.after_wait=change
            self.assertFalse(v.run('vardath.go.crystal.remote'))
            self.assertEqual(v.reward_requests,[]);self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],4)
            self.assertNotIn('vgo_crystal_remote_manifest',v.state)
    def test_snapshot_caps_items_added_during_wait(self):
        v=RemoteVM();v.vars['buyer']=BUYER
        v.after_wait=lambda v:v.state['vgo_crystal_stock'].update({WARES[0]:11})
        self.assertTrue(v.run('vardath.go.crystal.remote'))
        self.assertEqual(v.get('vgo_crystal_sold'),4);self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],7)
    def test_partial_payment_reload_retries_only_unpaid_balance_without_goods(self):
        v=RemoteVM();v.credit_limit=100000
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.get('vgo_crystal_sale_due'),300000)
        self.assertEqual(v.get('vgo_crystal_stock')[WARES[0]],0)
        v.state=copy.deepcopy(v.state);v.credit_limit=None
        self.assertFalse(v.run('vardath.go.sellcrystals'));self.assertEqual(v.reward_requests,[400000])
        v.age+=60;self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertEqual(v.reward_requests,[400000,300000]);self.assertEqual(sum(v.receipts),400000)
        self.assertEqual(v.get('vgo_crystal_sold'),4);self.assertEqual(v.goods_transfers,[])
    def test_no_price_or_no_stock_never_creates_cash(self):
        for stock in [{},{WARES[0]:4}]:
            v=RemoteVM(stock)
            with patch.dict(PRICES,{WARES[0]:0}):self.assertFalse(v.run('vardath.go.sellcrystals'))
            self.assertEqual(v.reward_requests,[])
            self.assertEqual(sum(v.get('vgo_crystal_stock').values()),sum(stock.values()))
    def test_first_invoice_never_compares_uninitialised_numeric_fields_to_zero(self):
        class StrictMissingNumbers(RemoteVM):
            def get(self,key,index=None):
                if key in ['vgo_crystal_sale_units','vgo_crystal_sale_due','vgo_crystal_sale_id','vgo_crystal_sale_completed','vgo_crystal_sold'] and key not in self.state:
                    return MISSING_CLOCK
                return super().get(key,index)
        v=StrictMissingNumbers();v.vars['buyer']=BUYER
        self.assertFalse(v.expr('@'+S+'.$vgo_crystal_sale_units le 0'))
        self.assertTrue(v.run('vardath.go.crystal.remote'));self.assertEqual(v.receipts,[400000])
        self.assertEqual(v.get('vgo_crystal_sale_id'),1);self.assertEqual(v.get('vgo_crystal_sale_completed'),1)
    def test_old_preparation_returns_same_crew_before_switching_to_broker(self):
        v=RemoteVM();v.start();actor=v.crew
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'prepare')
        self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertIs(v.crew,actor);self.assertIs(v.crew.room,v.shiproom)
        self.assertFalse(v.crew.isbusy);self.assertEqual(v.crew.controlpost,'engineer')
        self.assertEqual(v.get('vgo_crystal_sale_mode'),'off-screen broker')
        self.assertEqual([e for e in v.events if e[0]=='walk'],[])
    def test_existing_deployed_visit_finishes_return_before_success(self):
        v=RetailVM();self.assertTrue(v.reach_counter());v.ship.attention=0;v.player_sector=Obj('remote',exists=True)
        self.assertTrue(v.run('vardath.go.sellcrystals'))
        self.assertIs(v.crew.room,v.shiproom);self.assertEqual(v.get('vgo_crystal_sale_mode'),'counter')
        self.assertFalse(v.get('vgo_crystal_shop_deployed'))

class NativeCounterPosition(unittest.TestCase):
    def test_third_native_floor_candidate_is_used_and_actual_arrival_still_required(self):
        v=RetailVM();v.counter_points=False;v.floor_results=[False,False,True]
        self.assertTrue(v.run('vardath.go.crystal.shop'))
        self.assertEqual(v.floor_checks[:3],[(0,0,2),(0,0,3),(1.5,0,3)])
        self.assertTrue(any(e[0]=='walk' and e[2] is v.shoproom for e in v.events))
        self.assertEqual(v.receipts,[400000]);self.assertIs(v.crew.room,v.shiproom)
    def test_rejected_floor_positions_cannot_deploy_or_pay(self):
        v=RetailVM();v.counter_points=False;v.interaction_point=False;v.start()
        self.assertEqual(len(v.floor_checks),5);self.assertEqual(v.pending,{})
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'prepare')
        self.assertEqual(v.reward_requests,[]);self.assertFalse(v.get('vgo_crystal_shop_deployed'))
    def test_even_accepted_position_cannot_pay_without_actual_counter_arrival(self):
        v=RetailVM();v.counter_points=False;v.native_arrives=False;v.start()
        self.assertEqual(v.get('vgo_crystal_shop_phase'),'walking')
        self.assertFalse(v.run('vardath.go.crystal.settle'));self.assertEqual(v.goods_transfers,[])
    def test_no_npc_is_passed_to_object_only_interaction_point_api(self):
        self.assertIsNone(SHOP.find('.//find_actor_interaction_point'))
        floor=SHOP.find(".//library[@name='CustomerPositionV38']/actions")
        self.assertTrue(all(n.get('checkstate')=='false' for n in floor.iter('check_walk_path')))

class NativePassengers(PassengerVM):
    def __init__(self,job=2,count=2):
        super().__init__(job,count)
        self.ship.attention=0;self.visible=False;self.player_sector=Obj('elsewhere',exists=True)
        self.station.isoperational=True;self.actualdock=self.station
        self.order=Obj('worker',id='VGO_tour' if job==5 else 'VGO_taxi',exists=True)
        self.ship.order=self.order;self.ship.defaultorder=self.order
        self.station.owner=BUYER.owner
        self.seat.hastag=Obj('seat tags',service=False,marine=False)
        self.state.update(vgo_order=self.order,vgo_taxi_phase='boarding',vgo_taxi_manifest_ready=True,vgo_taxi_boarded=False)
        for e in self.state['vgo_passengers']:e['boarded']=False
        self.transit=set();self.registry=Seq([self.ship]);self.available_exits=False
        self.observed_ship=NULL;self.observed_station=NULL
    def expr(self,text):
        self.vars.update(native_dock=self.actualdock,native_transit=self.vars.get('entry',{}).get('template') in self.transit,
                         native_registry=self.registry,native_occupied=self.occupied,
                         observed_ship=self.observed_ship,observed_station=self.observed_station)
        text=text.replace('player.ship','$observed_ship').replace('player.station','$observed_station')
        text=text.replace('@$ship.dock.container','$native_dock')
        text=text.replace('Init.$Ships','$native_registry')
        text=text.replace('$ship == player.occupiedship','$native_occupied')
        text=text.replace('@$ship.people.{$entry.$template}.isintransit','$native_transit')
        text=text.replace('$actor.hascontext.{$ship}','$mock_actor_ship')
        text=text.replace('$actor.hascontext.{$station}','$mock_actor_station')
        text=text.replace('@$ship.defaultorder','$ship.defaultorder')
        self.vars['legacy_roster']=self.get('vgo_passenger') in self.roster
        text=text.replace('@$ship.people.{player.entity.$vgo_objects.{$ship}.$vgo_passenger}.exists','$legacy_roster')
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
            elif n.tag=='set_value' and n.get('name')=='$pointcache':self.assign(n.get('name'),{})
            elif n.tag=='add_to_group':pass # Native event group, not the passenger roster.
            else:super().execute([n])
    def board(self):
        self.execute(STATE.find(".//cue[@name='PassengerTransfersV2']/actions"))
        return self.state.get('vgo_taxi_boarded',False)

class NativePassengerRecovery(unittest.TestCase):
    def test_real_party_boards_without_loaded_rooms_then_leaves_at_booked_station(self):
        for job,count in [(2,2),(5,10)]:
            with self.subTest(job=job):
                v=NativePassengers(job,count);original=list(v.actors)
                self.assertTrue(v.board());self.assertEqual(v.roster,set(range(1,count+1)))
                self.assertTrue(all(a.exists and a.roleobject is v.ship and not a.room.exists for a in original))
                self.assertEqual(v.placements,[]);self.assertEqual(v.reward_requests,[])
                v.state['vgo_taxi_phase']='disembarking';self.assertTrue(v.complete())
                self.assertEqual(v.roster,set());self.assertEqual(v.actors,original)
                self.assertTrue(all(a.roleobject is v.station for a in original))
                self.assertTrue(v.run('vardath.go.passengers.pay'))
                expected=count*(800000 if job==2 else 50000000)
                self.assertEqual(v.receipts,[expected]);self.assertEqual(v.state['vgo_taxi_paid_id'],7)
    def test_in_transit_or_rejected_native_role_cannot_board(self):
        for cause in ['transit','role']:
            v=NativePassengers();v.available_exits=False
            v.place_succeeds=False
            if cause=='transit':v.transit=set(v.roster)
            else:v.role_transfer_accepts=False
            self.assertFalse(v.board());self.assertEqual(v.reward_requests,[])
            self.assertTrue(all(not e['boarded'] for e in v.state['vgo_passengers']))
    def test_visible_transfer_never_uses_offscreen_acknowledgement(self):
        v=NativePassengers();v.visible=True;v.player_sector=SECTOR;v.observed_station=v.station
        for a in v.actors:a.room=v.stationroom
        self.assertFalse(v.board());self.assertEqual(v.disconnected,[])
        self.assertFalse(any(e.get('native_abstract') for e in v.state['vgo_passengers']))
    def test_wrong_actual_dock_player_order_or_ownership_blocks_boarding(self):
        for cause in ['dock','order','owner','occupied']:
            v=NativePassengers()
            if cause=='dock':v.actualdock=NULL
            elif cause=='order':v.ship.order=Obj('manual',id='MoveWait',exists=True)
            elif cause=='owner':v.ship.isplayerowned=False;v.owned=False
            else:v.occupied=True
            self.assertFalse(v.board());self.assertEqual(v.reward_requests,[])
    def test_failed_template_release_or_station_role_handoff_cannot_complete_or_pay(self):
        for cause in ['release','role']:
            v=NativePassengers();self.assertTrue(v.board());v.state['vgo_taxi_phase']='disembarking'
            if cause=='release':v.release_succeeds=False
            else:v.role_transfer_accepts=False
            self.assertFalse(v.complete());self.assertFalse(v.run('vardath.go.passengers.pay'))
            self.assertEqual(v.removed,[]);self.assertEqual(v.reward_requests,[])
    def test_abstract_exit_still_requires_booked_dock_and_finished_tour(self):
        for cause in ['destination','dock','sites','sectors']:
            v=NativePassengers(job=5);self.assertTrue(v.board());v.state['vgo_taxi_phase']='disembarking'
            if cause=='destination':v.state['vgo_taxi_booked_destination']=Obj('booked elsewhere',exists=True)
            elif cause=='dock':v.actualdock=NULL
            elif cause=='sites':v.state['vgo_tour_trip']=Seq(range(9))
            else:v.state['vgo_tour_sectors']=Seq(range(2))
            self.assertFalse(v.complete());self.assertEqual(v.roster,{1,2});self.assertEqual(v.removed,[])
    def test_saved_party_does_not_create_replacement_actors_or_pay_before_five_seconds(self):
        v=NativePassengers();self.assertTrue(v.board());original=list(v.actors)
        v.state=copy.deepcopy(v.state);v.state['vgo_taxi_phase']='disembarking';v.transfer()
        self.assertEqual(v.removed,[]);v.age+=4;v.transfer();self.assertEqual(v.removed,[])
        v.age+=1;v.transfer();self.assertTrue(v.state['vgo_taxi_delivered'])
        self.assertEqual(v.actors,original);self.assertEqual(v.placements,[])
    def test_existing_roster_and_actor_reappear_when_player_returns(self):
        v=NativePassengers();self.assertTrue(v.board());v.visible=True;v.player_sector=SECTOR
        v.available_exits=True;v.vars['native_registry']=v.registry
        v.execute(STATE.find(".//cue[@name='PassengerBodiesV38']/actions"))
        self.assertEqual(len(v.placements),2);self.assertEqual(v.roster,{1,2})
        self.assertTrue(all(a.room is v.shiproom for a in v.actors))
        self.assertTrue(all(not e['native_abstract'] for e in v.state['vgo_passengers']))
    def test_released_bodyless_passengers_reconnect_at_booked_station_after_player_returns(self):
        v=NativePassengers();self.assertTrue(v.board());v.state['vgo_taxi_phase']='disembarking'
        v.role_transfer_accepts=False;v.transfer();self.assertEqual(v.roster,set())
        self.assertFalse(v.state.get('vgo_taxi_delivered',False))
        v.visible=True;v.player_sector=SECTOR;v.observed_station=v.station;v.available_exits=True;v.role_transfer_accepts=True
        v.transfer();self.assertTrue(all(a.room is v.stationroom for a in v.actors))
        self.assertEqual(v.reward_requests,[]);v.age+=5;v.transfer()
        self.assertTrue(v.state['vgo_taxi_delivered']);self.assertEqual(len(v.placements),2)

class RoomPointsVM(NativePassengers):
    """Run the actual room-point library against native slot/room query results."""
    def __init__(self):
        super().__init__();self.slots={};self.rooms={};self.waypoints={};self.queries=[]
        self.vars.update(pointcache={},pointcontainer=self.ship)
    def expr(self,text):
        cache=self.vars.get('pointcache');container=self.vars.get('pointcontainer')
        if text=='$pointcache?':return cache is not None
        text=text.replace('$pointcache?','true' if cache is not None else 'false')
        text=text.replace('@$pointcache','$pointcache')
        if '$pointcache.{$pointcontainer}' in text:
            self.vars['cached_points']=cache.get(container,Seq())
            text=text.replace('$pointcache.{$pointcontainer}?','true' if container in cache else 'false')
            text=text.replace('$pointcache.{$pointcontainer}','$cached_points')
        text=text.replace('@$roompoint','$roompoint')
        return super().expr(text)
    def assign(self,name,value,remove=False):
        if name=='$pointcache.{$pointcontainer}':self.vars['pointcache'][self.vars['pointcontainer']]=value
        elif name=='$pointlist.{$pointindex}':self.vars['pointlist'].pop(self.vars['pointindex']-1)
        else:super().assign(name,value,remove)
    def execute(self,nodes):
        previous=False
        for n in nodes:
            if n.tag=='do_if':
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag in ['find_room','find_npc_slot','find_npc_waypoint']:
                obj=self.expr(n.get('object'));self.queries.append((n.tag,obj,n.get('tags')))
                if n.tag=='find_room':found=self.rooms.get(obj,[])
                elif n.tag=='find_npc_waypoint':found=self.waypoints.get(obj,[])
                else:
                    found=self.slots.get(obj,[])
                    if n.get('tags'):found=[p for p in found if p.hastag.npc_generic]
                    if n.get('excludefilled')=='true':found=[p for p in found if not p.filled]
                old=self.vars.get(n.get('name')[1:],[]) if n.get('append')=='true' else []
                self.assign(n.get('name'),Seq([*old,*found]))
            else:super().execute([n])
    def points(self,container=None):
        self.vars['pointcontainer']=container or self.ship
        self.execute(STATE.find(".//library[@name='PassengerRoomPointsV32']/actions"))
        return self.vars['pointlist']
    def point(self,name,room=None,generic=False,service=False,marine=False,filled=False,ship=False):
        container=Obj('container',isclass=Obj('class',ship=ship))
        component=room or Obj('room',exists=True,container=container)
        return Obj(name,component=component,filled=filled,hastag=Obj('tags',npc_generic=generic,service=service,marine=marine))

class PassengerRoomSelection(unittest.TestCase):
    def test_generic_private_room_slots_are_discovered(self):
        v=RoomPointsVM();v.rooms[v.ship]=[v.shiproom];p=v.point('private seat',generic=True)
        v.slots[v.shiproom]=[p];self.assertEqual(v.points(),[p])
    def test_free_non_generic_point_recovers_when_generic_query_is_empty(self):
        v=RoomPointsVM();v.rooms[v.ship]=[v.shiproom];p=v.point('usable idle point')
        v.slots[v.shiproom]=[p];self.assertEqual(v.points(),[p])
    def test_crew_posts_and_occupied_slots_are_never_used_as_fallback(self):
        v=RoomPointsVM();v.rooms[v.ship]=[v.shiproom]
        v.slots[v.shiproom]=[v.point('service',service=True),v.point('marine',marine=True),v.point('filled',filled=True)]
        self.assertEqual(v.points(),[])
    def test_station_query_rejects_points_in_a_docked_ship(self):
        v=RoomPointsVM();v.rooms[v.station]=[v.stationroom]
        docked=v.point('docked ship point',ship=True);real=v.point('real station point')
        v.slots[v.stationroom]=[docked,real];self.assertEqual(v.points(v.station),[real])
    def test_real_transport_waypoint_is_final_fallback(self):
        v=RoomPointsVM();p=v.point('transport');v.rooms[v.ship]=[v.shiproom]
        v.waypoints[v.shiproom]=[p];self.assertEqual(v.points(),[p])
    def test_per_tick_cache_reuses_queries_but_returns_a_distinct_list(self):
        v=RoomPointsVM();p=v.point('generic',generic=True);v.slots[v.ship]=[p]
        first=v.points();count=len(v.queries);second=v.points()
        self.assertEqual(second,[p]);self.assertIsNot(first,second);self.assertEqual(len(v.queries),count)

class ServiceUpgrade(unittest.TestCase):
    def test_new_sales_setting_is_saved_after_state_tables_exist_and_refresh_preserves_false(self):
        actions=list(xml('vardath.go.worker').find('attention/actions'))
        setting=next(i for i,n in enumerate(actions) if n.get('name')==S+'.$vgo_simulatesales')
        state=next(i for i,n in enumerate(actions) if n.find("set_value[@name=\""+S+"\"]") is not None)
        self.assertLess(state,setting)
        refresh=xml('vardath.go.refreshdefault')
        value=refresh.find(".//set_value[@name='$settings.$simulatesales']").get('exact')
        self.assertIn('!= null',value);self.assertIn('defaultorder.$simulatesales',value)
        expression=value.replace('@this.ship.defaultorder.$simulatesales','false').replace('this.ship.defaultorder.$simulatesales','false')
        self.assertIs(RetailVM().expr(expression),False)
        self.assertIsNotNone(refresh.find(".//create_order/param[@name='simulatesales'][@value='$settings.$simulatesales']"))

if __name__=='__main__':unittest.main(verbosity=2)
