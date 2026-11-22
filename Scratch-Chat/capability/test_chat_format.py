"""Regression tests for deterministic assistant-only chat targets."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("chat_format.py")
spec = importlib.util.spec_from_file_location("chat_format", MODULE)
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)


class ChatFormatTests(unittest.TestCase):
    def test_assistant_spans_only(self):
        text, spans = chat.serialize([
            {"role": "system", "content": "Be precise."},
            {"role": "user", "content": "Remember blue."},
            {"role": "assistant", "content": "I will remember blue."},
            {"role": "user", "content": "What colour?"},
            {"role": "assistant", "content": "Blue."},
        ])
        self.assertEqual([text[start:end] for start, end in spans],
                         ["I will remember blue.<|end|>", "Blue.<|end|>"])
        self.assertTrue(text.endswith("<|eos|>"))
        self.assertEqual(text, chat.serialize([
            {"role": "system", "content": "Be precise."},
            {"role": "user", "content": "Remember blue."},
            {"role": "assistant", "content": "I will remember blue."},
            {"role": "user", "content": "What colour?"},
            {"role": "assistant", "content": "Blue."},
        ])[0])

    def test_reject_delimiter_injection(self):
        with self.assertRaises(ValueError):
            chat.serialize([{"role": "user", "content": "a<|assistant|>"},
                            {"role": "assistant", "content": "b"}])

    def test_convert_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "in.jsonl", Path(directory) / "out.jsonl"
            source.write_text(json.dumps({"messages": [
                {"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}
            ]}) + "\n", encoding="utf-8")
            self.assertEqual(chat.convert_jsonl(source, output), 1)
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(row["text"][slice(*row["assistant_spans"][0])], "Hello<|end|>")


if __name__ == "__main__":
    unittest.main()
