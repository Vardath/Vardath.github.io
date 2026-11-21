"""Smoke tests for bounded assistant-only SFT; no external corpus needed."""
import json
from pathlib import Path
import pytest
import torch
from capability.dialogue_sft_train import read_examples, run


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_rejects_masked_and_misaligned(tmp_path):
    p = tmp_path / "bad.jsonl"
    write_rows(p, [{"input_ids": [1, 2, 3], "labels": [-100, -100, -100]}])
    with pytest.raises(ValueError):
        read_examples(p, 16, 16)
    write_rows(p, [{"input_ids": [1, 2, 3], "labels": [-100, 5, 3]}])
    with pytest.raises(ValueError):
        read_examples(p, 16, 16)


def test_train_resume_and_provenance(tmp_path):
    train, valid, checkpoint = (tmp_path / x for x in ("train.jsonl", "valid.jsonl", "pilot.pt"))
    rows = [{"input_ids": [1, 2, 3, 4], "labels": [-100, -100, 3, 4]}]
    write_rows(train, rows)
    write_rows(valid, rows)
    result = run(train, valid, checkpoint, vocab_size=16, steps=1,
                 width=16, layers=1, heads=2, context_size=16)
    assert result["steps"] == 1
    state = torch.load(checkpoint, weights_only=True)
    assert state["origin"].startswith("random initialization")
    result = run(train, valid, checkpoint, vocab_size=16, steps=2,
                 width=16, layers=1, heads=2, context_size=16, resume=True)
    assert result["steps"] == 2
    write_rows(train, [{"input_ids": [1, 2, 3, 5], "labels": [-100, -100, 3, 5]}])
    with pytest.raises(ValueError, match="provenance"):
        run(train, valid, checkpoint, vocab_size=16, steps=3,
            width=16, layers=1, heads=2, context_size=16, resume=True)
