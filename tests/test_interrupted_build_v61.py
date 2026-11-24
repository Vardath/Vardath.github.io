import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.interrupted_build import validate_interrupted, RecoveryError, INTERRUPTED

class Store:
    def __init__(self,value):self.value=value
    def get(self,ident):return self.value
    def recovery_snapshot(self,job,steps):return self.value
    def list(self,ident):return self.value
    def _verify_binding(self,job,steps,records):
        root=Path(job['project'])
        return root,[(s['path'],root/s['path']) for s in steps]

class InterruptedBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.job=dict(id=1,project=str(self.root),mode='build',state='paused',detail=INTERRUPTED)
        self.steps=[dict(id=10,path='a.py',state='saved'),dict(id=11,path='b.py',state='planned')]
        self.grant={'files':[dict(step_id=10,path='a.py',before_sha256=None,written_sha256='hash-a'),
                             dict(step_id=11,path='b.py',before_sha256=None,written_sha256=None)]}
        self.graph={'state':'active','active_action':None,'nodes':[
            dict(node='file:10',state='saved',evidence_sha256='hash-a'),
            dict(node='file:11',state='waiting',evidence_sha256='')]}
        self.checkpoint={'reason':'artifact_saved','files':{'a.py':'hash-a','b.py':None}}
        self.hashes={'a.py':'hash-a','b.py':None}

    def validate(self,cycle=None):
        with patch('deepthort_local.interrupted_build._active',return_value=self.grant),\
             patch('deepthort_local.interrupted_build._safe_auto_path',side_effect=lambda root,path:(path,root/path)),\
             patch('deepthort_local.interrupted_build._sha',side_effect=lambda target:self.hashes[target.name]):
            return validate_interrupted(self.job,self.steps,grants=self.root,graphs=Store(self.graph),
                checkpoints=Store([self.checkpoint]),cycles=Store(cycle),enabled=True)

    def test_consistent_saved_prefix_resumes(self):
        self.assertEqual(self.validate(),{'job_id':1,'saved':1,'planned':1})

    def test_external_change_cannot_resume(self):
        self.hashes['a.py']='external'
        with self.assertRaisesRegex(RecoveryError,'Workspace differs'):self.validate()

    def test_uncertain_planned_write_cannot_resume(self):
        self.grant['files'][1]['written_sha256']='unexpected'
        with self.assertRaisesRegex(RecoveryError,'planned file'):self.validate()

    def test_cycle_or_running_lease_cannot_resume(self):
        with self.assertRaisesRegex(RecoveryError,'test or repair cycle'):self.validate({'phase':'testing'})
        self.graph['active_action']={'kind':'write'}
        with self.assertRaisesRegex(RecoveryError,'not idle'):self.validate()

    def test_user_paused_is_not_automatic_recovery(self):
        self.job['detail']='Paused by user'
        with self.assertRaisesRegex(RecoveryError,'shutdown-interrupted'):self.validate()

if __name__=='__main__':unittest.main()
