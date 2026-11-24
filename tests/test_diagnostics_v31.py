"""Regression: diagnostics must preserve bounded inspection proof, never raw source."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from deepthort_local.diagnostic_evidence import (
    summarize_x4_report, summarize_inventory, matches_project,
    save_snapshot, read_snapshot)
from deepthort_local.flight_recorder import export_diagnostics

class DiagnosticsEvidenceTests(unittest.TestCase):
    def test_x4_candidate_proof_is_exportable_and_limited(self):
        report = {
            'game_dir': r'D:\\SteamLibrary\\steamapps\\common\\X4 Foundations',
            'reference_dir': r'D:\\deepthort\\reference\\x4',
            'catalogs':['01.cat','02.cat'], 'ready_for_planning': True,
            'pe_macro_verified':True,'pe_component_verified':True,
            'pe_component_connections':[{'name':'connection_weapon01','tags':'weapon medium'}],
            'ship_candidates':[{'file':'assets/units/size_m/macros/ship_pe.xml',
                                'identifiers':['ship_xen_m_corvette_02_a_macro'],
                                'sha256':'a'*64}],
            'weapon_candidates':[{'file':'weapon.xml','identifiers':['medium_weapon_macro'],
                                  'sha256':'b'*64}],
            'turret_candidates':[{'file':'turret.xml','identifiers':['medium_turret_macro'],
                                  'sha256':'c'*64}],
            'storage_candidates':[], 'blocked_reasons':[],
            'catalog_index_hints':['UNTRUSTED RAW PRIVATE FILE TEXT'],
        }
        item=summarize_x4_report(report,project_dir=r'D:\\x4mods\\vardath_pe')
        self.assertTrue(item['ready_for_planning'])
        self.assertTrue(item['pe_component_verified'])
        self.assertEqual(item['paired_catalog_count'],2)
        self.assertEqual(item['candidate_evidence']['ship_candidates'][0]['identifiers'][0],
                         'ship_xen_m_corvette_02_a_macro')
        txt=json.dumps(item)
        self.assertNotIn('UNTRUSTED RAW PRIVATE FILE TEXT',txt)
        self.assertNotIn('SteamLibrary',txt)
        self.assertNotIn('D:\\x4mods',txt)
        self.assertTrue(matches_project(item,r'D:\\x4mods\\vardath_pe'))
        self.assertFalse(matches_project(item,r'D:\\x4mods\\other_mod'))

    def test_uninspected_never_claims_evidence(self):
        item=summarize_x4_report(None,game_dir=r'D:\\Steam\\X4 Foundations',
                                 project_dir=r'D:\\x4mods\\faction')
        self.assertFalse(item['inspected'])
        self.assertNotIn('ready_for_planning',item)

    def test_inventory_preserves_engine_readiness_not_private_paths(self):
        data={'hostname':'MY_PRIVATE_PC','project_folder':r'D:\\x4mods\\test_ship',
              'tools':[{'name':'Godot','found':True},{'name':'XRCatTool','found':False}],
              'drives':[{'path':'D:'}],
              'engine_preflight':{'engine':'x4_extension','static_issues':2,
                  'static_pending':3,'static_clean':False,
                  'tools':{'game':r'D:\\Steam\\X4 Foundations','extracted_reference':''},
                  'missing_prerequisites':['Extracted XML unavailable'],
                  'x4_reference_links':{'resolved_vanilla_count':7,'unresolved_count':5,
                                       'vanilla_index_available':{'macro':True}}}}
        item=summarize_inventory(data)
        self.assertEqual(item['tools_detected'],1)
        self.assertEqual(item['engine_preflight']['engine'],'x4_extension')
        self.assertEqual(item['engine_preflight']['x4_reference_links']['resolved_vanilla_count'],7)
        self.assertFalse(item['engine_preflight']['tool_presence']['extracted_reference'])
        serialized=json.dumps(item)
        self.assertNotIn('MY_PRIVATE_PC',serialized)
        self.assertNotIn('D:\\Steam',serialized)
        self.assertTrue(matches_project(item,r'D:\\x4mods\\test_ship'))

    def test_saved_snapshot_survives_restart_without_raw_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/'state'/'last-x4-inspection.json'
            entry=summarize_x4_report({'game_dir':r'D:\\Games\\X4 Foundations',
                'reference_dir':'','catalogs':[],'pe_macro_verified':False,
                'pe_component_verified':False,'ready_for_planning':False,
                'blocked_reasons':['Vanilla XML not extracted.']},project_dir=r'D:\\x4mods\\mod')
            self.assertTrue(save_snapshot(f,entry))
            self.assertEqual(read_snapshot(f),entry)
            self.assertTrue(matches_project(read_snapshot(f),r'D:\\x4mods\\mod'))
            f.write_text('{broken',encoding='utf-8')
            self.assertIsNone(read_snapshot(f))

    def test_summary_zip_includes_new_evidence_without_raw_documents(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);state=root/'state';state.mkdir()
            snapshot=summarize_x4_report({'game_dir':r'D:\\Games\\X4 Foundations',
                    'reference_dir':'','catalogs':[],'blocked_reasons':['Missing references'],
                    'ready_for_planning':False}, project_dir=r'D:\\x4mods\\test')
            zip_path=export_diagnostics(state,root/'diag.zip',app_root=root,app_state={
                'x4_source_inspection':snapshot,'engine_readiness_scan':summarize_inventory(None)})
            with zipfile.ZipFile(zip_path) as z:
                summary=json.loads(z.read('summary.json'))
                self.assertFalse(summary['application_state']['x4_source_inspection']['ready_for_planning'])
                self.assertFalse(summary['application_state']['engine_readiness_scan']['scanned'])
                self.assertNotIn('D:\\Games',z.read('summary.json').decode())

if __name__=='__main__':unittest.main()
