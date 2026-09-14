#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

import run_waterborne_child_fingertrap_v1_1 as v11

core = v11.core
CACHE_PATH = core.WORK / "en_full_extract_cache.json"


def _load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache):
    core.WORK.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_PATH)


def fetch_en_full_extracts(titles):
    """Fetch one full plaintext article per request, preserving frozen MAX_CHARS."""
    cache = _load_cache()
    out = {}
    new_since_save = 0

    for idx, title in enumerate(titles):
        rec = cache.get(title)
        if rec is None:
            data = v11.old.resilient_api_get("en", {
                "action": "query",
                "prop": "extracts|pageprops",
                "explaintext": 1,
                "exlimit": 1,
                "redirects": 1,
                "titles": title,
                "ppprop": "wikibase_item",
            })
            rec = {}
            for p in data.get("query", {}).get("pages", {}).values():
                if "missing" in p:
                    continue
                extract = p.get("extract", "")
                if not extract:
                    continue
                rec = {
                    "title": p.get("title", title),
                    "extract": extract[:core.MAX_CHARS],
                    "qid": p.get("pageprops", {}).get("wikibase_item"),
                }
                break
            cache[title] = rec
            new_since_save += 1

            # Deliberate low-rate pacing; the resilient helper handles 429 Retry-After.
            time.sleep(0.35)
            if new_since_save >= 25:
                _save_cache(cache)
                new_since_save = 0

        if rec:
            out[title] = rec

    _save_cache(cache)
    return out


# Acquisition-only override. All frozen v1 scientific code remains in core.
core.fetch_en_extracts = fetch_en_full_extracts


if __name__ == "__main__":
    v11.old.main()
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        print(json.dumps({
            "v1_2_full_extract_transport": "ok",
            "one_title_per_request": True,
            "cached_across_serial_passes": True,
            "max_chars": core.MAX_CHARS,
        }))
