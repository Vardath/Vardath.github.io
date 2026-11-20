import unittest
from pathlib import Path
import torch
from vardath_chat.tokenizer import (encode_text, decode_text, encode_chat,
                                    encode_training_example, ASSISTANT, EOS)
from vardath_chat.model import ModelConfig, ScratchTransformer
from vardath_chat.engine import LocalChatEngine, load_checkpoint

ROOT = Path(__file__).resolve().parent.parent


class ScratchChatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_unicode_round_trip(self):
        s = 'Hello 🌌 你好 café'
        self.assertEqual(decode_text(encode_text(s)), s)

    def test_train_targets_only_assistant(self):
        a, b = encode_training_example([{'role': 'user', 'content': 'hello'},
                                         {'role': 'assistant', 'content': 'world'}], 64)
        self.assertEqual(len(a), len(b))
        self.assertEqual(sum(v != -100 for v in b), len('world') + 1)
        self.assertEqual(b[-1], EOS)

    def test_chat_prompt_ends_with_assistant_marker(self):
        out = encode_chat([{'role': 'user', 'content': 'hi'}])
        self.assertEqual(out[-1], ASSISTANT)

    def test_model_causality(self):
        torch.manual_seed(3)
        m = ScratchTransformer(ModelConfig(context_size=32, width=32, layers=2, heads=4))
        m.eval()
        a = torch.tensor([[1, 2, 3, 4, 5]])
        b = torch.tensor([[1, 2, 3, 9, 8]])
        with torch.no_grad():
            x, y = m(a), m(b)
        self.assertTrue(torch.allclose(x[:, :3], y[:, :3], atol=1e-5))

    def test_actual_trained_weights(self):
        m, metadata = load_checkpoint(ROOT / 'checkpoints' / 'starter.pt')
        self.assertGreater(metadata['steps'], 0)
        self.assertGreater(sum(p.numel() for p in m.parameters()), 100000)
        engine = LocalChatEngine(ROOT / 'checkpoints' / 'starter.pt')
        reply = engine.reply([{'role': 'user', 'content': 'what is janus?'}],
                             max_tokens=100, temperature=0)
        self.assertIn('JANUS', reply)
        self.assertIn('Fano', reply)


if __name__ == '__main__':
    unittest.main()
