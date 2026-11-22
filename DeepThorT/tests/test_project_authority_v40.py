"""v40: job-bound grants, source fingerprints, revocation and fixed test profiles."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from deepthort_local.project_authority import (
    GrantError, authorize_file, authorize_test, default_policy, issue_grant,
    load_policy, recognized_test_command, record_file, revoke_grant, set_policy,
)
from deepthort_local.workspace import apply_approved_file


class ProjectAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.project = self.base / 'game'
        self.project.mkdir()
        self.grants = self.base / 'state' / 'project-grants'
        self.backups = self.base / 'state' / 'backups'
        self.job = {'id': 42, 'mode': 'build', 'state': 'queued',
                    'project': str(self.project), 'chat_id': 'thread-one',
                    'approval_key': 'draft:51'}
        self.steps = [{'id': 121, 'sequence': 0, 'path': 'src/ship.py',
                       'description': 'Generate game ship implementation',
                       'state': 'planned'}]

    def issue(self):
        return issue_grant(self.grants, self.job, self.steps)

    def save_step(self):
        self.job['state'] = 'running'
        approval = authorize_file(self.grants, self.job, self.steps,
                                  self.steps[0], enabled=True)
        apply_approved_file(self.project, self.steps[0]['path'],
                            'def build_ship():\n    return 1\n', self.backups,
                            expected_existing_sha=approval['before_sha256'])
        record_file(self.grants, self.job, self.steps, self.steps[0], enabled=True)
        self.steps[0]['state'] = 'saved'
        self.job['state'] = 'waiting_verification'

    def test_no_unapproved_grant(self):
        self.job['state'] = 'running'
        with self.assertRaises(GrantError):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=True)

    def test_default_and_persistent_opt_out(self):
        p = self.base / 'state' / 'project-work-policy.json'
        self.assertTrue(default_policy()['enabled'])
        self.assertTrue(load_policy(p)['enabled'])
        set_policy(p, False)
        self.assertFalse(load_policy(p)['enabled'])
        p.write_text('{"schema":"invalid","enabled":true}', 'utf-8')
        self.assertFalse(load_policy(p)['enabled'])

    def test_grant_only_after_approved_queued_build(self):
        self.job['state'] = 'needs_input'
        with self.assertRaises(GrantError):
            self.issue()
        self.job['state'] = 'queued'
        self.issue()
        with self.assertRaises(GrantError):
            self.issue()

    def test_write_and_fixed_verification_resume_after_restart(self):
        self.issue()
        self.save_step()
        cmd = [sys.executable, '-m', 'unittest', 'discover']
        self.assertTrue(authorize_test(self.grants, self.job, self.steps,
                                       cmd, enabled=True))
        saved = json.loads((self.grants / 'job-42.json').read_text('utf-8'))
        self.assertEqual(saved['files'][0]['path'], 'src/ship.py')
        self.assertEqual(saved['events'][-1]['kind'], 'file_saved_unverified')

    def test_modified_existing_file_denied(self):
        file = self.project / 'src' / 'ship.py'
        file.parent.mkdir(parents=True)
        file.write_text('original\n', 'utf-8')
        self.issue()
        file.write_text('external change\n', 'utf-8')
        self.job['state'] = 'running'
        with self.assertRaisesRegex(GrantError, 'changed'):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=True)

    def test_automatic_write_keeps_backup(self):
        file = self.project / 'src' / 'ship.py'
        file.parent.mkdir(parents=True)
        file.write_text('original\n', 'utf-8')
        self.issue()
        self.save_step()
        self.assertTrue(list(self.backups.rglob('ship.py')))
        self.assertEqual(file.read_text('utf-8').splitlines()[0],
                         'def build_ship()')

    def test_changed_generated_file_denies_automatic_test(self):
        self.issue()
        self.save_step()
        (self.project / 'src' / 'ship.py').write_text('unexpected\n', 'utf-8')
        with self.assertRaisesRegex(GrantError, 'changed'):
            authorize_test(self.grants, self.job, self.steps,
                           [sys.executable, '-m', 'unittest', 'discover'],
                           enabled=True)

    def test_revoke_prevents_new_actions(self):
        self.issue()
        self.assertTrue(revoke_grant(self.grants, 42))
        self.assertFalse(revoke_grant(self.grants, 42))
        self.job['state'] = 'running'
        with self.assertRaises(GrantError):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=True)

    def test_approval_is_bound_to_original_plan_and_job(self):
        self.issue()
        self.job['state'] = 'running'
        self.steps[0]['description'] = 'Changed meaning'
        with self.assertRaisesRegex(GrantError, 'changed'):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=True)

    def test_denies_hidden_or_binary_install_targets(self):
        for name in ('.git/config', '.github/workflows/x.yml',
                     'node_modules/x.js', 'bin/setup.exe', '../escape.py'):
            self.steps[0]['path'] = name
            with self.subTest(path=name), self.assertRaises((GrantError, ValueError)):
                self.issue()

    def test_no_guessed_or_injected_test_commands(self):
        self.project.joinpath('project.godot').write_text('', 'utf-8')
        self.assertTrue(recognized_test_command(
            ['godot', '--headless', '--path', str(self.project), '--editor', '--quit'],
            self.project))
        self.assertTrue(recognized_test_command(
            ['godot', '--headless', '--path', str(self.project), '-s',
             'addons/gut/gut_cmdln.gd', '-gdir=res://tests',
             '-ginclude_subdirs', '-gexit'], self.project))
        for cmd in (['bash', '-c', 'malicious'], ['python', '-c', 'print(3)'],
                    ['npm', 'run', 'postinstall'], ['winget', 'install', '--all'],
                    ['godot', '--headless', '--path', '/other', '--editor', '--quit']):
            with self.subTest(cmd=cmd):
                self.assertFalse(recognized_test_command(cmd, self.project))

    def test_policy_off_blocks_existing_grants(self):
        self.issue()
        self.job['state'] = 'running'
        with self.assertRaises(GrantError):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=False)

    def test_tampered_grant_is_rejected(self):
        self.issue()
        path = self.grants / 'job-42.json'
        row = json.loads(path.read_text('utf-8'))
        row['project'] = '/tmp/other-project'
        path.write_text(json.dumps(row), 'utf-8')
        self.job['state'] = 'running'
        with self.assertRaises(GrantError):
            authorize_file(self.grants, self.job, self.steps,
                           self.steps[0], enabled=True)


if __name__ == '__main__':
    unittest.main()
