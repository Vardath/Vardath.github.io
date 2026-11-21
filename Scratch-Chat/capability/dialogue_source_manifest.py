"""Fail-closed admission checks for external Scratch Chat dialogue sources.

This module validates a source manifest; it never downloads or approves data.
"""
import argparse
import hashlib
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


def verify_split_files(data, root):
    """Verify on-disk bytes, JSONL records and cross-split exact examples.

    This is not a semantic near-duplicate or provenance audit.
    """
    validate_manifest(data)
    root = Path(root)
    seen = {}
    seen_dialogue = {}
    seen_family = {}
    seen_prompts = {}
    for split in ("train", "validation", "test"):
        path = root / (split + ".jsonl")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != data[split + "_sha256"]:
            raise ValueError(f"{split} file SHA-256 mismatch")
        lines = raw.decode("utf-8").splitlines()
        if len(lines) != data[split + "_records"]:
            raise ValueError(f"{split} record count mismatch")
        for index, line in enumerate(lines, 1):
            if not line.strip():
                raise ValueError(f"{split} blank record {index}")
            record = json.loads(line)
            if not isinstance(record, dict) or not record:
                raise ValueError(f"{split} record {index} is not a nonempty object")
            canonical = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            if canonical in seen:
                raise ValueError(f"Duplicate record across or within splits: {seen[canonical]} and {split}:{index}")
            seen[canonical] = f"{split}:{index}"
            # Ignore record-level provenance/IDs when checking conversational
            # contamination: identical messages with different metadata must
            # not be placed in separate splits.
            messages = record.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError(f"{split} record {index} lacks nonempty messages")
            normalized = []
            for message in messages:
                if not isinstance(message, dict):
                    raise ValueError(f"{split} record {index} has malformed message")
                role, content = message.get("role"), message.get("content")
                if role not in ("system", "user", "assistant", "tool") or not isinstance(content, str) or not content.strip():
                    raise ValueError(f"{split} record {index} has invalid role/content")
                normalized.append((role, " ".join(content.split()).casefold()))
            # An upstream conversation or template family must not straddle
            # evaluation boundaries, even if its individual turns differ.
            for family_field in ("conversation_id", "source_conversation_id", "template_family_id"):
                family = record.get(family_field)
                if family is None:
                    continue
                if not isinstance(family, str) or not family.strip():
                    raise ValueError(f"{split} record {index} has invalid {family_field}")
                family_key = (family_field, data["source_id"], family.strip())
                previous = seen_family.get(family_key)
                if previous is not None and previous[0] != split:
                    raise ValueError(f"Cross-split conversation/template family leakage: {previous[1]} and {split}:{index}")
                seen_family[family_key] = (split, f"{split}:{index}")
            # A repeated user prompt with different assistant answers can leak
            # the evaluation task even when full dialogues are distinct.
            # Compare user turns only; exclude system boilerplate and answers.
            prompt = tuple(content for role, content in normalized if role == "user")
            if not prompt:
                raise ValueError(f"{split} record {index} has no user turn")
            previous_prompt = seen_prompts.get(prompt)
            if previous_prompt is not None and previous_prompt[0] != split:
                raise ValueError(f"Cross-split repeated user prompt: {previous_prompt[1]} and {split}:{index}")
            seen_prompts[prompt] = (split, f"{split}:{index}")
            key = json.dumps(normalized, ensure_ascii=False)
            if key in seen_dialogue:
                raise ValueError(f"Repeated normalized dialogue: {seen_dialogue[key]} and {split}:{index}")
            seen_dialogue[key] = f"{split}:{index}"
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--verify-files", type=Path, help="Directory containing train.jsonl, validation.jsonl, test.jsonl")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest(data)
    if args.verify_files is not None:
        verify_split_files(data, args.verify_files)
        print("Split bytes, record counts and exact JSONL duplicates checked; semantic and license review remain required.")
    else:
        print("Manifest structure accepted; provenance and license still require human verification.")


if __name__ == "__main__":
    main()
