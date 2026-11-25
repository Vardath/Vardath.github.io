"""v42 versioned exact-file source snapshots and explicitly approved rollback."""
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.source_checkpoints import CheckpointError,SourceCheckpoints

class CheckpointsTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.job={'id':32,'mode':'build','state':'queued','project':str(self.project),
                  'approval_key':'draft:11','chat_id':'c'}
        self.steps=[{'id':15,'sequence':0,'path':'src/app.py','description':'App'},
                    {'id':16,'sequence':1,'path':'tests/test_app.py','description':'Tests'}]
        self.store=SourceCheckpoints(self.root/'state'/'source-checkpoints')
        self.existing=self.project/'src'/'app.py';self.existing.parent.mkdir()
        self.existing.write_text('before = 1\n','utf-8')
        self.newfile=self.project/'tests'/'test_app.py';self.newfile.parent.mkdir()
        self.initial=self.store.capture(self.job,self.steps,'approval_baseline',baseline=True)

    def test_baseline_persists_original_and_absent_file(self):
        first=self.store.list(32)[0]
        self.assertIsNotNone(first['files']['src/app.py'])
        self.assertIsNone(first['files']['tests/test_app.py'])
        with self.assertRaises(CheckpointError):self.store.capture(self.job,self.steps,'approval_baseline',baseline=True)

    def test_changed_existing_source_and_created_source_roll_back(self):
        self.existing.write_text('after = 2\n','utf-8')
        self.newfile.write_text('def test():pass\n','utf-8')
        self.store.capture(self.job,self.steps,'artifact_saved')
        info=self.store.restore_preview(self.job,self.steps,self.initial['id'])
        self.assertEqual(len(info['changed']),2)
        with self.assertRaises(CheckpointError):self.store.rollback(self.job,self.steps,self.initial['id'])
        receipt=self.store.rollback(self.job,self.steps,self.initial['id'],explicit_approval=True)
        self.assertEqual(self.existing.read_text('utf-8'),'before = 1\n')
        self.assertFalse(self.newfile.exists())
        self.assertEqual(len(receipt['actions']),2)
        self.assertTrue(list((self.root/'state'/'source-checkpoints'/'job-32'/'quarantine').rglob('test_app.py')))
        self.assertTrue(list((self.root/'state'/'source-checkpoints'/'job-32'/'restore-backups').rglob('app.py')))
        self.assertEqual(self.store.list(32)[-1]['reason'],'restored')

    def test_external_change_blocks_all_files(self):
        self.existing.write_text('after = 2\n','utf-8')
        self.newfile.write_text('new\n','utf-8')
        self.store.capture(self.job,self.steps,'artifact_saved')
        self.existing.write_text('externally modified\n','utf-8')
        with self.assertRaisesRegex(CheckpointError,'External file change'):
            self.store.restore_preview(self.job,self.steps,self.initial['id'])
        self.assertEqual(self.newfile.read_text('utf-8'),'new\n')

    def test_changed_approved_plan_blocks_restoration(self):
        self.existing.write_text('after\n','utf-8')
        self.store.capture(self.job,self.steps,'artifact_saved')
        self.steps[0]['description']='changed scope'
        with self.assertRaisesRegex(CheckpointError,'scope|match'):
            self.store.restore_preview(self.job,self.steps,self.initial['id'])

    def test_corrupt_checkpoint_manifest_denied(self):
        row=self.store.list(32)[0]
        path=self.store._job_dir(32)/'revisions'/f"{row['id']}.json"
        content=json.loads(path.read_text('utf-8'))
        content['project']='/other';path.write_text(json.dumps(content),'utf-8')
        with self.assertRaisesRegex(CheckpointError,'corrupted'):
            self.store.list(32)

    def test_missing_snapshot_blob_cannot_restore(self):
        self.existing.write_text('after\n','utf-8')
        self.store.capture(self.job,self.steps,'artifact_saved')
        sha=self.store.list(32)[0]['files']['src/app.py']
        (self.store._job_dir(32)/'objects'/sha).unlink()
        with self.assertRaises(CheckpointError):
            self.store.rollback(self.job,self.steps,self.initial['id'],explicit_approval=True)

    def test_existing_empty_source_rollback(self):
        self.existing.write_text('','utf-8')
        empty=self.store.capture(self.job,self.steps,'artifact_saved')
        self.existing.write_text('changed','utf-8')
        self.store.capture(self.job,self.steps,'artifact_saved')
        self.store.rollback(self.job,self.steps,empty['id'],explicit_approval=True)
        self.assertEqual(self.existing.read_bytes(),b'')

    def test_untrusted_path_is_blocked(self):
        self.steps[0]['path']='../escape.py'
        with self.assertRaises((CheckpointError,ValueError)):
            self.store.capture(self.job,self.steps,'artifact_saved')

if __name__=='__main__':unittest.main()
