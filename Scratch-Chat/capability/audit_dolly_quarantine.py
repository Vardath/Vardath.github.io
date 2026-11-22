"""Bounded, non-admitting audit of an acquired Dolly quarantine.

Produces aggregate counts and hashed example identifiers only; never prints
personal data or changes training_allowed. Human review remains mandatory.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")
URL = re.compile(r"https?://[^\s<>]+", re.I)
SECRET = re.compile(r"(?i)(?:api[_ -]?key|password|secret[_ -]?token)\s*[:=]\s*\S+")
MAX_RECORDS = 100000

def audit(directory):
    root = Path(directory)
    manifest = json.loads((root / "acquisition.json").read_text(encoding="utf-8"))
    if manifest.get("training_allowed") is not False or manifest.get("status") != "QUARANTINED_NOT_APPROVED":
        raise ValueError("Expected unapproved quarantine")
    raw = (root / "upstream.jsonl").read_bytes()
    converted = (root / "quarantined.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest.get("raw_sha256"):
        raise ValueError("Upstream bytes differ from acquisition manifest")
    if hashlib.sha256(converted).hexdigest() != manifest.get("converted", {}).get("output_sha256"):
        raise ValueError("Converted bytes differ from acquisition manifest")
    counters = Counter()
    unique = set()
    flags = []
    for index, line in enumerate(converted.decode("utf-8").splitlines(), 1):
        if index > MAX_RECORDS:
            raise ValueError("Audit record cap exceeded")
        row = json.loads(line)
        if not isinstance(row, dict) or row.get("license") != "PENDING-REVIEW":
            raise ValueError("Record lacks quarantine license marker")
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 2 or [m.get("role") for m in messages] != ["user", "assistant"]:
            raise ValueError("Expected user/assistant pair")
        texts = [m.get("content") for m in messages]
        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Blank dialogue content")
        counters["records"] += 1
        counters["user_characters"] += len(texts[0])
        counters["assistant_characters"] += len(texts[1])
        normalized = "\0".join(" ".join(t.casefold().split()) for t in texts)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if digest in unique:
            counters["normalized_duplicate_pairs"] += 1
        unique.add(digest)
        detected = []
        for name, regex in (("email", EMAIL), ("phone_candidate", PHONE), ("url", URL), ("credential_candidate", SECRET)):
            if any(regex.search(t) for t in texts):
                counters["flag_" + name] += 1
                detected.append(name)
        if detected:
            flags.append({"record_id": row.get("id"), "content_sha256": digest, "flags": detected})
    if counters["records"] != manifest.get("converted", {}).get("records"):
        raise ValueError("Converted record count mismatch")
    return {
        "status": "QUARANTINED_NOT_APPROVED", "training_allowed": False,
        "source_commit": manifest.get("upstream_commit"),
        "raw_sha256": manifest["raw_sha256"],
        "converted_sha256": manifest["converted"]["output_sha256"],
        "counts": dict(sorted(counters.items())),
        "flagged_records": flags,
        "limitations": [
            "Heuristic PII/credential flags are incomplete and include false positives",
            "No semantic near-duplicate or upstream-source attribution review",
            "No license, privacy, consent, or training approval is conferred",
        ],
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.directory)
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite audit")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "flagged": len(result["flagged_records"])}))

if __name__ == "__main__":
    main()
