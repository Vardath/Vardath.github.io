#!/usr/bin/env python3
"""20-way sharded runner for the full Wiktionary man-grid reconstruction.

Phases:
  prepare -- scan the complete Wiktextract dump once, build the lexical DB,
             audit inherited-word regressions, and materialize 20 balanced
             concept shards containing all family/path evidence.
  shard   -- reconstruct one shard independently through the same man-grid
             operator model used by the full-dictionary experiment.
  merge   -- combine all 20 shard outputs into the final reconstruction and
             candidate original-language dictionary.

The split changes only execution topology, not the linguistic evidence or
reconstruction rules.
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Reuse the exact mapping, similarity, medoid, operator-bank and reconstruction
# machinery from the single-run experiment so sharding cannot silently change
# the model being tested.
import reconstruct_original_language_all_dictionaries as core

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data' / 'phonetic-all-dictionaries-shards'
WORK.mkdir(parents=True, exist_ok=True)
N_SHARDS = int(core.os.environ.get('N_SHARDS', '20'))


def dump_gz(path: Path, obj):
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def load_gz(path: Path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def prepare():
    con, stats, langs = core.ingest_all()
    hist = core.word_level_historical_audit(con)
    q = '''SELECT concept,COUNT(DISTINCT lang_code) nlang,COUNT(DISTINCT family) nfam
           FROM lex WHERE family!='Unclassified'
           GROUP BY concept HAVING nlang>=? AND nfam>=?
           ORDER BY nfam DESC,nlang DESC LIMIT ?'''
    concepts = list(con.execute(q, (core.MIN_LANGUAGES, core.MIN_FAMILIES, core.MAX_CONCEPTS)))

    shards = [[] for _ in range(N_SHARDS)]
    for ix, (concept, nlang, nfam) in enumerate(concepts):
        famc = defaultdict(Counter)
        for fam, path, n in con.execute(
            "SELECT family,path,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,path",
            (concept,),
        ):
            famc[fam][path] += int(n)
        # Preserve all family/path counts needed by the existing medoid stage.
        payload = {
            'meaning': concept,
            'languages': int(nlang),
            'families_reported': int(nfam),
            'family_paths': {
                fam: [[p, int(n)] for p, n in cnt.items()]
                for fam, cnt in famc.items()
            },
        }
        shards[ix % N_SHARDS].append(payload)

    manifest = {
        'version': 4,
        'shards': N_SHARDS,
        'eligible_meaning_groups': len(concepts),
        'scan': dict(stats),
        'historical_word_regression': hist,
        'method': {
            'coordinate_system': '16-state A1-D4 man-grid phonetic bridge',
            'historical_validation': 'Wiktionary inherited-from etymology links backtracked through the same grid when both forms have phonetics',
            'minimum_independent_families': core.MIN_FAMILIES,
            'minimum_languages': core.MIN_LANGUAGES,
            'max_concepts': core.MAX_CONCEPTS,
            'execution': f'{N_SHARDS} concurrent reconstruction shards after one complete dictionary scan',
        },
        'source': {
            'dataset': 'English Wiktionary via Wiktextract/Kaikki raw all-language dump',
            'url': core.RAW_URL,
            'scope': 'Every dictionary entry in the dump is scanned; entries with usable IPA and English glosses enter the man-grid lexical reconstruction.',
        },
    }
    (WORK / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    for i, payload in enumerate(shards):
        dump_gz(WORK / f'shard-{i:02d}.json.gz', payload)
    print(json.dumps({
        'phase': 'prepare', 'eligible': len(concepts), 'shards': N_SHARDS,
        'sizes': [len(x) for x in shards], 'scan': dict(stats),
        'historical_edges': hist.get('matched_inheritance_edges', 0),
    }, ensure_ascii=False), flush=True)


def reconstruct_one(item):
    fam_paths = {}
    fam_fit = {}
    for fam, rows in item['family_paths'].items():
        cnt = Counter({tuple(path.split()): int(n) for path, n in rows})
        m = core.medoid(cnt)
        if m:
            fam_paths[fam] = m[0]
            fam_fit[fam] = round(m[1], 4)
    if len(fam_paths) < core.MIN_FAMILIES:
        return None
    r = core.reconstruct(fam_paths)
    if not r:
        return None
    score, raw, cand, ops, fs = r
    stab = []
    if 4 <= len(fam_paths) <= 40:
        pairs = list(fam_paths.items())
        for i in range(min(len(pairs), 12)):
            rr = core.reconstruct(dict(pairs[:i] + pairs[i+1:]))
            if rr:
                stab.append(core.sim(rr[2], cand))
    stability = statistics.mean(stab) if stab else raw
    nlang = int(item['languages'])
    conf = .40*raw + .25*min(1, len(fam_paths)/8) + .20*stability + .15*min(1, nlang/25)
    evidence = []
    for (fam, p), op, s in zip(fam_paths.items(), ops, fs):
        evidence.append({
            'family': fam, 'path': list(p), 'operator': op,
            'fit': round(s, 4), 'within_family_medoid_fit': fam_fit[fam],
        })
    form = ''.join(core.PHONE[c] for c in cand)
    return {
        'meaning': item['meaning'], 'form': form, 'ipa': f'/{form}/',
        'path': list(cand), 'languages': nlang, 'families': len(fam_paths),
        'fit': round(raw, 4), 'stability': round(stability, 4),
        'confidence': round(conf, 4), 'evidence': evidence,
    }


def run_shard(shard_id: int):
    path = WORK / f'shard-{shard_id:02d}.json.gz'
    items = load_gz(path)
    entries = []
    for ix, item in enumerate(items, 1):
        e = reconstruct_one(item)
        if e:
            entries.append(e)
        if ix % 25 == 0:
            print(json.dumps({'shard': shard_id, 'processed': ix, 'of': len(items), 'reconstructed': len(entries)}), flush=True)
    out = {'shard': shard_id, 'input_meaning_groups': len(items), 'entries': entries}
    dump_gz(WORK / f'result-{shard_id:02d}.json.gz', out)
    print(json.dumps({'phase': 'shard', 'shard': shard_id, 'processed': len(items), 'reconstructed': len(entries)}), flush=True)


def merge():
    manifest = json.loads((WORK / 'manifest.json').read_text(encoding='utf-8'))
    entries = []
    shard_counts = []
    for i in range(N_SHARDS):
        p = WORK / f'result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing shard result {i}: {p}')
        r = load_gz(p)
        entries.extend(r['entries'])
        shard_counts.append({'shard': i, 'input': r['input_meaning_groups'], 'output': len(r['entries'])})
    entries.sort(key=lambda x: (-x['confidence'], -x['families'], -x['languages'], x['meaning']))

    summary = {
        'version': 4,
        'source': manifest['source'],
        'method': manifest['method'],
        'scan': manifest['scan'],
        'historical_word_regression': manifest['historical_word_regression'],
        'eligible_meaning_groups': manifest['eligible_meaning_groups'],
        'dictionary_entries': len(entries),
        'shard_counts': shard_counts,
        'research_boundary': 'This is a model-derived deep ancestral candidate dictionary. It can test consistency with documented historical chains but phonetic fit alone does not establish or overturn a historical relationship.',
    }
    core.OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    core.OUTDICT.write_text(json.dumps({
        'version': 4,
        'title': 'Candidate original-language dictionary — all-language 20-shard reconstruction',
        'method': manifest['method'],
        'summary': {
            'entries': len(entries),
            'languages_scanned': manifest['scan'].get('languages', 0),
            'dictionary_entries_scanned': manifest['scan'].get('dictionary_entries', 0),
            'eligible_meaning_groups': manifest['eligible_meaning_groups'],
            'shards': N_SHARDS,
        },
        'entries': entries,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [
        '# All-language full-dictionary man-grid reconstruction — 20 shards', '',
        f"Dictionary entries scanned: **{manifest['scan'].get('dictionary_entries', 0):,}**",
        f"Languages encountered: **{manifest['scan'].get('languages', 0):,}**",
        f"Entries with usable IPA+meaning: **{manifest['scan'].get('entries_with_mappable_ipa', 0):,}**",
        f"Matched historical inheritance edges: **{manifest['historical_word_regression'].get('matched_inheritance_edges', 0):,}**",
        f"Eligible cross-family meaning groups: **{manifest['eligible_meaning_groups']:,}**",
        f"Reconstructed dictionary entries: **{len(entries):,}**", '',
        'Execution was split into 20 concurrent shards after one complete corpus scan. Sharding changes execution time only; all shards use the same man-grid mapping, lexical operator bank, family medoid reconstruction, and confidence calculation.',
    ]
    core.OUTMD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'phase': 'merge', 'entries': len(entries), 'shards': shard_counts}, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='phase', required=True)
    sp.add_parser('prepare')
    s = sp.add_parser('shard'); s.add_argument('--id', type=int, required=True)
    sp.add_parser('merge')
    a = ap.parse_args()
    if a.phase == 'prepare':
        prepare()
    elif a.phase == 'shard':
        if not 0 <= a.id < N_SHARDS:
            raise SystemExit(f'shard id must be 0..{N_SHARDS-1}')
        run_shard(a.id)
    else:
        merge()


if __name__ == '__main__':
    main()
