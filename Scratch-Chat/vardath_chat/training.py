"""Train all model weights from random initialization on local JSONL conversations."""
from __future__ import annotations
import json
import random
import time
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F
from .model import ModelConfig, ScratchTransformer
from .tokenizer import encode_training_example, PAD
from .engine import save_checkpoint


def read_data(path: Path, context_size: int) -> list[tuple[list[int], list[int]]]:
    examples = []
    skipped = 0
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                messages = item["messages"]
                examples.append(encode_training_example(messages, context_size))
            except ValueError as e:
                if "exceeds context" in str(e):
                    skipped += 1
                    continue
                raise ValueError(f"Line {lineno}: {e}") from e
    if not examples:
        raise ValueError("No usable training conversations; increase --context or shorten samples")
    print(f"Loaded {len(examples)} examples (skipped {skipped} for context length).", flush=True)
    return examples


def train(data: Path, output: Path, *, steps: int = 800, batch: int = 12,
          context: int = 256, width: int = 96, layers: int = 3, heads: int = 4,
          lr: float = 0.0008, seed: int = 17, threads: int = 4,
          save_every: int = 100, resume: bool = False) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(max(1, threads))
    device = "cpu"  # Supported on Windows and the user's older AMD GPU setup.
    cfg = ModelConfig(context_size=context, width=width, layers=layers, heads=heads)
    records = read_data(data, context)
    model = ScratchTransformer(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    start_step = 0
    if resume and output.exists():
        state = torch.load(output, map_location="cpu", weights_only=True)
        if state["config"] != cfg.__dict__:
            raise ValueError("Checkpoint config does not match requested architecture")
        model.load_state_dict(state["state"])
        start_step = int(state.get("metadata", {}).get("steps", 0))
        print(f"Resuming from weights saved after step {start_step} (optimizer starts fresh).",flush=True)
    print(f"Training {sum(p.numel() for p in model.parameters()):,} randomly initialized parameters on CPU.", flush=True)
    t0 = time.monotonic()
    for step in range(start_step + 1, start_step + steps + 1):
        selected = random.choices(records, k=batch)
        length = max(len(x[0]) for x in selected)
        ids = torch.full((batch, length), PAD, dtype=torch.long, device=device)
        labels = torch.full((batch, length), -100, dtype=torch.long, device=device)
        for i, (sequence, target) in enumerate(selected):
            ids[i, :len(sequence)] = torch.tensor(sequence, dtype=torch.long)
            labels[i, :len(target)] = torch.tensor(target, dtype=torch.long)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = model(ids)
        loss = F.cross_entropy(logits.reshape(-1, cfg.vocab_size), labels.reshape(-1), ignore_index=-100)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        if step % 25 == 0 or step == 1:
            print(f"step {step:5d} | loss {loss.item():.4f} | elapsed {time.monotonic()-t0:.1f}s", flush=True)
        if step % save_every == 0 or step == start_step + steps:
            save_checkpoint(output, model, {"steps": step, "trained_from_random_init": True, "continued_training": bool(resume),
                                            "data_file": data.name, "training_loss": float(loss.item()),
                                            "seed": seed})
    print(f"Saved trained weights to {output}", flush=True)
