"""Convert reviewed, group-isolated chat splits to role-token training records.

Never mix held-out messages into tokenizer fitting. Keep original split artifacts
and audit results intact; output is a separate derived training directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
from capability.audit_near_duplicates import audit


def build(source: Path, output: Path):
    source, output = Path(source), Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite derived training artifacts")
    result = audit(source, threshold=0.8)
    if not result["passed"]:
        raise ValueError("Cross-split near-duplicate audit failed: " + json.dumps(result["findings"]))
    output.mkdir(parents=True, exist_ok=True)
    report = {"audit": result, "splits": {}}
    for split in ("train", "validation", "test"):
        raw = (source / (split + ".jsonl")).read_bytes()
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        if not rows:
            raise ValueError("Empty split: " + split)
        converted = []
        for row in rows:
            messages = row.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError("Missing messages")
            if any(not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant") or not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
                raise ValueError("Malformed message")
            converted.append({"kind": "chat", "messages": messages, "source_conversation_id": row.get("source_conversation_id"), "license": row.get("license")})
        payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in converted).encode()
        (output / (split + ".jsonl")).write_bytes(payload)
        report["splits"][split] = {"source_sha256": hashlib.sha256(raw).hexdigest(), "derived_sha256": hashlib.sha256(payload).hexdigest(), "conversations": len(rows)}
    (output / "provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    print(json.dumps(build(a.source, a.output), indent=2))
