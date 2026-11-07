#!/usr/bin/env python3
"""Source contracts for reported menu/physics recovery. These do not execute X4."""
import unittest
import xml.etree.ElementTree as ET
from source_contracts import xml, source, MOD

class RuntimeRecoveryContracts(unittest.TestCase):
    def test_crystal_physics_fallback_is_configurable_and_uses_normal_navigation(self):
        order=xml('aiscripts/order.vardath.go.crystal.xml')
        self.assertEqual(order.find("order/params/param[@name='simfallback']").get('default'),'true')
        root=xml('aiscripts/vardath.go.crystal.simulation.xml')
        self.assertIsNotNone(root.find(".//run_script[@name=\"'move.generic'\"]"))
        text=ET.tostring(root,encoding='unicode')
        self.assertIn('vgo_scope.indexof.{$sector}',text)
        self.assertIn('vgo_risk != 2',text)
        for tag in ['set_object_position','warp','create_object','create_drop','add_inventory','add_cargo','reward_player','set_object_attention']:
            self.assertEqual(len(list(root.iter(tag))),0)

    def test_crystal_commerce_dispatches_remote_simulation_without_following_player(self):
        worker=xml('aiscripts/vardath.go.worker.xml')
        self.assertIsNotNone(worker.find(".//run_script[@name=\"'vardath.go.crystal.commercial'\"]"))
        root=xml('aiscripts/vardath.go.crystal.commercial.xml')
        branch=next(n for n in root.iter('do_if') if n.find("run_script[@name=\"'vardath.go.crystal.simulation'\"]") is not None)
        self.assertIn('this.ship.sector != player.sector',branch.get('value'))
        self.assertIn('this.ship.attention lt attention.visible',branch.get('value'))
        sim=source('aiscripts/vardath.go.crystal.simulation.xml')
        self.assertNotIn('player.entity.relativeposition',sim)
        self.assertNotIn('exact="player.sector"',sim)
        self.assertIn('deplete_yield',sim)

    def test_crystal_loose_drop_recovery_filters_real_inventory_contents(self):
        root=xml('aiscripts/vardath.go.crystaldrops.xml')
        self.assertEqual(root.find('.//find_object').get('class'),'class.drop')
        self.assertIn('$drop.wares.{$ware}.count',ET.tostring(root,encoding='unicode'))
        self.assertIsNotNone(root.find(".//do_if[@value='$quantity gt 0']/append_to_list"))
        for tag in ['add_inventory','destroy_object','create_drop','reward_player']:
            self.assertEqual(len(list(root.iter(tag))),0)

    def test_crystal_pickup_native_player_fallback_cannot_generate_items(self):
        root=xml('aiscripts/vardath.go.collectcrystals.xml')
        fallback=next(n for n in root.iter('do_if') if n.find("collect_drop[@object='player.occupiedship']") is not None)
        self.assertIn('$drop.exists',fallback.get('value'))
        self.assertIn('not $pickup_confirmed',fallback.get('value'))
        self.assertIn('player.occupiedship.exists',fallback.get('value'))
        self.assertIsNotNone(fallback.find('wait'))
        for tag in ['add_inventory','destroy_object','create_drop','reward_player']:
            self.assertEqual(len(list(root.iter(tag))),0)

    def test_crystal_pickup_native_failure_retains_actual_drop_for_retry(self):
        root=xml('aiscripts/vardath.go.collectcrystals.xml')
        self.assertIn('player.age + 2min',ET.tostring(root,encoding='unicode'))
        self.assertIn('real drop retained for retry',ET.tostring(root,encoding='unicode'))
        self.assertIsNone(root.find('.//destroy_object'))

    def test_crystal_diagnostics_distinguish_search_fire_pickup_and_delivery(self):
        names=['vardath.go.find','vardath.go.fire','vardath.go.collectcrystals','vardath.go.forwardcrystals']
        markers=['GO crystal search:','GO crystal fire result:','GO crystal pickup:','GO crystals:']
        for name,marker in zip(names,markers):self.assertIn(marker,source('aiscripts/'+name+'.xml'))

    def test_hacker_catalogue_always_publishes_an_empty_or_populated_reply(self):
        root=xml('md/VGO_Hacker.xml')
        actions=root.find(".//library[@name='Catalogue']/actions")
        self.assertEqual(actions[-1].tag,'raise_lua_event')
        self.assertEqual(actions[-1].get('name'),"'VGO.HackCatalogue'")
        self.assertEqual(actions.find("set_value[@name='$public']").get('exact'),'[]')
        self.assertEqual(actions.find("set_value[@name='$cataloguestatus']").get('exact'),"'unavailable'")

    def test_hacker_ui_lookup_explicitly_refreshes_custom_actions(self):
        lua=(MOD/'ui/vgo_hacker.lua').read_text()
        self.assertIn('function H.catalogueReady',lua)
        self.assertIn('function H.poll',lua)
        self.assertIn('getElapsedTime()',lua)
        self.assertIn('H.decorate(menu)\n        menu.refresh = true',lua)
        self.assertIn('return original(...)',lua)

if __name__=='__main__':unittest.main(verbosity=2)
