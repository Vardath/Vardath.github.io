#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import sqlite3
import statistics
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import man_grid_exact_v4 as V
import man_grid_test5_v4_shard50 as T5

ROOT = Path(__file__).resolve().parents[1]
SRC_WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
SOURCE_DIR = ROOT / 'data' / 'test6-source'
WORK = ROOT / 'data' / 'man-grid-test6-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-06-exact-v4.json'
N = 20
SOURCE_RUN = 34660500756
SOURCE_BASE_ARTIFACT_ID = 10287516871
SOURCE_MERGED_ARTIFACT_ID = 10288413679
RAW = os.environ.get('WIKTEXTRACT_URL', 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
MIN_SHARED = 10
GAP = T5.GAP


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def read_gz(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def write_gz(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def find_test5_json():
    hits = list(SOURCE_DIR.rglob('man-grid-test-05-exact-v4.json'))
    if len(hits) != 1:
        raise RuntimeError(f'expected exactly one corrected Test 5 merged JSON, found {len(hits)}')
    return hits[0]


def build_byfirst(model):
    byfirst = defaultdict(list)
    for pid, p in model['params'].items():
        nm = unicodedata.normalize('NFC', p['name'])
        if nm and not any(ch.isspace() for ch in nm):
            byfirst[nm[0]].append((nm, pid))
    for k in byfirst:
        byfirst[k].sort(key=lambda x: (-len(x[0]), x[0], x[1]))
    return byfirst


def validate_corrected_test5(test5, model):
    if test5.get('status') != 'complete' or test5.get('test_id') != 5 or int(test5.get('shards', 0)) != 50:
        raise RuntimeError('corrected 50-shard Test 5 result is not complete')
    s = test5.get('summary', {})
    c = test5.get('calculation', {})
    if s.get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('Test 5 source is not the corrected mirror-grid reconstruction')
    if not s.get('mirror_grid_used_for_phoneme_snap') or not s.get('mirror_grid_used_for_sequence_scoring'):
        raise RuntimeError('Test 5 source does not verify mirror-grid phoneme snapping and sequence scoring')
    if c.get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('Test 5 calculation metadata does not exclude feature-distance reconstruction')
    mc = model.get('calculation', {})
    if mc.get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('downloaded Test 5 model is not the corrected mirror-grid model')
    if int(model.get('grid', {}).get('counts', {}).get('total_cells', 0)) != 1074:
        raise RuntimeError('model is not the exact 1,074-cell mirrored Man Grid')
    if len(model.get('root_ids', [])) != 36:
        raise RuntimeError('model does not contain the corrected 36-root Test 1 inventory')


def init_db():
    WORK.mkdir(parents=True, exist_ok=True)
    db = WORK / 'test6-attested-languages.sqlite3'
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('PRAGMA temp_store=MEMORY')
    con.executescript('''
      CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,concept TEXT,seq TEXT);
      CREATE INDEX lex_lang ON lex(lang_code);
      CREATE INDEX lex_concept ON lex(concept);
    ''')
    return con


def prepare():
    model_path = SRC_WORK / 'model.json.gz'
    if not model_path.exists():
        raise RuntimeError('corrected Test 5 base artifact model.json.gz is missing')
    model = read_gz(model_path)
    test5 = read_json(find_test5_json())
    validate_corrected_test5(test5, model)

    roots = {}
    root_ids = set(model['root_ids'])
    for e in test5.get('entries', []):
        seq = tuple(e.get('seq', []))
        if not seq or any(x not in root_ids for x in seq):
            raise RuntimeError(f"Test 5 entry has a non-root sequence: {e.get('meaning')}")
        roots[e['meaning']] = {
            'seq': list(seq),
            'ipa': e.get('ipa'),
            'confidence': e.get('confidence'),
            'languages': e.get('languages'),
            'families': e.get('families'),
        }
    if len(roots) != int(test5.get('summary', {}).get('entries', 0)):
        raise RuntimeError('Test 5 root dictionary contains duplicate or missing meanings')

    write_gz(WORK / 'model.json.gz', model)
    write_gz(WORK / 'test5-roots.json.gz', {
        'source_run': SOURCE_RUN,
        'test_id': 5,
        'entries': roots,
    })

    byfirst = build_byfirst(model)
    iso, names = T5.family_map()
    con = init_db()
    cur = con.cursor()
    batch = []
    stats = Counter()
    req = urllib.request.Request(RAW, headers={'User-Agent': 'Vardath-ManGrid-Test6-Mirror/6.0'})

    with urllib.request.urlopen(req) as resp, gzip.GzipFile(fileobj=resp) as gz, io.TextIOWrapper(
        gz, encoding='utf-8', errors='replace'
    ) as f:
        for line in f:
            stats['dictionary_entries'] += 1
            try:
                o = json.loads(line)
            except Exception:
                stats['json_errors'] += 1
                continue

            lc = str(o.get('lang_code') or '').strip()
            ln = str(o.get('lang') or '').strip()
            if not lc or not ln:
                continue

            concepts = []
            for g in V.get_glosses(o)[:8]:
                concept = V.norm_text(g)
                if concept in roots and concept not in concepts:
                    concepts.append(concept)
                if len(concepts) >= 4:
                    break
            if not concepts:
                continue

            seqs = []
            for raw in V.get_ipa(o)[:3]:
                q, unknown = T5.tokenize_ipa(raw, model, byfirst)
                stats['ipa_unknown_symbols'] += unknown
                if len(q) >= 2 and q not in seqs:
                    seqs.append(q)
            if not seqs:
                continue

            fam = iso.get(lc) or names.get(ln.lower()) or 'Unclassified'
            stats['entries_with_test5_meaning_and_mirror_ipa'] += 1
            for concept in concepts:
                for q in seqs[:2]:
                    batch.append((lc, ln, fam, concept, ' '.join(q)))
            if len(batch) >= 20000:
                cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?)', batch)
                batch.clear()
            if stats['dictionary_entries'] % 500000 == 0:
                con.commit()
                print(json.dumps({
                    'entries': stats['dictionary_entries'],
                    'matched': stats['entries_with_test5_meaning_and_mirror_ipa'],
                }), flush=True)

    if batch:
        cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?)', batch)
    con.commit()
    stats['languages_with_any_test5_meaning'] = con.execute('SELECT COUNT(DISTINCT lang_code) FROM lex').fetchone()[0]
    stats['test5_meanings_observed_in_attested_corpus'] = con.execute('SELECT COUNT(DISTINCT concept) FROM lex').fetchone()[0]

    shards = [[] for _ in range(N)]
    current_code = None
    rec = None

    def finish(r):
        if not r:
            return
        shards[V.h64('test6-language', r['code']) % N].append({
            'code': r['code'],
            'name': r['name'],
            'family': r['family'],
            'meanings': dict(r['meanings']),
        })

    q = '''
      SELECT lang_code,MAX(lang),MAX(family),concept,seq,COUNT(*)
      FROM lex
      GROUP BY lang_code,concept,seq
      ORDER BY lang_code,concept,seq
    '''
    for code, name, family, concept, seq, n in con.execute(q):
        if code != current_code:
            finish(rec)
            current_code = code
            rec = {'code': code, 'name': name, 'family': family, 'meanings': defaultdict(list)}
        rec['meanings'][concept].append([seq.split(), int(n)])
    finish(rec)

    for i, rows in enumerate(shards):
        rows.sort(key=lambda x: (x['code'], x['name']))
        write_gz(WORK / f'language-shard-{i:02d}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 6,
        'test': 'Nearest current and historical language to the corrected Test 5 reconstruction',
        'status': 'prepared',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'source_test5_base_artifact_id': SOURCE_BASE_ARTIFACT_ID,
        'source_test5_merged_artifact_id': SOURCE_MERGED_ARTIFACT_ID,
        'source_test5_entries': len(roots),
        'dependency': {
            'test5': 'required corrected 50-shard mirror-grid dictionary',
            'test4': 'not used; Test 4 is treated as the incomplete precursor to corrected Test 5',
        },
        'scope': 'All attested Wiktextract language records with at least one corrected Test 5 meaning and mirror-grid-mappable IPA are scanned; shard scoring requires at least 10 shared meanings. The corpus can contain modern and historical language records; chronological class is not guessed from language names.',
        'scan': dict(stats),
        'language_shard_sizes': [len(x) for x in shards],
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': {
            'metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'phoneme_snap': 'corrected Test 5 mirror-grid nearest-root map',
            'word_substitution': 'bilateral LEFT->RIGHT and RIGHT->LEFT mean normalized row/column distance across all 10 exact rectangular layers',
            'sequence_distance': 'normalized edit distance with mirror-grid substitution costs',
            'gap_cost': GAP,
            'feature_distance_used_for_test6_scoring': False,
            'test4_result_used': False,
        },
        'execution': {
            'version': 'exact-v4-test6-mirror-grid-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint language ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def substitution_costs(model):
    ids = list(model['root_ids'])
    return {a: {b: T5.mirror_grid_distance(a, b, model) for b in ids} for a in ids}


def seqdist(a, b, costs):
    a, b = tuple(a), tuple(b)
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    m = len(b)
    dp = [j * GAP for j in range(m + 1)]
    for i, x in enumerate(a, 1):
        nd = [i * GAP] + [0.0] * m
        for j, y in enumerate(b, 1):
            sub = costs[x][y]
            nd[j] = min(dp[j] + GAP, nd[j - 1] + GAP, dp[j - 1] + sub)
        dp = nd
    return min(1.0, dp[m] / max(len(a), len(b)))


def medoid(counter, costs, limit=24):
    items = counter.most_common(limit)
    if not items:
        return None
    den = sum(w for _, w in items)
    best = None
    for s, w in items:
        d = sum(seqdist(s, t, costs) * v for t, v in items) / den
        key = (d, -w, len(s), s)
        if best is None or key < best[0]:
            best = (key, s, d)
    return best[1], best[2]


def wrong_meaning(root_keys, root_pos, code, meaning):
    if len(root_keys) < 2:
        return meaning
    offset = 1 + (V.h64('wrong6-mirror', code, meaning) % (len(root_keys) - 1))
    return root_keys[(root_pos[meaning] + offset) % len(root_keys)]


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')
    model = read_gz(WORK / 'model.json.gz')
    roots_payload = read_gz(WORK / 'test5-roots.json.gz')
    roots = roots_payload['entries']
    langs = read_gz(WORK / f'language-shard-{shard:02d}.json.gz')
    costs = substitution_costs(model)
    root_keys = sorted(roots)
    root_pos = {m: i for i, m in enumerate(root_keys)}
    out = []

    for lr in langs:
        real = []
        control = []
        for meaning, rows in lr['meanings'].items():
            root = roots.get(meaning)
            if not root:
                continue
            cnt = Counter({tuple(seq): int(n) for seq, n in rows})
            mm = medoid(cnt, costs)
            if not mm:
                continue
            lang_seq = mm[0]
            real.append(seqdist(lang_seq, root['seq'], costs))
            wm = wrong_meaning(root_keys, root_pos, lr['code'], meaning)
            control.append(seqdist(lang_seq, roots[wm]['seq'], costs))

        if len(real) >= MIN_SHARED:
            md = statistics.mean(real)
            cd = statistics.mean(control) if control else None
            out.append({
                'code': lr['code'],
                'name': lr['name'],
                'family': lr['family'],
                'shared_meanings': len(real),
                'coverage_fraction_of_test5': round(len(real) / max(1, len(roots)), 8),
                'mean_distance': round(md, 8),
                'median_distance': round(statistics.median(real), 8),
                'similarity': round(1.0 - md, 8),
                'wrong_meaning_distance': round(cd, 8) if cd is not None else None,
                'control_advantage': round(cd - md, 8) if cd is not None else None,
                'real_better_than_wrong': bool(cd is not None and md < cd),
            })

    out.sort(key=lambda e: (-e['similarity'], -e['shared_meanings'], e['code']))
    write_gz(WORK / f't06-result-{shard:02d}.json.gz', {
        'test': 6,
        'shard': shard,
        'languages': out,
        'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps({'test': 6, 'shard': shard, 'languages': len(out)}), flush=True)


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't06-result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 6 shard {i}')
        parts.append(read_gz(p))

    languages = [x for p in parts for x in p.get('languages', [])]
    languages.sort(key=lambda e: (-e['similarity'], -e['shared_meanings'], e['code']))
    total_shared = sum(x['shared_meanings'] for x in languages)
    weighted_real = (
        sum(x['mean_distance'] * x['shared_meanings'] for x in languages) / total_shared
        if total_shared else None
    )
    weighted_control = (
        sum(x['wrong_meaning_distance'] * x['shared_meanings'] for x in languages if x['wrong_meaning_distance'] is not None)
        / sum(x['shared_meanings'] for x in languages if x['wrong_meaning_distance'] is not None)
        if any(x['wrong_meaning_distance'] is not None for x in languages) else None
    )

    out = {
        'version': 4,
        'test_id': 6,
        'test': 'Nearest current and historical language to the corrected Test 5 reconstruction',
        'status': 'complete',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'dependency': manifest['dependency'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': {
            'attested_languages_ranked': len(languages),
            'minimum_shared_meanings': MIN_SHARED,
            'shard_outputs': [len(p.get('languages', [])) for p in parts],
            'languages_real_better_than_wrong_meaning_control': sum(x['real_better_than_wrong'] for x in languages),
            'weighted_mean_real_distance': round(weighted_real, 8) if weighted_real is not None else None,
            'weighted_mean_wrong_meaning_distance': round(weighted_control, 8) if weighted_control is not None else None,
            'nearest_language': languages[0] if languages else None,
            'feature_distance_used_for_test6_scoring': False,
            'test4_result_used': False,
        },
        'languages': languages,
        'execution': manifest['execution'],
        'scope_boundary': manifest['scope'],
        'evidence_boundary': 'This is a nearest-language ranking under the corrected mirrored-Man-Grid lexical metric. Similarity does not establish descent, historical identity, geographic origin, or a literal single prehistoric world language. Borrowing, proper names, corpus coverage and semantic matching can affect rank.',
    }
    write_json(OUT, out)
    print(json.dumps(out['summary'], ensure_ascii=False, indent=2), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('prepare')
    r = sp.add_parser('run')
    r.add_argument('--shard', type=int, required=True)
    sp.add_parser('merge')
    a = ap.parse_args()
    if a.cmd == 'prepare':
        prepare()
    elif a.cmd == 'run':
        run(a.shard)
    else:
        merge()


if __name__ == '__main__':
    main()
