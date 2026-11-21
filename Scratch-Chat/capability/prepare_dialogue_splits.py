"""Deterministic, group-isolated split preparation for reviewed dialogue JSONL.

This does not grant dataset licensing approval. Preserve upstream provenance and
run dialogue_source_manifest.verify_split_files before training.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def prepare(source, output, *, seed="scratch-chat-v1", train_fraction=0.9, validation_fraction=0.05):
    if not (0 < validation_fraction < 1 and 0 < train_fraction < 1 and train_fraction + validation_fraction < 1):
        raise ValueError("Invalid split fractions")
    source, output = Path(source), Path(output)
    groups = defaultdict(list)
    prompt_owner = {}
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"Blank record at line {line_number}")
        record = json.loads(line)
        if not isinstance(record, dict) or not isinstance(record.get("messages"), list) or not record["messages"]:
            raise ValueError(f"Invalid dialogue at line {line_number}")
        messages = record["messages"]
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in ("system", "user", "assistant") or not isinstance(message.get("content"), str) or not message["content"].strip():
                raise ValueError(f"Invalid message at line {line_number}")
        if not any(m["role"] == "user" for m in messages) or not any(m["role"] == "assistant" for m in messages):
            raise ValueError(f"Missing user/assistant at line {line_number}")
        family = next((str(record[key]).strip() for key in ("source_conversation_id", "conversation_id", "template_family_id") if record.get(key)), None)
        # Without upstream IDs, use normalized user-turn text to prevent
        # identical prompts with different answers crossing split boundaries.
        prompts = "\n".join(" ".join(m["content"].split()).casefold() for m in messages if m["role"] == "user")
        if not prompts:
            raise ValueError("Missing user prompt")
        group_key = family or "prompt:" + prompts
        previous = prompt_owner.get(prompts)
        if previous is not None and previous != group_key:
            raise ValueError(f"Same user prompt assigned to different upstream families at line {line_number}")
        prompt_owner[prompts] = group_key
        groups[group_key].append(record)
    if len(groups) < 3:
        raise ValueError("At least three independent conversation groups required")
    ranked = sorted(groups, key=lambda key: hashlib.sha256((seed + ":" + key).encode()).hexdigest())
    # Assign groups by rank, not individual turns, with nonempty partitions.
    count = len(ranked)
    n_train = max(1, min(count - 2, round(count * train_fraction)))
    n_val = max(1, min(count - n_train - 1, round(count * validation_fraction)))
    partitions = {"train": ranked[:n_train], "validation": ranked[n_train:n_train + n_val], "test": ranked[n_train + n_val:]}
    output.mkdir(parents=True, exist_ok=True)
    report = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "seed": seed, "splits": {}}
    for split, keys in partitions.items():
        # Canonical, stable JSONL; provenance metadata is retained.
        data = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for key in keys for record in groups[key]).encode("utf-8")
        (output / (split + ".jsonl")).write_bytes(data)
        report["splits"][split] = {"groups": len(keys), "records": sum(len(groups[key]) for key in keys), "sha256": hashlib.sha256(data).hexdigest()}
    (output / "split_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", default="scratch-chat-v1")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
