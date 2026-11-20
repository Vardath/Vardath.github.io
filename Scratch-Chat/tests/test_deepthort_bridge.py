"""Regression tests for the DeepThorT JSON-line bridge; no trained weights needed."""
import unittest
from capability.bpe import ByteBPE
from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.deepthort_bridge import respond


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok = ByteBPE([])
        cls.model = ModernScratchTransformer(ModernConfig(
            vocab_size=cls.tok.vocab_size, context_size=32, width=16,
            layers=1, heads=2)).eval()

    def test_one_turn(self):
        result = respond(self.model, self.tok, [{"role": "user", "content": "Hello"}], max_new_tokens=2)
        self.assertIsInstance(result, str)

    def test_multi_turn(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Again"},
        ]
        self.assertIsInstance(respond(self.model, self.tok, messages, max_new_tokens=2), str)

    def test_reject_invalid_role(self):
        with self.assertRaises(ValueError):
            respond(self.model, self.tok, [{"role": "developer", "content": "test"}])

    def test_reject_unbounded_generation(self):
        with self.assertRaises(ValueError):
            respond(self.model, self.tok, [{"role": "user", "content": "test"}], max_new_tokens=10000)

    def test_reject_non_integer_generation(self):
        with self.assertRaises(ValueError):
            respond(self.model, self.tok, [{"role": "user", "content": "test"}], max_new_tokens=True)

    def test_reject_large_input(self):
        with self.assertRaises(ValueError):
            respond(self.model, self.tok, [{"role": "user", "content": "x" * 16001}])


if __name__ == "__main__":
    unittest.main()
