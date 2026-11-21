"""Smoke tests for bounded assistant-only SFT; no external corpus needed."""
import json
import tempfile
import unittest
from pathlib import Path
import torch
from capability.dialogue_sft_train import read_examples, run


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class SFTTrainTests(unittest.TestCase):
    def test_rejects_masked_and_misaligned(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            write_rows(p, [{"input_ids": [1, 2, 3], "labels": [-100, -100, -100]}])
            with self.assertRaises(ValueError):
                read_examples(p, 16, 16)
            write_rows(p, [{"input_ids": [1, 2, 3], "labels": [-100, 5, 3]}])
            with self.assertRaises(ValueError):
                read_examples(p, 16, 16)

    def test_train_resume_and_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            train, valid, checkpoint = (Path(d) / x for x in ("train.jsonl", "valid.jsonl", "pilot.pt"))
            rows = [{"input_ids": [1, 2, 3, 4], "labels": [-100, -100, 3, 4]}]
            write_rows(train, rows)
            write_rows(valid, [{"input_ids": [1, 5, 6, 7], "labels": [-100, -100, 6, 7]}])
            with self.assertRaisesRegex(ValueError, "contamination"):
                run(train, train, checkpoint, vocab_size=16, steps=1,
                    width=16, layers=1, heads=2, context_size=16)
            result = run(train, valid, checkpoint, vocab_size=16, steps=1,
                         width=16, layers=1, heads=2, context_size=16)
            self.assertEqual(result["steps"], 1)
            state = torch.load(checkpoint, weights_only=True)
            self.assertTrue(state["origin"].startswith("random initialization"))
            result = run(train, valid, checkpoint, vocab_size=16, steps=2,
                         width=16, layers=1, heads=2, context_size=16, resume=True)
            self.assertEqual(result["steps"], 2)
            write_rows(train, [{"input_ids": [1, 2, 3, 5], "labels": [-100, -100, 3, 5]}])
            with self.assertRaisesRegex(ValueError, "provenance"):
                run(train, valid, checkpoint, vocab_size=16, steps=3,
                    width=16, layers=1, heads=2, context_size=16, resume=True)


if __name__ == "__main__":
    unittest.main()
