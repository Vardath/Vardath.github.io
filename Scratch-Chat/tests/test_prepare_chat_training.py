"""Training conversion must preserve turns and fail closed on contamination."""
import json
import tempfile
import unittest
from pathlib import Path
from capability.prepare_chat_training import build


class ChatTrainingConversionTests(unittest.TestCase):
    def test_preserves_roles_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"
            source.mkdir()
            for split, phrase in (("train", "violet orbit"), ("validation", "copper river"), ("test", "silver meadow")):
                record = {"license": "CC0-1.0", "source_conversation_id": phrase,
                          "messages": [{"role": "user", "content": "Describe " + phrase},
                                       {"role": "assistant", "content": "This is " + phrase}]}
                (source / (split + ".jsonl")).write_text(json.dumps(record) + "\n")
            report = build(source, target)
            self.assertTrue(report["audit"]["passed"])
            for split in ("train", "validation", "test"):
                row = json.loads((target / (split + ".jsonl")).read_text().strip())
                self.assertEqual(row["kind"], "chat")
                self.assertEqual([m["role"] for m in row["messages"]], ["user", "assistant"])
                self.assertEqual(row["license"], "CC0-1.0")
            with self.assertRaises(FileExistsError):
                build(source, target)

    def test_rejects_cross_split_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            record = {"messages": [{"role": "user", "content": "Repeat identical secret phrase"},
                                   {"role": "assistant", "content": "The identical answer phrase"}]}
            for split in ("train", "validation", "test"):
                (source / (split + ".jsonl")).write_text(json.dumps(record) + "\n")
            with self.assertRaises(ValueError):
                build(source, Path(tmp) / "target")


if __name__ == "__main__":
    unittest.main()
