#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError

import run_waterborne_child_fingertrap_v1_resilient as old

core = old.core


def wikidata_get(params, retries=10):
    params = dict(params)
    params["format"] = "json"
    params["utf8"] = 1
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": core.UA, "Accept": "application/json"})
    delay = 8.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if attempt == retries - 1:
                raise
            wait = delay
            if e.code == 429 and e.headers:
                try:
                    wait = max(delay, float(e.headers.get("Retry-After") or delay))
                except (TypeError, ValueError):
                    pass
            print(f"Wikidata request retry in {wait:.1f}s", flush=True)
            time.sleep(wait)
            delay = min(delay * 2.0, 120.0)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 120.0)


def resolve_local_via_wikidata(lang, pages):
    byid = {p["pageid"]: dict(p) for p in pages}

    for batch in core.batches(list(byid), 50):
        data = old.resilient_api_get(lang, {
            "action": "query",
            "prop": "pageprops",
            "pageids": "|".join(str(x) for x in batch),
            "ppprop": "wikibase_item",
        })
        for p in data.get("query", {}).get("pages", {}).values():
            pid = p.get("pageid")
            if pid not in byid:
                continue
            byid[pid]["qid"] = p.get("pageprops", {}).get("wikibase_item")
            if lang == "en":
                byid[pid]["en_title"] = p.get("title") or byid[pid].get("title")
        time.sleep(0.35)

    if lang == "en":
        return list(byid.values())

    qids = sorted({p.get("qid") for p in byid.values() if p.get("qid")})
    en_by_qid = {}
    for batch in core.batches(qids, 50):
        data = wikidata_get({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "sitelinks",
            "sitefilter": "enwiki",
        })
        for qid, entity in data.get("entities", {}).items():
            title = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
            if title:
                en_by_qid[qid] = title
        time.sleep(0.5)

    for p in byid.values():
        qid = p.get("qid")
        if qid in en_by_qid:
            p["en_title"] = en_by_qid[qid]

    return list(byid.values())


core.resolve_local = resolve_local_via_wikidata


if __name__ == "__main__":
    old.main()
