"""Assistant-only SFT must teach turn termination without supervising user text."""
import unittest
from capability.bpe import ByteBPE
from capability.dialogue_format import serialize
from capability.dialogue_labels import encode_assistant_labels


class AssistantTerminationTrainingTests(unittest.TestCase):
    def test_assistant_end_marker_is_supervised(self):
        item = serialize([
            {"role": "user", "content": "Unique user prompt"},
            {"role": "assistant", "content": "A short answer"},
        ])
        self.assertEqual(
            [item["text"][a:b] for a, b in item["assistant_termination_char_spans"]],
            ["<|im_end|>"])
        labeled = encode_assistant_labels(item, ByteBPE([]))
        tokens = labeled["input_ids"]
        labels = labeled["labels"]
        supervised = bytes(t for t, y in zip(tokens, labels) if y != -100).decode()
        self.assertIn("A short answer", supervised)
        self.assertIn("<|im_end|>", supervised)
        self.assertNotIn("Unique user prompt", supervised)

    def test_invalid_termination_marker_is_rejected(self):
        item = serialize([{"role": "user", "content": "Hello"},
                          {"role": "assistant", "content": "Hi"}])
        item["assistant_termination_char_spans"] = [[0, 2]]
        with self.assertRaises(ValueError):
            encode_assistant_labels(item, ByteBPE([]))


if __name__ == "__main__":
    unittest.main()
