"""Train an independent ByteBPE tokenizer on dialogue TRAIN only.

Validation and test examples must never influence vocabulary fitting.
"""
import argparse
import hashlib
import json
from pathlib import Path
from capability.bpe import ByteBPE

def build(corpus: Path, output: Path, merges: int = 128):
    source = corpus / "train.jsonl"
    raw = source.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty training split")
    texts = []
    for row in rows:
        if row.get("kind") == "chat" and isinstance(row.get("messages"), list):
            messages = row["messages"]
            if not messages or any(not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant") or not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
                raise ValueError("Malformed chat training record")
            texts.extend(m["content"] for m in messages)
        elif isinstance(row.get("text"), str) and row["text"].strip():
            texts.append(row["text"])
        else:
            raise ValueError("Missing or malformed dialogue training text")
    tokenizer = ByteBPE.train(texts, merges=merges)
    tokenizer.save(output)
    return {"source_split": "train", "train_sha256": hashlib.sha256(raw).hexdigest(),
            "vocab_size": tokenizer.vocab_size, "merges": len(tokenizer.merges),
            "held_out_used_for_fitting": False}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.corpus, args.output), indent=2))
