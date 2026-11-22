"""v27 conservative semantic reconciliation and verified-source interface evidence."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.agent_plan import PlanError
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.job_queue import JobStore
from deepthort_local.requirements_intelligence import requirement_candidates
from deepthort_local.semantic_reconciliation import (
    explicit_constraints, reconcile_explicit_requirements,
    acceptance_candidates, audit_python_interfaces)
from deepthort_local.specification_library import SpecificationIndex


def candidates(text):
    return requirement_candidates(text, [(0,0,len(text),'','','')])


class ExplicitRequirementTests(unittest.TestCase):
    def test_opposing_musts_detected_with_exact_anchors(self):
        text='- The ship must support cargo docking.\n- The ship must not support cargo docking.\n'
        result=reconcile_explicit_requirements(text,candidates(text))
        self.assertEqual(result['blocking_conflicts'][0]['kind'],'opposing_explicit_obligations')
        for side in ('left','right'):
            marker=result['blocking_conflicts'][0][side]
            self.assertEqual(marker['source'],text[marker['start_char']:marker['end_char']])

    def test_shall_and_must_conflict(self):
        t='1. The program shall allow local saves.\n2. The program must not allow local saves.\n'
        self.assertEqual(len(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts']),1)

    def test_should_does_not_override_must(self):
        t='- The program should allow local saves.\n- The program must not allow local saves.\n'
        self.assertEqual(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts'],[])

    def test_subtle_different_actions_not_guessed_equivalent(self):
        t='- The fleet must accept cargo loads.\n- The fleet must not receive cargo.\n'
        self.assertFalse(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts'])

    def test_conditional_exception_is_not_automatically_called_conflict(self):
        t='- The ship must allow boarding.\n- The ship must not allow boarding unless authorized.\n'
        self.assertFalse(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts'])

    def test_numeric_impossible_range_blocks(self):
        t='- Stations must support at least 100 docking bays.\n- Stations must support at most 50 docking bays.\n'
        conflicts=reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts']
        self.assertEqual(conflicts[0]['kind'],'incompatible_numeric_bounds')

    def test_numeric_non_conflicting_range_is_valid(self):
        t='- Stations must support at least 10 docking bays.\n- Stations must support at most 50 docking bays.\n'
        self.assertFalse(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts'])

    def test_numerical_different_measurements_not_compared(self):
        t='- Stations must support at least 100 docking bays.\n- Stations must support at most 50 cargo drones.\n'
        self.assertFalse(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts'])

    def test_exact_numeric_difference_fails(self):
        t='- Stations must have exactly 20 repair drones.\n- Stations must have exactly 40 repair drones.\n'
        self.assertEqual(len(reconcile_explicit_requirements(t,candidates(t))['blocking_conflicts']),1)

    def test_candidates_stay_unverified_and_verbatim(self):
        t='Opening prose.\n- Player ships must permit docking.\n- Keep stylistic tone consistent.\n'
        answer=acceptance_candidates(t,candidates(t))
        self.assertEqual(answer['count'],1)
        self.assertEqual(answer['criteria'][0]['criterion'],'Player ships must permit docking.')
        self.assertEqual(answer['criteria'][0]['verification_state'],'unverified')
        self.assertFalse(answer['all_verified'])


class InterfaceAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'src').mkdir()
        self.steps=[{'path':'src/provider.py','description':'exports API'},
                    {'path':'src/consumer.py','description':'imports API'}]

    def test_valid_local_import_is_checked_without_importing_modules(self):
        (self.root/'src/provider.py').write_text('def calculate(x):\n    return x+1\n')
        (self.root/'src/consumer.py').write_text('from src.provider import calculate\n')
        audit=audit_python_interfaces(self.root,self.steps)
        self.assertEqual(audit['checked_local_imports'],1)
        self.assertEqual(audit['issues'],[])

    def test_broken_export_is_reported(self):
        (self.root/'src/provider.py').write_text('def something_else(): pass\n')
        (self.root/'src/consumer.py').write_text('from src.provider import calculate\n')
        issues=audit_python_interfaces(self.root,self.steps)['issues']
        self.assertEqual(issues[0]['kind'],'missing_local_export')
        self.assertEqual(issues[0]['symbol'],'calculate')

    def test_relative_import_supported(self):
        (self.root/'src/provider.py').write_text('class Engine: pass\n')
        (self.root/'src/consumer.py').write_text('from .provider import Engine\n')
        audit=audit_python_interfaces(self.root,self.steps)
        self.assertEqual(audit['issues'],[])
        self.assertEqual(audit['checked_local_imports'],1)

    def test_pending_source_is_not_reported_as_verified(self):
        audit=audit_python_interfaces(self.root,self.steps)
        self.assertEqual(len(audit['pending_files']),2)
        self.assertEqual(audit['parsed_files'],0)

    def test_syntax_error_found_without_execution(self):
        (self.root/'src/provider.py').write_text('def no(:\n')
        issues=audit_python_interfaces(self.root,self.steps)['issues']
        self.assertEqual(issues[0]['kind'],'source_parse_error')

    def test_external_import_not_claimed_checked(self):
        (self.root/'src/consumer.py').write_text('from nonexistent_dependency import wont_exist\n')
        audit=audit_python_interfaces(self.root,self.steps)
        self.assertEqual(audit['checked_local_imports'],0)
        self.assertEqual(audit['issues'],[])

    def test_path_escape_is_blocked(self):
        with self.assertRaises((ValueError, OSError)):
            audit_python_interfaces(self.root,[{'path':'../outside.py','description':'unsafe'}])

    def test_symlink_escape_is_blocked(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside)/'secret.py').write_text('SECRET=True\n')
            (self.root/'src/provider.py').symlink_to(Path(outside)/'secret.py')
            with self.assertRaises(ValueError):
                audit_python_interfaces(self.root,self.steps)


class RoadmapSemanticTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'p';self.project.mkdir()
        self.idx=SpecificationIndex(self.root/'spec.db')
        self.road=HierarchicalPlanStore(self.root/'road.db')
        self.id=12

    def _plan(self, original):
        self.idx.index(self.id,original)
        n=0
        while (r:=self.idx.next_section(self.id,original)) is not None:
            self.idx.save_response(self.id,original,r['ordinal'],json.dumps({'files':[
                {'path':f'code/part{n}.py','description':f'Implement part {n}'}]}),project=self.project)
            n+=1
        return self.road.prepare(self.idx,self.id,original,self.project,chat_id='chat')

    def test_conflict_blocks_roadmap_and_job_creation(self):
        original='- Modules must allow external updates.\n'+('a'*3100)+'\n- Modules must not allow external updates.\n'
        self.idx.index(self.id,original)
        count=0
        while (r:=self.idx.next_section(self.id,original)) is not None:
            self.idx.save_response(self.id,original,r['ordinal'],json.dumps({'files':[
                {'path':f'code/m{count}.py','description':f'Implement {count}'}]}),project=self.project)
            count+=1
        with self.assertRaisesRegex(PlanError,'conflicting explicit requirements'):
            self.road.prepare(self.idx,self.id,original,self.project,chat_id='chat')
        self.assertIsNone(JobStore(self.root/'jobs.db').next_any_queued())

    def test_semantic_and_interface_reports_survive_restart(self):
        original='- The program must provide local status.\n'+'x'*3010+'\n'
        progress=self._plan(original)
        self.assertFalse(progress['acceptance_confirmed'])
        new=HierarchicalPlanStore(self.root/'road.db')
        report=new.semantic_report(self.idx,self.id,original)
        self.assertEqual(report['acceptance']['count'],1)
        self.assertEqual(report['acceptance']['criteria'][0]['verification_state'],'unverified')
        self.assertEqual(new.interface_report(self.idx,self.id,original)['planned_python_files'],1)

    def test_changed_requirement_is_rejected(self):
        original='- The system must retain original user text.\n'+'x'*3010+'\n'
        self._plan(original)
        with self.assertRaises((ValueError, PlanError)):
            self.road.semantic_report(self.idx,self.id,original+' altered')


if __name__ == '__main__': unittest.main()

class ExecutableVerificationGates(unittest.TestCase):
    def test_broken_real_import_blocks_verified_milestone_until_repaired(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'game';(project/'src').mkdir(parents=True)
            request='- The program must provide a testable API.\n'+'x'*2800
            idx=SpecificationIndex(root/'spec.sqlite3');idx.index(33,request)
            idx.save_response(33,request,0,json.dumps({'files':[
                {'path':'src/provider.py','description':'Provide the API'},
                {'path':'src/consumer.py','description':'Consume the API; depends-on: src/provider.py'}]}),project=project)
            roadmap=HierarchicalPlanStore(root/'road.sqlite3')
            roadmap.prepare(idx,33,request,project,chat_id='test',max_files=2)
            entry=roadmap.milestone(idx,33,request,1)
            jobs=JobStore(root/'jobs.sqlite3')
            number=jobs.submit_approved_milestone_build(entry['project'],entry['chat_id'],
                entry['scope_prompt'],entry['steps'],entry['approval_key'],
                master_prompt=request,master_steps=entry['master_steps'])
            roadmap.link_job(idx,33,request,1,number)
            (project/'src/provider.py').write_text('def other(): pass\n')
            (project/'src/consumer.py').write_text('from src.provider import expected\n')
            for step in jobs.steps(number):jobs.set_step(step['id'],'saved')
            jobs.change(number,'complete','Verified: test command exited 0 (reported)',allowed=('queued',))
            state=roadmap.reconcile_jobs(idx,33,request,jobs)
            self.assertEqual(state['milestones_verified'],0)
            self.assertIn('static Python interface error',state['blocked_reason'])
            (project/'src/provider.py').write_text('def expected(): return True\n')
            # An edit must NOT redeem an old successful test. User has to
            # explicitly approve a new test after repairing the actual file.
            state=roadmap.reconcile_jobs(idx,33,request,jobs)
            self.assertEqual(state['milestones_verified'],0)
            self.assertEqual(jobs.get(number)['state'],'waiting_verification')
            self.assertTrue(jobs.change(number,'running','Rerunning user-approved build check',
                                        allowed=('waiting_verification',)))
            from deepthort_local.semantic_reconciliation import capture_verified_sources
            snapshot=capture_verified_sources(project,entry['steps'])
            self.assertTrue(jobs.change(number,'complete',
                'Verified: test command exited 0 (approved retest)',
                result=json.dumps(snapshot),allowed=('running',)))
            state=roadmap.reconcile_jobs(idx,33,request,jobs)
            self.assertEqual(state['milestones_verified'],1)
            self.assertFalse(state['acceptance_confirmed'])

class SourceFingerprintTests(unittest.TestCase):
    def test_verified_snapshot_invalidated_by_edits_and_deletions(self):
        from deepthort_local.semantic_reconciliation import (capture_verified_sources,
            verified_sources_current)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); (p/'source.py').write_text('def original(): return 1\n')
            steps=[{'path':'source.py','description':'Tested file'}]
            snapshot=capture_verified_sources(p,steps)
            self.assertTrue(verified_sources_current(p,steps,snapshot))
            (p/'source.py').write_text('def original(): return 2\n')
            self.assertFalse(verified_sources_current(p,steps,snapshot))
            snapshot=capture_verified_sources(p,steps)
            (p/'source.py').unlink()
            self.assertFalse(verified_sources_current(p,steps,snapshot))

    def test_invalid_and_misleading_evidence_is_not_current(self):
        from deepthort_local.semantic_reconciliation import (capture_verified_sources,
            verified_sources_current)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); (p/'a.py').write_text('a=1\n')
            steps=[{'path':'a.py','description':'Saved'}]
            real=capture_verified_sources(p,steps)
            fake=dict(real,sha256='0'*64)
            self.assertFalse(verified_sources_current(p,steps,fake))
            self.assertFalse(verified_sources_current(p,steps,{'result':'passed'}))

    def test_unsaved_steps_cannot_generate_successful_snapshot(self):
        from deepthort_local.semantic_reconciliation import capture_verified_sources
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                capture_verified_sources(td,[{'path':'not_saved.py','description':'No source'}])

class ExplicitRequirementDependencyTests(unittest.TestCase):
    def test_persisted_source_labels_produce_exact_edges(self):
        from deepthort_local.semantic_reconciliation import declared_requirement_dependencies
        t=('REQ-1: Implement the simulation.\n'
           'REQ-2: Implement the UI; depends-on: REQ-1\n')
        edges=declared_requirement_dependencies(t,candidates(t))
        self.assertEqual([(e['requirement'],e['requires']) for e in edges],[('REQ-2','REQ-1')])

    def test_missing_source_requirement_is_rejected(self):
        from deepthort_local.semantic_reconciliation import declared_requirement_dependencies
        t='REQ-12: Build UI; depends-on: REQ-999\n'
        with self.assertRaisesRegex(PlanError,'unknown requirement'):
            declared_requirement_dependencies(t,candidates(t))

    def test_cycle_in_user_spec_is_not_silently_resolved(self):
        from deepthort_local.semantic_reconciliation import declared_requirement_dependencies
        t=('REQ-1: Implement simulation; depends-on: REQ-2\n'
           'REQ-2: Implement UI; depends-on: REQ-1\n')
        with self.assertRaisesRegex(PlanError,'cycle'):
            declared_requirement_dependencies(t,candidates(t))

    def test_duplicate_requirement_labels_are_rejected(self):
        from deepthort_local.semantic_reconciliation import declared_requirement_dependencies
        t='REQ-5: First requirement.\nREQ-5: Second requirement.\n'
        with self.assertRaisesRegex(PlanError,'Duplicate'):
            declared_requirement_dependencies(t,candidates(t))

    def test_unlabelled_prose_retained_without_invented_edges(self):
        from deepthort_local.semantic_reconciliation import declared_requirement_dependencies
        t='Game systems depend on each other and should work together.\n'
        self.assertEqual(declared_requirement_dependencies(t,candidates(t)),[])

class InspectCliTests(unittest.TestCase):
    def test_read_only_inspect_spec_exit_code_and_output(self):
        import io
        from contextlib import redirect_stdout
        from deepthort_local.semantic_reconciliation import main
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'spec.txt'
            p.write_text('- Ship must permit docking.\n- Ship must not permit docking.\n')
            out=io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(['requirements',str(p),'--limit','5']),2)
            report=json.loads(out.getvalue())
            self.assertEqual(len(report['blocking_conflicts']),1)
            self.assertFalse(report['acceptance']['all_verified'])

    def test_read_only_inspect_interfaces(self):
        import io
        from contextlib import redirect_stdout
        from deepthort_local.semantic_reconciliation import main
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'provider.py').write_text('def service(): return 1\n')
            (p/'consumer.py').write_text('from provider import service\n')
            (p/'plan.json').write_text(json.dumps({'files':[
                {'path':'provider.py','description':'Provide'},
                {'path':'consumer.py','description':'Consume'}]}))
            out=io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(['interfaces',str(p),str(p/'plan.json')]),0)
            self.assertEqual(json.loads(out.getvalue())['checked_local_imports'],1)
