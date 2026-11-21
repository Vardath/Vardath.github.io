"""X4 deterministic recovery and safe source staging regressions."""
import tempfile
import unittest
from pathlib import Path
from deepthort_local.agent_plan import (
    PlanError, verified_x4_pe_plan, build_budgeted_file_step_prompt,
    validate_generated_x4_xml, parse_build_plan,
)

REPORT = {
    'ready_for_planning': True,
    'pe_macro_verified': True,
    'pe_component_verified': True,
    'pe_component_file': 'assets/units/size_m/ship_xen_m_corvette_02_a.xml',
    'pe_component_connections': [{'name':'weapon_01','tags':'weapon medium'},
                                  {'name':'turret_01','tags':'turret medium'}],
    'ship_candidates': [{'file':'assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml',
                         'identifiers':['ship_xen_m_corvette_02_a_macro']}],
    'weapon_candidates': [{'file':'assets/props/WeaponSystems/laser/macros/weapon_known.xml'}],
    'turret_candidates': [{'file':'assets/props/WeaponSystems/turret/macros/turret_known.xml'}],
}
REQ='Make an X4 Foundations Xenon PE with 10x cargo, 4x speed, 50,000 per hit and 60 seconds respawn, high rate of fire, good handling and compatible connections.'

class RecoveryTests(unittest.TestCase):
    def test_source_gate_blocks_without_verified_references(self):
        with self.assertRaises(PlanError):
            verified_x4_pe_plan(REQ, {'ready_for_planning':False})
        with self.assertRaises(PlanError):
            verified_x4_pe_plan('Build a normal desktop app', REPORT)

    def test_deterministic_plan_contains_every_required_mod_stage(self):
        plan=verified_x4_pe_plan(REQ,REPORT)
        self.assertEqual(len(plan),6)
        import json
        with tempfile.TemporaryDirectory() as d:
            parse_build_plan(json.dumps({'files':plan}),Path(d),request=REQ)
        notes=' '.join(x['description'] for x in plan)
        for phrase in ('10x','4x','50,000','60 seconds','owned','weapon','turret',
                       'handling','installed','connection','vanilla'):
            self.assertIn(phrase,notes)
        self.assertTrue(all(x['path'].endswith('.xml') for x in plan))

    def test_bounded_file_prompt_preserves_original_and_essential_step(self):
        plan=verified_x4_pe_plan(REQ,REPORT)
        request=REQ + (' Preserve other requirements.' * 120)
        output=build_budgeted_file_step_prompt(request,plan[0]['path'],
                plan[0]['description'],'',plan,evidence='PE connection: weapon_01')
        self.assertLessEqual(len(output),7500)
        self.assertIn(request,output)
        self.assertIn(plan[0]['description'],output)

    def test_oversized_approved_requirement_causes_stop_not_truncation(self):
        plan=verified_x4_pe_plan(REQ,REPORT)
        with self.assertRaisesRegex(PlanError,'no requirements were discarded'):
            build_budgeted_file_step_prompt('preserve absolutely every part '*400,
                plan[0]['path'],plan[0]['description'],'',plan)

    def test_xml_checks_are_syntax_guards_not_game_claims(self):
        validate_generated_x4_xml('content.xml','<content id="vardath_pe"/>')
        validate_generated_x4_xml('md/respawn.xml','<mdscript name="watcher"/>')
        validate_generated_x4_xml('assets/foo/macros/bar.xml','<macros/>')
        for path,source in [('content.xml','<wrong/>'),('md/test.xml','<mdscript>'),
                            ('content.xml','```xml\n<content/>\n```'),
                            ('content.xml','<content id="REPLACE_ME"/>')]:
            with self.subTest(path=path,source=source), self.assertRaises(PlanError):
                validate_generated_x4_xml(path,source)

if __name__ == '__main__': unittest.main()
