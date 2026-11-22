"""Independent post-split leakage audit; never grants training approval."""
import argparse
import hashlib
import json
from pathlib import Path

def normalized(text):
    return " ".join(text.casefold().split())

def audit_splits(directory):
    directory = Path(directory)
    owners = {}
    overlaps = []
    counts = {}
    hashes = {}
    for split in ("train", "validation", "test"):
        path = directory / (split + ".jsonl")
        raw = path.read_bytes()
        hashes[split] = hashlib.sha256(raw).hexdigest()
        counts[split] = 0
        for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            row = json.loads(line)
            if not isinstance(row.get("messages"), list):
                raise ValueError(f"Invalid messages in {split}:{number}")
            prompts = [normalized(m["content"]) for m in row["messages"] if m.get("role") == "user"]
            if not prompts:
                raise ValueError(f"No user prompt in {split}:{number}")
            key = "\\n".join(prompts)
            previous = owners.setdefault(key, split)
            if previous != split:
                overlaps.append({"split": split, "previous_split": previous, "line": number,
                                 "prompt_sha256": hashlib.sha256(key.encode()).hexdigest()})
            counts[split] += 1
    report = {"status": "QUARANTINED_NOT_APPROVED", "training_allowed": False,
              "split_records": counts, "split_sha256": hashes,
              "cross_split_exact_prompt_overlap": len(overlaps), "overlaps": overlaps[:50],
              "limitations": "Exact normalized prompts only; semantic/paraphrase leakage and benchmark contamination untested"}
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_splits(args.directory)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["split_records"], "cross_split_overlap": report["cross_split_exact_prompt_overlap"]}))
    if report["cross_split_exact_prompt_overlap"]:
        raise SystemExit("Cross-split prompt contamination detected")

if __name__ == "__main__":
    main()
