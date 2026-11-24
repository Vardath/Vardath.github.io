"""v28: explicit source contracts, test traceability, and actual process evidence."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.acceptance_contracts import (
    explicit_requirement_labels, model_contracts, inspect_model_contracts,
    source_ambiguities)
from deepthort_local.agent_plan import PlanError
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.job_queue import JobStore
from deepthort_local.requirements_intelligence import requirement_candidates
from deepthort_local.semantic_reconciliation import (
    capture_verified_sources, verified_sources_current)
from deepthort_local.specification_library import SpecificationIndex
from deepthort_local.verification_evidence import assess_verification, attach_verification


def reqs(text):
    return requirement_candidates(text, [(0,0,len(text),'','','')])


class ReadOnlyContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'src').mkdir()
        (self.root/'tests').mkdir()
        self.spec='REQ-1: Player navigation must work.\nREQ-2: Ship orders must be saved.\n'
        self.steps=[
            {'path':'src/api.py','description':'Exports ship orders; provides: save_orders'},
            {'path':'src/ui.py','description':'Uses ship orders; uses: src/api.py::save_orders'},
            {'path':'tests/test_api.py','description':'Tests the save API; verifies: REQ-2'},
        ]

    def test_declared_test_and_public_api_are_inspected_not_executed(self):
        (self.root/'src/api.py').write_text('def save_orders(): return True\n')
        (self.root/'src/ui.py').write_text('from src.api import save_orders\n')
        (self.root/'tests/test_api.py').write_text('def test_save_orders(): assert True\n')
        report=inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))
        self.assertEqual(report['issues'],[])
        self.assertEqual(report['model_declared_contracts'],3)
        self.assertEqual(report['unlinked_labelled_requirements'],['REQ-1'])
        self.assertIn('static_test_discovered',[r['state'] for r in report['checks']])
        self.assertFalse(report['acceptance_confirmed'])

    def test_missing_export_and_malformed_test_are_not_accepted(self):
        (self.root/'src/api.py').write_text('def not_save(): pass\n')
        (self.root/'src/ui.py').write_text('from src.api import save_orders\n')
        (self.root/'tests/test_api.py').write_text('"""Not a test."""\n')
        report=inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))
        kinds={r['state'] for r in report['issues']}
        self.assertIn('missing_declared_export',kinds)
        self.assertIn('missing_provider_export',kinds)
        self.assertIn('no_test_cases_found',kinds)

    def test_pending_model_proposals_not_misrepresented_as_passing(self):
        report=inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))
        self.assertEqual(report['issues'],[])
        self.assertTrue(all(c['state']=='pending_source' for c in report['checks']))

    def test_unknown_requirement_does_not_get_fabricated(self):
        self.steps[-1]['description']='Tests all requirements; verifies: REQ-3'
        with self.assertRaisesRegex(PlanError,'missing explicit requirement'):
            inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))

    def test_implementation_file_cannot_claim_test_coverage(self):
        self.steps[0]['description']='Claim verify; verifies: REQ-1'
        with self.assertRaisesRegex(PlanError,'not a test-file'):
            inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))

    def test_unknown_provider_and_missing_symbol(self):
        self.steps[1]['description']='uses: src/unknown.py::save_orders'
        with self.assertRaisesRegex(PlanError,'unknown local use'):
            inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))

    def test_duplicate_explicit_labels_blocked(self):
        spec='REQ-2: First.\nREQ-2: Second.\n'
        with self.assertRaisesRegex(PlanError,'Duplicate'):
            explicit_requirement_labels(spec,reqs(spec))

    def test_no_executable_script_triggered_by_source(self):
        (self.root/'src/api.py').write_text('raise RuntimeError("should never execute")\ndef save_orders(): pass\n')
        (self.root/'src/ui.py').write_text('from src.api import save_orders\n')
        (self.root/'tests/test_api.py').write_text('def test_stuff(): pass\n')
        result=inspect_model_contracts(self.root,self.steps,self.spec,reqs(self.spec))
        self.assertEqual(result['issues'],[])

    def test_nonblocking_ambiguity_is_anchored(self):
        text='REQ-1: Allow approximately 40 ships, perhaps more.\n'
        flagged=source_ambiguities(text,reqs(text))
        self.assertTrue(flagged)
        self.assertTrue(all(text[r['start_char']:r['end_char']]==r['phrase'] for r in flagged))
        self.assertTrue(all(r['status']=='review_suggested_not_blocking' for r in flagged))


class ApprovedTestEvidenceTests(unittest.TestCase):
    def test_zero_test_unittest_success_is_rejected(self):
        args=['python','-m','unittest','discover']
        report=assess_verification(args,0,['----------------------------------------------------------------------',
                'Ran 0 tests in 0.000s','OK'])
        self.assertFalse(report['accepted'])
        self.assertEqual(report['test_count'],0)

    def test_real_unittest_success_attested_separately_from_gameplay(self):
        cmd=['python','-m','unittest','discover']
        report=assess_verification(cmd,0,['........','Ran 8 tests in 0.12s','OK'])
        self.assertTrue(report['accepted'])
        self.assertEqual(report['assurance'],'python_tests_passed')
        self.assertEqual(report['test_count'],8)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'a.py').write_text('def run():return True\n')
            steps=[{'path':'a.py','description':'run'}]
            snapshot=attach_verification(capture_verified_sources(p,steps),report,cmd)
            self.assertTrue(verified_sources_current(p,steps,snapshot))
            (p/'a.py').write_text('def run():return False\n')
            self.assertFalse(verified_sources_current(p,steps,snapshot))

    def test_missing_ok_line_rejected_and_process_failure_rejected(self):
        cmd=['python','-m','unittest','discover']
        self.assertFalse(assess_verification(cmd,0,['Ran 2 tests in 0.02s','FAILED (errors=1)'])['accepted'])
        self.assertFalse(assess_verification(cmd,1,['Ran 2 tests in 0.02s','OK'])['accepted'])

    def test_godot_editor_run_is_not_gameplay_test(self):
        r=assess_verification(['godot','--headless','--editor','--quit'],0,['Load successful'])
        self.assertTrue(r['accepted'])
        self.assertEqual(r['assurance'],'editor_load_only')
        self.assertIsNone(r['test_count'])

    def test_dotnet_zero_tests_not_accepted(self):
        r=assess_verification(['dotnet','test','--no-restore'],0,['Total tests: 0'])
        self.assertFalse(r['accepted'])

    def test_unsupported_extra_snapshot_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'a.py').write_text('a=1\n');steps=[{'path':'a.py','description':'x'}]
            real=capture_verified_sources(p,steps)
            self.assertFalse(verified_sources_current(p,steps,dict(real,extra='fake')))
            self.assertFalse(verified_sources_current(p,steps,dict(real,verification={'assurance':'game_verified'})))


class RoadmapContractIntegrationTests(unittest.TestCase):
    def test_static_bad_test_blocks_milestone_even_with_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);project=root/'game';project.mkdir()
            spec='REQ-1: The program must provide navigation.\n'+('a'*2200)
            index=SpecificationIndex(root/'spec.db');index.index(44,spec)
            index.save_response(44,spec,0,json.dumps({'files':[
                {'path':'src.py','description':'Implements navigation'},
                {'path':'test_nav.py','description':'Acceptance test; verifies: REQ-1'}]}),project=project)
            store=HierarchicalPlanStore(root/'road.db')
            store.prepare(index,44,spec,project,chat_id='chat',max_files=2)
            report=store.acceptance_contract_report(index,44,spec)
            self.assertEqual(report['model_declared_contracts'],1)
            self.assertEqual(report['checks'][0]['state'],'pending_source')
            entry=store.milestone(index,44,spec,1)
            jobs=JobStore(root/'jobs.db')
            job=jobs.submit_approved_milestone_build(entry['project'],entry['chat_id'],
                entry['scope_prompt'],entry['steps'],entry['approval_key'],
                master_prompt=spec,master_steps=entry['master_steps'])
            store.link_job(index,44,spec,1,job)
            (project/'src.py').write_text('def navigation():return True\n')
            (project/'test_nav.py').write_text('x=3\n')
            for step in jobs.steps(job):jobs.set_step(step['id'],'saved')
            jobs.change(job,'complete','Verified: test command exited 0 (mock)',
                        result=json.dumps(capture_verified_sources(project,entry['steps'])),allowed=('queued',))
            result=store.reconcile_jobs(index,44,spec,jobs)
            self.assertEqual(result['milestones_verified'],0)
            self.assertEqual(jobs.get(job)['state'],'waiting_verification')
            self.assertIn('contract',jobs.get(job)['detail'])
            # Repairing a test without a new approved check is insufficient.
            (project/'test_nav.py').write_text('def test_navigation():assert True\n')
            result=store.reconcile_jobs(index,44,spec,jobs)
            self.assertEqual(result['milestones_verified'],0)
            jobs.change(job,'running','User approved retest',allowed=('waiting_verification',))
            jobs.change(job,'complete','Verified: test command exited 0 (user retest)',
                        result=json.dumps(capture_verified_sources(project,entry['steps'])),allowed=('running',))
            result=store.reconcile_jobs(index,44,spec,jobs)
            self.assertEqual(result['milestones_verified'],1)
            self.assertFalse(result['acceptance_confirmed'])

if __name__=='__main__':unittest.main()

class ContractCliTests(unittest.TestCase):
    def test_read_only_report_and_nonzero_on_unimplemented_contract(self):
        import io
        from contextlib import redirect_stdout
        from deepthort_local.acceptance_contracts import main
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'src').mkdir()
            (p/'src/api.py').write_text('def unrelated():pass\n')
            spec=p/'requirements.txt';spec.write_text('REQ-1: Program must save the file.\n')
            plan=p/'plan.json';plan.write_text(json.dumps({'files':[
                {'path':'src/api.py','description':'API contract; provides: save_file'}]}))
            out=io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main([str(p),str(plan),str(spec)]),2)
            report=json.loads(out.getvalue())
            self.assertEqual(report['checks'][0]['state'],'missing_declared_export')
            (p/'src/api.py').write_text('def save_file(): pass\n')
            out=io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main([str(p),str(plan),str(spec)]),0)
            self.assertFalse(json.loads(out.getvalue())['acceptance_confirmed'])

    def test_incremental_planner_prompts_for_explicit_test_claims_only(self):
        with tempfile.TemporaryDirectory() as td:
            project=Path(td)
            index=SpecificationIndex(project/'spec.db')
            spec='REQ-1: The app must allow saving user files.\n'
            index.index(5,spec)
            prompt=index.model_prompt(5,spec)
            self.assertIn('verifies: REQ-N',prompt)
            self.assertIn('provides: Symbol',prompt)
            self.assertIn(spec,prompt)
