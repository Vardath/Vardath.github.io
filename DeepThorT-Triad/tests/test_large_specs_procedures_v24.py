"""v24 large text persistence, exact scoped coverage, and real JANUS check evidence."""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from deepthort_local.specification_library import (
    MAX_STORED_REQUEST_CHARS, SpecificationIndex, generate_indexed_plan, sections, sha,
)
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.job_queue import JobStore
from deepthort_local.agent_plan import PlanError
from deepthort_local.capability_library import CapabilityLibrary
from deepthort_local.janus_engine import JanusStore


class FakeModel:
    def __init__(self):self.calls=[]
    def chat(self,session,prompt,max_tokens):
        self.calls.append((session,prompt,max_tokens))
        # Each distinct section proposes a model-authored relative file.
        index=int(session.rsplit('-spec-',1)[1].split('-')[0])
        return json.dumps({'files':[{'path':f'module_{index}.py',
                                     'description':f'Implement section {index} in a module'}]})


class LargeSpecificationV24(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project'
        self.project.mkdir()
        self.registry=ConversationStore(self.root/'state'/'conversations.sqlite3')
        self.index=SpecificationIndex(self.root/'state'/'specs.sqlite3')

    def test_exact_sections_cover_every_character_and_roundtrip(self):
        original=('Introduction to the application.\n\n'+'Source data X'*4000+'\nFinal instruction.')
        spans=sections(original)
        self.assertGreater(len(spans),3)
        self.assertEqual(''.join(original[a:b] for a,b in spans),original)
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        meta=self.index.index(ident,original)
        self.assertEqual(meta['characters'],len(original))
        self.assertEqual(meta['sections'],len(spans))
        self.assertEqual(meta['sha256'],sha(original))
        restored=SpecificationIndex(self.index.path)
        self.assertEqual(restored.status(ident,original),meta)
        self.assertEqual(restored.next_section(ident,original)['text'],original[slice(*spans[0])])

    def test_storage_limit_exceeds_old_250k_and_accepts_multi_million_characters(self):
        original='A whole specification for testing.\n' + ('Detailed feature requirement.\n'*110_000)
        self.assertGreater(len(original),2_000_000)
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        self.assertEqual(self.registry.get(ident)['prompt'],original)
        self.assertGreater(MAX_STORED_REQUEST_CHARS,len(original))
        jobs=JobStore(self.root/'state'/'jobs.sqlite3')
        job=jobs.submit(str(self.project),'chat1','plan',original)
        self.assertEqual(jobs.get(job)['prompt'],original)

    def test_model_receives_single_labelled_section_never_the_whole_spec(self):
        original=('Build a reference project with complete traceability.\n'*90)
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        self.index.index(ident,original)
        prompt=self.index.model_prompt(ident,original)
        self.assertIn('section 1/',prompt)
        self.assertIn('NOT the entire project',prompt)
        self.assertLessEqual(len(prompt),7500)
        self.assertNotEqual(prompt,original)

    def test_incomplete_review_remains_unapproved_and_resumes_across_restart(self):
        original='Build an offline Python document index.\n'+('The index must preserve every item.\n'*160)
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        model=FakeModel()
        with self.assertRaisesRegex(PlanError,'still require model inspection'):
            generate_indexed_plan(model,self.index,ident,'project-x',original,self.project,max_rounds=1)
        status=self.index.status(ident,original)
        self.assertEqual(status['reviewed'],1)
        self.assertGreater(status['pending'],0)
        again=SpecificationIndex(self.index.path)
        # Continue with the actual saved section progress, not from section 1.
        for _ in range(status['pending']):
            pending=again.next_section(ident,original)
            if pending is None:break
            response=json.dumps({'files':[{'path':f'module_{pending["ordinal"]}.py',
                                           'description':'Implement the source section'}]})
            again.save_response(ident,original,pending['ordinal'],response,project=self.project)
        self.assertEqual(again.status(ident,original)['pending'],0)
        answer,steps=generate_indexed_plan(model,again,ident,'project-x',original,self.project,max_rounds=1)
        self.assertEqual(len(model.calls),1)  # only the initial section required inference
        self.assertEqual(len(json.loads(answer)['files']),len(steps))

    def test_changed_source_cannot_reuse_old_index_or_model_outcomes(self):
        original='Original request. '*600
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        self.index.index(ident,original)
        with self.assertRaisesRegex(ValueError,'changed'):
            self.index.index(ident,original+'extra')
        with self.assertRaisesRegex(ValueError,'changed'):
            self.index.status(ident,original+'extra')

    def test_invalid_json_does_not_advance_review(self):
        original='Plan a small text parser.\n'*200
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        self.index.index(ident,original)
        row=self.index.next_section(ident,original)
        with self.assertRaises(PlanError):
            self.index.save_response(ident,original,row['ordinal'],'{"files":[',project=self.project)
        self.assertEqual(self.index.status(ident,original)['reviewed'],0)
        self.assertEqual(self.index.next_section(ident,original)['attempts'],1)

    def test_cancellation_preserves_all_completed_sections(self):
        original='Make an application.\n'*300
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        flag=[False]
        def cancel():
            if len(model.calls)>=1:flag[0]=True
            return flag[0]
        model=FakeModel()
        with self.assertRaisesRegex(PlanError,'stopped by user'):
            generate_indexed_plan(model,self.index,ident,'project-z',original,self.project,
                                  cancelled=cancel,max_rounds=3)
        self.assertEqual(self.index.status(ident,original)['reviewed'],0)
        # Caller must only mark completed sections after the cancellation gate.

    def test_model_proposals_not_hardcoded_and_conflicts_rejected(self):
        original=('First requirement for game.\n'*140)
        ident=self.registry.submit('chat1',str(self.project),'draft_plan',original)
        self.index.index(ident,original)
        for _ in range(2):
            row=self.index.next_section(ident,original)
            self.assertIsNotNone(row)
            response=json.dumps({'files':[{'path':'same.txt',
                 'description':f'Independent content for {row["ordinal"]}'}]})
            self.index.save_response(ident,original,row['ordinal'],response,project=self.project)
        with self.assertRaisesRegex(PlanError,'Conflicting'):
            self.index.merged_steps(ident,original)


class VerifiedWorkflowV24(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.library=CapabilityLibrary(self.root/'state'/'capabilities.sqlite3')
        self.janus=JanusStore(self.root/'state'/'janus.sqlite3')
        self.artifact=self.project/'content.xml'
        self.artifact.write_text('<root/>')
        self.procedure=self.library.add_candidate('x4','Build metadata','Validate X4 content.xml',
                      ['Write content XML','Run approved verification'])
        self.library.verify_artifact(self.procedure,self.project,'content.xml',check='xml')
        self.log=self.root/'state'/'action-1.log'
        self.log.write_text('PASS: checked exact project\n')

    def action(self,*,approved=True,kind='verification',status='succeeded',exit=0,cwd=None):
        ident=self.janus.add_approved_action(argv=['python','-m','unittest','discover'],cwd=cwd or self.project,
                    label='Python: unit tests',kind=kind,user_approved=approved)
        self.janus.update_action(ident,status,detail='Completed local check',
                                 returncode=exit,output_file=str(self.log))
        return ident

    def test_user_approved_successful_action_plus_current_artifact_can_verify(self):
        action=self.action()
        self.assertTrue(self.library.verify_workflow(self.procedure,self.project,self.janus.path,action))
        row=self.library.procedures()[0]
        self.assertEqual(row['status'],'verified_workflow')
        context=self.library.retrieval_context(self.project,'X4 Build metadata',max_chars=800)
        self.assertIn('user-approved verification exited 0',context)
        self.assertIn('not end-to-end game acceptance',context)

    def test_no_promotion_without_current_artifact(self):
        self.artifact.write_text('<changed/>')
        with self.assertRaisesRegex(ValueError,'changed'):
            self.library.verify_workflow(self.procedure,self.project,self.janus.path,self.action())
        self.assertEqual(self.library.procedures(),[])

    def test_failed_running_or_non_verification_actions_rejected(self):
        for status,exit,kind in [('failed',1,'verification'),('running',None,'verification'),
                                 ('succeeded',0,'tool')]:
            with self.subTest(status=status,kind=kind):
                ident=self.action(status=status,exit=exit,kind=kind)
                with self.assertRaises(ValueError):
                    self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)
        self.assertEqual(self.library.procedures()[0]['status'],'artifact_checked')

    def test_unrelated_successful_command_cannot_verify_workflow(self):
        ident=self.janus.add_approved_action(argv=['python','-V'],cwd=self.project,
                    label='Python version',kind='verification',user_approved=True)
        self.janus.update_action(ident,'succeeded',detail='Version found',returncode=0,output_file=str(self.log))
        with self.assertRaisesRegex(ValueError,'Unrelated successful commands'):
            self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)

    def test_cross_project_action_rejected(self):
        other=self.root/'other';other.mkdir()
        ident=self.action(cwd=other)
        with self.assertRaisesRegex(ValueError,'another workspace'):
            self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)

    def test_log_mutation_invalidates_verification(self):
        ident=self.action()
        self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)
        self.assertEqual(len(self.library.procedures()),1)
        self.log.write_text('Altered log\n')
        self.assertEqual(self.library.procedures(),[])

    def test_action_status_change_invalidates_verification(self):
        ident=self.action()
        self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)
        self.janus.update_action(ident,'failed',detail='Late failure',returncode=1)
        self.assertEqual(self.library.procedures(),[])

    def test_updated_candidate_cannot_keep_previous_workflow_promotion(self):
        ident=self.action()
        self.library.verify_workflow(self.procedure,self.project,self.janus.path,ident)
        self.library.add_candidate('x4','Build metadata','Updated unverified method',
                                   ['Check source references again'])
        self.assertEqual(self.library.procedures(),[])
        self.assertEqual(self.library.procedures(include_candidates=True)[0]['status'],'candidate')


if __name__=='__main__':unittest.main()

class ImportedSpecificationV24(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'full_specification.md'

    def test_import_preserves_multi_million_character_file_with_extra_instructions(self):
        from deepthort_local.large_input import imported_source, resolve_import
        body='Original documented section.\n'*80_000
        self.assertGreater(len(body),2_000_000)
        self.path.write_text(body,encoding='utf-8')
        item=imported_source(self.path)
        self.assertEqual(item['characters'],len(body))
        self.assertEqual(resolve_import(item),body)
        self.assertEqual(resolve_import(item,'Do not change the main menu'),
           body+'\n\nADDITIONAL USER INSTRUCTIONS (entered after importing):\nDo not change the main menu')

    def test_import_rejects_change_or_non_utf8_instead_of_silent_replacement(self):
        from deepthort_local.large_input import imported_source, resolve_import
        self.path.write_text('All original instructions remain.',encoding='utf-8')
        item=imported_source(self.path)
        self.path.write_text('Changed instructions.',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'changed'):
            resolve_import(item)
        self.path.write_bytes(b'\xff\xfe\xfd')
        with self.assertRaises(UnicodeDecodeError):
            imported_source(self.path)

    def test_import_rejects_unexpected_binary_file(self):
        from deepthort_local.large_input import imported_source
        image=Path(self.tmp.name)/'not_a_spec.exe'
        image.write_bytes(b'\0\0\1')
        with self.assertRaisesRegex(ValueError,'text formats'):
            imported_source(image)

class AutomaticReadOnlyTestObservationV24(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.project=self.root/'workspace';self.project.mkdir()
        self.library=CapabilityLibrary(self.root/'state'/'capabilities.sqlite3')
        self.janus=JanusStore(self.root/'state'/'janus.sqlite3')
        self.log=self.root/'state'/'action-1.log'
        self.log.write_text('unittest complete: 25 tests passed\n')

    def action(self,*,cwd=None,status='succeeded',exit_code=0):
        ident=self.janus.add_approved_action(
            argv=['python','-m','unittest','discover'],cwd=cwd or self.project,
            label='Python: unit tests',kind='verification',user_approved=True)
        self.janus.update_action(ident,status,detail='Verification finished',
                                 output_file=str(self.log),returncode=exit_code)
        return ident

    def test_completed_actions_are_observed_without_executing_any_tool(self):
        self.action()
        with patch('subprocess.Popen',side_effect=AssertionError('Library must not execute tests')):
            report=self.library.inspect_project(self.project)
        self.assertEqual(report['approved_test_actions_observed'],1)
        self.assertEqual(len(self.library.tool_evidence.current(self.project)),1)
        self.assertEqual(self.library.procedures(),[])  # no skill self-promotion
        evidence=self.library.retrieval_context(self.project,'Python unit tests',max_chars=1000)
        self.assertIn('Approved JANUS check',evidence)
        self.assertIn('no claim of overall project correctness',evidence)

    def test_log_change_invalidates_observed_outcome(self):
        self.action();self.library.inspect_project(self.project)
        self.log.write_text('Edited result after the check\n')
        self.assertEqual(self.library.tool_evidence.current(self.project),[])

    def test_unrelated_project_and_running_actions_are_not_imported(self):
        other=self.root/'other';other.mkdir()
        self.action(cwd=other)
        self.action(status='running',exit_code=None)
        self.assertEqual(self.library.inspect_project(self.project)['approved_test_actions_observed'],0)
        self.assertEqual(self.library.tool_evidence.current(self.project),[])

    def test_failed_action_is_diagnostic_evidence_not_verified_skill(self):
        self.action(status='failed',exit_code=1)
        self.library.inspect_project(self.project)
        rows=self.library.tool_evidence.current(self.project)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['observed_status'],'failed')
        self.assertEqual(self.library.procedures(),[])
