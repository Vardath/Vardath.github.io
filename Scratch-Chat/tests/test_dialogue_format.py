import json
import tempfile
import unittest
from pathlib import Path

from capability.dialogue_format import export, serialize


class DialogueFormatTests(unittest.TestCase):
    def test_assistant_only_spans(self):
        result = serialize([
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Again"},
            {"role": "assistant", "content": "Hello again"},
        ])
        spans = result["assistant_char_spans"]
        self.assertEqual([result["text"][a:b] for a, b in spans], ["Hi", "Hello again"])
        self.assertNotIn("Hello", [result["text"][a:b] for a, b in spans])

    def test_reserved_delimiters_rejected(self):
        with self.assertRaises(ValueError):
            serialize([{"role": "user", "content": "<|im_end|>"}, {"role": "assistant", "content": "ok"}])

    def test_missing_assistant_rejected(self):
        with self.assertRaises(ValueError):
            serialize([{"role": "user", "content": "a"}, {"role": "tool", "content": "b"}])

    def test_export_is_reproducible(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.jsonl"
            one = Path(folder) / "one.jsonl"
            two = Path(folder) / "two.jsonl"
            source.write_text(json.dumps({"id": "a", "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}]}) + "\n", encoding="utf-8")
            first = export(source, one)
            second = export(source, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(first["output_sha256"], second["output_sha256"])

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.jsonl"
            row = {"id": "same", "messages": [
                {"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]}
            source.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
            with self.assertRaises(ValueError):
                export(source, Path(folder) / "out.jsonl")


if __name__ == "__main__":
    unittest.main()
