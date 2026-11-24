"""v25 exact-source hierarchical roadmaps, stage approvals, and verified gating."""
from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from deepthort_local.agent_plan import PlanError
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.job_queue import JobStore
from deepthort_local.specification_library import SpecificationIndex, generate_indexed_plan


class RoadmapCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'game'
        self.project.mkdir()
        self.index = SpecificationIndex(self.root / 'spec.sqlite3')
        self.hierarchy = HierarchicalPlanStore(self.root / 'hierarchy.sqlite3')
        self.jobs = JobStore(self.root / 'jobs.sqlite3')
        self.chat = 'my-chat'
        self.req = 17
        # Four exact, individually recognizable source sections.
        self.original = ''.join(f'Work package {i}. Build a small verified software component. '
                                + 'Requirement detail '+str(i)+' ' * 3015+'\n'
                                for i in range(1,5))
        self.index.index(self.req,self.original)

    def _populate(self, specs=None):
        specs=specs or [[{'path':f'src/module{i}.py','description':f'Implement module {i} with tests'}]
                        for i in range(1,5)]
        for set_of_steps in specs:
            row=self.index.next_section(self.req,self.original)
            self.assertIsNotNone(row)
            self.index.save_response(self.req,self.original,row['ordinal'],
                json.dumps({'files':set_of_steps}),project=self.project)
        self.assertIsNone(self.index.next_section(self.req,self.original))

    def _roadmap(self,steps=None,max_files=2):
        self._populate(steps)
        return self.hierarchy.prepare(self.index,self.req,self.original,
                                      self.project,chat_id=self.chat,max_files=max_files)

    def _approve_first(self):
        milestone=self.hierarchy.milestone(self.index,self.req,self.original,1)
        job=self.jobs.submit_approved_milestone_build(
            milestone['project'],milestone['chat_id'],milestone['scope_prompt'],
            milestone['steps'],milestone['approval_key'],master_prompt=self.original,
            master_steps=milestone['master_steps'])
        self.hierarchy.link_job(self.index,self.req,self.original,1,job)
        return job

    def _verify(self,job):
        for step in self.jobs.steps(job):
            self.jobs.set_step(step['id'],'saved','Code saved, not yet tested')
        self.jobs.change(job,'running','Generating',allowed=('queued',))
        self.jobs.change(job,'complete','Verified: test command exited 0 (approved local check)',allowed=('running',))
        return self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)

    def test_split_into_bounded_stages(self):
        summary=self._roadmap(max_files=2)
        self.assertEqual(summary['milestones_total'],4)
        self.assertEqual(summary['sections_reviewed'],4)
        self.assertEqual(summary['next_approvable'],1)
        self.assertFalse(summary['complete'])
        self.assertEqual(len(self.hierarchy.milestone(self.index,self.req,self.original,1)['steps']),1)

    def test_every_original_section_is_traced(self):
        self._roadmap()
        links=self.hierarchy.coverage(self.index,self.req,self.original)
        self.assertEqual(set(x['section_ordinal'] for x in links),set(range(4)))
        self.assertEqual(set(x['path'] for x in links),{f'src/module{i}.py' for i in range(1,5)})

    def test_scoped_prompt_contains_unmodified_sections(self):
        self._roadmap()
        first=self.hierarchy.milestone(self.index,self.req,self.original,1)
        for i in first['source_sections']:
            rows=self.index._verified_rows(self.req,self.original)
            r=rows[i-1]
            self.assertIn(self.original[r[1]:r[2]],first['scope_prompt'])
        self.assertIn('Full original remains in local storage',first['scope_prompt'])
        self.assertLessEqual(len(first['scope_prompt']),6500)

    def test_milestones_cannot_advance_without_approved_verification(self):
        self._roadmap()
        first=self._approve_first()
        current=self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)
        self.assertEqual(current['milestones_verified'],0)
        self.assertIsNone(current['next_approvable'])
        with self.assertRaises(PlanError):
            self.hierarchy.link_job(self.index,self.req,self.original,2,first)
        self.assertEqual(self._verify(first)['next_approvable'],2)

    def test_saving_files_does_not_verify(self):
        self._roadmap()
        job=self._approve_first()
        for s in self.jobs.steps(job):
            self.jobs.set_step(s['id'],'saved')
        self.jobs.change(job,'running','Generating',allowed=('queued',))
        self.jobs.change(job,'waiting_verification','Saved files not verified',allowed=('running',))
        summary=self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)
        self.assertEqual(summary['milestones_verified'],0)
        self.assertIsNone(summary['next_approvable'])

    def test_unapproved_or_failed_result_never_verifies(self):
        self._roadmap()
        job=self._approve_first()
        self.jobs.change(job,'running','Generating',allowed=('queued',))
        self.jobs.change(job,'needs_input','Build test failed with exit 1',allowed=('running',))
        self.assertEqual(self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)['milestones_verified'],0)

    def test_incomplete_stage_files_do_not_verify_even_with_complete_status(self):
        self._roadmap()
        job=self._approve_first()
        self.jobs.change(job,'complete','Verified: test command exited 0 (test)',allowed=('queued',))
        self.assertEqual(self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)['milestones_verified'],0)

    def test_verification_of_each_stage_finishes_roadmap(self):
        self._roadmap()
        first=self._approve_first()
        self._verify(first)
        for ordinal in range(2,5):
            next_stage=self.hierarchy.milestone(self.index,self.req,self.original,ordinal)
            job=self.jobs.submit_approved_milestone_build(
                next_stage['project'],next_stage['chat_id'],next_stage['scope_prompt'],
                next_stage['steps'],next_stage['approval_key'],master_prompt=self.original,
                master_steps=next_stage['master_steps'])
            self.hierarchy.link_job(self.index,self.req,self.original,ordinal,job)
            result=self._verify(job)
        self.assertTrue(result['complete'])
        self.assertEqual(result['milestones_verified'],4)

    def test_recover_roadmap_and_approval_after_restart(self):
        self._roadmap()
        job=self._approve_first()
        new=HierarchicalPlanStore(self.root/'hierarchy.sqlite3')
        self.assertIsNone(new.status(self.index,self.req,self.original)['next_approvable'])
        self.assertEqual(new.milestone(self.index,self.req,self.original,1)['job_id'],job)
        self.assertEqual(new.latest_for_chat(self.chat,self.project),self.req)

    def test_replay_is_idempotent(self):
        one=self._roadmap()
        two=self.hierarchy.prepare(self.index,self.req,self.original,self.project,chat_id=self.chat)
        self.assertEqual(one['milestones_total'],4)
        self.assertEqual(two['milestones_total'],4)  # existing milestone grouping preserved
        self.assertEqual(self.hierarchy.milestone(self.index,self.req,self.original,1)['ordinal'],1)
        first=self._approve_first()
        m=self.hierarchy.milestone(self.index,self.req,self.original,1)
        retry=self.jobs.submit_approved_milestone_build(
            m['project'],m['chat_id'],m['scope_prompt'],m['steps'],m['approval_key'],
            master_prompt=self.original,master_steps=m['master_steps'])
        self.assertEqual(first,retry)
        self.hierarchy.link_job(self.index,self.req,self.original,1,retry)

    def test_modified_source_invalidates_roadmap(self):
        self._roadmap()
        with self.assertRaises((PlanError,ValueError)):
            self.hierarchy.status(self.index,self.req,self.original+'CHANGED')

    def test_tampered_requirement_trace_is_rejected(self):
        self._roadmap()
        with closing(sqlite3.connect(self.hierarchy.path)) as db, db:
            db.execute('DELETE FROM hierarchy_trace WHERE request_id=? AND section_ordinal=0',(self.req,))
        with self.assertRaisesRegex(PlanError,'trace'):
            self.hierarchy.status(self.index,self.req,self.original)

    def test_conflicting_repeated_file_blocks_approval(self):
        steps=[[{'path':'src/common.py','description':f'Contradictory semantics {i}'}]
               for i in range(1,5)]
        self._populate(steps)
        with self.assertRaisesRegex(PlanError,'Conflicting'):
            self.hierarchy.prepare(self.index,self.req,self.original,self.project,chat_id=self.chat)

    def test_shared_file_with_too_many_requirements_blocks_approval(self):
        same={'path':'src/common.py','description':'Provide shared implementation for every requirement'}
        self._populate([[same] for _ in range(4)])
        with self.assertRaisesRegex(PlanError,'reconcile or split'):
            self.hierarchy.prepare(self.index,self.req,self.original,
                                   self.project,chat_id=self.chat)

    def test_approval_must_reference_correct_master_step(self):
        self._roadmap()
        m=self.hierarchy.milestone(self.index,self.req,self.original,1)
        with self.assertRaisesRegex(ValueError,'does not belong'):
            self.jobs.submit_approved_milestone_build(m['project'],m['chat_id'],
                m['scope_prompt'],[{'path':'evil.py','description':'Wrong file'}],
                m['approval_key'],master_prompt=self.original,master_steps=m['master_steps'])

    def test_repeated_key_with_different_scope_rejected(self):
        self._roadmap()
        m=self.hierarchy.milestone(self.index,self.req,self.original,1)
        self._approve_first()
        with self.assertRaisesRegex(ValueError,'different milestone'):
            self.jobs.submit_approved_milestone_build(m['project'],m['chat_id'],
                m['scope_prompt']+'Alteration',m['steps'],m['approval_key'],
                master_prompt=self.original,master_steps=m['master_steps'])

    def test_no_unapproved_work_on_generate_indexed_plan(self):
        # Responses are authored by a scripted model, never canned fallback files.
        model=Mock()
        model.completed_exchange=None
        model.chat.side_effect=[json.dumps({'files':[{'path':f'src/module{i}.py',
                         'description':f'Implement module {i} with tests'}]}) for i in range(1,5)]
        response,steps=generate_indexed_plan(model,self.index,self.req,'s',self.original,
                            self.project,max_rounds=40,hierarchy=self.hierarchy,chat_id=self.chat)
        self.assertEqual(steps,[])
        self.assertIn('hierarchy_ready',json.loads(response))
        self.assertIsNone(self.jobs.next_any_queued())
        self.assertEqual(model.chat.call_count,4)

    def test_no_stale_spurious_project_roadmap(self):
        self._roadmap()
        self.assertIsNone(self.hierarchy.latest_for_chat('other',self.project))
        self.assertIsNone(self.hierarchy.latest_for_chat(self.chat,self.root/'another'))

    def test_scope_rejects_overloaded_shared_file(self):
        self._populate([[{'path':'src/shared.py','description':'Implement both modules with tests'}]]*4)
        with self.assertRaisesRegex(PlanError,'reconcile or split'):
            self.hierarchy.prepare(self.index,self.req,self.original,self.project,
                                   chat_id=self.chat,max_files=1)


    def test_invalid_hierarchy_job_cannot_forge_verification(self):
        self._roadmap()
        good=self.hierarchy.milestone(self.index,self.req,self.original,1)
        wrong=self.jobs.submit_approved_build(
            str(self.project),self.chat,'A separate general programming task',
            [{'path':'src/module1.py','description':'Implement module 1 with tests'}],
            'draft:44')
        # The caller must not attach arbitrary unrelated jobs as milestone proof.
        self.hierarchy.link_job(self.index,self.req,self.original,1,wrong)
        for step in self.jobs.steps(wrong):self.jobs.set_step(step['id'],'saved')
        self.jobs.change(wrong,'complete','Verified: test command exited 0 (test)',allowed=('queued',))
        progress=self.hierarchy.reconcile_jobs(self.index,self.req,self.original,self.jobs)
        self.assertEqual(progress['milestones_verified'],0)

    def test_batched_file_proposals_stay_below_24_file_executor_limit(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);project=p/'workspace';project.mkdir()
            original='Create a program using these design constraints: '+'x'*2800
            index=SpecificationIndex(p/'spec.sqlite3');index.index(1,original)
            rows=index._verified_rows(1,original)
            self.assertEqual(len(rows),1)
            proposed=[{'path':f'src/file_{n:02}.py','description':f'Implement module {n} with tests'}
                      for n in range(24)]
            index.save_response(1,original,0,json.dumps({'files':proposed}),project=project)
            store=HierarchicalPlanStore(p/'h.sqlite3')
            status=store.prepare(index,1,original,project,chat_id='chat',max_files=12)
            self.assertEqual(status['milestones_total'],2)
            self.assertEqual(len(store.milestone(index,1,original,1)['steps']),12)
            self.assertEqual(len(store.milestone(index,1,original,2)['steps']),12)

    def test_25_files_spanning_sections_no_longer_hit_single_plan_cap(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); project=p/'workspace';project.mkdir()
            original=''.join(f'Scope {i}: '+'a'*3100+'\n' for i in range(26))
            index=SpecificationIndex(p/'spec.sqlite3')
            index.index(1,original)
            total=index.status(1,original)['sections']
            self.assertGreater(total,24)
            model=Mock();model.completed_exchange=None
            model.chat.side_effect=[json.dumps({'files':[{'path':f'src/{i:03}.py',
                  'description':f'Implement system {i} and validate it'}]}) for i in range(total)]
            hierarchy=HierarchicalPlanStore(p/'h.sqlite3')
            answer,files=generate_indexed_plan(model,index,1,'session',original,project,
                max_rounds=40,hierarchy=hierarchy,chat_id='chat')
            roadmap=json.loads(answer)['hierarchy_ready']
            self.assertGreater(roadmap['milestones_total'],1)
            self.assertEqual(files,[])
            self.assertEqual(len(hierarchy.coverage(index,1,original)),total)
            self.assertTrue(all(len(hierarchy.milestone(index,1,original,i)['steps'])<=24
                           for i in range(1,roadmap['milestones_total']+1)))

    def test_model_description_changed_after_roadmap_is_rejected(self):
        self._roadmap()
        with closing(sqlite3.connect(self.index.path)) as db, db:
            db.execute('UPDATE specification_sections SET steps_json=? WHERE request_id=? AND ordinal=1',
                (json.dumps([{'path':'src/module2.py','description':'Rewritten unapproved intent'}]),self.req))
        with self.assertRaisesRegex(PlanError,'stale'):
            self.hierarchy.status(self.index,self.req,self.original)

    def test_approval_requires_aggregate_android_game_plan(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);project=p/'game';project.mkdir()
            original='Create an Android game for galaxy sector simulation and an interactive map UI. '+'x'*2700
            index=SpecificationIndex(p/'spec.sqlite3');index.index(1,original)
            index.save_response(1,original,0,json.dumps({'files':[
                {'path':'README.md','description':'Describe future features'}]}),project=project)
            h=HierarchicalPlanStore(p/'h.sqlite3')
            with self.assertRaisesRegex(PlanError,'Game plan is incomplete'):
                h.prepare(index,1,original,project,chat_id='chat')

    def test_no_stage_can_be_approved_from_a_different_chat(self):
        self._roadmap()
        with self.assertRaisesRegex(PlanError,'does not match'):
            self.hierarchy.prepare(self.index,self.req,self.original,self.project,chat_id='another')

    def test_faction_command_inspired_by_x4_is_android_game_not_x4_extension(self):
        from deepthort_local.agent_plan import project_kind,validate_project_plan
        request=('Build Faction Command as a complete Android game inspired by X4. '
                 'Include sector simulation, station management, a touch map UI, '
                 'Gradle build, deterministic tests and APK packaging.')
        self.assertEqual(project_kind(request),'android_game')
        files=[
            {'path':'app/src/main/AndroidManifest.xml','description':'Configure Android build and application lifecycle'},
            {'path':'app/src/main/java/world/Sectors.kt','description':'Implement galaxy sectors and economy simulation gameplay'},
            {'path':'app/src/main/java/world/MapScreen.kt','description':'Implement game touch map screen interface'},
            {'path':'app/src/test/java/world/SectorsTest.kt','description':'Implement deterministic automated acceptance tests'},
        ]
        self.assertEqual(validate_project_plan(files,request),files)

    def test_unsafe_model_path_rejected(self):
        unsafe=[[{'path':'../outside.py','description':'Write outside workspace'}]]*4
        with self.assertRaises(ValueError):
            self._populate(unsafe)


if __name__=='__main__':
    unittest.main()
