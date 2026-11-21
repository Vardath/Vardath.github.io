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
    "clarification": [("Help me choose a device.", "What will you use it for?"), ("Book a table for me.", "What date, time, and party size do you want?"), ("Summarize the document.", "Please provide the document to summarize.")],
    "tool_boundary": [("Can you see my private calendar?", "I cannot access your calendar without a connected tool."), ("Run a calculator for me.", "No calculator tool is available in this session."), ("Have you sent the email?", "No. I have not sent an email.")],
    "multi_turn": [("User: Remember that the parcel is blue.\nAssistant: Understood.\nUser: What color is the parcel?", "The parcel is blue."), ("User: My destination is Perth.\nAssistant: Noted.\nUser: Which city did I name?", "Perth."), ("User: The project is called Orion.\nAssistant: Understood.\nUser: What is the project called?", "Orion.")],
    "uncertainty": [("What is my password?", "I do not know your password."), ("What did I eat yesterday?", "I do not have that information."), ("Can you guarantee every answer is correct?", "No. My answers can contain errors.")],
}
SPLITS = {"train": ("arithmetic", "format", "conversation", "uncertainty", "clarification", "tool_boundary", "multi_turn"),
          "validation": ("explanation",),
          "test": ("reasoning",)}

def validate(out: Path):
    """Check manifest digests, split isolation and duplicate dialogue leakage."""
    manifest = json.loads((out / "source.json").read_text(encoding="utf-8"))
    if manifest.get("license") != "CC0-1.0":
        raise ValueError("Unexpected dialogue provenance")
    families_seen = set()
    texts_seen = set()
    for split in ("train", "validation", "test"):
        payload = (out / (split + ".jsonl")).read_bytes()
        if hashlib.sha256(payload).hexdigest() != manifest["sha256"][split]:
            raise ValueError("Corpus digest mismatch: " + split)
        rows = [json.loads(line) for line in payload.decode("utf-8").splitlines()]
        if len(rows) != manifest["examples"][split] or not rows:
            raise ValueError("Corpus count mismatch: " + split)
        families = set()
        for row in rows:
            if set(row) != {"text", "family"} or not isinstance(row["text"], str) or not isinstance(row["family"], str):
                raise ValueError("Malformed dialogue row")
            if not row["text"].startswith("User: ") or "\nAssistant: " not in row["text"]:
                raise ValueError("Malformed dialogue turns")
            if row["text"] in texts_seen:
                raise ValueError("Dialogue leakage across rows or splits")
            texts_seen.add(row["text"])
            families.add(row["family"])
        if families & families_seen:
            raise ValueError("Task family leakage between splits")
        families_seen.update(families)
    return {"validated": True, "examples": len(texts_seen), "families": len(families_seen)}


def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for split, families in SPLITS.items():
        rows = []
        for family in families:
            for question, answer in FAMILIES[family]:
                rows.append({"text": (question if question.startswith("User: ") else "User: " + question) + "\nAssistant: " + answer + "\n", "family": family})
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        (out / (split + ".jsonl")).write_text(payload, encoding="utf-8")
        hashes[split] = hashlib.sha256(payload.encode()).hexdigest()
    manifest = {"license": "CC0-1.0", "origin": "Original examples authored for this repository",
                "purpose": "Data-format and split-isolation smoke test only",
                "split_policy": "Disjoint task families; no family shared across splits",
                "examples": {s: sum(len(FAMILIES[f]) for f in fs) for s, fs in SPLITS.items()},
                "sha256": hashes, "warning": "Tiny authored seed; insufficient for a capable conversational model."}
    (out / "source.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    validate(out)
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
