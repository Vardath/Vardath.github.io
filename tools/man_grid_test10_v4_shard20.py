#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import man_grid_exact_v4 as V
import man_grid_test5_v4_shard50 as T5

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / 'data' / 'test10-source'
WORK = ROOT / 'data' / 'man-grid-test10-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-10-exact-v4.json'
TEST9_PATH = ROOT / 'data' / 'man-grid-test-09-exact-v4.json'
N = 20
SOURCE_TEST6_RUN = 34669265024
SOURCE_TEST6_BASE_ARTIFACT_ID = 10290147185
GAP = T5.GAP
MIN_HELDOUT = 6
MAX_HELDOUT = 12


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


def weighted_medoid(rows, costs, limit=24):
    cnt = Counter({tuple(seq): int(n) for seq, n in rows})
    items = cnt.most_common(limit)
    if not items:
        return None
    den = sum(w for _, w in items)
    best = None
    for s, w in items:
        d = sum(seqdist(s, t, costs) * v for t, v in items) / den
        key = (d, -w, len(s), s)
        if best is None or key < best[0]:
            best = (key, s)
    return best[1]


def align_sequences(a, b, costs):
    a, b = tuple(a), tuple(b)
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * GAP
        bt[i][0] = 'up'
    for j in range(1, m + 1):
        dp[0][j] = j * GAP
        bt[0][j] = 'left'
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opts = [
                (dp[i - 1][j - 1] + costs[a[i - 1]][b[j - 1]], 0, 'diag'),
                (dp[i - 1][j] + GAP, 1, 'up'),
                (dp[i][j - 1] + GAP, 2, 'left'),
            ]
            val, _, op = min(opts)
            dp[i][j] = val
            bt[i][j] = op
    out = []
    i, j = n, m
    while i or j:
        op = bt[i][j]
        if op == 'diag':
            out.append((a[i - 1], b[j - 1]))
            i -= 1; j -= 1
        elif op == 'up':
            out.append((a[i - 1], None))
            i -= 1
        else:
            out.append((None, b[j - 1]))
            j -= 1
    out.reverse()
    return out


def infer_parent(a, b, model, costs):
    roots = list(model['root_ids'])
    aligned = align_sequences(a, b, costs)
    parent = []
    for x, y in aligned:
        if x is None:
            parent.append(y)
            continue
        if y is None:
            parent.append(x)
            continue
        if x == y:
            parent.append(x)
            continue
        # Discrete Frechet midpoint on the actual mirrored-Man-Grid metric.
        # Squared-distance energy favours an available root near the midpoint,
        # rather than simply choosing one descendant endpoint.
        r = min(
            roots,
            key=lambda q: (
                costs[q][x] * costs[q][x] + costs[q][y] * costs[q][y],
                max(costs[q][x], costs[q][y]),
                abs(costs[q][x] - costs[q][y]),
                q,
            ),
        )
        parent.append(r)
    return tuple(parent)


def ipa(seq, model):
    return '/' + ''.join(str(model['params'][p]['name']) for p in seq) + '/'


def validate_sources(model, roots_payload, test9):
    if int(model.get('grid', {}).get('counts', {}).get('total_cells', 0)) != 1074:
        raise RuntimeError('source model is not the exact 1,074-cell mirrored Man Grid')
    if len(model.get('root_ids', [])) != 36:
        raise RuntimeError('source model does not contain the corrected 36-root inventory')
    if roots_payload.get('test_id') != 5:
        raise RuntimeError('Test 6 base artifact does not contain corrected Test 5 roots')
    if test9.get('status') != 'complete' or test9.get('test_id') != 9 or int(test9.get('shards', 0)) != 20:
        raise RuntimeError('published corrected Test 9 result is not complete')
    calc = test9.get('calculation', {})
    if calc.get('feature_distance_used_for_test9_scoring') is not False:
        raise RuntimeError('Test 9 source did not exclude feature-space scoring')
    if calc.get('test4_result_used') is not False:
        raise RuntimeError('Test 9 source reused invalid Test 4 output')
    if calc.get('occitan_or_indonesian_hard_coded') is not False:
        raise RuntimeError('Test 9 source hard-coded previous sibling guesses')
    a = test9.get('summary', {}).get('branch_a_anchor') or {}
    b = test9.get('summary', {}).get('branch_b_anchor') or {}
    if not a.get('code') or not b.get('code') or a['code'] == b['code']:
        raise RuntimeError('Test 9 did not publish two distinct discovered anchors')
    return a, b


def load_languages():
    rows = []
    files = sorted(SOURCE_DIR.glob('language-shard-*.json.gz'))
    if len(files) != 20:
        raise RuntimeError(f'expected 20 Test 6 language shards, found {len(files)}')
    for p in files:
        rows.extend(read_gz(p))
    return rows


def prepare():
    model = read_gz(SOURCE_DIR / 'model.json.gz')
    roots_payload = read_gz(SOURCE_DIR / 'test5-roots.json.gz')
    test9 = read_json(TEST9_PATH)
    anchor_a_meta, anchor_b_meta = validate_sources(model, roots_payload, test9)
    anchor_a = anchor_a_meta['code']
    anchor_b = anchor_b_meta['code']
    roots = roots_payload['entries']
    root_ids = set(model['root_ids'])
    costs = substitution_costs(model)

    languages = load_languages()
    by_code = {x['code']: x for x in languages}
    if anchor_a not in by_code or anchor_b not in by_code:
        raise RuntimeError('one or both discovered Test 9 anchors are absent from the corrected Test 6 language pool')

    # Compute one mirror-grid medoid form per language/meaning once, then build
    # independent held-out panels. Test 5 roots are evaluation targets only.
    per_meaning = defaultdict(list)
    anchor_forms = {anchor_a: {}, anchor_b: {}}
    observed_forms = 0
    for lr in languages:
        code = lr['code']
        for meaning, variants in lr.get('meanings', {}).items():
            if meaning not in roots:
                continue
            s = weighted_medoid(variants, costs)
            if not s:
                continue
            if any(p not in root_ids for p in s):
                raise RuntimeError(f'non-root phoneme in attested form {code}/{meaning}')
            observed_forms += 1
            rec = {'code': code, 'name': lr.get('name') or code, 'family': lr.get('family') or 'Unclassified', 'seq': list(s)}
            per_meaning[meaning].append(rec)
            if code in anchor_forms:
                anchor_forms[code][meaning] = list(s)

    overlap = sorted(set(anchor_forms[anchor_a]) & set(anchor_forms[anchor_b]) & set(roots))
    shards = [[] for _ in range(N)]
    eligible = 0
    for meaning in overlap:
        others = [x for x in per_meaning[meaning] if x['code'] not in (anchor_a, anchor_b)]
        if len(others) < MIN_HELDOUT + 2:
            continue
        root = tuple(roots[meaning]['seq'])
        if not root or any(p not in root_ids for p in root):
            continue
        others.sort(key=lambda x: x['code'])
        row = {
            'meaning': meaning,
            'root': list(root),
            'anchor_a_seq': anchor_forms[anchor_a][meaning],
            'anchor_b_seq': anchor_forms[anchor_b][meaning],
            'others': others,
        }
        shard = V.h64('test10-meaning', meaning) % N
        shards[shard].append(row)
        eligible += 1

    for rows in shards:
        rows.sort(key=lambda x: x['meaning'])

    WORK.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / 'model.json.gz', model)
    for i, rows in enumerate(shards):
        write_gz(WORK / f'meaning-shard-{i:02d}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 10,
        'test': 'Common-parent test of the two data-driven sibling anchors discovered by corrected Test 9',
        'status': 'prepared',
        'shards': N,
        'dependency': {
            'test9': 'required corrected 20-shard sibling-anchor discovery',
            'test5': 'corrected Test 5 root dictionary used only as an evaluation target, never to infer the Test 10 parent',
            'test6': 'corrected attested-language forms reused from the Test 6 base artifact',
            'test4': 'not used; Test 4 is treated as the incomplete precursor to corrected Test 5',
        },
        'discovered_anchors': {
            'branch_a': anchor_a_meta,
            'branch_b': anchor_b_meta,
            'labels_exchangeable': True,
        },
        'prepared': {
            'attested_languages_loaded': len(languages),
            'attested_language_meaning_medoid_forms': observed_forms,
            'anchor_overlap_meanings_before_heldout_requirement': len(overlap),
            'eligible_meanings': eligible,
            'minimum_other_languages_per_meaning': MIN_HELDOUT + 2,
            'heldout_languages_per_meaning_max': MAX_HELDOUT,
            'meaning_shard_sizes': [len(x) for x in shards],
        },
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': {
            'metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'sequence_alignment': 'dynamic-programming alignment with mirror-grid phoneme substitution costs and Test 5 gap cost',
            'parent_inference': 'align the two Test 9 anchor forms for the same meaning, then choose at each aligned two-phoneme position the corrected 36-root phoneme minimizing summed squared exact mirrored-Man-Grid distance to the two descendants; unmatched descendant phonemes are retained conservatively',
            'root_evaluation': 'compare inferred parent to the pre-existing corrected Test 5 root only after inference; Test 5 root never participates in parent construction',
            'heldout_evaluation': f'compare inferred parent to up to {MAX_HELDOUT} deterministic attested languages excluding both discovered anchors and excluding random-control languages',
            'wrong_meaning_control': 'pair branch-A form with branch-B form from a deterministic different meaning in the same shard and compare that pseudo-parent with the real meaning root and held-out languages',
            'random_anchor_control': 'infer a same-meaning parent from a deterministic pair of non-anchor attested languages, preferring different families, then compare it with the same root and held-out panel',
            'feature_distance_used_for_test10_scoring': False,
            'test4_result_used': False,
            'test5_root_used_for_parent_inference': False,
            'central_circle_operator_used': False,
        },
        'execution': {
            'version': 'exact-v4-test10-common-parent-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint meaning ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 10 asks whether the two independently discovered Test 9 branch anchors reconstruct a common Man-Grid parent that agrees with the earlier Test 5 root and unseen attested languages better than wrong-meaning and random-language-pair controls. It does not establish historical sister-language status, chronology, homeland, or a central-circle transformation.',
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def choose_wrong(rows, idx):
    if len(rows) < 2:
        return None
    cur = rows[idx]
    pool = [j for j in range(len(rows)) if j != idx]
    return pool[V.h64('test10-wrong-meaning', cur['meaning']) % len(pool)]


def choose_random_pair(others, meaning):
    ordered = sorted(others, key=lambda x: (V.h64('test10-random-anchor', meaning, x['code']), x['code']))
    if len(ordered) < 2:
        return None
    first = ordered[0]
    for second in ordered[1:]:
        if second['family'] != first['family']:
            return first, second
    return first, ordered[1]


def choose_heldout(others, meaning, excluded):
    rows = [x for x in others if x['code'] not in excluded]
    rows.sort(key=lambda x: (V.h64('test10-heldout', meaning, x['code']), x['code']))
    return rows[:MAX_HELDOUT]


def paired_dz(real, ctrl):
    diffs = [b - a for a, b in zip(real, ctrl)]
    if len(diffs) < 2:
        return None
    sd = statistics.stdev(diffs)
    return statistics.mean(diffs) / sd if sd else None


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')
    model = read_gz(WORK / 'model.json.gz')
    rows = read_gz(WORK / f'meaning-shard-{shard:02d}.json.gz')
    costs = substitution_costs(model)
    out = []

    for i, row in enumerate(rows):
        wi = choose_wrong(rows, i)
        if wi is None:
            continue
        rp = choose_random_pair(row['others'], row['meaning'])
        if not rp:
            continue
        r1, r2 = rp
        held = choose_heldout(row['others'], row['meaning'], {r1['code'], r2['code']})
        if len(held) < MIN_HELDOUT:
            continue

        real_parent = infer_parent(row['anchor_a_seq'], row['anchor_b_seq'], model, costs)
        wrong_parent = infer_parent(row['anchor_a_seq'], rows[wi]['anchor_b_seq'], model, costs)
        random_parent = infer_parent(r1['seq'], r2['seq'], model, costs)
        root = tuple(row['root'])

        real_root = seqdist(real_parent, root, costs)
        wrong_root = seqdist(wrong_parent, root, costs)
        random_root = seqdist(random_parent, root, costs)
        held_seqs = [tuple(x['seq']) for x in held]
        real_held = statistics.mean(seqdist(real_parent, s, costs) for s in held_seqs)
        wrong_held = statistics.mean(seqdist(wrong_parent, s, costs) for s in held_seqs)
        random_held = statistics.mean(seqdist(random_parent, s, costs) for s in held_seqs)

        out.append({
            'meaning': row['meaning'],
            'parent_seq': list(real_parent),
            'parent_ipa': ipa(real_parent, model),
            'test5_root_seq': list(root),
            'test5_root_ipa': ipa(root, model),
            'parent_to_test5_root_distance': round(real_root, 8),
            'wrong_meaning_parent_to_root_distance': round(wrong_root, 8),
            'random_pair_parent_to_root_distance': round(random_root, 8),
            'real_beats_wrong_root': real_root < wrong_root,
            'real_beats_random_root': real_root < random_root,
            'heldout_languages': len(held),
            'parent_to_heldout_mean_distance': round(real_held, 8),
            'wrong_parent_to_heldout_mean_distance': round(wrong_held, 8),
            'random_parent_to_heldout_mean_distance': round(random_held, 8),
            'real_beats_wrong_heldout': real_held < wrong_held,
            'real_beats_random_heldout': real_held < random_held,
            'wrong_meaning': rows[wi]['meaning'],
            'random_pair': [
                {'code': r1['code'], 'name': r1['name'], 'family': r1['family']},
                {'code': r2['code'], 'name': r2['name'], 'family': r2['family']},
            ],
            'heldout_codes': [x['code'] for x in held],
        })

    rr = [x['parent_to_test5_root_distance'] for x in out]
    wr = [x['wrong_meaning_parent_to_root_distance'] for x in out]
    qr = [x['random_pair_parent_to_root_distance'] for x in out]
    rh = [x['parent_to_heldout_mean_distance'] for x in out]
    wh = [x['wrong_parent_to_heldout_mean_distance'] for x in out]
    qh = [x['random_parent_to_heldout_mean_distance'] for x in out]
    summary = {
        'test': 10,
        'shard': shard,
        'meanings': len(out),
        'mean_parent_to_test5_root_distance': round(statistics.mean(rr), 8) if rr else None,
        'mean_wrong_parent_to_root_distance': round(statistics.mean(wr), 8) if wr else None,
        'mean_random_parent_to_root_distance': round(statistics.mean(qr), 8) if qr else None,
        'root_real_better_than_wrong': sum(x['real_beats_wrong_root'] for x in out),
        'root_real_better_than_random': sum(x['real_beats_random_root'] for x in out),
        'mean_parent_to_heldout_distance': round(statistics.mean(rh), 8) if rh else None,
        'mean_wrong_parent_to_heldout_distance': round(statistics.mean(wh), 8) if wh else None,
        'mean_random_parent_to_heldout_distance': round(statistics.mean(qh), 8) if qh else None,
        'heldout_real_better_than_wrong': sum(x['real_beats_wrong_heldout'] for x in out),
        'heldout_real_better_than_random': sum(x['real_beats_random_heldout'] for x in out),
    }
    write_gz(WORK / f't10-result-{shard:02d}.json.gz', {
        'test': 10,
        'shard': shard,
        'summary': summary,
        'meanings': out,
        'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps(summary), flush=True)


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't10-result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 10 shard {i}')
        parts.append(read_gz(p))
    rows = [x for p in parts for x in p.get('meanings', [])]
    rows.sort(key=lambda x: x['meaning'])

    rr = [x['parent_to_test5_root_distance'] for x in rows]
    wr = [x['wrong_meaning_parent_to_root_distance'] for x in rows]
    qr = [x['random_pair_parent_to_root_distance'] for x in rows]
    rh = [x['parent_to_heldout_mean_distance'] for x in rows]
    wh = [x['wrong_parent_to_heldout_mean_distance'] for x in rows]
    qh = [x['random_parent_to_heldout_mean_distance'] for x in rows]

    shard_summaries = [p['summary'] for p in parts]
    root_real_vs_wrong_shards = sum(
        s['mean_parent_to_test5_root_distance'] is not None and
        s['mean_parent_to_test5_root_distance'] < s['mean_wrong_parent_to_root_distance']
        for s in shard_summaries
    )
    root_real_vs_random_shards = sum(
        s['mean_parent_to_test5_root_distance'] is not None and
        s['mean_parent_to_test5_root_distance'] < s['mean_random_parent_to_root_distance']
        for s in shard_summaries
    )
    held_real_vs_wrong_shards = sum(
        s['mean_parent_to_heldout_distance'] is not None and
        s['mean_parent_to_heldout_distance'] < s['mean_wrong_parent_to_heldout_distance']
        for s in shard_summaries
    )
    held_real_vs_random_shards = sum(
        s['mean_parent_to_heldout_distance'] is not None and
        s['mean_parent_to_heldout_distance'] < s['mean_random_parent_to_heldout_distance']
        for s in shard_summaries
    )

    summary = {
        'meanings_tested': len(rows),
        'shards_completed': len(parts),
        'mean_parent_to_test5_root_distance': round(statistics.mean(rr), 8) if rr else None,
        'median_parent_to_test5_root_distance': round(statistics.median(rr), 8) if rr else None,
        'mean_wrong_meaning_parent_to_root_distance': round(statistics.mean(wr), 8) if wr else None,
        'mean_random_pair_parent_to_root_distance': round(statistics.mean(qr), 8) if qr else None,
        'meanings_real_parent_beats_wrong_root': sum(x['real_beats_wrong_root'] for x in rows),
        'meanings_real_parent_beats_random_root': sum(x['real_beats_random_root'] for x in rows),
        'root_effect_dz_vs_wrong': round(paired_dz(rr, wr), 8) if paired_dz(rr, wr) is not None else None,
        'root_effect_dz_vs_random': round(paired_dz(rr, qr), 8) if paired_dz(rr, qr) is not None else None,
        'shards_real_root_better_than_wrong': root_real_vs_wrong_shards,
        'shards_real_root_better_than_random': root_real_vs_random_shards,
        'mean_parent_to_heldout_distance': round(statistics.mean(rh), 8) if rh else None,
        'mean_wrong_parent_to_heldout_distance': round(statistics.mean(wh), 8) if wh else None,
        'mean_random_parent_to_heldout_distance': round(statistics.mean(qh), 8) if qh else None,
        'meanings_real_parent_beats_wrong_heldout': sum(x['real_beats_wrong_heldout'] for x in rows),
        'meanings_real_parent_beats_random_heldout': sum(x['real_beats_random_heldout'] for x in rows),
        'heldout_effect_dz_vs_wrong': round(paired_dz(rh, wh), 8) if paired_dz(rh, wh) is not None else None,
        'heldout_effect_dz_vs_random': round(paired_dz(rh, qh), 8) if paired_dz(rh, qh) is not None else None,
        'shards_real_heldout_better_than_wrong': held_real_vs_wrong_shards,
        'shards_real_heldout_better_than_random': held_real_vs_random_shards,
        'feature_distance_used_for_test10_scoring': False,
        'test4_result_used': False,
        'test5_root_used_for_parent_inference': False,
        'central_circle_operator_used': False,
    }
    out = {
        'version': 4,
        'test_id': 10,
        'test': manifest['test'],
        'status': 'complete',
        'shards': N,
        'dependency': manifest['dependency'],
        'discovered_anchors': manifest['discovered_anchors'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': summary,
        'shard_summaries': shard_summaries,
        'meanings': rows,
        'execution': manifest['execution'],
        'prepared': manifest['prepared'],
        'evidence_boundary': manifest['evidence_boundary'],
    }
    write_json(OUT, out)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


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
