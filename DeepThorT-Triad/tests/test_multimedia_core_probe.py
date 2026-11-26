import tempfile
import unittest
from pathlib import Path
from deepthort_local.multimedia_core_probe import exercise


class MultimediaCoreTests(unittest.TestCase):
    def test_absent_model_is_blocked_not_passed(self):
        with tempfile.TemporaryDirectory() as root:
            result = exercise(root)
            self.assertEqual(result['status'], 'blocked')
            self.assertIn('not detected', result['detail'])

    def test_legacy_weights_are_not_fourth_core(self):
        with tempfile.TemporaryDirectory() as root:
            model = Path(root) / 'models' / 'stable-diffusion-v1-5'
            model.mkdir(parents=True)
            (model / 'model_index.json').write_text('{}')
            for part in ('unet', 'vae', 'text_encoder'):
                (model / part).mkdir()
                (model / part / 'model.safetensors').write_bytes(b'fixture')
            result = exercise(root)
            self.assertEqual(result['status'], 'blocked')
            self.assertEqual(result['evidence']['count'], 3)
            self.assertIn('presence only', result['detail'])

    def test_cancelled(self):
        self.assertEqual(exercise('.', cancelled=lambda: True)['status'], 'cancelled')


if __name__ == '__main__':
    unittest.main()
