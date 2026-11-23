"""Download an explicitly pinned dialogue source snapshot for offline license review.

Acquisition is NOT admission: no downloaded records may enter training until
source-manifest review, privacy screening and split contamination checks pass.
Only HTTPS and a caller-supplied SHA-256 are accepted. No automatic redirects
to untrusted hosts, no credentials, no archive extraction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused; pin the final immutable HTTPS URL")

def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Only credential-free HTTPS URLs without fragments are accepted")
    if parsed.hostname.lower() in ("localhost",) or parsed.hostname.endswith(".local"):
        raise ValueError("Local destinations are forbidden")
    return url

def acquire(url, expected_sha256, destination, *, max_bytes=100_000_000):
    validate_url(url)
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise ValueError("Expected SHA-256 must be 64 lowercase hex digits")
    if not 0 < max_bytes <= 1_000_000_000:
        raise ValueError("Invalid byte limit")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("Refusing to overwrite existing snapshot")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    if temporary.exists():
        raise FileExistsError("Partial download already exists")
    digest = hashlib.sha256()
    count = 0
    opener = build_opener(NoRedirect)
    try:
        with opener.open(Request(url, headers={"User-Agent": "ScratchChatSourceReview/1"}), timeout=30) as response, temporary.open("xb") as output:
            while True:
                chunk = response.read(min(1024 * 1024, max_bytes - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                if count > max_bytes:
                    raise ValueError("Snapshot exceeds byte limit")
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError("Snapshot SHA-256 mismatch")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"url": url, "sha256": digest.hexdigest(), "bytes": count,
            "path": str(destination), "admission": "NOT_APPROVED",
            "required_next": "Verify license, provenance, consent, privacy and split audits"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Immutable snapshot URL, not a floating branch")
    parser.add_argument("--sha256", required=True, help="Independently obtained expected digest")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-bytes", type=int, default=100_000_000)
    args = parser.parse_args()
    print(json.dumps(acquire(args.url, args.sha256, args.output, max_bytes=args.max_bytes), indent=2))

if __name__ == "__main__":
    main()
