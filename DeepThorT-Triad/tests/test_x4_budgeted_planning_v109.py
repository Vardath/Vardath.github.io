"""Ensure automatic X4 inspection never overflows the local model input."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import os
from deepthort_local.agent_plan import (
    build_plan_prompt, build_budgeted_plan_prompt, PlanError,
)

SPEC = ("Create a real X4 Foundations Xenon PE mod; keep every constraint: "
        "50,000 damage per hit, 4x base speed, 10x cargo, improved handling, "
        "high fire rate weapon and turrets, respawn after 60 seconds without "
        "player owned PE, inspect game references first.\n" +
        ("Preserve existing saves, correct original component slots and ensure "
         "the ship has installed working weapons and independent mod XML.\n" * 36))
EVIDENCE = '\n'.join([
    'ship_candidates: assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml IDs ship_xen_m_corvette_02_a_macro SHA aaedeeabc123',
    'weapon_candidates: assets/props/WeaponSystems/weapon_macros.xml IDs weapon_gen_m_bolt_01_macro SHA aaedeeabc124',
    'turret_candidates: assets/props/WeaponSystems/turret_macros.xml IDs turret_gen_m_bolt_01_macro SHA aaedeeabc125',
    'PE connection: weapon_conn_01 tags weapon medium',
    'PE connection: turret_conn_01 tags turret medium',
    *[f'weapon_candidates: assets/props/WeaponSystems/candidate_{i}.xml IDs other_weapon_{i} SHA aaffeeabcd99' for i in range(12)],
    *[f'turret_candidates: assets/props/WeaponSystems/candidate_{i}_turret.xml IDs other_turret_{i} SHA aaffeeabcd99' for i in range(12)],
])


class BudgetedPlanningTests(unittest.TestCase):
    def test_preserves_complete_spec_and_representative_verified_evidence(self):
        # The old code rejected the request after it added the X4 evidence.
        self.assertGreater(len(build_plan_prompt(SPEC, x4_evidence=EVIDENCE)), 7500)
        compact = build_budgeted_plan_prompt(SPEC, x4_evidence=EVIDENCE)
        self.assertLessEqual(len(compact), 7500)
        self.assertIn(SPEC, compact)
        for expected in ['PE connection:', 'ship_xen_m_corvette_02_a_macro',
                         'weapon_gen_m_bolt_01_macro', 'turret_gen_m_bolt_01_macro']:
            self.assertIn(expected, compact)
        self.assertNotIn('SHA aaedeeabc123', compact)

    def test_under_budget_evidence_is_left_identical(self):
        prompt = build_plan_prompt('Build X4 mod', x4_evidence='PE connection: a')
        self.assertEqual(build_budgeted_plan_prompt('Build X4 mod', x4_evidence='PE connection: a'), prompt)

    def test_oversize_user_specification_never_silently_truncated(self):
        huge = 'X4 Foundations mod: ' + 'preserve the user request and every detail ' * 280
        with self.assertRaisesRegex(PlanError,'Nothing was truncated'):
            build_budgeted_plan_prompt(huge, x4_evidence=EVIDENCE)

    @unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'GUI required')
    def test_draft_request_with_x4_evidence_dispatches_under_7500(self):
        import desktop_app as appmod
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);project=root/'x4mods';project.mkdir()
            app_root=root/'deepthort';app_root.mkdir()
            refs=app_root/'reference'/'x4'
            a=refs/'assets'/'units'/'size_m'
            (a/'macros').mkdir(parents=True)
            (a/'macros'/'ship_xen_m_corvette_02_a_macro.xml').write_text('<macros><macro name="ship_xen_m_corvette_02_a_macro"><component ref="ship_xen_m_corvette_02_a"/></macro></macros>')
            (a/'ship_xen_m_corvette_02_a.xml').write_text('<components><component name="ship_xen_m_corvette_02_a"><connections><connection name="gun" tags="weapon medium"/><connection name="turret" tags="turret medium"/></connections></component></components>')
            w=refs/'assets'/'props'/'WeaponSystems'
            (w/'laser'/'macros').mkdir(parents=True)
            (w/'turret'/'macros').mkdir(parents=True)
            (w/'laser'/'macros'/'weapon_gen_m_laser_macro.xml').write_text('<macros><macro name="weapon_gen_m_laser_macro"/></macros>')
            (w/'turret'/'macros'/'turret_gen_m_laser_macro.xml').write_text('<macros><macro name="turret_gen_m_laser_macro"/></macros>')
            game=root/'X4 Foundations';game.mkdir();(game/'X4.exe').write_bytes(b'x4')
            with patch.object(appmod,'ROOT',app_root),patch.object(appmod,'STATE',app_root/'state'), \
                 patch.object(appmod.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(appmod.DeepThorTDesktop,'_auto_start_if_installed',lambda self:None), \
                 patch.object(appmod,'x4_evidence_for_prompt',return_value=EVIDENCE), \
                 patch.object(appmod.messagebox,'showwarning'),patch.object(appmod.messagebox,'showerror'),patch.object(appmod.messagebox,'showinfo'):
                ui=appmod.DeepThorTDesktop()
                try:
                    ui._set_project(project);ui.x4_game_dir=str(game)
                    # Request longer than an ordinary prompt but still reasonable.
                    req=ui.conversations.submit(ui.current_chat,str(project),'draft_plan',SPEC)
                    captured=[]
                    ui.client.chat=lambda session,prompt,**kw: captured.append(prompt) or '{"files":[]}'
                    ui._execute_conversation(ui.conversations.get(req))
                    deadline=time.monotonic()+5
                    while not captured and time.monotonic()<deadline:
                        ui._handle_events();time.sleep(.02)
                    self.assertTrue(captured)
                    self.assertGreater(len(build_plan_prompt(SPEC,x4_evidence=EVIDENCE)),7500)
                    self.assertIn(SPEC,captured[0])
                    self.assertIn('PE connection:',captured[0])
                    self.assertLessEqual(len(captured[0]),7500)
                    self.assertEqual(ui.jobs.items(str(project)),[])
                    # Wait for the background planner to finish before the
                    # temporary fixture is removed. Merely seeing its first
                    # model call leaves that worker free to recreate state/.
                    deadline=time.monotonic()+5
                    while ui.conversations.get(req)['state']=='running' and time.monotonic()<deadline:
                        ui._handle_events();time.sleep(.02)
                    self.assertNotEqual(ui.conversations.get(req)['state'],'running')
                finally:ui._quit()

if __name__=='__main__':unittest.main()
