"""Original, reproducible dialogue seed corpus. Not a substitute for large-scale licensed data.

Split by task family, not random utterances, to avoid template leakage into
held-out evaluation. This is a pipeline smoke test, NOT an independent benchmark.
"""
import argparse
import hashlib
import json
from pathlib import Path

FAMILIES = {
    "arithmetic": [("What is 2 plus 3?", "5"), ("What is 7 minus 4?", "3"), ("What is 6 times 2?", "12")],
    "format": [("Reply with only the word amber.", "amber"), ("Reply with only the word copper.", "copper"), ("Reply with only the word silver.", "silver")],
    "explanation": [("Why do objects fall?", "Gravity accelerates objects toward Earth."), ("Why does ice melt?", "Ice melts when it absorbs enough heat."), ("Why does rain fall?", "Water droplets fall when gravity overcomes the forces keeping them aloft.")],
    "reasoning": [("If I have four apples and give away one, how many remain?", "Three apples remain."), ("A box contains two red balls and one blue ball. How many balls?", "Three balls."), ("Is 9 greater than 12?", "No, 9 is less than 12.")],
    "conversation": [("Hello!", "Hello. How can I help?"), ("Thank you.", "You're welcome."), ("Can you explain that again?", "Yes. Which part would you like clarified?")],
    "uncertainty": [("What is my password?", "I do not know your password."), ("What did I eat yesterday?", "I do not have that information."), ("Can you guarantee every answer is correct?", "No. My answers can contain errors.")],
}
SPLITS = {"train": ("arithmetic", "format", "conversation", "uncertainty"),
          "validation": ("explanation",),
          "test": ("reasoning",)}

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for split, families in SPLITS.items():
        rows = []
        for family in families:
            for question, answer in FAMILIES[family]:
                rows.append({"text": "User: " + question + "\nAssistant: " + answer + "\n", "family": family})
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        (out / (split + ".jsonl")).write_text(payload, encoding="utf-8")
        hashes[split] = hashlib.sha256(payload.encode()).hexdigest()
    manifest = {"license": "CC0-1.0", "origin": "Original examples authored for this repository",
                "purpose": "Data-format and split-isolation smoke test only",
                "split_policy": "Disjoint task families; no family shared across splits",
                "examples": {s: sum(len(FAMILIES[f]) for f in fs) for s, fs in SPLITS.items()},
                "sha256": hashes, "warning": "Tiny authored seed; insufficient for a capable conversational model."}
    (out / "source.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
