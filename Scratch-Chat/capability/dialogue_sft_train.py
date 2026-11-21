"""Bounded assistant-only SFT pilot for independently initialized Scratch Chat.

Input: JSONL from capability.dialogue_labels.export; never silently load
pretrained weights. CPU pilot only; not a conversational acceptance claim.
"""
import argparse
import json
import random
from dataclasses import asdict
from pathlib import Path

import torch

from capability.modern_model import ModernConfig, ModernScratchTransformer
from capability.dialogue_sft_loss import assistant_causal_loss
from capability.pretrain import atomic_save, file_hash

FORMAT = "vardath-scratch-assistant-sft-v1"


def read_examples(path, vocab_size, context_size):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        ids, labels = row["input_ids"], row["labels"]
        if (len(ids) != len(labels) or len(ids) < 2 or len(ids) > context_size
                or any(type(x) is not int or x < 0 or x >= vocab_size for x in ids)
                or any(type(y) is not int or (y != -100 and y != x)
                       for x, y in zip(ids, labels))
                or not any(y != -100 for y in labels[1:])):
            raise ValueError("Invalid or unsupervised SFT example")
        rows.append((ids, labels))
    if not rows:
        raise ValueError("Empty SFT dataset")
    return rows


def run(train_path, validation_path, checkpoint, *, vocab_size, steps=10,
        width=64, layers=2, heads=4, context_size=256, lr=0.0003,
        seed=2026, resume=False):
    if steps < 1 or lr <= 0:
        raise ValueError("Invalid SFT controls")
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    cfg = ModernConfig(vocab_size=vocab_size, width=width, layers=layers,
                       heads=heads, context_size=context_size)
    train = read_examples(train_path, vocab_size, context_size)
    valid = read_examples(validation_path, vocab_size, context_size)
    # Validation must not contain any training sequence, even under different row IDs.
    train_sequences = {tuple(ids) for ids, _ in train}
    if any(tuple(ids) in train_sequences for ids, _ in valid):
        raise ValueError("Train/validation sequence contamination")
    immutable = {"train_sha256": file_hash(train_path),
                 "validation_sha256": file_hash(validation_path),
                 "config": asdict(cfg), "lr": lr, "seed": seed}
    random.seed(seed)
    torch.manual_seed(seed)
    model = ModernScratchTransformer(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    start = 0
    checkpoint = Path(checkpoint)
    if resume:
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        if state.get("format") != FORMAT or state.get("immutable") != immutable:
            raise ValueError("SFT resume provenance mismatch")
        model.load_state_dict(state["model_state"])
        optimizer.load_state_dict(state["optimizer_state"])
        torch.set_rng_state(state["rng_state"])
        start = int(state["step"])
    elif checkpoint.exists():
        raise FileExistsError("Checkpoint exists; explicitly resume")
    if steps <= start:
        raise ValueError("Target steps must exceed saved step")
    for step in range(start + 1, steps + 1):
        ids, labels = train[(step - 1) % len(train)]
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = assistant_causal_loss(
            model(torch.tensor([ids])), torch.tensor([labels]))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        weighted_loss = 0.0
        supervised_tokens = 0
        for ids, labels in valid:
            loss = assistant_causal_loss(
                model(torch.tensor([ids])), torch.tensor([labels]))
            count = sum(y != -100 for y in labels[1:])
            weighted_loss += float(loss) * count
            supervised_tokens += count
    # Token-weighted corpus loss, not an average of differently sized examples.
    metric = weighted_loss / supervised_tokens
    atomic_save({"format": FORMAT, "immutable": immutable, "step": steps,
                 "model_state": model.state_dict(),
                 "optimizer_state": optimizer.state_dict(),
                 "rng_state": torch.get_rng_state(),
                 "validation_assistant_loss": metric,
                 "validation_supervised_tokens": supervised_tokens,
                 "origin": "random initialization; no pretrained weights"}, checkpoint)
    return {"steps": steps, "validation_assistant_loss": metric,
            "parameters": model.parameter_count, "train_examples": len(train),
            "validation_examples": len(valid),
            "validation_supervised_tokens": supervised_tokens}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--validation", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--vocab-size", type=int, required=True)
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--resume", action="store_true")
    a = p.parse_args()
    print(json.dumps(run(a.train, a.validation, a.checkpoint,
                         vocab_size=a.vocab_size, steps=a.steps,
                         resume=a.resume), indent=2))
