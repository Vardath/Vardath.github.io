"""v50: real shared-ONNX reasoning consultation + separately scoped game XML preview."""
import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.project_source_view import relevant_x4_sources,read_verified_x4_source
from deepthort_local.reasoning_council import ReasoningCouncil,limited_guidance
from deepthort_local.agent_plan import remaining_plan_gaps
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.specification_library import SpecificationIndex,generate_indexed_plan


def xml_ref(root,rel,text):
    path=root/rel;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,'utf-8')
    return {'file':rel,'sha256':hashlib.sha256(text.encode()).hexdigest(),'identifiers':['ship_xen_m_corvette_02_a_macro']}


class SourceSelection(unittest.TestCase):
    def test_selects_scanned_real_paths_not_fake_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rel='assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml'
            pe=xml_ref(root,rel,'<macros/>')
            comp=xml_ref(root,'assets/units/size_m/pe_component.xml','<components/>')
            turret=xml_ref(root,'assets/props/WeaponSystems/turret.xml','<macros/>')
            report={'reference_dir':str(root),'ship_candidates':[pe],
                    'pe_component_file':comp['file'],'pe_component_sha256':comp['sha256'],
                    'turret_candidates':[turret],
                    'weapon_candidates':[{'file':'../bad.xml','sha256':'0'*64},
                                         {'file':'no_hash.xml','sha256':''}]}
            visible=relevant_x4_sources(report)
            self.assertEqual(len(visible),3)
            self.assertEqual(visible[0]['file'],rel)
            self.assertIn('verified',visible[1]['role'])
            self.assertIn('<macros/>',read_verified_x4_source(visible[0]))
            (root/rel).write_text('<modified/>')
            with self.assertRaisesRegex(ValueError,'changed'):
                read_verified_x4_source(visible[0])

    def test_rejects_reference_symlink_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);external=root.parent/'v50_never_read.xml'
            path=root/'ref.xml'; path.write_text('<ok/>')
            item={'reference_dir':str(root),'file':'ref.xml',
                  'sha256':hashlib.sha256(b'<ok/>').hexdigest()}
            self.assertEqual(read_verified_x4_source(item),'<ok/>')
            self.assertEqual(path.read_text(),'<ok/>')
            with self.assertRaises(ValueError):
                read_verified_x4_source(dict(item,file='../ref.xml'))
            if os.name!='nt':
                path.unlink()
                path.symlink_to('/etc/passwd')
                with self.assertRaisesRegex(ValueError,'symlink'):
                    read_verified_x4_source(item)


class NeuralCouncil(unittest.TestCase):
    def test_two_neural_roles_persist_and_reuse_without_model_replay(self):
        class Model:
            def __init__(self):self.calls=[]
            def chat(self,session,prompt,*,max_tokens):
                self.calls.append((session,prompt,max_tokens))
                return ('JANUS: compare two XML approaches' if 'JANUS /' in prompt
                        else 'SENTINEL: reference not independently verified')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);model=Model();store=ReasoningCouncil(root/'state.sqlite3')
            kwargs=dict(session='task',original='Create an X4 PE mod',project=root,
                        gaps=['PE macro compatibility'],saved_steps=[],source_section='use vanilla PE',
                        inspected_evidence='PE macro verified: sha abc')
            first=store.deliberate(model,**kwargs)
            self.assertEqual(len(model.calls),2)
            self.assertFalse(first['verified'])
            self.assertIn('JANUS',limited_guidance(first))
            second=ReasoningCouncil(root/'state.sqlite3').deliberate(model,**kwargs)
            self.assertEqual(first,second)
            self.assertEqual(len(model.calls),2)
            changed=store.deliberate(model,**dict(kwargs,source_section='different source'))
            self.assertNotEqual(changed['evidence_sha'],first['evidence_sha'])
            self.assertEqual(len(model.calls),4)

    def test_indexed_x4_stall_invokes_two_roles_then_verifies_model_revision(self):
        class Model:
            def __init__(self):self.calls=[]
            def chat(self,session,prompt,*,max_tokens):
                self.calls.append((session,prompt,max_tokens))
                if prompt.startswith('JANUS: translate the original requirement'):
                    return 'Plan an independent PE variant and MD respawn; verify exact vanilla equipment connections before build.'
                if prompt.startswith('SENTINEL: independently inspect'):
                    return 'ACCEPT\nDo not claim ship slots verified without original component XML.'
                if 'JANUS RETRANSLATED NEXT TASK' in prompt:
                    return json.dumps({'files':[
                        {'path':'content.xml','description':'X4 extension metadata validated with installed vanilla PE game references'},
                        {'path':'md/pe_spawn.xml','description':'Mission Director PE player-owned ship respawn and preservation of equipment'},
                        {'path':'libraries/ship.xml','description':'X4 PE ship source macro equipment connections, cargo storage, speed handling, forward weapons and turrets'}]})
                return 'not json'
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'x4mods';project.mkdir()
            original=('Build a Xenon PE ship X4 mod preserving vanilla source references, '
                      'speed, storage and forward weapons, turrets, player-owned respawn.\n')*75
            index=SpecificationIndex(root/'specification_index.sqlite3')
            hierarchy=HierarchicalPlanStore(root/'plans.sqlite3')
            index.index(5,original)
            while (row:=index.next_section(5,original)) is not None:
                index.save_response(5,original,row['ordinal'],json.dumps({'files':[
                    {'path':f'docs/note-{row["ordinal"]}.txt','description':'Partial missing X4 roadmap note'}]}),
                    project=project)
            model=Model()
            answer,steps=generate_indexed_plan(
                model,index,5,'session',original,project,chat_id='chat',hierarchy=hierarchy,
                max_rounds=7,neural_council=True,inspected_evidence='Verified PE macro source')
            self.assertEqual(steps,[])
            self.assertIn('hierarchy_ready',json.loads(answer))
            self.assertEqual(len(model.calls),6)  # 3 corrections, 2 neural turns, 1 correction
            self.assertIn('SENTINEL',model.calls[-1][1])
            self.assertFalse(remaining_plan_gaps(index.merged_steps(5,original),original))
            self.assertTrue((root/'reasoning-council-v50.sqlite3').exists())
            self.assertTrue((root/'janus.sqlite3').exists())
            self.assertTrue((root/'sentinel.sqlite3').exists())
            self.assertFalse((project/'content.xml').exists())  # No build approval


class X4ReferenceGUI(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Needs Tk display')
    def test_discovered_source_readonly_and_excluded_without_touching_game(self):
        import desktop_app as desktop
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'my-project';project.mkdir()
            game=root/'extracted';game.mkdir()
            entry=xml_ref(game,'assets/units/size_m/macros/ship_xen_m_corvette_02_a_macro.xml','<macros/>')
            with patch.object(desktop,'STATE',root/'state'),\
                patch.object(desktop.DeepThorTDesktop,'_refresh_inventory',lambda self:None),\
                patch.object(desktop.messagebox,'showerror'):
                app=desktop.DeepThorTDesktop()
                try:
                    app._set_project(project)
                    app.x4_report={'reference_dir':str(game),'ship_candidates':[entry]}
                    app._x4_report_project=str(project.resolve())
                    app._render_project_files()
                    ref_rows=[(k,v) for k,v in app._file_rows.items() if v[0]=='x4_reference']
                    self.assertEqual(len(ref_rows),1)
                    ref_row,(_,ref_item)=ref_rows[0]
                    app.files.selection_set(ref_row)
                    app._on_file()
                    self.assertIsNone(app.current_file)  # Cannot queue a vanilla XML edit
                    self.assertIn('Read-only X4 source',app.file_title.get())
                    app._hide_x4_reference(ref_item)
                    self.assertEqual([v for v in app._file_rows.values() if v[0]=='x4_reference'],[])
                    self.assertEqual((game/entry['file']).read_text(),'<macros/>')
                    self.assertFalse((project/entry['file']).exists())
                finally:
                    app._quit()


if __name__=='__main__':unittest.main()
