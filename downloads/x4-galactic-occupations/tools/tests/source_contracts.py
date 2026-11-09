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
        wrappers = [p for p in (MOD/'aiscripts').glob('order.vardath.go.*.xml') if ET.parse(p).find('order').get('infinite') == 'true']
        self.assertEqual(len(wrappers),13)
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
    def test_boarded_ack_has_physical_context_or_verified_native_person_record(self):
        root=xml('md/VGO_State.xml');parents={c:p for p in root.iter() for c in p}
        assignments=[x for x in root.iter('set_value') if x.get('name')=='$ship.$vgo_passengers.{$i}.$boarded' and x.get('exact')=='true']
        self.assertEqual(len(assignments),6)
        for node in assignments:
            guards=[]
            while node in parents:
                node=parents[node]
                if node.tag=='do_if':guards.append(node.get('value',''))
            self.assertTrue(any('hascontext.{$ship}' in v for v in guards) or any('roleobject == $ship' in v and 'people.{$entry.$template}.exists' in v and 'isintransit' in v for v in guards))
    def test_whole_ship_boarded_requires_all_passengers(self):
        r=xml('md/VGO_State.xml').find(".//cue[@name='PassengerTransfersV2']")
        ack=r.find(".//do_if[@value='$allaboard']/set_value[@name='$ship.$vgo_taxi_boarded']")
        self.assertIsNotNone(ack)
        board=source('aiscripts/vardath.go.passengers.board.xml')
        self.assertIn('not $entry.$boarded',board)
        self.assertNotIn('wait exact="2s"/><return value="true"',board)
    def test_new_tours_default_to_ten_unique_stops_and_multiple_sectors(self):
        order=xml('aiscripts/order.vardath.go.tour.xml')
        self.assertEqual(order.find("./order/params/param[@name='stops']").get('default'),'10')
        self.assertEqual(order.find("./order/params/param[@name='ticketfee']").get('default'),'500000Cr')
        task=xml('aiscripts/vardath.go.task.tour.xml')
        gate=next(n for n in task.iter('do_if') if 'trip.count ge' in n.get('value',''))
        self.assertIn('vgo_tour_sectors.count ge',gate.get('value'))
        self.assertIsNotNone(gate.find(".//run_script[@name=\"'vardath.go.passengers.deliver'\"]"))
        self.assertIn('vgo_tour_trip.indexof',ET.tostring(task,encoding='unicode'))
    def test_passenger_fares_have_persistent_duplicate_guard(self):
        route=xml('aiscripts/vardath.go.reward.xml')
        self.assertIsNotNone(route.find(".//run_script[@name=\"'vardath.go.passengers.pay'\"]"))
        s=source('aiscripts/vardath.go.passengers.pay.xml')
        self.assertIn('vgo_taxi_completed_id == @this.ship.$vgo_taxi_paid_id',s)
        self.assertIn('name="this.ship.$vgo_taxi_paid_id"',s)
    def test_scanner_does_not_reject_normal_ai_scanner_levels(self):
        s=source('aiscripts/vardath.go.task.scanner.xml')
        self.assertNotIn('this.ship.maxscanlevel lt player.maxscanlevel',s)
        self.assertNotIn('$module.secrecylevel gt this.ship.maxscanlevel',s)
    def test_survey_reveals_only_after_real_surface_and_los_work(self):
        r=xml('aiscripts/vardath.go.task.scanner.xml')
        publish=xml('aiscripts/vardath.go.survey.publish.xml')
        self.assertEqual({n.get('object') for n in publish.iter('set_object_scanned')},{'$module'})
        self.assertIsNotNone(r.find(".//run_script[@name=\"'vardath.go.survey.publish'\"]"))
        self.assertIsNotNone(r.find('.//find_object_surface'))
        self.assertIsNotNone(r.find('.//check_line_of_sight'))
        self.assertIsNotNone(r.find(".//do_all[@exact='10']/check_line_of_sight"))
        self.assertIn('$module.scannedlevel gt $before',ET.tostring(publish,encoding='unicode'))
        self.assertIn('player.maxscanlevel gt 0',ET.tostring(publish,encoding='unicode'))
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
            if root.find('order').get('infinite') != 'true': continue
            self.assertTrue(root.find('order/location').get('object').endswith('else this.ship)'))
            self.assertIsNotNone(root.find(".//resume[@label='work']"))
            self.assertIsNone(root.find('.//patch//edit_order_param'))
            self.assertIn('this.ship.defaultorder.id',ET.tostring(root.find('attention/actions'),encoding='unicode'))
    def test_crystal_prerequisite_wait_does_not_create_hold_or_income(self):
        root=xml('aiscripts/vardath.go.worker.xml')
        branch=next(n for n in root.iter('do_if') if n.get('value','').startswith('$compatible_turrets == 0 and'))
        self.assertIsNotNone(branch.find("resume[@label='start']"))
        self.assertIsNotNone(branch.find('wait'))
        self.assertIsNotNone(branch.find('.//write_to_logbook'))
        for tag in ['create_order','reward_player','transfer_money']:
            self.assertEqual(len(list(branch.iter(tag))),0)
    def test_yaki_plan_uses_supported_numeric_iteration(self):
        path=BASE.parent/'x4-yaki-terran-habs/vardath_yaki_terran_habs/md/vardath_yaki_faction_habitats.xml'
        root=ET.parse(path).getroot()
        self.assertIsNone(root.find(".//do_for_each[@in='$CurrentPlan']"))
        self.assertIsNone(root.find(".//set_value[@exact='$CurrentPlan.{$PlanIndex}']"))
        self.assertIn('$CurrentPlan.{$PlanIndex}.macro',ET.tostring(root,encoding='unicode'))
    def test_tour_selects_a_real_next_stop_after_boarding(self):
        root=xml('aiscripts/vardath.go.task.tour.xml')
        boarded=root.find(".//do_if[@value='not @this.ship.$vgo_taxi_boarded']")
        self.assertIsNotNone(boarded.find("run_script[@name=\"'vardath.go.find'\"]"))
        self.assertIsNotNone(boarded.find("set_value[@name='$target'][@exact='$nextstop']"))
        self.assertIsNone(boarded.find("return[@value='false']"))
    def test_departure_uses_native_undocking_before_proximity_success(self):
        root=xml('aiscripts/vardath.go.depart.xml')
        call=root.find(".//run_script[@name=\"'move.undock'\"]")
        self.assertEqual(call.find("param[@name='skipwait']").get('value'),'true')
        actions=xml('aiscripts/vardath.go.approach.xml').find('attention/actions')
        depart=next(i for i,n in enumerate(actions) if n.tag=='run_script' and n.get('name')=="'vardath.go.depart'")
        loop=next(i for i,n in enumerate(actions) if n.tag=='do_all')
        self.assertLess(depart,loop)
    def test_foreign_trader_escort_does_not_run_same_faction_fleet_order(self):
        for p in (MOD/'aiscripts').glob('*.xml'):
            root=ET.parse(p).getroot()
            self.assertIsNone(root.find(".//run_script[@name=\"'order.fight.escort'\"]"))
            self.assertIsNone(root.find(".//run_script[@name=\"'order.fight.attack.object'\"]"))
        root=xml('aiscripts/vardath.go.queueattack.xml')
        order=root.find('.//create_order')
        self.assertEqual(order.get('id'),"'Attack'")
        self.assertEqual(order.get('override'),'true')
        self.assertNotEqual(order.get('default'),'true')
    def test_native_icon_aliases_cover_all_registered_orders(self):
        root=xml('libraries/icons.xml')
        actual={n.get('name') for n in root.iter('icon')}
        expected={'order_'+ET.parse(p).find('order').get('id').lower() for p in (MOD/'aiscripts').glob('order.vardath.go.*.xml')}
        self.assertEqual(actual,expected)
    def test_cargo_illegality_is_not_counted(self):
        text=source('aiscripts/vardath.go.task.inspection.xml')
        self.assertIn('cargo.illegalto.{$jurisdiction}',text)
        self.assertNotIn('illegalto.{$jurisdiction}.count',text)
    def test_delivery_is_gated_by_actual_station_arrival_for_all_passengers(self):
        root=xml('md/VGO_State.xml')
        cue=root.find(".//library[@name='PassengerDisembarkV35']")
        text=ET.tostring(cue,encoding='unicode')
        self.assertNotIn('vgo_taxi_phase_started + 15s',text)
        self.assertIn('$actor.room.hascontext.{$station} and not $actor.room.hascontext.{$ship}',text)
        self.assertIn('$completed == $ship.$vgo_passengers.count',text)
        self.assertIsNotNone(cue.find('.//add_actor_to_room[@slot="$exit"]'))
        self.assertIsNotNone(cue.find('.//add_actor_to_room[@slot="$rollback"]'))
    def test_taxi_undocks_even_for_same_sector_delivery_and_keeps_real_manifest(self):
        root=xml('aiscripts/vardath.go.passengers.deliver.xml')
        first=root.find(".//do_if[@value='@this.ship.dock.container != $destination']")
        self.assertIsNotNone(first.find("run_script[@name=\"'vardath.go.depart'\"]"))
        self.assertIn('not @this.ship.$vgo_taxi_boarded',ET.tostring(root,encoding='unicode'))
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

    def test_transient_target_sector_never_reaches_native_movement_as_null(self):
        actions=xml('aiscripts/vardath.go.approach.xml').find('attention/actions')
        attempt=actions.find("do_all[@counter='$attempt']")
        resolve=attempt.find("do_all[@exact='12']")
        self.assertIsNotNone(resolve.find("set_value[@name='$sector'][@exact='$target.sector']"))
        self.assertEqual(resolve.find('wait').get('exact'),'5s')
        reject=attempt.find("do_if[@value='not $sector.exists']")
        self.assertEqual(reject.find('return').get('value'),'false')
        move=attempt.find("run_script[@name=\"'move.generic'\"]")
        self.assertLess(list(attempt).index(reject),list(attempt).index(move))
        self.assertEqual(move.find("param[@name='destination']").get('value'),'$sector')
        self.assertEqual(attempt.find('get_safe_pos').get('sector'),'$sector')
        self.assertIsNotNone(attempt.find("do_if[@value='this.ship.$vgo_scope? and not this.ship.$vgo_scope.indexof.{$sector}']/return[@value='false']"))

    def test_unlocated_wreck_and_pilotless_candidates_are_rejected_before_properties(self):
        loop=xml('aiscripts/vardath.go.find.xml').find('.//do_while')
        guards=[n for n in loop if n.tag=='do_if']
        sector=next(i for i,n in enumerate(guards) if n.get('value')=='not $candidate.sector.exists')
        live=next(i for i,n in enumerate(guards) if 'not $candidate.isoperational' in n.get('value',''))
        owner=next(i for i,n in enumerate(guards) if '$candidate.sector.owner' in n.get('value',''))
        capture=next(i for i,n in enumerate(guards) if '$candidate.iscapturable' in n.get('value',''))
        pilot=next(i for i,n in enumerate(guards) if 'not $candidate.pilot.exists' in n.get('value',''))
        self.assertLess(sector,owner)
        self.assertLess(live,capture)
        self.assertLess(pilot,capture)
        for i in [sector,live,pilot]:self.assertIsNotNone(guards[i].find('continue'))

    def test_recruitment_revalidates_operational_target_after_communication(self):
        actions=xml('aiscripts/vardath.go.task.recruit.xml').find('attention/actions')
        wait=actions.find("wait[@exact='8s']")
        tail=list(actions)[list(actions).index(wait)+1:]
        self.assertEqual(tail[0].get('value'),'not $target.isoperational')
        self.assertEqual(tail[0].find('return').get('value'),'false')
        self.assertEqual(tail[1].get('value'),'not $target.pilot.exists')

    def test_activity_reports_are_throttled_observations_of_registered_ships(self):
        cue=xml('md/VGO_State.xml').find(".//cue[@name='ActivityReportsV24']")
        self.assertEqual(cue.find('.//do_for_each').get('in'),'Init.$Ships')
        self.assertIn('player.age + 5min',ET.tostring(cue,encoding='unicode'))
        self.assertIn('vgo_report_after gt player.age',ET.tostring(cue,encoding='unicode'))
        self.assertIsNotNone(cue.find('.//write_to_logbook'))
        self.assertIsNotNone(cue.find('.//debug_text'))
        for tag in ['find_ship','find_station','reward_player','transfer_money','add_skill','set_owner','set_object_scanned']:
            self.assertEqual(len(list(cue.iter(tag))),0)

    def test_completion_counters_follow_task_success_without_creating_payments(self):
        worker=xml('aiscripts/vardath.go.worker.xml')
        calls=worker.findall(".//run_script[@name=\"'vardath.go.recordresult'\"]")
        completed=[n for n in calls if n.find("param[@name='outcome']").get('value')=="'completed'"]
        self.assertEqual(len(completed),2)
        for result in ['$success','$crystalcycle == 1']:
            self.assertTrue(any(n in list(worker.find(".//do_if[@value='"+result+"']").iter()) for n in completed))
        result=xml('aiscripts/vardath.go.recordresult.xml')
        self.assertIn('$last_serial',ET.tostring(result,encoding='unicode'))
        for tag in ['reward_player','transfer_money','create_npc_template','add_inventory','set_object_scanned','set_owner']:
            self.assertEqual(len(list(result.iter(tag))),0)

    def test_scanner_preserves_geometry_wait_reason_and_stops_unloaded_module_loop(self):
        root=xml('aiscripts/vardath.go.task.scanner.xml')
        missing=root.find(".//do_if[@value='not $module.isphysicsready or $module.attention lt attention.visible or $module.sector != player.sector']")
        self.assertIsNotNone(missing.find('break'))
        self.assertIsNone(missing.find('continue'))
        self.assertIn('Component survey waiting for loaded collision geometry',ET.tostring(root,encoding='unicode'))

    def test_crystal_job_accepts_all_ship_sizes_and_retires_restrictive_controls(self):
        order=xml('aiscripts/order.vardath.go.crystal.xml').find('order')
        size=next(n for n in order.findall('requires/match') if n.get('class','').startswith('['))
        self.assertEqual(size.get('class'),'[class.ship_s, class.ship_m, class.ship_l, class.ship_xl]')
        names={n.get('name') for n in order.findall('params/param')}
        self.assertFalse(names & {'beamonly','sell','sellthreshold','collectionlimit'})
        worker=source('aiscripts/vardath.go.worker.xml')
        self.assertNotIn('($job == 6 or $job == 8) and this.ship.iscapitalship',worker)
        self.assertNotIn("'vardath.go.sellcrystals'",worker)
        self.assertNotIn("'vardath.go.crystalcount'",worker)

    def test_forward_weapons_and_turrets_have_real_firing_and_alignment_paths(self):
        fire=xml('aiscripts/vardath.go.fire.xml')
        self.assertIn('this.ship.maxcombatrange.missiles.all',ET.tostring(fire,encoding='unicode'))
        forward=next(n for n in fire.iter('do_if') if n.get('value','').startswith('this.ship.maxcombatrange.lasers.all gt 0 or'))
        self.assertIsNotNone(forward.find('.//shoot_at'))
        self.assertIsNotNone(fire.find(".//run_script[@name=\"'vardath.go.aligncrystal'\"]"))
        self.assertNotIn('$vgo_beamonly',ET.tostring(fire,encoding='unicode'))
        align=xml('aiscripts/vardath.go.aligncrystal.xml')
        self.assertEqual({n.get('orientation') for n in align.iter('create_orientation')},{'look_at','align_left','align_right','look_away'})
        self.assertIsNotNone(align.find('.//move_to/interrupt_after_time'))
        for tag in ['set_weapon_mode','activate_weapongroup','reset_weapongroups']:
            self.assertEqual(len(list(fire.iter(tag)))+len(list(align.iter(tag))),0)

    def test_crystal_collection_consumes_only_real_attributed_drops_near_ship(self):
        root=xml('aiscripts/vardath.go.collectcrystals.xml')
        loop=root.find('.//do_for_each')
        self.assertEqual(loop.get('in'),'this.ship.$vgo_crystal_drops')
        self.assertEqual(loop.find('collect_drop').get('object'),'this.ship')
        self.assertEqual(loop.find('collect_drop').get('drop'),'$drop')
        self.assertIn('5km + this.ship.size / 2',ET.tostring(loop,encoding='unicode'))
        self.assertIn('$drop.wares.{$ware}.count',ET.tostring(loop,encoding='unicode'))
        self.assertIsNotNone(loop.find("run_script[@name=\"'vardath.go.forwardcrystals'\"]"))
        for tag in ['add_inventory','create_object','create_drop','find_object','reward_player']:
            self.assertEqual(len(list(root.iter(tag))),0)

    def test_crystal_forwarding_uses_observed_withdrawal_and_partial_credit_rollback(self):
        root=xml('aiscripts/vardath.go.forwardcrystals.xml')
        text=ET.tostring(root,encoding='unicode')
        self.assertIn('$sourcebefore - this.ship.pilot.inventory.{$ware}.count',text)
        self.assertIsNotNone(root.find(".//add_inventory[@entity='player.entity'][@exact='$removed']"))
        self.assertIsNotNone(root.find(".//do_if[@value='$added lt $removed']/add_inventory[@entity='this.ship.pilot']"))
        self.assertNotIn('wait', {n.tag for n in root.iter()})
        for tag in ['reward_player','transfer_money','remove_cargo','add_cargo']:
            self.assertEqual(len(list(root.iter(tag))),0)

    def test_pending_crystal_drops_survive_a_task_restart(self):
        root=xml('aiscripts/vardath.go.task.crystal.xml')
        self.assertIsNotNone(root.find(".//do_if[@value='not this.ship.$vgo_crystal_drops?']/set_value"))
        self.assertIsNone(root.find("./attention/actions/set_value[@name='this.ship.$vgo_crystal_drops']"))
        self.assertIn('vgo_crystal_drops',source('aiscripts/vardath.go.find.xml'))
        self.assertIn('vgo_crystal_sent',source('md/VGO_State.xml'))

    def test_crystal_discovery_uses_native_per_asteroid_component_traversal(self):
        for name in ['aiscripts/vardath.go.find.xml','md/VGO_Turrets.xml']:
            root=xml(name)
            nodes=[n for n in root.iter('find_object_component') if n.get('class')=='class.crystal']
            self.assertEqual(len(nodes),1)
            self.assertEqual(nodes[0].get('object'),'$rock')
            self.assertEqual(nodes[0].get('append'),'true')
            self.assertIsNotNone(root.find(".//do_for_each[@name='$rock'][@in='$rocks']"))

    def test_standalone_turret_controller_yields_to_crystal_occupation(self):
        root=xml('md/VGO_Turrets.xml')
        text=ET.tostring(root,encoding='unicode')
        self.assertIn("or @$ship.defaultorder.id == 'VGO_crystal'",text)
        self.assertNotIn('$ship.iscapitalship',text)
        self.assertNotIn('not $turret.isclass.missileturret',text)

    def test_demolition_does_not_count_a_missing_reference_as_destruction(self):
        root=xml('aiscripts/vardath.go.fire.xml')
        event=root.find('.//interrupts/handler/conditions/event_object_destroyed')
        self.assertEqual(event.get('object'),'$target')
        self.assertNotIn('not $target.exists or $target.hull le 0',ET.tostring(root,encoding='unicode'))
        actions=root.find("attention[@min='visible']/actions")
        self.assertIsNotNone(actions.find("do_if[@value='$destroyed']/return[@value='true']"))
        self.assertEqual(actions[-1].get('value'),'false')

if __name__=='__main__': unittest.main(verbosity=2)
