import unittest
from unittest.mock import patch
from types import SimpleNamespace
from triad_openvino_worker import bounded_scheduler,final_text,smoke_result,model_messages,thinking_enabled,Engine,MAX_CONTEXT_TOKENS
from deepthort_local.quiet_playtest import is_capped_windows_process

class NativeMemoryTests(unittest.TestCase):
    def test_scheduler_has_explicit_bounds(self):
        cfg=bounded_scheduler(SimpleNamespace(SchedulerConfig=SimpleNamespace))
        self.assertEqual(cfg.max_num_seqs,1)
        self.assertEqual(cfg.max_num_batched_tokens,64)
        self.assertEqual(cfg.num_kv_blocks,128)
        self.assertEqual(MAX_CONTEXT_TOKENS,2048)
        self.assertFalse(cfg.enable_prefix_caching)
    def test_named_root_validator_is_used(self):
        with patch('deepthort_local.triad_job.verify_root_cap',return_value=(14*1024**3,24*1024**3,40*1024**3)) as verify:
            self.assertTrue(is_capped_windows_process(os_name='nt'))
            verify.assert_called_once()
        with patch('deepthort_local.triad_job.verify_root_cap',side_effect=RuntimeError('not capped')):
            self.assertFalse(is_capped_windows_process(os_name='nt'))

    def test_reasoning_final_answer_is_not_fabricated(self):
        self.assertEqual(final_text('janus','<think>calculate</think>4'),'4')
        self.assertEqual(final_text('janus','calculate</think>PLAN_READY'),'PLAN_READY')
        self.assertEqual(final_text('sentinel','<think>\n\n</think>REVIEW_READY'),'REVIEW_READY')
        self.assertEqual(final_text('implementation','print("<think>")'),'print("<think>")')
        with self.assertRaises(ValueError):final_text('janus','<think>unfinished')
        with self.assertRaises(ValueError):final_text('janus','<think>reason</think>')

    def test_nonempty_generation_is_not_an_exact_answer_pass(self):
        result=smoke_result('janus','To solve the problem, add the numbers.')
        self.assertEqual(result['native_generation'],'passed')
        self.assertEqual(result['exact_arithmetic_reply'],'failed')
        self.assertEqual(smoke_result('janus','<think>unfinished')['exact_arithmetic_reply'],'failed')
        self.assertEqual(smoke_result('janus','<think>calculate</think>4')['exact_arithmetic_reply'],'passed')
        with self.assertRaises(RuntimeError):smoke_result('janus',' ')

    def test_smollm3_mode_preserves_user_and_system_text(self):
        messages=[{'role':'system','content':'Preserve the original specification.'},{'role':'user','content':'Plan the next test.'}]
        prepared=model_messages('janus',messages)
        self.assertEqual(prepared[0]['content'],'Preserve the original specification.\n/no_think')
        self.assertEqual(messages[0]['content'],'Preserve the original specification.')
        self.assertEqual(prepared[1],messages[1])
        self.assertEqual(model_messages('sentinel',messages),messages)
        self.assertEqual(model_messages('implementation',messages),messages)
        self.assertEqual(model_messages('janus',messages[1:])[0],{'role':'system','content':'/no_think'})

    def test_bounded_reasoning_mode_only_for_long_sentinel_requests(self):
        for tokens in (16,32,96,192,511):
            self.assertFalse(thinking_enabled('sentinel',tokens))
        self.assertTrue(thinking_enabled('sentinel',768))
        self.assertFalse(thinking_enabled('janus',768))
        self.assertFalse(thinking_enabled('implementation',768))
        e=Engine.__new__(Engine);e.role='sentinel'
        with patch.object(e,'generate_raw',return_value='reasoning text</think>{"required":360,"verdict":"mismatch"}'):
            self.assertEqual(e.generate([],768),'{"required":360,"verdict":"mismatch"}')
        with patch.object(e,'generate_raw',return_value='unfinished reasoning'):
            with self.assertRaises(ValueError):e.generate([],768)

    def test_reduced_context_error_stays_classified(self):
        from deepthort_local.triad_errors import native_error
        self.assertEqual(native_error(ValueError('Input 1500 + output 768 exceeds 2048-token Triad profile; use indexed planning')),'context_limit')
        self.assertEqual(native_error(RuntimeError("Check 'shape_size(shape) == 0 || m_ptr != nullptr' failed")),'native_error')
