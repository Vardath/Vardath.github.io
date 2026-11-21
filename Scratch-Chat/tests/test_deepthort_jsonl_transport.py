"""Exercise the actual newline-delimited DeepThorT transport with a tiny random model.

Protocol tests are not conversation-quality acceptance tests.
"""
import io
import json
import unittest
from unittest.mock import patch

from capability.bpe import ByteBPE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.deepthort_bridge import serve


class JSONLineTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = ByteBPE([])
        cls.model = ModernScratchTransformer(ModernConfig(
            vocab_size=cls.tokenizer.vocab_size, context_size=64,
            width=16, layers=1, heads=2)).eval()

    def exchange(self, lines):
        incoming = io.StringIO("".join(json.dumps(x) + "\n" if not isinstance(x, str) else x + "\n" for x in lines))
        outgoing = io.StringIO()
        with patch("sys.stdin", incoming), patch("sys.stdout", outgoing):
            serve(self.model, self.tokenizer, {"step": 0})
        responses = [json.loads(line) for line in outgoing.getvalue().splitlines()]
        self.assertEqual(len(responses), len(lines), "Exactly one response per request")
        return responses

    def test_health_chat_multiturn_and_recovery(self):
        results = self.exchange([
            {"method": "health"},
            {"method": "chat", "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
                {"role": "user", "content": "Continue"}], "max_new_tokens": 2},
            {"method": "chat", "messages": [{"role": "tool", "content": "unsafe"}]},
            {"method": "health"},
        ])
        self.assertTrue(results[0]["ok"])
        self.assertFalse(results[0]["ready_for_conversation"])
        self.assertTrue(results[1]["ok"])
        self.assertIsInstance(results[1]["response"], str)
        self.assertFalse(results[2]["ok"])
        self.assertTrue(results[3]["ok"])

    def test_malformed_json_and_unknown_method(self):
        results = self.exchange(['{bad json', {"method": "unknown"}, {"method": "health"}])
        self.assertFalse(results[0]["ok"])
        self.assertFalse(results[1]["ok"])
        self.assertTrue(results[2]["ok"])


if __name__ == "__main__":
    unittest.main()
