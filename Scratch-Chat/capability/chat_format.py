"""Deterministic supervised chat serialization for original-weight Scratch Chat.

Assistant-only loss masks prevent training the model to predict user prompts.
This is a preparation primitive, not evidence of conversational capability.
"""
import json

ROLES = {"system", "user", "assistant", "tool"}
MARKERS = {"system": "<|system|>", "user": "<|user|>", "assistant": "<|assistant|>", "tool": "<|tool|>"}
END = "<|end|>"
EOS = "<|eos|>"


def serialize(messages):
    """Return (text, assistant character spans) for tokenizer-aware masking."""
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a nonempty list")
    parts, spans, position = [], [], 0
    has_user = has_assistant = False
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("message must be an object")
        role, value = message.get("role"), message.get("content")
        if role not in ROLES or not isinstance(value, str) or not value.strip():
            raise ValueError("invalid role/content")
        if any(marker in value for marker in (*MARKERS.values(), END, EOS)):
            raise ValueError("reserved delimiter inside message")
        if role == "user":
            has_user = True
        if role == "assistant":
            has_assistant = True
        prefix = MARKERS[role] + "\n"
        chunk = prefix + value + END + "\n"
        if role == "assistant":
            spans.append((position + len(prefix), position + len(prefix) + len(value) + len(END)))
        parts.append(chunk)
        position += len(chunk)
    if not (has_user and has_assistant):
        raise ValueError("dialogue requires user and assistant turns")
    parts.append(EOS)
    return "".join(parts), spans


def serialize_record(record):
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    return serialize(record.get("messages"))


def convert_jsonl(source, destination):
    """Write deterministic training JSONL with explicit assistant spans."""
    from pathlib import Path
    source, destination = Path(source), Path(destination)
    count = 0
    with source.open(encoding="utf-8") as src, destination.open("w", encoding="utf-8") as dst:
        for number, line in enumerate(src, 1):
            if not line.strip():
                raise ValueError(f"blank line {number}")
            text, spans = serialize_record(json.loads(line))
            dst.write(json.dumps({"text": text, "assistant_spans": spans}, ensure_ascii=False) + "\n")
            count += 1
    return count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    print(f"Converted {convert_jsonl(args.source, args.destination)} conversations")
