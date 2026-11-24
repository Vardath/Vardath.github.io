"""v41 durable test/diagnose/repair/retest: bounded and fail-closed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from deepthort_local.development_cycle import (
    DevelopmentCycleStore, CycleError, MAX_TEST_ATTEMPTS,
    MAX_REPAIR_ATTEMPTS, build_repair_prompt, parse_repair_response,
)
from deepthort_local.project_authority import (
    GrantError, authorize_file, authorize_test, authorize_repair,
    authorize_repair_context, issue_grant, record_file, record_repair,
)
from deepthort_local.workspace import apply_approved_file


class DevelopmentCycleTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.project=self.root/'project';self.project.mkdir()
        self.store=DevelopmentCycleStore(self.root/'cycle.sqlite3')
        self.grants=self.root/'grants';self.backups=self.root/'backups'
        self.job={'id':37,'project':str(self.project),'mode':'build','state':'queued',
                  'approval_key':'draft:8','chat_id':'the-chat','prompt':'Build a working addition function and tests'}
        self.steps=[{'id':12,'path':'main.py','state':'planned','sequence':0,
                     'description':'Add two values'}]
        self.cmd=[sys.executable,'-m','unittest','discover']
        issue_grant(self.grants,self.job,self.steps)
        self.job['state']='running'
        approve=authorize_file(self.grants,self.job,self.steps,self.steps[0],enabled=True)
        apply_approved_file(self.project,'main.py','def add(a, b):\n    return a - b\n',
                            self.backups,expected_existing_sha=approve['before_sha256'])
        record_file(self.grants,self.job,self.steps,self.steps[0],enabled=True)
        self.steps[0]['state']='saved';self.job['state']='waiting_verification'

    def test_new_cycle_requires_saved_approved_job(self):
        self.assertTrue(authorize_test(self.grants,self.job,self.steps,self.cmd,enabled=True))
        cycle=self.store.begin_test(self.job,self.steps,self.cmd)
        self.assertEqual(cycle['tests'],1)
        self.assertEqual(cycle['phase'],'testing')

    def test_cannot_double_start_test(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        with self.assertRaises(CycleError):self.store.begin_test(self.job,self.steps,self.cmd)

    def test_success_is_only_recorded_from_explicit_accepted_evidence(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.assertEqual(self.store.finish_test(37,0,True,['Ran 1 test','OK'])['phase'],'verified')
        with self.assertRaises(CycleError):self.store.begin_test(self.job,self.steps,self.cmd)

    def test_zero_exit_without_evidence_blocks(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.assertEqual(self.store.finish_test(37,0,False,['empty test'])['phase'],'needs_attention')

    def test_missing_tool_is_not_source_repair(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.assertEqual(self.store.finish_test(37,127,False,['command not found'])['phase'],'needs_attention')

    def test_failed_test_becomes_single_local_repair(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        cycle=self.store.finish_test(37,1,False,['AssertionError: 1 != 2','FAILED (failures=1)'])
        self.assertEqual(cycle['phase'],'repair_ready')
        self.assertEqual(self.store.pending_repairs(),[37])
        self.assertEqual(self.store.claim_repair(37)['repairs'],1)
        with self.assertRaises(CycleError):self.store.claim_repair(37)

    def test_repair_cannot_modify_unapproved_file(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.store.finish_test(37,1,False,['FAILED (failures=1)'])
        self.store.claim_repair(37)
        self.job['state']='running'
        forged={'id':99,'path':'other.py','state':'saved'}
        with self.assertRaises(GrantError):
            authorize_repair(self.grants,self.job,self.steps,forged,enabled=True)

    def test_full_fail_repair_retest_success(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.store.finish_test(37,1,False,['Traceback','AssertionError: 4 != 5'])
        self.job['state']='waiting_repair'
        self.assertTrue(authorize_repair_context(self.grants,self.job,self.steps,enabled=True))
        prompt,files=build_repair_prompt(self.job,self.steps,self.store.get(37)['diagnostic'])
        self.assertIn('UNTRUSTED DATA',prompt)
        self.assertIn('main.py',files)
        target,code=parse_repair_response(json.dumps({'path':'main.py','code':
            'def add(a, b):\n    return a + b\n'}),files)
        self.store.claim_repair(37)
        self.job['state']='running'
        approval=authorize_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)
        apply_approved_file(self.project,target,code,self.backups,
                            expected_existing_sha=approval['before_sha256'])
        receipt=record_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)
        self.store.finish_repair(37,target,receipt['sha256'])
        self.assertEqual(self.store.get(37)['phase'],'repair_saved')
        self.job['state']='waiting_verification'
        self.assertTrue(authorize_test(self.grants,self.job,self.steps,self.cmd,enabled=True))
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.assertEqual(self.store.finish_test(37,0,True,['Ran 1 test','OK'])['phase'],'verified')
        self.assertTrue(list(self.backups.rglob('main.py')))
        self.assertEqual(self.store.get(37)['tests'],2)
        self.assertEqual(self.store.get(37)['repairs'],1)

    def test_no_restart_auto_replay_of_uncertain_test(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        reopened=DevelopmentCycleStore(self.store.path)
        self.assertEqual(reopened.interrupted(),[37])
        self.assertEqual(reopened.get(37)['phase'],'needs_attention')
        self.assertEqual(reopened.interrupted(),[])
        with self.assertRaises(CycleError):reopened.begin_test(self.job,self.steps,self.cmd)

    def test_no_restart_auto_replay_of_uncertain_repair(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.store.finish_test(37,1,False,['Traceback'])
        self.store.claim_repair(37)
        self.assertEqual(DevelopmentCycleStore(self.store.path).interrupted(),[37])
        self.assertEqual(self.store.pending_repairs(),[])

    def test_no_beyond_test_budget(self):
        for attempt in range(MAX_TEST_ATTEMPTS):
            if attempt:
                self.store.claim_repair(37)
                self.store.finish_repair(37,'main.py','a'*64)
            self.store.begin_test(self.job,self.steps,self.cmd)
            state=self.store.finish_test(37,1,False,['AssertionError'])
        self.assertEqual(state['phase'],'needs_attention')
        self.assertEqual(state['tests'],MAX_TEST_ATTEMPTS)
        with self.assertRaises(CycleError):self.store.begin_test(self.job,self.steps,self.cmd)

    def test_repair_limit_and_source_fingerprint(self):
        self.job['state']='running'
        for i in range(MAX_REPAIR_ATTEMPTS):
            auth=authorize_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)
            apply_approved_file(self.project,'main.py',f'def add(a,b): return {i+7}\n',
                                self.backups,expected_existing_sha=auth['before_sha256'])
            record_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)
        with self.assertRaises(GrantError):
            authorize_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)

    def test_external_modification_never_auto_overwritten(self):
        self.job['state']='running'
        (self.project/'main.py').write_text('third party change\n','utf-8')
        with self.assertRaises(GrantError):
            authorize_repair(self.grants,self.job,self.steps,self.steps[0],enabled=True)

    def test_unapproved_repair_model_output_rejected(self):
        prompt,candidates=build_repair_prompt(self.job,self.steps,'AssertionError')
        for invalid in ('{"path":"../../outside.py","code":"print(1)"}',
                        '{"path":"main.py","code":""}',
                        '{"path":"main.py","code":"hi","command":"sh -c evil"}',
                        'print(123)',
                        '{"path":"main.py","code":"def add(a, b):\\n    return a - b\\n"}'):
            with self.subTest(invalid=invalid),self.assertRaises(CycleError):
                parse_repair_response(invalid,candidates)

    def test_repair_diagnostics_are_local_bounded_and_redacted(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        lines=['ERROR: token=superprivateXYZ','AssertionError: 5 != 6']*90
        row=self.store.finish_test(37,1,False,lines)
        self.assertLessEqual(len(row['diagnostic']),2200)
        self.assertNotIn('superprivateXYZ',row['diagnostic'])
        self.assertIn('[REDACTED]',row['diagnostic'])

    def test_job_plan_mutation_denies_second_test(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.store.finish_test(37,1,False,['Traceback'])
        self.store.claim_repair(37)
        self.store.finish_repair(37,'main.py','b'*64)
        self.steps[0]['description']='Unauthorized changed objective'
        with self.assertRaises(CycleError):self.store.begin_test(self.job,self.steps,self.cmd)

    def test_failure_is_durable_and_visible(self):
        self.store.begin_test(self.job,self.steps,self.cmd)
        self.store.finish_test(37,1,False,['AssertionError'])
        events=self.store.events(37)
        self.assertTrue(any(e['phase']=='testing' for e in events))
        self.assertTrue(any(e['phase']=='repair_ready' for e in events))
        self.assertEqual(DevelopmentCycleStore(self.store.path).get(37)['tests'],1)


if __name__=='__main__':unittest.main()
