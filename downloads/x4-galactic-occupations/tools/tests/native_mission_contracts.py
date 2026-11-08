#!/usr/bin/env python3
"""Exercise actual signal survey dispatch with real native identifier contracts.

Native cues, discounts and mission execution remain mocks; no live mission
generation or save/load claim is made here.
"""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_references import invalid_native_cue_refs
from survey_contracts import SurveyVM, SURVEY

API=json.loads((Path(__file__).resolve().parents[1]/'api_contracts.json').read_text())


class NativeMissionVM(SurveyVM):
    def __init__(self):super().__init__();self.requests=[]
    def execute(self,nodes):
        for n in nodes:
            if n.tag=='signal_cue_instantly' and n.get('cue')=='$missionrequest':
                cue=self.expr(n.get('cue'))
                if cue is not self.mission_request or not cue.exists:
                    raise AssertionError('Cannot signal an absent/non-native request cue')
                self.requests.append((cue,self.expr(n.get('param'))))
            else:super().execute([n])


class NativeCueReferenceContracts(unittest.TestCase):
    def test_old_failing_parent_property_reference_is_rejected(self):
        old='md.GenericMissions.Manager.SelectMission'
        self.assertEqual(invalid_native_cue_refs(old,API['native_md_cues']),[old])
    def test_flat_native_cue_and_its_guard_are_accepted(self):
        for value in ['@md.GenericMissions.SelectMission','md.GenericMissions.SelectMission.exists']:
            self.assertEqual(invalid_native_cue_refs(value,API['native_md_cues']),[])
    def test_real_manager_variables_are_not_mistaken_for_child_cue_identifiers(self):
        self.assertEqual(invalid_native_cue_refs('md.GenericMissions.Manager.$MissionCues',API['native_md_cues']),[])
    def test_unknown_native_cue_is_not_accepted_merely_because_script_is_known(self):
        self.assertEqual(invalid_native_cue_refs('md.GenericMissions.NotACue',API['native_md_cues']),['md.GenericMissions.NotACue'])


class NativeMissionDispatch(unittest.TestCase):
    def test_completed_real_station_visit_signals_exact_native_cue_with_real_payload(self):
        v=NativeMissionVM();self.assertTrue(v.decode());self.assertEqual(len(v.requests),1)
        cue,payload=v.requests[0];self.assertIs(cue,v.mission_request)
        self.assertIs(payload['Sector'],v.station.sector);self.assertIs(payload['OfferObject'],v.station)
        self.assertTrue(v.vars['generated'])
    def test_unavailable_native_request_cue_preserves_other_earned_benefits(self):
        v=NativeMissionVM();v.mission_request.exists=False
        self.assertTrue(v.decode());self.assertEqual(v.requests,[]);self.assertFalse(v.vars['generated'])
        self.assertTrue(any(c[0]=='add_player_discount' for c in v.native_calls))
    def test_native_manager_disabled_prevents_request_without_blocking_survey(self):
        v=NativeMissionVM();v.gm_enabled=False
        self.assertTrue(v.decode());self.assertEqual(v.requests,[]);self.assertFalse(v.vars['generated'])
    def test_same_station_cooldown_prevents_duplicate_native_generation(self):
        v=NativeMissionVM();self.assertTrue(v.decode());v.state['vgo_leak_work'].pop('accepted')
        self.assertFalse(v.decode());self.assertEqual(len(v.requests),1)
        self.assertFalse(list(SURVEY.iter('accept_offer')));self.assertFalse(list(SURVEY.iter('reward_player')))


if __name__=='__main__':unittest.main(verbosity=2)
