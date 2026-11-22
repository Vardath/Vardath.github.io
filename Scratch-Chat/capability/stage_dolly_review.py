"""Create quarantined, filtered review partitions from an audited Dolly acquisition.

This does NOT license or approve records for training.
"""
import argparse
import hashlib
import json
from pathlib import Path

from capability.audit_dolly_quarantine import audit, EMAIL, PHONE, URL, SECRET
from capability.prepare_dialogue_splits import prepare

PATTERNS = (EMAIL, PHONE, URL, SECRET)


def stage(directory, output):
    directory, output = Path(directory), Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite review staging")
    report = audit(directory)
    flagged = {str(item["record_id"]) for item in report["flagged_records"]}
    seen = set()
    retained = []
    removed_flags = removed_duplicates = 0
    for line in (directory / "quarantined.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        messages = record["messages"]
        if str(record["id"]) in flagged or any(
            pattern.search(m["content"]) for pattern in PATTERNS for m in messages
        ):
            removed_flags += 1
            continue
        canonical = "\0".join(" ".join(m["content"].casefold().split()) for m in messages)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if digest in seen:
            removed_duplicates += 1
            continue
        seen.add(digest)
        retained.append(record)
    if len(retained) < 3:
        raise ValueError("Insufficient independent clean candidates")
    output.mkdir(parents=True)
    source = output / "review_candidates.jsonl"
    source.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in retained), encoding="utf-8")
    splits = prepare(source, output / "review_splits")
    summary = {
        "status": "QUARANTINED_NOT_APPROVED",
        "training_allowed": False,
        "source_commit": report["source_commit"],
        "source_raw_sha256": report["raw_sha256"],
        "source_converted_sha256": report["converted_sha256"],
        "source_records": report["counts"]["records"],
        "removed_flagged_records": removed_flags,
        "removed_exact_duplicate_pairs": removed_duplicates,
        "retained_records": len(retained),
        "split_report": splits,
        "limitations": [
            "Regex filtering does not guarantee removal of personal information",
            "No semantic or paraphrase decontamination; no independent benchmark review",
            "Dolly license, attribution, consent and commercial-use obligations remain unapproved",
            "These partitions are quarantined review material, NOT approved training data",
        ],
    }
    (output / "review_report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = stage(args.directory, args.output)
    print(json.dumps({k: result[k] for k in ("status", "source_records", "removed_flagged_records", "removed_exact_duplicate_pairs", "retained_records")}))


if __name__ == "__main__":
    main()
