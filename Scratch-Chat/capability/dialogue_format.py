"""Deterministic assistant-only SFT serialization for admitted dialogue JSONL.

Use only after dialogue_admission.audit has approved source/splits.
This module does not download data, train a model, or approve licenses.
"""
import argparse
import hashlib
import json
from pathlib import Path

VALID_ROLES = {"system", "user", "assistant", "tool"}


def serialize(messages):
    """Return text and character spans for assistant content only.

    Boundaries are explicit; the caller must map character spans to tokenizer
    offsets before applying token-level labels. Never train on all tokens by default.
    """
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError("At least two messages required")
    parts, spans, position = [], [], 0
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in VALID_ROLES:
            raise ValueError("Invalid role")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Empty/invalid content")
        if "<|im_start|>" in content or "<|im_end|>" in content:
            raise ValueError("Reserved chat delimiter in content")
        prefix = "<|im_start|>" + message["role"] + "\n"
        suffix = "<|im_end|>\n"
        parts.extend((prefix, content, suffix))
        if message["role"] == "assistant":
            spans.append([position + len(prefix), position + len(prefix) + len(content)])
        position += len(prefix) + len(content) + len(suffix)
    if not spans or not any(m["role"] == "user" for m in messages):
        raise ValueError("Missing user or assistant")
    return {"text": "".join(parts), "assistant_char_spans": spans}


def export(input_path, output_path):
    """Create deterministic serialization and record the input/output digests."""
    source = Path(input_path).read_bytes()
    output = []
    ids = set()
    for line in source.decode("utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("Missing/duplicate ID")
        ids.add(identifier)
        item = serialize(record["messages"])
        output.append(json.dumps({"id": identifier, **item}, ensure_ascii=False, sort_keys=True))
    if not output:
        raise ValueError("Empty input")
    data = ("\n".join(output) + "\n").encode("utf-8")
    Path(output_path).write_bytes(data)
    return {"count": len(output), "input_sha256": hashlib.sha256(source).hexdigest(),
            "output_sha256": hashlib.sha256(data).hexdigest(),
            "warning": "Character spans are not token masks; map through tokenizer offsets before SFT."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
