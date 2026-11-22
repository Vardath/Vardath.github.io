"""Exercise the actual line-oriented DeepThorT bridge with a random-initialized model.

Protocol acceptance only: random weights do not demonstrate conversation quality.
"""
import io
import json
import unittest
from unittest.mock import patch

from capability.bpe import ByteBPE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.deepthort_bridge import serve


class JsonLineTransportTests(unittest.TestCase):
    def test_multiple_requests_and_error_recovery(self):
        tokenizer = ByteBPE([])
        model = ModernScratchTransformer(ModernConfig(
            vocab_size=tokenizer.vocab_size, context_size=32,
            width=16, layers=1, heads=2)).eval()
        requests = [
            {"method": "health"},
            {"method": "chat", "messages": [{"role": "user", "content": "Hello"}],
             "max_new_tokens": 1},
            {"method": "chat", "messages": [{"role": "assistant", "content": "orphan"}],
             "max_new_tokens": 1},
            {"method": "chat", "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "Continue"}], "max_new_tokens": 1},
            {"method": "health"},
        ]
        incoming = "\n".join(json.dumps(request) for request in requests) + "\n"
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(incoming)), patch("sys.stdout", output):
            serve(model, tokenizer, {"step": 0})
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), len(requests))
        results = [json.loads(line) for line in lines]
        self.assertTrue(results[0]["ok"])
        self.assertFalse(results[0]["ready_for_conversation"])
        self.assertTrue(results[1]["ok"])
        self.assertIsInstance(results[1]["response"], str)
        self.assertFalse(results[2]["ok"])
        self.assertTrue(results[3]["ok"])
        self.assertTrue(results[4]["ok"])


if __name__ == "__main__":
    unittest.main()
