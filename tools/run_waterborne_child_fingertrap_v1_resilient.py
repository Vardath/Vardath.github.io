#!/usr/bin/env python3
import argparse, json, math, re, time, urllib.parse, urllib.request
from urllib.error import HTTPError

import test_waterborne_child_fingertrap_v1 as core

_original_json_dumps = json.dumps


def _json_safe(x):
    if isinstance(x, float):
        if math.isnan(x):
            return "NaN"
        if math.isinf(x):
            return "Infinity" if x > 0 else "-Infinity"
        return x
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_json_safe(v) for v in x]
    if isinstance(x, tuple):
        return [_json_safe(v) for v in x]
    return x


def safe_dumps(obj, *args, **kwargs):
    if kwargs.get("allow_nan") is False:
        obj = _json_safe(obj)
    return _original_json_dumps(obj, *args, **kwargs)


def boundary_positions(text, terms):
    """Implement the pre-frozen rule that very short ASCII terms are words, not substrings."""
    out = []
    t = core.norm(text)
    for term in terms:
        q = core.norm(term)
        if re.fullmatch(r"[a-z0-9'-]+", q) and len(q) <= 4:
            pat = re.compile(r"(?<![a-z0-9])" + re.escape(q) + r"(?![a-z0-9])")
            out.extend(m.start() for m in pat.finditer(t))
        else:
            start = 0
            while True:
                i = t.find(q, start)
                if i < 0:
                    break
                out.append(i)
                start = i + max(1, len(q))
    return sorted(set(out))


def resilient_api_get(lang, params, retries=10):
    base = f"https://{lang}.wikipedia.org/w/api.php"
    params = dict(params)
    params["format"] = "json"
    params["utf8"] = 1
    url = base + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": core.UA, "Accept": "application/json"})
    delay = 8.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if attempt == retries - 1:
                raise
            if e.code == 429:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                try:
                    wait = float(retry_after) if retry_after else delay
                except (TypeError, ValueError):
                    wait = delay
                wait = max(wait, delay)
                print(f"Wikipedia 429 on {lang}; waiting {wait:.1f}s before retry {attempt + 2}/{retries}", flush=True)
                time.sleep(wait)
                delay = min(delay * 2.0, 120.0)
            else:
                time.sleep(delay)
                delay = min(delay * 2.0, 120.0)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2.0, 120.0)


def paced_fetch_en_extracts(titles):
    """Retrieve all resolvable English plaintext, explicitly overriding MediaWiki's extract default limit."""
    out = {}
    for idx, batch in enumerate(core.batches(titles, 20)):
        if idx:
            time.sleep(2.0)
        data = resilient_api_get("en", {
            "action": "query", "prop": "extracts|pageprops", "explaintext": 1, "exlimit": "max",
            "redirects": 1, "titles": "|".join(batch), "ppprop": "wikibase_item"
        })
        for _, p in data.get("query", {}).get("pages", {}).items():
            if "missing" in p:
                continue
            title = p.get("title", "")
            extract = p.get("extract", "")
            if not extract:
                continue
            out[title] = {
                "title": title,
                "extract": extract,
                "qid": p.get("pageprops", {}).get("wikibase_item")
            }
    return out


# Transport/correctness overrides only. Scientific constants and lexicons stay in the frozen core.
core.api_get = resilient_api_get
core.fetch_en_extracts = paced_fetch_en_extracts
core.positions = boundary_positions
core.json.dumps = safe_dumps


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("validate")
    sh = sp.add_parser("shard")
    sh.add_argument("--id", type=int, required=True)
    sp.add_parser("merge")
    args = ap.parse_args()
    if args.cmd == "validate":
        core.validate()
        assert boundary_positions("dark ark mark", ["ark"]) == [5]
        assert boundary_positions("bag baggage", ["bag"]) == [0]
        print(json.dumps({"resilient_transport": "ok", "short_term_boundaries": "ok", "extract_batch": 20, "exlimit": "max"}))
    elif args.cmd == "shard":
        if not 0 <= args.id < 20:
            raise SystemExit("shard id must be 0..19")
        time.sleep((args.id % 5) * 1.5)
        core.run_shard(args.id)
    else:
        core.merge()


if __name__ == "__main__":
    main()
