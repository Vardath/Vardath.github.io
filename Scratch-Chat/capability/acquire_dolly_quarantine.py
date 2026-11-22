"""Acquire a revision-pinned Dolly candidate into quarantine; never approve or train."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from capability.import_dolly_candidate import convert

API = "https://huggingface.co/api/datasets/databricks/databricks-dolly-15k"
MAX_BYTES = 32 * 1024 * 1024

def fetch(url, limit=MAX_BYTES):
    request = urllib.request.Request(url, headers={"User-Agent": "ScratchChat-DatasetAudit/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError("Download exceeds bounded size limit")
    return payload

def acquire(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("Refusing to overwrite acquisition directory")
    metadata = json.loads(fetch(API, 1024 * 1024))
    revision = metadata.get("sha")
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision.lower()):
        raise ValueError("No immutable 40-character upstream commit")
    paths = [x["rfilename"] for x in metadata.get("siblings", [])
             if isinstance(x, dict) and isinstance(x.get("rfilename"), str)]
    matches = [p for p in paths if p.endswith(".jsonl") and ".." not in p.split("/") and not p.startswith("/")]
    if len(matches) != 1:
        raise ValueError("Expected exactly one upstream JSONL file; found " + repr(matches))
    source_path = matches[0]
    url = f"https://huggingface.co/datasets/databricks/databricks-dolly-15k/resolve/{revision}/{source_path}"
    raw = fetch(url)
    digest = hashlib.sha256(raw).hexdigest()
    # Prepare all outputs in memory before creating destination.
    lines = raw.decode("utf-8").splitlines()
    if not lines or not all(json.loads(line) for line in lines if line.strip()):
        raise ValueError("Empty or invalid JSONL source")
    output.mkdir(parents=True)
    source = output / "upstream.jsonl"
    source.write_bytes(raw)
    result = convert(source, output / "quarantined.jsonl", revision=revision,
                     expected_sha256=digest, source_id="databricks-dolly-15k")
    manifest = {
        "status": "QUARANTINED_NOT_APPROVED",
        "upstream_api": API, "upstream_url": url, "upstream_commit": revision,
        "upstream_path": source_path, "raw_sha256": digest,
        "raw_bytes": len(raw), "converted": result,
        "upstream_license_label_unverified": metadata.get("cardData", {}).get("license") if isinstance(metadata.get("cardData"), dict) else None,
        "review_required": ["license and attribution", "consent and privacy", "content filtering", "decontaminated split admission"],
        "training_allowed": False,
    }
    (output / "acquisition.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(acquire(args.output), indent=2))

if __name__ == "__main__":
    main()
