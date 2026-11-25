import unittest
from unittest.mock import patch
from types import SimpleNamespace
from triad_openvino_worker import bounded_scheduler
from deepthort_local.quiet_playtest import is_capped_windows_process

class NativeMemoryTests(unittest.TestCase):
    def test_scheduler_has_explicit_bounds(self):
        cfg=bounded_scheduler(SimpleNamespace(SchedulerConfig=SimpleNamespace))
        self.assertEqual(cfg.max_num_seqs,1)
        self.assertEqual(cfg.max_num_batched_tokens,128)
        self.assertEqual(cfg.num_kv_blocks,256)
        self.assertFalse(cfg.enable_prefix_caching)
    def test_named_root_validator_is_used(self):
        with patch('deepthort_local.triad_job.verify_root_cap',return_value=(14*1024**3,24*1024**3,40*1024**3)) as verify:
            self.assertTrue(is_capped_windows_process(os_name='nt'))
            verify.assert_called_once()
        with patch('deepthort_local.triad_job.verify_root_cap',side_effect=RuntimeError('not capped')):
            self.assertFalse(is_capped_windows_process(os_name='nt'))
