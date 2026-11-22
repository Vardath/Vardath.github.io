"""Convert serialized assistant character spans to strict ByteBPE token labels.

A token crossing a supervision boundary is ignored rather than leaking prompt
bytes into assistant targets. Labels use -100 for ignored positions.
"""
import json
from pathlib import Path
from capability.bpe import ByteBPE


def encode_assistant_labels(record, tokenizer):
    text = record["text"]
    spans = record["assistant_char_spans"]
    endings = record.get("assistant_termination_char_spans", [])
    if not isinstance(endings, list) or (endings and len(endings) != len(spans)):
        raise ValueError("Invalid assistant termination spans")
    for start, end in endings:
        if not (isinstance(start, int) and isinstance(end, int)
                and text[start:end] == "<|im_end|>"):
            raise ValueError("Invalid assistant termination marker")
    spans = sorted(spans + endings, key=lambda pair: pair[0])
    if not isinstance(text, str) or not isinstance(spans, list):
        raise ValueError("Invalid serialized conversation")
    byte_spans = []
    previous = 0
    for pair in spans:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(x) is not int for x in pair):
            raise ValueError("Invalid assistant span")
        start, end = pair
        if not (previous <= start < end <= len(text)):
            raise ValueError("Overlapping or invalid assistant span")
        byte_spans.append((len(text[:start].encode("utf-8")), len(text[:end].encode("utf-8"))))
        previous = end
    if not byte_spans:
        raise ValueError("No assistant targets")
    ids = tokenizer.encode(text)
    labels = []
    offset = 0
    for token in ids:
        size = len(tokenizer.byte_values[token])
        end = offset + size
        labels.append(token if any(start <= offset and end <= stop for start, stop in byte_spans) else -100)
        offset = end
    if offset != len(text.encode("utf-8")):
        raise ValueError("Tokenizer byte offsets do not reconstruct text")
    if all(label == -100 for label in labels):
        raise ValueError("No fully aligned assistant tokens")
    return {"input_ids": ids, "labels": labels}


def export(input_path, tokenizer_path, output_path):
    tokenizer = ByteBPE.load(Path(tokenizer_path))
    records = []
    for line in Path(input_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records.append({"id": record["id"], **encode_assistant_labels(record, tokenizer)})
    if not records:
        raise ValueError("Empty training split")
    Path(output_path).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    return {"examples": len(records), "supervised_tokens": sum(sum(x != -100 for x in r["labels"]) for r in records)}
