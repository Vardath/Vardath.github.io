#!/usr/bin/env python3
"""Execute the actual nullable-list expressions; no X4 execution is claimed."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
MOD=Path(__file__).resolve().parents[2]/'vardath_galactic_occupations'
S='player.entity.$vgo_objects.{this.ship}'
WORKER=ET.parse(MOD/'aiscripts/vardath.go.worker.xml').getroot()

class CacheVM:
    def __init__(self,state=None,variables=None):
        self.state=dict(state or {});self.variables={'job':3,'home':'home','range':99};self.variables.update(variables or {})
    def eval(self,expression):
        if expression.startswith('if '):
            condition,branches=expression[3:].split(' then ',1);yes,no=branches.split(' else ',1)
            return self.eval(yes if self.eval(condition) else no)
        text=expression
        pattern=r'@?'+re.escape(S)+r'\.\$vgo_(\w+)(\?|\.clone)?'
        def state(m):
            key,suffix=m[1],m[2]
            if suffix=='?':return 'present('+repr(key)+')'
            if suffix=='.clone':return 'clone(s('+repr(key)+'))'
            return 's('+repr(key)+')'
        text=re.sub(pattern,state,text)
        text=re.sub(r'@?\$(\w+)(\?)?',lambda m:('has('+repr(m[1])+')') if m[2] else ('v('+repr(m[1])+')'),text)
        text=re.sub(r'\bnull\b','None',text)
        def clone(value):
            if not isinstance(value,list):raise TypeError('Attempted clone/count on a null/non-list value')
            return list(value)
        return eval(text,{'__builtins__':{}},{'s':lambda n:self.state.get(n),'present':lambda n:n in self.state,'v':lambda n:self.variables.get(n),'has':lambda n:n in self.variables,'clone':clone})
    def apply_guard(self,node):
        if self.eval(node.get('value')):
            for action in node:
                self.variables[action.get('name').lstrip('$')]=self.eval(action.get('exact'))

class Debug7Contracts(unittest.TestCase):
    def test_missing_and_present_null_cached_lists_are_real_empty_lists(self):
        init=WORKER.find("attention/actions/set_value[@name='$sectors']").get('exact')
        for extra in [{},{'sectors':None}]:
            state={'navigation_version':2,'searchjob':3,'searchhome':'home','searchrange':99,**extra}
            with self.subTest(extra=extra):self.assertEqual(CacheVM(state).eval(init),[])
    def test_valid_cache_is_cloned_and_preserved(self):
        source=['a','b'];state={'navigation_version':2,'searchjob':3,'searchhome':'home','searchrange':99,'sectors':source}
        init=WORKER.find("attention/actions/set_value[@name='$sectors']").get('exact')
        result=CacheVM(state).eval(init);self.assertEqual(result,source);self.assertIsNot(result,source)
    def test_resuming_at_either_label_repairs_a_present_null_local(self):
        actions=list(WORKER.find('attention/actions'))
        for label in ['start','nextsector']:
            i=next(i for i,n in enumerate(actions) if n.tag=='label' and n.get('name')==label)
            for variables in [{},{'sectors':None},{'sectors':['kept']}]:
                with self.subTest(label=label,variables=variables):
                    vm=CacheVM(variables=variables);vm.apply_guard(actions[i+1]);self.assertIsInstance(vm.variables['sectors'],list)
                    if variables.get('sectors'):self.assertEqual(vm.variables['sectors'],['kept'])
    def test_null_scope_cannot_be_cloned_during_refill(self):
        refill=next(n for n in WORKER.iter('set_value') if n.get('name')=='$sectors' and '.$vgo_scope.clone else []' in n.get('exact',''))
        self.assertEqual(CacheVM({'scope':None}).eval(refill.get('exact')),[])
    def test_hacker_order_uses_native_queue_defaults_without_conflicting_flags(self):
        root=ET.parse(MOD/'md/VGO_Hacker.xml').getroot();order=root.find('.//create_order')
        self.assertFalse('default' in order.attrib and 'immediate' in order.attrib)
        self.assertEqual(order.get('default','false'),'false');self.assertEqual(order.get('immediate','false'),'false');self.assertEqual(order.get('override'),'false')
    def test_report_displays_credits_not_native_hundredths(self):
        state=ET.parse(MOD/'md/VGO_State.xml').getroot();report=state.find(".//cue[@name='ActivityReportsV24']//set_value[@name='$report']").get('exact')
        self.assertIn('received: %9 Cr',report)
        arg=report.split(', $started, $completed,',1)[1].split(']',1)[0].strip()
        for native,credits in [(500000000,5000000),(2400000,24000),(0,0)]:
            expression=arg.replace('$income',str(native)).replace('1Cr','100');expression=re.sub(r'\)f$',')',expression)
            self.assertEqual(eval(expression,{'__builtins__':{}}),credits)
    def test_passenger_points_query_private_rooms_and_transport_waypoints(self):
        root=ET.parse(MOD/'md/VGO_State.xml').getroot();lib=root.find(".//library[@name='PassengerRoomPointsV32']")
        self.assertIsNotNone(lib.find('.//find_room'))
        self.assertIsNotNone(lib.find(".//find_npc_slot[@object='$pointroom']"))
        self.assertIsNotNone(lib.find(".//find_npc_waypoint[@object='$pointroom'][@tags='tag.npctransport']"))
        for tag in ['create_cue_actor','remove_npc_template','add_inventory','reward_player','set_owner']:self.assertEqual(len(list(lib.iter(tag))),0)
        cue=root.find(".//cue[@name='PassengerTransfersV2']")
        departure=root.find(".//library[@name='PassengerDisembarkV35']")
        self.assertIsNotNone(cue.find(".//include_actions[@ref='PassengerDisembarkV35']"))
        self.assertGreaterEqual(len(cue.findall(".//include_actions[@ref='PassengerRoomPointsV32']"))+len(departure.findall(".//include_actions[@ref='PassengerRoomPointsV32']")),5)
        self.assertEqual(len(root.findall(".//set_value[@exact='true'][@name='player.entity.$vgo_objects.{$ship}.$vgo_passengers.{$i}.$boarded']")),4)
        native=root.find(".//library[@name='PassengerAbstractBoardV38']")
        self.assertIsNotNone(native.find('.//set_entity_role_object'))
        self.assertEqual(list(native.iter('reward_player')),[])

    def test_cargo_docking_recovery_is_single_attempt_and_has_no_manual_transfer(self):
        path=MOD.parents[1]/'x4-universal-cargo-teleport/vardath_universal_cargo_teleport/aiscripts/order.trade.perform.xml'
        root=ET.parse(path).getroot();block=root.find("add[@pos='after'][@sel=\"/aiscript/attention/actions//execute_trade[@tradepartner='this.ship'][@result='$traderesult']\"]/do_if")
        self.assertIsNotNone(block)
        self.assertIn('not $traderesult',block.get('value'))
        self.assertIn('$tradedeal.transferredamount == 0',block.get('value'))
        self.assertIn('not @$VardathTeleportDockRetry',block.get('value'))
        self.assertIsNotNone(block.find("set_value[@name='$VardathTeleportDockRetry'][@exact='true']"))
        self.assertEqual(block.find('resume').get('label'),'move_to_targetobject')
        for tag in ['add_cargo','remove_cargo','transfer_money','reward_player']:
            self.assertEqual(len(list(root.iter(tag))),0)

if __name__=='__main__':unittest.main(verbosity=2)
