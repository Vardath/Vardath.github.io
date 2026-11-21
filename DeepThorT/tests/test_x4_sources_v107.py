"""Focused regression for evidence-backed X4 discovery, with no real game required."""
import re
import tempfile
import unittest
from pathlib import Path

from deepthort_local.x4_sources import (
    likely_installations, inspect_x4_sources, format_x4_inspection,
    x4_evidence_for_prompt, find_catalog_tool, catalog_extraction_command,
)
from deepthort_local.agent_plan import build_plan_prompt


class X4SourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/'SteamLibrary'/'steamapps'/'common'/'X4 Foundations'
        self.game.mkdir(parents=True)
        (self.game/'X4.exe').write_bytes(b'GAME')
        (self.game/'01.cat').write_text('assets/units/size_m/macros/ship_xen_m_corvette_something_macro.xml 0 1234\n')
        (self.game/'01.dat').write_bytes(b'fake data')
        self.ref=self.root/'reference'
        self.ref.mkdir()

    def _write_ref(self,path,identifier):
        p=self.ref/path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('<root><macro name="'+identifier+'" /></root>',encoding='utf-8')
        return p

    def test_named_installation_detection_never_traverses_whole_disk(self):
        roots=[self.root/'SteamLibrary']
        installed=likely_installations(roots)
        self.assertIn(self.game.resolve(),installed)

    def test_catalogs_without_xml_are_not_verified_equipment(self):
        result=inspect_x4_sources(game_dir=self.game,discover_roots=[self.root/'SteamLibrary'])
        self.assertEqual(result['catalogs'],['01.cat'])
        self.assertFalse(result['ready_for_planning'])
        self.assertEqual(result['ship_candidates'],[])
        self.assertIn('not extracted',format_x4_inspection(result))

    def test_extracted_actual_xml_can_supply_evidence(self):
        self._write_ref('assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml','ship_xen_m_corvette_02_a_macro')
        (self.ref/'assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml').write_text('<macros><macro name="ship_xen_m_corvette_02_a_macro"><component ref="ship_xen_m_corvette_02_a"/></macro></macros>')
        component=self.ref/'assets/units/size_m/ship_xen_m_corvette_02_a.xml'
        component.write_text('<components><component name="ship_xen_m_corvette_02_a"><connections><connection name="gun1" tags="weapon medium"/><connection name="turret1" tags="turret medium"/></connections></component></components>')
        self._write_ref('assets/props/WeaponSystems/laser/macros/weapon_gen_m_laser_macro.xml','weapon_gen_m_laser_macro')
        self._write_ref('assets/props/WeaponSystems/turret/macros/turret_gen_m_laser_macro.xml','turret_gen_m_laser_macro')
        self._write_ref('index/macros.xml','index_of_macros')
        result=inspect_x4_sources(game_dir=self.game,reference_dir=self.ref)
        self.assertTrue(result['ready_for_planning'])
        self.assertEqual(len(result['ship_candidates']),1)
        self.assertTrue(result['pe_component_verified'])
        self.assertEqual(len(result['pe_component_connections']),2)
        self.assertEqual(len(result['weapon_candidates']),1)
        self.assertEqual(len(result['turret_candidates']),1)
        self.assertEqual(len(result['files']),1)
        detail=x4_evidence_for_prompt(result)
        self.assertIn('ship_xen_m_corvette_02_a_macro',detail)
        self.assertIn('SHA ',detail)
        prompt=build_plan_prompt('Create an X4 Xenon PE mod',x4_evidence=detail)
        self.assertIn('VERIFIED LOCAL X4 REFERENCE CANDIDATES',prompt)
        self.assertIn('not necessarily PE',prompt)

    def test_fake_malformed_and_oversized_sources_are_not_claimed_as_evidence(self):
        invalid=self._write_ref('assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml','ship_xen_m_corvette_02_a_macro')
        invalid.write_text('<not xml')
        self._write_ref('assets/props/WeaponSystems/laser/macros/weapon_gen_m_laser_macro.xml','weapon_gen_m_laser_macro')
        self._write_ref('assets/props/WeaponSystems/turret/macros/turret_gen_m_laser_macro.xml','turret_gen_m_laser_macro')
        result=inspect_x4_sources(game_dir=self.game,reference_dir=self.ref)
        self.assertFalse(result['ready_for_planning'])
        self.assertIn('Exact Xenon PE', ' '.join(result['blocked_reasons']))

    def test_tool_is_not_guessed_from_filename_alone(self):
        self.assertIsNone(find_catalog_tool(selected=self.root/'XRCatTool.exe',roots=[self.root]))
        (self.root/'XRCatTool.exe').write_bytes(b'tool stub')
        self.assertEqual(find_catalog_tool(selected=self.root/'XRCatTool.exe'),str((self.root/'XRCatTool.exe').resolve()))

    def test_extraction_requires_real_game_and_avoids_writing_inside_it(self):
        tool=self.root/'XRCatTool.exe';tool.write_bytes(b'tool stub')
        with self.assertRaises(ValueError):catalog_extraction_command(tool,self.game,self.game/'reference')
        cmd=catalog_extraction_command(tool,self.game,self.root/'reference')
        self.assertEqual(cmd[0],str(tool))
        self.assertEqual(cmd[1],'-in')
        self.assertIn(str(self.game/'01.cat'),cmd)
        self.assertEqual(cmd[cmd.index('-out')+1],str(self.root/'reference'))
        filters=cmd[cmd.index('-include')+1:]
        self.assertTrue(any(re.match(regex,'assets/units/size_m/macros/ship_xen.xml') for regex in filters))
        self.assertTrue(any(re.match(regex,'assets/props/WeaponSystems/laser/macros/weapon_gen_m_macro.xml') for regex in filters))
        self.assertFalse(any(re.match(regex,'example.exe') for regex in filters))

    def test_catalog_with_missing_dat_is_not_a_paired_archive(self):
        (self.game/'01.dat').unlink()
        result=inspect_x4_sources(game_dir=self.game)
        self.assertEqual(result['catalogs'],[])
        tool=self.root/'XRCatTool.exe';tool.write_bytes(b'tool stub')
        with self.assertRaises(ValueError):catalog_extraction_command(tool,self.game,self.root/'output')

    def test_project_directory_is_not_mistaken_for_game(self):
        project=self.root/'x4mods';project.mkdir()
        result=inspect_x4_sources(project_dir=project,discover_roots=[project])
        self.assertFalse(result['ready_for_planning'])
        self.assertEqual(result['ship_candidates'],[])


if __name__=='__main__':unittest.main()
