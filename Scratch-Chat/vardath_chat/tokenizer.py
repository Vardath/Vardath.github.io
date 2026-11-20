"""A dependency-free, byte-level UTF-8 tokenizer written from scratch.

Unicode input is supported. No downloaded vocabulary or tokenizer is needed.
Special IDs are outside the byte interval 0...255.
"""
from __future__ import annotations

BOS, USER, ASSISTANT, EOS, SYSTEM, PAD = range(256, 262)
SPECIAL = {BOS, USER, ASSISTANT, EOS, SYSTEM, PAD}


def encode_text(text: str) -> list[int]:
    return list(text.encode("utf-8"))


def decode_text(ids: list[int]) -> str:
    return bytes(i for i in ids if 0 <= i < 256).decode("utf-8", errors="replace")


def encode_chat(messages: list[dict], context_size: int = 256) -> list[int]:
    """Serialize a complete request and reserve an assistant response marker."""
    if not messages:
        raise ValueError("messages must not be empty")
    ids: list[int] = [BOS]
    for item in messages:
        role = item["role"]
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"Unknown role: {role}")
        marker = {"system": SYSTEM, "user": USER, "assistant": ASSISTANT}[role]
        ids.append(marker)
        ids.extend(encode_text(str(item["content"])))
        ids.append(EOS)
    ids.append(ASSISTANT)
    # Preserve as much recent context as possible and always start at a role boundary when feasible.
    if len(ids) > context_size:
        remaining = ids[-context_size:]
        for i, token in enumerate(remaining[:-1]):
            if token in {SYSTEM, USER, ASSISTANT}:
                remaining = remaining[i:]
                break
        ids = [BOS] + remaining if len(remaining) < context_size else remaining
    return ids


def encode_training_example(messages: list[dict], context_size: int) -> tuple[list[int], list[int]]:
    """Return (inputs, labels); loss is charged on assistant text/end tokens only."""
    ids = [BOS]
    trained_positions: set[int] = set()
    for item in messages:
        role = item["role"]
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"Unknown role: {role}")
        marker = {"system": SYSTEM, "user": USER, "assistant": ASSISTANT}[role]
        ids.append(marker)
        for token in encode_text(str(item["content"])):
            ids.append(token)
            if role == "assistant":
                trained_positions.add(len(ids)-1)
        ids.append(EOS)
        if role == "assistant":
            trained_positions.add(len(ids)-1)
    if len(ids) > context_size + 1:
        # With short-context training, skip examples instead of silently truncating the question.
        raise ValueError(f"Example length {len(ids)} exceeds context+1 ({context_size + 1})")
    inputs = ids[:-1]
    labels = [ids[i+1] if i+1 in trained_positions else -100 for i in range(len(inputs))]
    if not any(x != -100 for x in labels):
        raise ValueError("Example must contain an assistant response")
    return inputs, labels
