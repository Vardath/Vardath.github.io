"""v19 regressions for real JANUS crash and background model contention."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import janus_worker
from janus_worker import JanusWorker
from deepthort_local.janus_counsel import LocalCounsel


class JanusIdleTimerTests(unittest.TestCase):
    def test_clock_moving_past_deadline_never_sleeps_negative(self):
        worker=object.__new__(JanusWorker)
        worker._stopping=False
        worker.game_gate=SimpleNamespace(gaming=lambda: False)
        worker.store=SimpleNamespace(recover_interrupted_actions=Mock(),append_event=Mock())
        worker.observe_once=Mock()
        worker.execute_next_approved=Mock()
        calls=iter([100.0,100.0,101.10])
        durations=[]
        def sleep(seconds):
            durations.append(seconds)
            self.assertGreater(seconds,0)
            self.assertLessEqual(seconds,.25)
            worker._stopping=True
        with patch.object(janus_worker.time,'monotonic',side_effect=lambda:next(calls)), \
             patch.object(janus_worker.time,'sleep',side_effect=sleep), \
             patch.object(janus_worker.signal,'signal'):
            worker.run(interval=1.0)
        self.assertEqual(durations,[.25])
        worker.observe_once.assert_called_once()

    def test_overdue_tick_is_skipped_without_negative_sleep(self):
        worker=object.__new__(JanusWorker)
        worker._stopping=False
        worker.game_gate=SimpleNamespace(gaming=lambda: False)
        worker.store=SimpleNamespace(recover_interrupted_actions=Mock(),append_event=Mock())
        def observe():pass
        def next_approved():worker._stopping=True
        worker.observe_once=observe
        worker.execute_next_approved=next_approved
        with patch.object(janus_worker.time,'monotonic',return_value=100.0), \
             patch.object(janus_worker.time,'sleep') as sleep, \
             patch.object(janus_worker.signal,'signal'):
            worker.run(interval=1.0)
        sleep.assert_not_called()


class JanusCounselContentionTests(unittest.TestCase):
    def test_busy_interactive_model_is_not_called_by_janus_advice(self):
        with tempfile.TemporaryDirectory() as td:
            counsel=LocalCounsel(Path(td)/'lease.sqlite3')
            response={'ready':True,'offline':True,'model':'deepthort-qwen-coder-onnx',
                      'inference_busy':True}
            opener=Mock()
            opener.open.return_value=io.BytesIO(json.dumps(response).encode())
            with patch('deepthort_local.janus_counsel.urllib.request.build_opener',return_value=opener), \
                 patch.object(counsel,'_acquire') as acquire:
                self.assertIsNone(counsel.request(society='janus',goal='game',problem='plan',evidence='log'))
            opener.open.assert_called_once()
            acquire.assert_not_called()


if __name__=='__main__':unittest.main()
