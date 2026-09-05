#!/usr/bin/env python3
"""Full reproducible benchmark for the Vardath 4x4 phonetic bridge.

Pinned inputs:
- WikiPron corpus snapshot
- PHOIBLE CLDF snapshot

Outputs:
- data/phonetic-benchmark-summary.json
- data/phonetic-benchmark-languages.csv
- data/phonetic-benchmark-datasets.csv
- data/phonetic-benchmark-pairs.csv

The benchmark keeps the PHOIBLE data layer distinct from the experimental
A1-D4 classifier. Unknown/prosodic tokens BREAK a trajectory rather than
creating an artificial transition across missing data.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import random
import time
import urllib.request
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

WP = "d282e848a211ea31cfd730f0ced8bc8cdab9e83d"
PH = "5c477f1934f57b3c1a16168fadc08e83dbc03362"
WPBASE = f"https://raw.githubusercontent.com/CUNY-CL/wikipron/{WP}/data/scrape/"
PHBASE = f"https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/"

CELLS = ["A1","A2","A3","A4","B1","B2","B3","B4","C1","C2","C3","C4","D1","D2","D3","D4"]
MAGIC = [16,2,3,13,5,11,10,8,9,7,6,12,4,14,15,1]
MAGIC_EXP = [m - 1 for m in MAGIC]
FEATURES = [
    "tone","stress","syllabic","short","long","consonantal","sonorant","continuant",
    "delayedRelease","approximant","tap","trill","nasal","lateral","labial","round",
    "labiodental","coronal","anterior","distributed","strident","dorsal","high","low",
    "front","back","tense","retractedTongueRoot","advancedTongueRoot","periodicGlottalSource",
    "epilaryngealSource","spreadGlottis","constrictedGlottis","fortis","raisedLarynxEjective",
    "loweredLarynxImplosive","click"
]
PRIMARY = {"syllabic","consonantal","sonorant","continuant","labial","coronal","dorsal","high","low","front","back"}

SAMPLE_WORDS = int(os.environ.get("BENCHMARK_SAMPLE_WORDS", "20000"))
MIN_GATE_COUNT = int(os.environ.get("BENCHMARK_MIN_GATE_COUNT", "3"))
MAX_WORKERS = int(os.environ.get("BENCHMARK_WORKERS", "8"))
OUT = Path("data")
OUT.mkdir(exist_ok=True)


def fetch_text(url: str, retries: int = 4) -> str:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Vardath-Phonetic-Benchmark/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8-sig")
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def fnum(v: str | None) -> float:
    if v is None or v in ("", "0", "N"):
        return 0.0
    n = c = 0
    for x in str(v).split(","):
        if x == "+": n += 1; c += 1
        elif x == "-": n -= 1; c += 1
    return n / c if c else 0.0


def plus(v: str | None) -> bool:
    return fnum(v) > 0.25


def classify(p: dict | None) -> str | None:
    if not p:
        return None
    sc = (p.get("SegmentClass") or "").lower()
    if sc == "tone" or plus(p.get("tone")):
        return None
    if sc == "vowel" or (plus(p.get("syllabic")) and not plus(p.get("consonantal"))):
        vertical = fnum(p.get("high")) - fnum(p.get("low"))
        horizontal = fnum(p.get("front")) - fnum(p.get("back"))
        if vertical >= 0:
            return "A1" if horizontal >= 0 else "A3"
        return "A2" if horizontal >= 0 else "A4"
    row = "B" if plus(p.get("sonorant")) else ("C" if plus(p.get("continuant")) else "D")
    places = [("1", fnum(p.get("labial"))), ("2", fnum(p.get("coronal"))), ("3", fnum(p.get("dorsal")))]
    places.sort(key=lambda x: x[1], reverse=True)
    col = places[0][0] if places[0][1] > 0.25 else "4"
    return row + col


def normalize_phone(s: str) -> str:
    return s.strip().strip("/").replace("\ufeff", "")


def build_phoible_maps():
    params_text = fetch_text(PHBASE + "parameters.csv")
    langs_text = fetch_text(PHBASE + "languages.csv")
    params = {}
    for p in csv.DictReader(io.StringIO(params_text)):
        name = (p.get("Name") or "").strip()
        if name:
            params[name] = p
    families = {}
    for row in csv.DictReader(io.StringIO(langs_text)):
        iso = (row.get("ISO639P3code") or "").strip()
        if iso and iso not in families:
            families[iso] = {
                "family": (row.get("Family_Name") or "").strip() or "Unclassified",
                "macroarea": (row.get("Macroarea") or "").strip(),
                "phoible_name": (row.get("Name") or "").strip(),
            }
    return params, families


def phone_class(phone: str, params: dict) -> str | None:
    n = normalize_phone(phone)
    p = params.get(n)
    if p:
        return classify(p)
    # Conservative cleanup: remove standalone stress/boundary marks only.
    base = n.replace("ˈ", "").replace("ˌ", "").replace(".", "").replace("‿", "").replace("#", "")
    if base != n:
        p = params.get(base)
        if p:
            return classify(p)
    return None


def parse_summary():
    text = fetch_text(WPBASE + "summary.tsv")
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        a = line.split("\t")
        a += [""] * (9 - len(a))
        rows.append({
            "file": a[0], "iso": a[1], "name": a[2], "wiki": a[3], "script": a[4],
            "dialect": a[5], "filtered": a[6], "kind": a[7], "declared_entries": int(a[8] or 0)
        })
    return rows


def dataset_score(d):
    broad = d["kind"].lower() == "broad"
    filtered = d["filtered"].lower() == "true"
    tier = 4 if broad and filtered else 3 if broad else 2 if filtered else 1
    return (tier, d["declared_entries"])


def analyze_lines(lines, params):
    counts = [0] * 256
    mapped = unknown = transitions = words = 0
    delta_counts = {str(i): 0 for i in range(-15, 16)}
    for line in lines:
        if not line:
            continue
        tab = line.find("\t")
        if tab < 0:
            continue
        words += 1
        phones = line[tab+1:].strip().split()
        prev = None
        for ph in phones:
            c = phone_class(ph, params)
            if c is None:
                unknown += 1
                prev = None  # do not fabricate a transition across missing/prosodic data
                continue
            mapped += 1
            cur = CELLS.index(c)
            if prev is not None:
                gi = prev * 16 + cur
                counts[gi] += 1
                transitions += 1
                delta = MAGIC_EXP[cur] - MAGIC_EXP[prev]
                delta_counts[str(delta)] += 1
            prev = cur
    active = sum(1 for x in counts if x > 0)
    stable = sum(1 for x in counts if x >= MIN_GATE_COUNT)
    entropy = 0.0
    if transitions:
        for x in counts:
            if x:
                p = x / transitions
                entropy -= p * math.log2(p)
    return {
        "words": words, "counts": counts, "mapped_tokens": mapped, "unknown_tokens": unknown,
        "transitions": transitions, "active_gates": active, "stable_gates": stable,
        "gate_density": active / 256, "stable_gate_density": stable / 256,
        "mapping_coverage": mapped / (mapped + unknown) if mapped + unknown else 0.0,
        "entropy_bits": entropy, "power_delta_counts": delta_counts,
    }


def deterministic_reservoir(lines, k, seed_text):
    rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16))
    sample = []
    seen = 0
    for line in lines:
        if not line:
            continue
        seen += 1
        if len(sample) < k:
            sample.append(line)
        else:
            j = rng.randrange(seen)
            if j < k:
                sample[j] = line
    rng.shuffle(sample)
    return sample


def analyze_dataset(d, params):
    text = fetch_text(WPBASE + "tsv/" + d["file"])
    lines = [x for x in text.splitlines() if x]
    sample_lines = deterministic_reservoir(lines, min(SAMPLE_WORDS, len(lines)), d["file"] + str(SAMPLE_WORDS))
    full = analyze_lines(lines, params)
    sample = analyze_lines(sample_lines, params)
    return {**d, "full": full, "sample": sample}


def stable_support(result):
    return [1 if x >= MIN_GATE_COUNT else 0 for x in result["sample"]["counts"]]


def cosine_counts(a, b):
    ta, tb = sum(a), sum(b)
    if not ta or not tb: return 0.0
    dot = aa = bb = 0.0
    for x, y in zip(a, b):
        px, py = x / ta, y / tb
        dot += px * py; aa += px * px; bb += py * py
    return dot / math.sqrt(aa * bb) if aa and bb else 0.0


def jsd_counts(a, b):
    ta, tb = sum(a), sum(b)
    if not ta or not tb: return 1.0
    s = 0.0
    for x, y in zip(a, b):
        px, py = x / ta, y / tb
        m = (px + py) / 2
        if px: s += 0.5 * px * math.log2(px / m)
        if py: s += 0.5 * py * math.log2(py / m)
    return s


def shortest_paths_from_support(support):
    adj = [[] for _ in range(16)]
    for i, on in enumerate(support):
        if on:
            a, b = divmod(i, 16)
            adj[a].append(b)
    dist = [[math.inf] * 16 for _ in range(16)]
    for s in range(16):
        dist[s][s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if dist[s][v] == math.inf:
                    dist[s][v] = dist[s][u] + 1
                    q.append(v)
    return dist


def reroute(source_counts, target_support):
    dist = shortest_paths_from_support(target_support)
    total = sum(source_counts)
    if not total: return {"mean_extra_hops": 0.0, "unreachable_mass": 0.0, "direct_mass": 0.0}
    extra = unreachable = direct = 0.0
    for i, n in enumerate(source_counts):
        if not n: continue
        a, b = divmod(i, 16)
        mass = n / total
        if target_support[i]:
            direct += mass
        else:
            d = dist[a][b]
            if math.isinf(d): unreachable += mass
            else: extra += mass * max(0, d - 1)
    return {"mean_extra_hops": extra, "unreachable_mass": unreachable, "direct_mass": direct}


def pair_metrics(a, b):
    sa, sb = stable_support(a), stable_support(b)
    inter = sum(1 for x, y in zip(sa, sb) if x and y)
    union = sum(1 for x, y in zip(sa, sb) if x or y)
    ra = reroute(a["sample"]["counts"], sb)
    rb = reroute(b["sample"]["counts"], sa)
    return {
        "iso_a": a["iso"], "iso_b": b["iso"], "name_a": a["name"], "name_b": b["name"],
        "shared_stable_gates": inter, "union_stable_gates": union,
        "jaccard": inter / union if union else 1.0,
        "cosine": cosine_counts(a["sample"]["counts"], b["sample"]["counts"]),
        "jsd_bits": jsd_counts(a["sample"]["counts"], b["sample"]["counts"]),
        "a_to_b_mean_extra_hops": ra["mean_extra_hops"],
        "a_to_b_unreachable_mass": ra["unreachable_mass"],
        "a_to_b_direct_mass": ra["direct_mass"],
        "b_to_a_mean_extra_hops": rb["mean_extra_hops"],
        "b_to_a_unreachable_mass": rb["unreachable_mass"],
        "b_to_a_direct_mass": rb["direct_mass"],
    }


def gate_prevalence(canonical):
    n = len(canonical)
    counts = [0] * 256
    for r in canonical:
        s = stable_support(r)
        for i, x in enumerate(s): counts[i] += x
    rows = []
    for i, c in enumerate(counts):
        a, b = divmod(i, 16)
        rows.append({
            "index": i, "gate": f"{CELLS[a]}→{CELLS[b]}", "source": CELLS[a], "target": CELLS[b],
            "languages": c, "prevalence": c / n if n else 0.0,
            "magic_source": MAGIC[a], "magic_target": MAGIC[b],
            "power_exponent_delta": MAGIC_EXP[b] - MAGIC_EXP[a],
        })
    return rows


def family_cores(canonical):
    fams = defaultdict(list)
    for r in canonical:
        fams[r.get("family", "Unclassified")].append(r)
    out = []
    for fam, rows in sorted(fams.items()):
        if len(rows) < 3: continue
        prev = gate_prevalence(rows)
        out.append({
            "family": fam, "languages": len(rows),
            "strict_core": [g["gate"] for g in prev if g["prevalence"] >= 1.0],
            "core_80": [g["gate"] for g in prev if g["prevalence"] >= 0.8],
            "core_50": [g["gate"] for g in prev if g["prevalence"] >= 0.5],
        })
    return out


def aggregate_power_profile(canonical):
    agg = {str(i): 0 for i in range(-15, 16)}
    per_lang_presence = {str(i): 0 for i in range(-15, 16)}
    for r in canonical:
        d = r["sample"]["power_delta_counts"]
        for k, v in d.items():
            agg[k] += v
            if v >= MIN_GATE_COUNT: per_lang_presence[k] += 1
    total = sum(agg.values()) or 1
    n = len(canonical) or 1
    return [
        {"delta": i, "ratio": f"3^{i}", "transitions": agg[str(i)], "mass": agg[str(i)]/total,
         "language_prevalence": per_lang_presence[str(i)]/n}
        for i in range(-15, 16)
    ]


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def slim_dataset_row(r, canonical=False):
    s, f = r["sample"], r["full"]
    return {
        "canonical": canonical, "iso": r["iso"], "name": r["name"], "family": r.get("family", "Unclassified"),
        "macroarea": r.get("macroarea", ""), "file": r["file"], "script": r["script"], "dialect": r["dialect"],
        "kind": r["kind"], "filtered": r["filtered"], "declared_entries": r["declared_entries"],
        "full_words": f["words"], "full_transitions": f["transitions"], "full_active_gates": f["active_gates"],
        "full_gate_density": f["gate_density"], "sample_words": s["words"], "sample_transitions": s["transitions"],
        "sample_active_gates": s["active_gates"], "sample_stable_gates": s["stable_gates"],
        "sample_gate_density": s["gate_density"], "sample_stable_gate_density": s["stable_gate_density"],
        "mapping_coverage": s["mapping_coverage"], "entropy_bits": s["entropy_bits"],
    }


def main():
    print("Loading PHOIBLE…")
    params, families = build_phoible_maps()
    datasets = parse_summary()
    print(f"Indexed {len(datasets)} WikiPron datasets; benchmarking with {MAX_WORKERS} workers")

    results = []
    failures = []
    def job(d):
        r = analyze_dataset(d, params)
        meta = families.get(d["iso"], {})
        r["family"] = meta.get("family", "Unclassified")
        r["macroarea"] = meta.get("macroarea", "")
        return r

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(job, d): d for d in datasets}
        done = 0
        for fut in as_completed(futs):
            d = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                failures.append({"file": d["file"], "error": str(e)})
                print("FAILED", d["file"], e)
            done += 1
            if done % 25 == 0 or done == len(futs):
                print(f"{done}/{len(futs)} complete")

    results.sort(key=lambda r: (r["name"], r["file"]))
    by_iso = defaultdict(list)
    for r in results: by_iso[r["iso"]].append(r)
    canonical = []
    for iso, rows in by_iso.items():
        canonical.append(max(rows, key=dataset_score))
    canonical.sort(key=lambda r: r["name"])
    canonical_files = {r["file"] for r in canonical}

    prevalence = gate_prevalence(canonical)
    thresholds = {}
    for t in (0.5, 0.8, 0.9, 0.95, 1.0):
        thresholds[str(t)] = [g["gate"] for g in prevalence if g["prevalence"] >= t]

    # Pairwise reproducibility table.
    pairs = []
    for i in range(len(canonical)):
        for j in range(i + 1, len(canonical)):
            pairs.append(pair_metrics(canonical[i], canonical[j]))

    dataset_rows = [slim_dataset_row(r, r["file"] in canonical_files) for r in results]
    language_rows = [slim_dataset_row(r, True) for r in canonical]
    family_rows = family_cores(canonical)
    power_profile = aggregate_power_profile(canonical)

    summary = {
        "benchmark_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pins": {"wikipron": WP, "phoible": PH},
        "method": {
            "sample_words_per_dataset": SAMPLE_WORDS,
            "stable_gate_min_count": MIN_GATE_COUNT,
            "unknown_tokens_break_trajectory": True,
            "canonical_dataset_rule": "prefer filtered broad; then broad; then filtered narrow; then narrow; largest dataset within tier",
            "powers_of_3": "cell magic value n maps to 3^(n-1); a gate maps to exponent delta target-source",
        },
        "counts": {
            "wikipron_datasets_indexed": len(datasets), "datasets_completed": len(results), "datasets_failed": len(failures),
            "canonical_languages": len(canonical), "families_ge_3_languages": len(family_rows), "pairwise_comparisons": len(pairs),
        },
        "failures": failures,
        "core_thresholds": thresholds,
        "gate_prevalence": prevalence,
        "family_cores": family_rows,
        "power_delta_profile": power_profile,
        "languages": [
            {**slim_dataset_row(r, True), "sample_counts": r["sample"]["counts"],
             "sample_power_delta_counts": r["sample"]["power_delta_counts"]}
            for r in canonical
        ],
        "magic_square": MAGIC,
        "cells": CELLS,
    }

    (OUT / "phonetic-benchmark-summary.json").write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    fields = list(dataset_rows[0].keys()) if dataset_rows else []
    write_csv(OUT / "phonetic-benchmark-datasets.csv", dataset_rows, fields)
    fields = list(language_rows[0].keys()) if language_rows else []
    write_csv(OUT / "phonetic-benchmark-languages.csv", language_rows, fields)
    fields = list(pairs[0].keys()) if pairs else []
    write_csv(OUT / "phonetic-benchmark-pairs.csv", pairs, fields)

    print(json.dumps(summary["counts"], indent=2))
    print("Core >=80%:", ", ".join(thresholds["0.8"]) or "none")
    print("Strict core:", ", ".join(thresholds["1.0"]) or "none")


if __name__ == "__main__":
    main()
