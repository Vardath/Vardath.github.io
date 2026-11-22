"""Assistant-only label integrity checks without external training fixtures."""
import unittest
from capability.bpe import ByteBPE
from capability.dialogue_format import serialize
from capability.dialogue_labels import encode_assistant_labels


class AssistantLabelsTest(unittest.TestCase):
    def test_masks_user_system_and_tool(self):
        tok = ByteBPE()
        row = serialize([
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Secret question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "tool", "content": "Tool result"},
            {"role": "assistant", "content": "Final answer"},
        ])
        encoded = encode_assistant_labels(row, tok)
        selected = tok.decode([x for x in encoded["labels"] if x != -100])
        self.assertEqual(selected, "First answer<|im_end|>Final answer<|im_end|>")
        self.assertEqual(len(encoded["labels"]), len(encoded["input_ids"]))

    def test_unicode_byte_offsets(self):
        tok = ByteBPE()
        row = serialize([{"role": "user", "content": "café?"}, {"role": "assistant", "content": "Oui ☕"}])
        encoded = encode_assistant_labels(row, tok)
        self.assertEqual(tok.decode([x for x in encoded["labels"] if x != -100]), "Oui ☕<|im_end|>")

    def test_rejects_invalid_span(self):
        with self.assertRaises(ValueError):
            encode_assistant_labels({"text": "abc", "assistant_char_spans": [[0, 4]]}, ByteBPE())

    def test_cross_boundary_bpe_is_ignored(self):
        tok = ByteBPE([(ord("a"), ord("b"))])
        with self.assertRaises(ValueError):
            encode_assistant_labels({"text": "ab", "assistant_char_spans": [[1, 2]]}, tok)


if __name__ == "__main__":
    unittest.main()
