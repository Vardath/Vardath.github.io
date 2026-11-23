"""Fail-closed readiness gate for dialogue training, separate from pipeline smoke tests.

Usage: python -m capability.dialogue_readiness PATH_TO_SPLITS
A passing smoke test is not evidence of a sufficiently broad training corpus.
"""
import argparse
import json
from pathlib import Path

from .audit_near_duplicates import audit


def assess(directory, *, min_train=1000, min_validation=100, min_test=100,
           threshold=0.8):
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 1
           for n in (min_train, min_validation, min_test)):
        raise ValueError("minimum record counts must be positive integers")
    directory = Path(directory)
    counts = {}
    groups = {}
    for split in ("train", "validation", "test"):
        path = directory / (split + ".jsonl")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        counts[split] = len(rows)
        groups[split] = set()
        for row in rows:
            family = row.get("source_conversation_id") or row.get("conversation_id")
            if not isinstance(family, str) or not family.strip():
                raise ValueError(f"missing source conversation ID in {split}")
            groups[split].add(family)
            if row.get("license") not in ("CC0-1.0", "CC-BY-4.0", "Apache-2.0", "MIT"):
                raise ValueError(f"unreviewed or missing license in {split}")
    overlap = sorted((groups["train"] & groups["validation"]) |
                     (groups["train"] & groups["test"]) |
                     (groups["validation"] & groups["test"]))
    contamination = audit(directory, threshold=threshold)
    minimums = {"train": min_train, "validation": min_validation, "test": min_test}
    reasons = [f"{split} has {counts[split]} records; minimum {minimums[split]}"
               for split in minimums if counts[split] < minimums[split]]
    if overlap:
        reasons.append(f"{len(overlap)} source conversations cross splits")
    if not contamination["passed"]:
        reasons.append(f"{len(contamination['findings'])} cross-split lexical overlaps")
    reasons.append("License labels are self-reported; independent provenance approval is still required")
    return {"ready_for_capacity_training": False,
            "automated_preflight_passed": not reasons[:-1],
            "counts": counts, "minimums": minimums,
            "contamination": contamination, "cross_split_groups": overlap,
            "reasons": reasons}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = assess(args.directory)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["automated_preflight_passed"] else 1)


if __name__ == "__main__":
    main()
