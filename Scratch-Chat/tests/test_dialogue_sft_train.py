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

    def test_resumed_training_matches_uninterrupted_weights(self):
        """A checkpoint resume must reproduce the exact original-weight trajectory."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            train, valid = root / "train.jsonl", root / "valid.jsonl"
            write_rows(train, [
                {"input_ids": [1, 2, 3, 4], "labels": [-100, -100, 3, 4]},
                {"input_ids": [1, 2, 5, 6], "labels": [-100, -100, 5, 6]},
                {"input_ids": [1, 2, 7, 8], "labels": [-100, -100, 7, 8]},
            ])
            write_rows(valid, [
                {"input_ids": [1, 9, 10, 11], "labels": [-100, -100, 10, 11]}
            ])
            settings = dict(vocab_size=16, width=16, layers=1, heads=2,
                            context_size=16, seed=42)
            uninterrupted = root / "full.pt"
            resumed = root / "resume.pt"
            run(train, valid, uninterrupted, steps=5, **settings)
            run(train, valid, resumed, steps=2, **settings)
            run(train, valid, resumed, steps=5, resume=True, **settings)
            a = torch.load(uninterrupted, weights_only=True)
            b = torch.load(resumed, weights_only=True)
            self.assertEqual(a["step"], b["step"])
            self.assertEqual(a["immutable"], b["immutable"])
            self.assertEqual(a["validation_assistant_loss"], b["validation_assistant_loss"])
            for name, tensor in a["model_state"].items():
                self.assertTrue(torch.equal(tensor, b["model_state"][name]), name)
            self.assertTrue(torch.equal(a["rng_state"], b["rng_state"]))

    def test_resume_rejects_corrupted_step_and_rng(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            train, valid, checkpoint = (root / name for name in ("train.jsonl", "valid.jsonl", "pilot.pt"))
            write_rows(train, [{"input_ids": [1, 2, 3, 4], "labels": [-100, -100, 3, 4]}])
            write_rows(valid, [{"input_ids": [1, 5, 6, 7], "labels": [-100, -100, 6, 7]}])
            opts = dict(vocab_size=16, width=16, layers=1, heads=2, context_size=16)
            run(train, valid, checkpoint, steps=1, **opts)
            original = torch.load(checkpoint, weights_only=True)
            for bad_step in (-1, 0, "1", True):
                torch.save(dict(original, step=bad_step), checkpoint)
                with self.assertRaisesRegex(ValueError, "checkpoint step"):
                    run(train, valid, checkpoint, steps=2, resume=True, **opts)
            for bad_rng in (None, torch.tensor([1, 2], dtype=torch.uint8)):
                torch.save(dict(original, rng_state=bad_rng), checkpoint)
                with self.assertRaisesRegex(ValueError, "RNG state"):
                    run(train, valid, checkpoint, steps=2, resume=True, **opts)

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
            self.assertEqual(result["validation_supervised_tokens"], 2)
            self.assertEqual(torch.load(checkpoint, weights_only=True)["validation_supervised_tokens"], 2)
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
