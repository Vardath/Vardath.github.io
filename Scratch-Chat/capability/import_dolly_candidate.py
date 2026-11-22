"""Quarantine converter for a revision-pinned Dolly-style JSONL export.

Never approves a source or feeds it to training automatically. The caller must
verify upstream licensing, provenance and privacy independently.
"""
import argparse
import hashlib
import json
from pathlib import Path


def convert(source, output, *, revision, expected_sha256, source_id="dolly-candidate"):
    if not revision or revision in {"main", "master", "latest"}:
        raise ValueError("An immutable upstream revision is required")
    raw = Path(source).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError("Raw source SHA-256 mismatch")
    records = []
    seen = set()
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError("Expected JSON object")
        instruction = item.get("instruction")
        response = item.get("response")
        context = item.get("context", "")
        if not isinstance(instruction, str) or not instruction.strip():
            continue
        if not isinstance(response, str) or not response.strip():
            continue
        if not isinstance(context, str):
            raise ValueError("Invalid context")
        user = instruction.strip()
        if context.strip():
            user += "\n\nContext:\n" + context.strip()
        signature = hashlib.sha256((user + "\0" + response.strip()).encode()).hexdigest()
        if signature in seen:
            continue
        seen.add(signature)
        records.append({
            "id": f"{source_id}:{line_number}",
            "source_id": source_id,
            "source_revision": revision,
            "source_line": line_number,
            "license": "PENDING-REVIEW",
            "messages": [
                {"role": "user", "content": user},
                {"role": "assistant", "content": response.strip()},
            ],
        })
    if not records:
        raise ValueError("No usable instruction/response pairs")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Refusing to overwrite quarantined corpus")
    payload = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in records)
    output.write_text(payload, encoding="utf-8")
    return {
        "status": "QUARANTINED_NOT_APPROVED",
        "source_id": source_id, "revision": revision,
        "raw_sha256": actual, "records": len(records),
        "output_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "next": "Independently review upstream license, attribution, privacy and provenance; run admission/split audit before training.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source-id", default="dolly-candidate")
    args = parser.parse_args()
    print(json.dumps(convert(args.source, args.output, revision=args.revision,
                             expected_sha256=args.sha256, source_id=args.source_id), indent=2))


if __name__ == "__main__":
    main()
