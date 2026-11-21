"""Fail-closed lexical near-duplicate audit for prepared dialogue splits.

This is a screening aid, not semantic paraphrase detection or license approval.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def shingles(tokens, width=3):
    if len(tokens) < width:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i:i + width]) for i in range(len(tokens) - width + 1)}


def audit(directory, threshold=0.8):
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0,1]")
    directory = Path(directory)
    records = []
    for split in ("train", "validation", "test"):
        path = directory / (split + ".jsonl")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                raise ValueError(f"blank line: {path}:{number}")
            record = json.loads(line)
            messages = record.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError(f"missing messages: {path}:{number}")
            prompts = [m["content"] for m in messages if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)]
            if not prompts:
                raise ValueError(f"missing user text: {path}:{number}")
            tokens = normalize(" ".join(prompts))
            if not tokens:
                raise ValueError(f"empty normalized prompt: {path}:{number}")
            records.append((split, number, shingles(tokens)))
    findings = []
    for i, (split_a, line_a, a) in enumerate(records):
        for split_b, line_b, b in records[i + 1:]:
            if split_a == split_b:
                continue
            similarity = len(a & b) / len(a | b)
            if similarity >= threshold:
                findings.append({"a": f"{split_a}:{line_a}", "b": f"{split_b}:{line_b}", "jaccard": round(similarity, 6)})
    return {"passed": not findings, "records": len(records), "threshold": threshold, "findings": findings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()
    result = audit(args.directory, args.threshold)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
