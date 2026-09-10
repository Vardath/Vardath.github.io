#!/usr/bin/env python3
"""Build a browser-friendly, repo-backed store for the reconstructed dictionary.

The authoritative full reconstruction remains data/phonetic-original-language-dictionary.json.
This script emits:
  - data/original-language-web/index.json       compact searchable metadata
  - data/original-language-web/shard-NNN.jsonl detailed records, one word per line

JSONL makes every word directly addressable on GitHub by line number while keeping
browser fetches small. No linguistic evidence or reconstructed values are changed.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "phonetic-original-language-dictionary.json"
OUT = ROOT / "data" / "original-language-web"
SHARD_SIZE = 100


def slug(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s[:72] or "word"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entries = data.get("entries") or []

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    index_entries = []
    used = {}

    for i, entry in enumerate(entries):
        shard = i // SHARD_SIZE
        line = i % SHARD_SIZE + 1

        base = slug(str(entry.get("meaning") or entry.get("form") or f"word-{i+1}"))
        n = used.get(base, 0) + 1
        used[base] = n
        word_id = base if n == 1 else f"{base}-{n}"

        detail = dict(entry)
        detail["id"] = word_id

        shard_path = OUT / f"shard-{shard:03d}.jsonl"
        with shard_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n")

        index_entries.append({
            "id": word_id,
            "meaning": entry.get("meaning", ""),
            "form": entry.get("form", ""),
            "ipa": entry.get("ipa", ""),
            "path": entry.get("path", []),
            "families": entry.get("families", 0),
            "languages": entry.get("languages", 0),
            "fit": entry.get("fit", 0),
            "stability": entry.get("stability", entry.get("loo_stability", 0)),
            "confidence": entry.get("confidence", 0),
            "shard": shard,
            "line": line,
        })

    web_index = {
        "version": 1,
        "title": data.get("title", "Candidate original-language dictionary"),
        "method": data.get("method", {}),
        "summary": dict(data.get("summary", {}), web_shards=(len(entries) + SHARD_SIZE - 1) // SHARD_SIZE),
        "research_boundary": (
            "These are model-derived candidate ancestral forms reconstructed from phonetic and semantic "
            "regularities across the scanned dictionary evidence. They are experimental reconstructions, "
            "not attested historical words, and phonetic fit alone cannot establish a single historical "
            "Proto-World language or override documentary chronology, morphology, borrowing evidence, "
            "archaeology, or established comparative sound laws."
        ),
        "storage": {
            "format": "JSON Lines",
            "shard_size": SHARD_SIZE,
            "detail_path_template": "data/original-language-web/shard-{shard:03d}.jsonl",
            "github_source_template": "https://github.com/Vardath/Vardath.github.io/blob/main/data/original-language-web/shard-{shard:03d}.jsonl?plain=1#L{line}",
        },
        "entries": index_entries,
    }
    (OUT / "index.json").write_text(
        json.dumps(web_index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(json.dumps({"entries": len(entries), "shards": web_index["summary"]["web_shards"]}))


if __name__ == "__main__":
    main()
