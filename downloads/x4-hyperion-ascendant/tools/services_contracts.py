"""Hyperion service static contracts grounded in native XML and the error log.

These are source checks, not a substitute for a running X4 game. The previous
model-based VM treated ship components as writable MD variable namespaces and
create_module as a valid ship retrofit. Both assumptions were disproven by the
2026-11-11 log. No test may reintroduce those false engine assumptions.
"""
import unittest
from pathlib import Path
from lxml import etree as E

MOD = Path(__file__).resolve().parents[1] / "vardath_hyperion_ascendant"
REFS = {}
DEPLOYABLES = {
    "macro.eq_arg_satellite_02_macro",
    "macro.eq_arg_resourceprobe_01_macro",
    "macro.env_deco_nav_beacon_t1_macro",
    "macro.weapon_gen_mine_03_macro",
}
DRONES = {
    "macro.ship_gen_xs_buildingdrone_01_a_macro",
    "macro.ship_gen_xs_cargodrone_empty_01_a_macro",
}

class ServiceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = E.parse(str(MOD / "md/VHA_Services.xml"))
        cls.cue = cls.xml.find(".//cue[@name='ReplenishV103']")

    def test_one_rate_limited_service_cue(self):
        self.assertEqual(len(self.xml.xpath("//cue")), 1)
        self.assertIsNotNone(self.cue)
        self.assertEqual(self.cue.get("checkinterval"), "10min")
        self.assertIsNotNone(self.cue.find("./actions/reset_cue[@cue='this']"))

    def test_no_ship_component_state_or_unsupported_retrofit(self):
        body = E.tostring(self.xml, encoding="unicode")
        self.assertNotIn("$Ship.$vha_", body)
        self.assertNotIn("create_module", body)
        self.assertNotIn("find_object_component", body)
        self.assertNotIn("set_object_name", body)
        self.assertNotIn("<remove_", body)
        self.assertNotIn("set_cargo", body)

    def test_all_ships_are_filtered_by_true_owner_and_custom_macro(self):
        n = self.cue.find("./actions/find_ship_by_true_owner")
        self.assertIsNotNone(n)
        self.assertEqual(n.get("faction"), "faction.player")
        self.assertEqual(n.get("macro"), "macro.ship_vardath_hyperion_ascendant_macro")
        self.assertEqual(n.get("space"), "player.galaxy")
        self.assertEqual(n.get("multiple"), "true")
        guard = self.cue.find("./actions/do_for_each/do_if")
        self.assertIn("$Ship.isplayerowned",guard.get("value"))
        self.assertIn("$Ship.isoperational",guard.get("value"))

    def test_supplies_only_requested_consumables_and_drones(self):
        ammo = self.xml.xpath("//add_ammo")
        units = self.xml.xpath("//add_units")
        self.assertEqual({n.get("macro") for n in ammo},
            DEPLOYABLES | {"macro.countermeasure_flares_01_macro"})
        self.assertEqual({n.get("macro") for n in units}, DRONES)
        for n in ammo + units:
            self.assertEqual(n.get("object"), "$Ship")
            self.assertTrue(n.get("amount") or n.get("exact"))
        self.assertFalse(self.xml.xpath("//add_cargo | //remove_cargo | //remove_units | //remove_ammo"))

    def test_all_replenishment_is_capacity_guarded(self):
        for n in self.xml.xpath("//add_ammo | //add_units"):
            ancestors = list(n.iterancestors("do_if"))
            self.assertTrue(any("free gt 0" in (a.get("value") or "") for a in ancestors),
                            E.tostring(n, encoding="unicode"))

    def test_new_hull_static_builder_capacity_and_storage(self):
        ship = E.parse(str(MOD / "assets/units/size_l/macros/ship_vardath_hyperion_ascendant_macro.xml"))
        self.assertEqual(ship.find(".//people").get("capacity"), "700")
        self.assertEqual(ship.find(".//purpose").get("primary"), "build")
        self.assertEqual(ship.find(".//properties/ship").get("type"), "builder")
        self.assertIsNotNone(ship.find(".//connection[@ref='con_shipstorage_s_01']"))
        self.assertIsNotNone(ship.find(".//connection[@ref='con_storage_01']"))

    def test_default_methods_exist_for_all_five_custom_wares(self):
        wares = E.parse(str(MOD / "libraries/wares.xml")).xpath("/diff/add/ware")
        self.assertEqual(len(wares), 5)
        for ware in wares:
            production = ware.find("production")
            self.assertIsNotNone(production, ware.get("id"))
            self.assertEqual(production.get("method"), "default")
            self.assertIsNotNone(production.find("primary/ware"))
            self.assertIsNotNone(ware.find("component"))
            self.assertIsNone(ware.find("owner"))

    def test_no_native_ship_runtime_module_creation(self):
        self.assertFalse(self.xml.xpath("//create_module | //create_dockingbay"))
        hangar = E.parse(str(MOD / "assets/props/SurfaceElements/macros/shipstorage_vardath_hyperion_s_macro.xml"))
        self.assertEqual(hangar.find("macro").get("class"), "dockingbay")
