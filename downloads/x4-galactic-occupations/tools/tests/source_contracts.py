#!/usr/bin/env python3
"""Guards for the reported scope/boarding/survey/payment bugs. These are source checks, not game tests."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[2]
MOD = BASE / 'vardath_galactic_occupations'
BUILDER = BASE.parent / 'x4-living-factions-builders/vardath_living_factions_builders'

def source(name):
    return (MOD/name).read_text().replace('player.entity.$vgo_objects.{this.ship}', 'this.ship').replace('player.entity.$vgo_objects.{$ship}', '$ship')
def xml(name): return ET.fromstring(source(name))

class SourceContracts(unittest.TestCase):
    def test_every_behaviour_uses_shared_galaxy_worker(self):
        wrappers = list((MOD/'aiscripts').glob('order.vardath.go.*.xml'))
        self.assertEqual(len(wrappers),12)
        for path in wrappers:
            r=ET.parse(path).getroot()
            self.assertEqual(r.find("./order/params/param[@name='range']").get('default'),'99')
            self.assertIsNotNone(r.find(".//run_script[@name=\"'vardath.go.worker'\"]"))
    def test_99_uses_native_unlimited_search(self):
        root=xml('aiscripts/vardath.go.scope.xml')
        unlimited=root.find(".//do_if[@value='this.ship.$vgo_range ge 99']/find_sector_in_range")
        self.assertIsNotNone(unlimited)
        self.assertNotIn('maxdistance',unlimited.attrib)
        limited=root.find('.//do_else/find_sector_in_range')
        self.assertEqual(limited.get('maxdistance'),'this.ship.$vgo_range')
    def test_local_work_cannot_prevent_sector_rotation(self):
        a=xml('aiscripts/vardath.go.worker.xml').find('./attention/actions')
        early=next(i for i,n in enumerate(a) if any(x.get('label')=='nextsector' for x in n.findall('.//resume')))
        search=next(i for i,n in enumerate(a) if n.tag=='run_script' and n.get('name')=="'vardath.go.find'")
        self.assertLess(early,search)
        self.assertIn('this.ship.$vgo_rotate',ET.tostring(a,encoding='unicode'))
    def test_tour_catalogue_queries_entire_scope(self):
        r=xml('aiscripts/vardath.go.tourcatalogue.xml')
        searches=[n for n in r.iter() if n.tag in ['find_object','find_ship','find_station']]
        self.assertGreaterEqual(len(searches),6)
        self.assertTrue(all(n.get('space')=='this.ship.$vgo_scope' for n in searches))
    def test_taxi_has_no_three_jump_destination_limit(self):
        s=source('aiscripts/vardath.go.task.taxi.xml')
        self.assertIn('this.ship.$vgo_scope.clone',s)
        self.assertNotIn('maxdistance="3"',s)
    def test_passengers_are_capped_and_capacity_is_never_forced(self):
        r=xml('md/VGO_State.xml').find(".//cue[@name='PassengerTransfersV2']")
        seats=r.find(".//set_value[@name='$seats']").get('exact')
        self.assertIn('10 - $ship.$vgo_passengers.count',seats)
        self.assertIn('$ship.people.free',seats)
        self.assertEqual(r.find('.//create_npc_template').get('force'),'false')
    def test_each_boarded_ack_has_physical_actor_context(self):
        root=xml('md/VGO_State.xml');parents={c:p for p in root.iter() for c in p}
        assignments=[x for x in root.iter('set_value') if x.get('name')=='$ship.$vgo_passengers.{$i}.$boarded' and x.get('exact')=='true']
        self.assertEqual(len(assignments),2)
        for node in assignments:
            guards=[]
            while node in parents:
                node=parents[node]
                if node.tag=='do_if':guards.append(node.get('value',''))
            self.assertTrue(any('hascontext.{$ship}' in v for v in guards))
    def test_whole_ship_boarded_requires_all_passengers(self):
        r=xml('md/VGO_State.xml').find(".//cue[@name='PassengerTransfersV2']")
        ack=r.find(".//do_if[@value='$allaboard']/set_value[@name='$ship.$vgo_taxi_boarded']")
        self.assertIsNotNone(ack)
        board=source('aiscripts/vardath.go.passengers.board.xml')
        self.assertIn('not $entry.$boarded',board)
        self.assertNotIn('wait exact="2s"/><return value="true"',board)
    def test_tours_need_ten_unique_stops_and_multiple_sectors(self):
        order=xml('aiscripts/order.vardath.go.tour.xml')
        self.assertEqual(order.find("./order/params/param[@name='stops']").get('default'),'10')
        self.assertEqual(order.find("./order/params/param[@name='ticketfee']").get('default'),'500000Cr')
        task=xml('aiscripts/vardath.go.task.tour.xml')
        gate=next(n for n in task.iter('do_if') if 'trip.count ge' in n.get('value',''))
        self.assertIn('vgo_tour_sectors.count ge',gate.get('value'))
        self.assertIsNotNone(gate.find(".//run_script[@name=\"'vardath.go.passengers.deliver'\"]"))
        self.assertIn('vgo_tour_trip.indexof',ET.tostring(task,encoding='unicode'))
    def test_passenger_fares_have_persistent_duplicate_guard(self):
        s=source('aiscripts/vardath.go.reward.xml')
        self.assertIn('vgo_taxi_completed_id == @this.ship.$vgo_taxi_paid_id',s)
        self.assertIn('name="this.ship.$vgo_taxi_paid_id"',s)
    def test_scanner_does_not_reject_normal_ai_scanner_levels(self):
        s=source('aiscripts/vardath.go.task.scanner.xml')
        self.assertNotIn('this.ship.maxscanlevel lt player.maxscanlevel',s)
        self.assertNotIn('$module.secrecylevel gt this.ship.maxscanlevel',s)
    def test_survey_reveals_only_after_real_surface_and_los_work(self):
        r=xml('aiscripts/vardath.go.task.scanner.xml')
        self.assertEqual({n.get('object') for n in r.iter('set_object_scanned')},{'$module'})
        self.assertIsNotNone(r.find('.//find_object_surface'))
        self.assertIsNotNone(r.find('.//check_line_of_sight'))
        self.assertIsNotNone(r.find(".//do_all[@exact='10']/check_line_of_sight"))
        self.assertIn('$module.scannedlevel gt $levelbefore',ET.tostring(r,encoding='unicode'))
    def test_large_stations_are_not_permanently_capped_at_80_modules(self):
        r=xml('aiscripts/vardath.go.scanmodules.xml')
        self.assertTrue(all('sortlimit' not in n.attrib for n in r.iter('find_object_component')))
    def test_native_receipt_adapter_has_no_layout_or_helper_overrides(self):
        self.assertEqual((MOD/'ui/vardath_income_ledger.lua').read_bytes(),(BUILDER/'ui/vardath_income_ledger.lua').read_bytes())
        for folder in [MOD,BUILDER]:
            self.assertIsNotNone(ET.parse(folder/'ui.xml').find(".//file[@name='ui/vardath_income_ledger.lua']"))
        lua=(MOD/'ui/vardath_income_ledger.lua').read_text()
        for forbidden in ['frame.content','frame:addTable','createTransactionLog =','transactionLogSearchHelper =','addPanel','mergeNative']:
            self.assertNotIn(forbidden,lua)
        self.assertIn('pcall(Helper.registerCallback, "createTransactionLog_on_before_adding_entry"',lua)
        self.assertIn('return ok and result or entry',lua)
        self.assertNotIn('require("extensions.',lua)
    def test_reported_runtime_constraints(self):
        for path in MOD.rglob('*.xml'):
            r=ET.parse(path).getroot()
            for node in r.iter():
                if node.tag in ['event_object_dropped_objects','event_object_changed_room']:
                    self.assertTrue(node.get('object') or node.get('group'))
            for attention in r.findall('attention'):
                if attention.find('.//shoot_at') is not None:self.assertEqual(attention.get('min'),'visible')
        self.assertIn('player.entity.$vgo_objects',(MOD/'aiscripts/vardath.go.worker.xml').read_text())

    def test_logbook_reads_only_actual_paid_journal_and_shares_a_cursor(self):
        for path in [MOD/'md/VGO_State.xml',BUILDER/'md/vardath_builder_contracts.xml']:
            root=ET.parse(path).getroot()
            cue=root.find(".//cue[@name='PaymentReceiptsV22']")
            self.assertIsNotNone(cue)
            self.assertEqual(cue.get('checkinterval'),'5s')
            self.assertIsNotNone(cue.find('.//write_to_logbook'))
            self.assertIn('vardath_income_logged_seq',ET.tostring(cue,encoding='unicode'))
            self.assertEqual(len(list(cue.iter('reward_player'))),0)
            self.assertEqual(len(list(cue.iter('transfer_money'))),0)
    def test_default_wrappers_retry_and_always_have_valid_locations(self):
        for path in (MOD/'aiscripts').glob('order.vardath.go.*.xml'):
            root=ET.parse(path).getroot()
            self.assertTrue(root.find('order/location').get('object').endswith('else this.ship)'))
            self.assertIsNotNone(root.find(".//resume[@label='work']"))
            self.assertIsNotNone(root.find('.//patch//edit_order_param'))
    def test_crystal_prerequisite_wait_does_not_create_hold_or_income(self):
        root=xml('aiscripts/vardath.go.worker.xml')
        branch=root.find(".//do_if[@value='$compatible_turrets == 0']")
        self.assertIsNotNone(branch.find("resume[@label='start']"))
        self.assertIsNotNone(branch.find('wait'))
        self.assertIsNotNone(branch.find('.//write_to_logbook'))
        for tag in ['create_order','reward_player','transfer_money']:
            self.assertEqual(len(list(branch.iter(tag))),0)
    def test_yaki_plan_uses_supported_numeric_iteration(self):
        path=BASE.parent/'x4-yaki-terran-habs/vardath_yaki_terran_habs/md/vardath_yaki_faction_habitats.xml'
        root=ET.parse(path).getroot()
        self.assertIsNone(root.find(".//do_for_each[@in='$CurrentPlan']"))
        self.assertIsNotNone(root.find(".//do_all[@exact='$CurrentPlan.count']/set_value[@exact='$CurrentPlan.{$PlanIndex}']"))
    def test_builder_rates_and_payment_guards_are_preserved(self):
        r=ET.parse(BUILDER/'md/vardath_builder_contracts.xml').getroot()
        self.assertEqual(len(list(r.iter('reward_player'))),2)
        s=ET.tostring(r,encoding='unicode')
        for required in ['100000Cr','25000Cr','200000Cr',"$Contract.$Owed gt 0Cr",'checkinterval="1min"']:
            self.assertIn(required,s)
        self.assertEqual(len(r.findall(".//include_actions[@ref='RecordIncome']")),2)
    def test_income_records_use_actual_balance_change(self):
        s=source('aiscripts/vardath.go.reward.xml')
        self.assertIn('player.money - $moneybefore',s)
        self.assertIn("'vardath.go.recordpayment'",s)
        self.assertIn('player.money - $MoneyBefore',(BUILDER/'md/vardath_builder_contracts.xml').read_text())

if __name__=='__main__': unittest.main(verbosity=2)
