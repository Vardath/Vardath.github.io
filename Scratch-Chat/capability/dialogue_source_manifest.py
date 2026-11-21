"""Fail-closed admission checks for external Scratch Chat dialogue sources.

This module validates a source manifest; it never downloads or approves data.
"""
import argparse
import json
import re
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = ("source_id", "upstream_url", "revision", "license_url",
            "license_identifier", "attribution", "collection_method",
            "privacy_review", "moderation_procedure", "original_sha256",
            "train_sha256", "validation_sha256", "test_sha256",
            "train_records", "validation_records", "test_records",
            "reviewer", "decision")


def validate_manifest(data):
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        raise ValueError("Missing manifest fields: " + ", ".join(missing))
    for key in REQUIRED:
        value = data[key]
        if key.endswith("_records"):
            if type(value) is not int or value < 1:
                raise ValueError(f"{key} must be a positive integer")
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a nonempty string")
    for key in ("original_sha256", "train_sha256",
                "validation_sha256", "test_sha256"):
        if not SHA256.fullmatch(data[key]):
            raise ValueError(f"{key} must be lowercase SHA-256 hex")
    if len({data[k] for k in ("train_sha256", "validation_sha256",
                              "test_sha256")}) != 3:
        raise ValueError("Split hashes must be distinct")
    if data["decision"] != "approved":
        raise ValueError("Only explicitly approved manifests are admissible")
    if data["upstream_url"].startswith("https://") is False:
        raise ValueError("Source must use HTTPS")
    if data["license_url"].startswith("https://") is False:
        raise ValueError("License reference must use HTTPS")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
    print("Manifest structure accepted; provenance and license still require human verification.")


if __name__ == "__main__":
    main()
