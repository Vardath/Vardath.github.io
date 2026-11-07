#!/usr/bin/env python3
"""Execute native-tool loan/return XML with mocked inventories, plus safety source contracts.
No test here can establish X4 NPC pathing, engine panel effects, or live payments.
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as E

MOD=Path(__file__).resolve().parents[2]/'vardath_galactic_occupations'
ROOT=E.parse(MOD/'md/VGO_Hacker.xml').getroot()
STATE='player.entity.$vgo_objects.{$ship}.$vgo_hack_'
class Break(Exception):pass
class ToolVM:
    def __init__(self,player=None,actor=None,costs=None,remove_limit=None,credit_limit=None):
        self.stock={'player':dict(player or {}),'actor':dict(actor or {})}
        self.state={'costs':list(costs or []),'loans':[]}
        self.vars={};self.age=100;self.remove_limit=remove_limit or {};self.credit_limit=credit_limit or {};self.logs=[];self.busycall=False
    def expr(self,text):
        if text=='if '+STATE+'loans? then '+STATE+'loans else []':return self.state.get('loans',[])
        s=text.replace('@Init.$CallShip.exists','callbusy').replace('$actor.exists','True').replace('$actor.isbusy','False').replace('player.age','age').replace('10min','600').replace('2s','2')
        s=re.sub(re.escape(STATE)+r'(\w+)',lambda m:'st('+repr(m[1])+')',s)
        s=re.sub(r'player\.entity\.inventory\.\{(\$\w+(?:\.\{\d+\})?)\}\.count',lambda m:'inv("player",'+m[1]+')',s)
        s=re.sub(r'\$actor\.inventory\.\{(\$\w+(?:\.\{\d+\})?)\}\.count',lambda m:'inv("actor",'+m[1]+')',s)
        s=re.sub(r'(\$\w+)\.\{(\d+)\}',lambda m:'idx('+m[1]+','+m[2]+')',s)
        s=re.sub(r'(st\([^)]*\))\.count',r'len(\1)',s)
        s=re.sub(r'\$(\w+)',lambda m:'v('+repr(m[1])+')',s)
        for token,op in [('le','<='),('ge','>='),('lt','<'),('gt','>')]:s=re.sub(r'\b'+token+r'\b',op,s)
        while re.search(r'\[([^\[\]]*)\]\.(min|max)',s):s=re.sub(r'\[([^\[\]]*)\]\.(min|max)',lambda m:m[2]+'('+m[1]+')',s)
        s=re.sub(r'\btrue\b','True',s);s=re.sub(r'\bfalse\b','False',s)
        return eval(s,{'__builtins__':{}},{'v':lambda n:self.vars[n],'st':lambda n:self.state.get(n,[]),'inv':lambda o,w:self.stock[o].get(w,0),'idx':lambda x,i:x[i-1],'min':min,'max':max,'len':len,'age':self.age,'callbusy':self.busycall})
    def name(self,name):return ('state',name[len(STATE):]) if name.startswith(STATE) else ('vars',name.lstrip('$'))
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
                for value in list(self.expr(n.get('in'))):
                    self.vars[n.get('name').lstrip('$')]=value
                    try:self.execute(n)
                    except Break:break
            elif tag=='set_value':
                obj,key=self.name(n.get('name'));getattr(self,obj)[key]=self.expr(n.get('exact'))
            elif tag=='append_to_list':
                obj,key=self.name(n.get('name'));getattr(self,obj)[key].append(self.expr(n.get('exact')))
            elif tag=='include_actions':self.library(n.get('ref'))
            elif tag=='break':raise Break()
            elif tag in ('add_inventory','remove_inventory'):
                owner={'$actor':'actor','player.entity':'player'}[n.get('entity')];ware=self.expr(n.get('ware'));amount=self.expr(n.get('exact'));assert amount>=0
                if tag=='remove_inventory':amount=min(amount,self.stock[owner].get(ware,0),self.remove_limit.get(owner,float('inf')));self.stock[owner][ware]=self.stock[owner].get(ware,0)-amount
                else:amount=min(amount,self.credit_limit.get(owner,float('inf')));self.stock[owner][ware]=self.stock[owner].get(ware,0)+amount
            elif tag=='write_to_logbook':self.logs.append(n.get('title'))
            else:raise AssertionError('Unmodelled XML command '+tag)
    def library(self,name):self.execute(ROOT.find(".//library[@name='"+name+"']/actions"))
    def total(self,ware):return sum(x.get(ware,0) for x in self.stock.values())

class ToolAccounting(unittest.TestCase):
    def test_real_tools_are_reserved_and_returned_without_touching_existing_crew_items(self):
        v=ToolVM({'slicer':3},{'slicer':7,'parts':11},[('slicer',2)]);v.library('LoanTools');self.assertTrue(v.vars['ready']);self.assertEqual(v.stock['player']['slicer'],1);self.assertEqual(v.state['loans'],[['slicer',2]]);v.library('ReturnTools');self.assertEqual(v.stock,{'player':{'slicer':3},'actor':{'slicer':7,'parts':11}})
    def test_missing_tools_do_not_partially_remove_a_multi_item_request(self):
        v=ToolVM({'slicer':1},costs=[('slicer',1),('decryptor',1)]);v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.stock['player'],{'slicer':1});self.assertEqual(v.stock['actor'],{});self.assertEqual(v.state['nexttool'],700)
    def test_rejected_withdrawal_never_adds_tools_to_actor(self):
        v=ToolVM({'slicer':2},costs=[('slicer',1)],remove_limit={'player':0});v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.total('slicer'),2);self.assertEqual(v.stock['actor'].get('slicer',0),0)
    def test_rejected_actor_credit_rolls_back_player_withdrawal(self):
        v=ToolVM({'slicer':2},costs=[('slicer',1)],credit_limit={'actor':0});v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.stock['player']['slicer'],2)
    def test_partial_credit_returns_only_actual_loan(self):
        v=ToolVM({'slicer':4},costs=[('slicer',3)],credit_limit={'actor':1});v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.stock['player']['slicer'],4);self.assertEqual(v.state['loans'],[])
    def test_failed_player_return_stays_reserved_and_blocks_a_second_loan(self):
        v=ToolVM({'slicer':5},costs=[('slicer',2)]);v.library('LoanTools');v.credit_limit={'player':0};v.library('ReturnTools');self.assertEqual(v.state['loans'],[['slicer',2]]);v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.state['loans'],[['slicer',2]]);self.assertEqual(v.total('slicer'),5);v.credit_limit={};v.library('LoanTools');self.assertTrue(v.vars['ready']);self.assertEqual(v.total('slicer'),5)
    def test_partial_return_then_retry_is_idempotent(self):
        v=ToolVM({'slicer':4},costs=[('slicer',4)]);v.library('LoanTools');v.credit_limit={'player':1};v.library('ReturnTools');self.assertEqual(v.state['loans'],[['slicer',3]]);self.assertEqual(v.total('slicer'),4);v.credit_limit={};v.library('ReturnTools');v.library('ReturnTools');self.assertEqual(v.stock['player']['slicer'],4);self.assertEqual(v.state['loans'],[])
    def test_loan_waits_for_pending_native_consumption_without_borrowing(self):
        v=ToolVM({'slicer':4},costs=[('slicer',1)]);v.busycall=True;v.library('LoanTools');self.assertFalse(v.vars['ready']);self.assertEqual(v.stock['actor'],{});self.assertEqual(v.state['nexttool'],102)

class HackerSourceContracts(unittest.TestCase):
    def test_thirteen_default_behaviours_and_distinct_finite_order(self):
        wrappers=[E.parse(p).getroot() for p in (MOD/'aiscripts').glob('order.vardath.go.*.xml')];self.assertEqual(sum(r.find('order').get('infinite')=='true' for r in wrappers),13)
        once=E.parse(MOD/'aiscripts/order.vardath.go.hackonce.xml');self.assertEqual(once.find('order').get('infinite'),'false');self.assertEqual(once.find("order/params/param[@name='panelid']").get('type'),'internal')
    def test_no_crew_clones_ownership_changes_or_station_room_teleports(self):
        for tag in ['create_cue_actor','create_npc_template','remove_npc_template','destroy_object','set_object_owner','add_actor_to_room','set_object_hacked']:self.assertEqual(len(list(ROOT.iter(tag))),0,tag)
        self.assertIsNotNone(ROOT.find('.//find_object_component[@class="class.npc"]'))
    def test_native_effect_and_ack_are_required_before_completion(self):
        verified=next(n for n in ROOT.iter('do_if') if 'hack_call_sent and $station.iscontrolpanelhacked' in n.get('value',''));self.assertIn('hack_apiissued',verified.get('value'))
        task=(MOD/'aiscripts/vardath.go.task.hacker.xml').read_text();self.assertIn('hack_departed and @',task);self.assertIn('hack_actor.room.hascontext.{$ship}',task)
    def test_walk_requires_real_room_proximity_and_dwell(self):
        near=ROOT.find(".//set_value[@name='$near']").get('exact');self.assertIn('$actor.room ==',near);self.assertIn('le 4m',near);self.assertIn('not $actor.iswalking',near)
        self.assertIn('hack_step + 10s',E.tostring(ROOT,encoding='unicode'));self.assertGreaterEqual(len(ROOT.findall(".//signal_objects[@param=\"'npc_move_to'\"]")),3)
    def test_panels_are_discovered_from_actual_native_rooms(self):
        self.assertIsNotNone(ROOT.find('.//find_room[@hascontrolpanel]'));self.assertIsNotNone(ROOT.find('.//find_hack_slot'));self.assertIn('hack_type.requireditems.table',E.tostring(ROOT,encoding='unicode'))
    def test_queued_hack_does_not_replace_orders_or_defaults(self):
        order=ROOT.find('.//create_order');self.assertEqual(order.get('default'),'false');self.assertEqual(order.get('immediate'),'false');self.assertEqual(order.get('override'),'false');self.assertNotIn('append',order.attrib)
    def test_bridge_has_cancelled_request_cleanup_and_tokens(self):
        self.assertGreaterEqual(len(ROOT.findall(".//remove_value[@name='player.entity.$vgo_hack_call']")),2);self.assertIn('hack_token == event.param3.{2}',E.tostring(ROOT,encoding='unicode'))
    def test_hacking_has_no_unsponsored_pay_or_reputation(self):
        for tag in ['reward_player','transfer_money','add_faction_relation']:self.assertEqual(len(list(ROOT.iter(tag))),0)
    def test_patrol_fees_follow_verified_arrival(self):
        patrol=E.parse(MOD/'aiscripts/vardath.go.task.patrol.xml');self.assertEqual(patrol.find(".//param[@name='fee']").get('value'),'if $target.isplayerowned then 0Cr else 8000Cr')
        convoy=(MOD/'aiscripts/vardath.go.task.convoy.xml').read_text();self.assertIn('vgo_convoy_near',convoy);self.assertIn('dock.container == $destination',convoy)
    def test_payments_log_measured_balances_and_do_not_backpay_historical_completions(self):
        reward=(MOD/'aiscripts/vardath.go.reward.xml').read_text();self.assertIn('GO payment:',reward);self.assertIn('balance_before=',reward);self.assertIn('player.money - $moneybefore',reward);self.assertEqual(len(list(ROOT.iter('reward_player'))),0)

if __name__=='__main__':unittest.main(verbosity=2)
