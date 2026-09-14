#!/usr/bin/env python3
"""Shard-local corpus acquisition for the frozen waterborne-child fingertrap v2 protocol.

Scientific rules live in test_waterborne_child_fingertrap_v2.py and are unchanged.
Each language shard discovers/maps candidates, bulk-fetches full English page source in
batches through MediaWiki revisions, cleans it locally to prose, and stores the frozen
5,000-character evidence window inside its artifact. Final merge performs zero network calls.
"""
import argparse
import html
import json
import re
import time

import test_waterborne_child_fingertrap_v2 as core
import run_waterborne_child_fingertrap_v2_fast as fast

BATCH_SIZE = 20
BATCH_PAUSE = 1.0


def clean_wikitext(s):
    s = s or ""
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<ref\b[^>/]*/\s*>", " ", s, flags=re.I)
    s = re.sub(r"<ref\b[^>]*>.*?</ref\s*>", " ", s, flags=re.I | re.S)
    s = re.sub(r"\{\|.*?\|\}", " ", s, flags=re.S)
    s = re.sub(r"\[\[(?:File|Image):.*?\]\]", " ", s, flags=re.I | re.S)
    s = re.sub(r"\[\[Category:[^\]]+\]\]", " ", s, flags=re.I)
    # Remove nested templates iteratively; this strips infobox/navigation boilerplate.
    for _ in range(12):
        ns = re.sub(r"\{\{[^{}]*\}\}", " ", s, flags=re.S)
        if ns == s:
            break
        s = ns
    s = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[(?:https?://|//)[^\s\]]+\s+([^\]]+)\]", r"\1", s)
    s = re.sub(r"(?:https?://|//)\S+", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"^\s*=+\s*(.*?)\s*=+\s*$", r" \1 ", s, flags=re.M)
    s = s.replace("'''", "").replace("''", "")
    s = re.sub(r"__\w+__", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def revision_content(page):
    revs = page.get("revisions") or []
    if not revs:
        return ""
    rev = revs[0]
    slots = rev.get("slots") or {}
    main = slots.get("main") or {}
    return main.get("*") or main.get("content") or rev.get("*") or rev.get("content") or ""


def fetch_evidence_batches(titles):
    unique = list(dict.fromkeys(t for t in titles if t))
    out_qid = {}
    out_title = {}
    for n, batch in enumerate(core.batches(unique, BATCH_SIZE), 1):
        data = core.wiki_get("en", {
            "action": "query",
            "prop": "revisions|pageprops",
            "rvprop": "content",
            "rvslots": "main",
            "redirects": 1,
            "titles": "|".join(batch),
            "ppprop": "wikibase_item",
        })
        pages = data.get("query", {}).get("pages", {})
        if isinstance(pages, list):
            page_iter = pages
        else:
            page_iter = pages.values()
        batch_resolved = 0
        for p in page_iter:
            if "missing" in p:
                continue
            prose = clean_wikitext(revision_content(p))
            if not prose:
                continue
            rec = {
                "title": p.get("title") or "",
                "qid": p.get("pageprops", {}).get("wikibase_item"),
                "extract": prose[:core.MAX_CHARS],
            }
            if rec["qid"]:
                out_qid[rec["qid"]] = rec
            if rec["title"]:
                out_title[core.norm(rec["title"])] = rec
            batch_resolved += 1
        print(json.dumps({"evidence_batch": n, "batch_size": len(batch), "batch_resolved": batch_resolved, "resolved_total": len(out_title)}), flush=True)
        if n * BATCH_SIZE < len(unique):
            time.sleep(BATCH_PAUSE)
    return out_qid, out_title


def shard_with_evidence(i):
    if not 0 <= i < 20:
        raise SystemExit("shard id must be 0..19")
    core.run_shard(i)
    path = core.WORK / f"shard-{i:02d}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]

    time.sleep((i % 10) * 0.6)
    by_qid, by_title = fetch_evidence_batches([r.get("en_title") for r in rows])

    missing_titles = []
    for r in rows:
        if not r.get("en_title"):
            r["evidence"] = None
            continue
        rec = by_qid.get(r.get("qid")) if r.get("qid") else None
        if not rec:
            rec = by_title.get(core.norm(r["en_title"]))
        r["evidence"] = rec
        if not rec:
            missing_titles.append(r["en_title"])

    if missing_titles:
        rq, rt = fetch_evidence_batches(missing_titles)
        for r in rows:
            if r.get("evidence") or not r.get("en_title"):
                continue
            rec = rq.get(r.get("qid")) if r.get("qid") else None
            if not rec:
                rec = rt.get(core.norm(r["en_title"]))
            r["evidence"] = rec

    mapped = sum(bool(r.get("en_title")) for r in rows)
    fetched = sum(bool(r.get("evidence")) for r in rows)
    payload["evidence_architecture"] = "shard_local_bulk_revisions_clean"
    payload["evidence_batch_size"] = BATCH_SIZE
    payload["evidence_mapped_occurrences"] = mapped
    payload["evidence_fetched_occurrences"] = fetched
    payload["evidence_missing_occurrences"] = mapped - fetched
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"shard": i, "lang": payload["lang"], "mapped": mapped, "evidence_fetched": fetched, "evidence_missing": mapped - fetched}), flush=True)


def merge_local():
    paths = sorted(core.WORK.glob("shard-*.json"))
    if len(paths) != 20:
        raise SystemExit(f"need 20 shard files, found {len(paths)}")
    payloads = [json.loads(p.read_text(encoding="utf-8")) for p in paths]

    cache = {}
    for sh in payloads:
        for r in sh["rows"]:
            ev = r.get("evidence")
            title = r.get("en_title")
            if ev and title:
                cache.setdefault(core.norm(title), ev)

    def local_fetch(title):
        return cache.get(core.norm(title))

    original_fetch = core.fetch_extract
    core.fetch_extract = local_fetch
    try:
        fast.fast_merge(workers=1)
    finally:
        core.fetch_extract = original_fetch

    summary_path = core.RESULTS / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    mapped = sum(p.get("english_mapped", 0) for p in payloads)
    fetched = sum(p.get("evidence_fetched_occurrences", 0) for p in payloads)
    summary["execution_architecture"] = "shard_local_bulk_revisions_then_zero_network_merge"
    summary["merge_transport"] = "local_frozen_shard_corpus"
    summary["merge_network_requests"] = 0
    summary["evidence_source"] = "MediaWiki revisions content, locally cleaned to prose"
    summary["evidence_batch_size"] = BATCH_SIZE
    summary["evidence_mapped_occurrences"] = mapped
    summary["evidence_fetched_occurrences"] = fetched
    summary["evidence_missing_occurrences"] = mapped - fetched
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    report_path = core.RESULTS / "report.md"
    report = report_path.read_text(encoding="utf-8")
    header = (
        "# Execution architecture\n\n"
        "- Evidence acquisition: shard-local MediaWiki revisions, 20 English titles/request\n"
        "- Page source is cleaned locally to prose before scoring\n"
        "- Evidence window: frozen first 5,000 characters, unchanged\n"
        "- Final merge network requests: 0\n"
        f"- English-mapped occurrences: {mapped}\n"
        f"- Evidence-fetched occurrences: {fetched}\n"
        f"- Evidence-missing occurrences: {mapped - fetched}\n\n"
    )
    report_path.write_text(header + report, encoding="utf-8")
    print(json.dumps({"merge": "complete", "network_requests": 0, "mapped": mapped, "evidence_fetched": fetched, "evidence_missing": mapped - fetched}), flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str), flush=True)


def validate():
    core.validate()
    assert BATCH_SIZE == 20
    assert clean_wikitext("'''Moses''' was [[adopted]] by a [[Pharaoh|royal household]].") == "Moses was adopted by a royal household."
    print(json.dumps({"status": "ok", "scientific_protocol": "waterborne_child_fingertrap_v2", "execution_architecture": "shard_local_bulk_revisions_then_zero_network_merge", "merge_network_requests": 0}))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("validate")
    sh = sp.add_parser("shard")
    sh.add_argument("--id", type=int, required=True)
    sp.add_parser("merge")
    a = ap.parse_args()
    if a.cmd == "validate":
        validate()
    elif a.cmd == "shard":
        shard_with_evidence(a.id)
    else:
        merge_local()


if __name__ == "__main__":
    main()
