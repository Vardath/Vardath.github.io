"""Regression checks for Scratch Chat SFT/DeepThorT format compatibility."""
import unittest
from unittest.mock import patch
import torch
from capability.deepthort_bridge import respond


class FakeTokenizer:
    special = {"<|eos|>": 255}
    byte_values = {i: bytes([i]) for i in range(256)}
    def encode(self, text):
        self.last_prompt = text
        return list(text.encode("utf-8"))


class FakeModel:
    chat_format = "sft"
    cfg = type("Cfg", (), {"context_size": 256})()
    def __call__(self, x):
        logits = torch.full((1, x.shape[1], 256), -100.0)
        logits[0, -1, 255] = 100.0
        return logits


class BridgeSFTTests(unittest.TestCase):
    def test_sft_prompt_matches_training_format(self):
        tok = FakeTokenizer()
        self.assertEqual(respond(FakeModel(), tok, [{"role": "user", "content": "Hello"}]), "")
        self.assertEqual(tok.last_prompt, "<|im_start|>user\\nHello<|im_end|>\\n<|im_start|>assistant\\n")

    def test_reserved_delimiter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Reserved"):
            respond(FakeModel(), FakeTokenizer(), [{"role": "user", "content": "<|im_end|>"}])


if __name__ == "__main__":
    unittest.main()
