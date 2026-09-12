#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import statistics
from collections import Counter
from pathlib import Path

import man_grid_exact_v4 as V
import man_grid_test5_v4_shard50 as T5

ROOT = Path(__file__).resolve().parents[1]
SRC_WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
SOURCE_DIR = ROOT / 'data' / 'test8-source'
WORK = ROOT / 'data' / 'man-grid-test8-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-08-exact-v4.json'
N = 20
SOURCE_RUN = 34660500756
SOURCE_BASE_ARTIFACT_ID = 10287516871
SOURCE_MERGED_ARTIFACT_ID = 10288413679
MIN_FAMILIES = 4
SPLIT_SALTS = ('split-a', 'split-b', 'split-c')
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


def medoid(seqs, costs):
    unique = sorted(set(tuple(x) for x in seqs))
    if not unique:
        return None
    return min(
        unique,
        key=lambda c: (
            statistics.mean(seqdist(c, s, costs) for s in seqs),
            len(c),
            c,
        ),
    )


def split_panels(evidence, meaning, salt):
    ordered = sorted(
        evidence,
        key=lambda x: (V.h64('test8-panel', salt, meaning, x['family']), x['family'])
    )
    return ordered[::2], ordered[1::2]


def prepare():
    model_path = SRC_WORK / 'model.json.gz'
    if not model_path.exists():
        raise RuntimeError('corrected Test 5 base artifact model.json.gz is missing')
    model = read_gz(model_path)
    test5 = read_json(find_test5_json())
    validate_corrected_test5(test5, model)

    root_ids = set(model['root_ids'])
    shards = [[] for _ in range(N)]
    family_counts = Counter()
    eligible = 0

    for e in test5.get('entries', []):
        meaning = str(e.get('meaning') or '').strip()
        root = tuple(e.get('seq') or [])
        if not meaning or not root:
            continue
        if any(p not in root_ids for p in root):
            raise RuntimeError(f'non-root Test 5 reconstructed sequence in {meaning!r}')

        evidence = []
        seen = set()
        for x in e.get('family_evidence', []):
            fam = str(x.get('family') or '').strip()
            seq = tuple(x.get('seq') or [])
            if not fam or fam == 'Unclassified' or not seq or fam in seen:
                continue
            if any(p not in root_ids for p in seq):
                raise RuntimeError(f'non-root family evidence sequence in {meaning!r} / {fam!r}')
            seen.add(fam)
            family_counts[fam] += 1
            evidence.append({'family': fam, 'seq': list(seq)})

        if len(evidence) < MIN_FAMILIES:
            continue

        eligible += 1
        evidence.sort(key=lambda x: x['family'])
        shard = V.h64('test8-meaning', meaning) % N
        shards[shard].append({
            'meaning': meaning,
            'root': list(root),
            'families': evidence,
        })

    for rows in shards:
        rows.sort(key=lambda x: x['meaning'])

    WORK.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / 'model.json.gz', model)
    for i, rows in enumerate(shards):
        write_gz(WORK / f'meaning-shard-{i:02d}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 8,
        'test': 'Reverse-family convergence through the corrected exact mirrored Man Grid',
        'status': 'prepared',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'source_test5_base_artifact_id': SOURCE_BASE_ARTIFACT_ID,
        'source_test5_merged_artifact_id': SOURCE_MERGED_ARTIFACT_ID,
        'source_test5_entries': int(test5.get('summary', {}).get('entries', 0)),
        'dependency': {
            'test5': 'required corrected 50-shard mirror-grid dictionary',
            'test4': 'not used; Test 4 is treated as the incomplete precursor to corrected Test 5',
        },
        'prepared': {
            'eligible_meanings': eligible,
            'classified_families_seen': len(family_counts),
            'minimum_families_per_meaning': MIN_FAMILIES,
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
            'sequence_distance': 'normalized edit distance with mirror-grid substitution costs',
            'reverse_projection': 'each classified family contributes its independently reconstructed Test 5 family medoid sequence on the corrected 36-root mirrored-Man-Grid inventory',
            'independent_attractors': 'for each meaning, families are deterministically split into two disjoint balanced panels; each panel independently infers its medoid attractor, and the two attractors are compared',
            'split_repetitions': list(SPLIT_SALTS),
            'wrong_meaning_control': 'compare panel-A attractors to panel-B attractors from a deterministic different meaning in the same shard, preferring the same panel-B family count',
            'root_reference': 'record distance from each independent panel attractor to the corrected Test 5 full-family reconstructed root; this is a secondary reference, not an independent control',
            'gap_cost': GAP,
            'feature_distance_used_for_test8_scoring': False,
            'test4_result_used': False,
            'learned_historical_transform_used': False,
            'fixed_modern_language_attractor_used': False,
        },
        'execution': {
            'version': 'exact-v4-test8-mirror-grid-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint meaning ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 8 tests whether disjoint family panels independently converge on similar same-meaning attractors in the corrected mirrored-Man-Grid representation. No historical direction, chronology, geographic origin, circle transformation, or learned sound-change rule is assumed.',
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def evaluate_record(row, costs):
    meaning = row['meaning']
    evidence = row['families']
    root = tuple(row['root'])
    splits = []

    for salt in SPLIT_SALTS:
        a, b = split_panels(evidence, meaning, salt)
        if len(a) < 2 or len(b) < 2:
            continue
        ma = medoid([tuple(x['seq']) for x in a], costs)
        mb = medoid([tuple(x['seq']) for x in b], costs)
        if ma is None or mb is None:
            continue
        splits.append({
            'salt': salt,
            'panel_a_families': [x['family'] for x in a],
            'panel_b_families': [x['family'] for x in b],
            'panel_a_count': len(a),
            'panel_b_count': len(b),
            'panel_a_attractor': list(ma),
            'panel_b_attractor': list(mb),
            'same_meaning_distance': seqdist(ma, mb, costs),
            'panel_a_to_root': seqdist(ma, root, costs),
            'panel_b_to_root': seqdist(mb, root, costs),
        })

    if not splits:
        return None

    return {
        'meaning': meaning,
        'families': len(evidence),
        'root': list(root),
        'splits': splits,
        'panel_b_count_key': splits[0]['panel_b_count'],
    }


def choose_wrong_index(evaluated, idx):
    cur = evaluated[idx]
    same_count = [
        j for j, x in enumerate(evaluated)
        if j != idx and x['panel_b_count_key'] == cur['panel_b_count_key']
    ]
    pool = same_count if same_count else [j for j in range(len(evaluated)) if j != idx]
    if not pool:
        return None
    return pool[V.h64('test8-wrong-meaning', cur['meaning']) % len(pool)]


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')

    model = read_gz(WORK / 'model.json.gz')
    rows = read_gz(WORK / f'meaning-shard-{shard:02d}.json.gz')
    costs = substitution_costs(model)

    evaluated = []
    for row in rows:
        x = evaluate_record(row, costs)
        if x:
            evaluated.append(x)

    results = []
    for i, x in enumerate(evaluated):
        j = choose_wrong_index(evaluated, i)
        if j is None:
            continue
        wrong = evaluated[j]
        wrong_by_salt = {s['salt']: s for s in wrong['splits']}
        split_rows = []

        for s in x['splits']:
            w = wrong_by_salt.get(s['salt'])
            if not w:
                continue
            a = tuple(s['panel_a_attractor'])
            wb = tuple(w['panel_b_attractor'])
            cd = seqdist(a, wb, costs)
            split_rows.append({
                **s,
                'wrong_meaning': wrong['meaning'],
                'wrong_meaning_panel_b_attractor': list(wb),
                'wrong_meaning_distance': cd,
                'same_better_than_wrong': s['same_meaning_distance'] < cd,
            })

        if not split_rows:
            continue

        same_mean = statistics.mean(s['same_meaning_distance'] for s in split_rows)
        wrong_mean = statistics.mean(s['wrong_meaning_distance'] for s in split_rows)
        root_mean = statistics.mean(
            (s['panel_a_to_root'] + s['panel_b_to_root']) / 2 for s in split_rows
        )
        results.append({
            'meaning': x['meaning'],
            'families': x['families'],
            'mean_same_attractor_distance': round(same_mean, 8),
            'mean_wrong_meaning_distance': round(wrong_mean, 8),
            'convergence_advantage': round(wrong_mean - same_mean, 8),
            'relative_advantage': round((wrong_mean - same_mean) / wrong_mean, 8) if wrong_mean else None,
            'mean_panel_to_test5_root_distance': round(root_mean, 8),
            'same_better_than_wrong': same_mean < wrong_mean,
            'splits': split_rows,
        })

    same = [r['mean_same_attractor_distance'] for r in results]
    wrong = [r['mean_wrong_meaning_distance'] for r in results]
    diffs = [b - a for a, b in zip(same, wrong)]
    dz = None
    if len(diffs) > 1:
        sd = statistics.stdev(diffs)
        if sd:
            dz = statistics.mean(diffs) / sd

    shard_summary = {
        'test': 8,
        'shard': shard,
        'meanings': len(results),
        'mean_same_attractor_distance': round(statistics.mean(same), 8) if same else None,
        'mean_wrong_meaning_distance': round(statistics.mean(wrong), 8) if wrong else None,
        'mean_convergence_advantage': round(statistics.mean(diffs), 8) if diffs else None,
        'paired_effect_dz': round(dz, 8) if dz is not None else None,
        'meanings_same_better_than_wrong': sum(r['same_better_than_wrong'] for r in results),
        'mean_panel_to_test5_root_distance': round(
            statistics.mean(r['mean_panel_to_test5_root_distance'] for r in results), 8
        ) if results else None,
    }

    write_gz(WORK / f't08-result-{shard:02d}.json.gz', {
        'test': 8,
        'shard': shard,
        'summary': shard_summary,
        'meanings': results,
        'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps(shard_summary, ensure_ascii=False), flush=True)


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't08-result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 8 shard {i}')
        parts.append(read_gz(p))

    meanings = [x for p in parts for x in p.get('meanings', [])]
    same = [x['mean_same_attractor_distance'] for x in meanings]
    wrong = [x['mean_wrong_meaning_distance'] for x in meanings]
    root = [x['mean_panel_to_test5_root_distance'] for x in meanings]
    diffs = [b - a for a, b in zip(same, wrong)]

    dz = None
    if len(diffs) > 1:
        sd = statistics.stdev(diffs)
        if sd:
            dz = statistics.mean(diffs) / sd

    shard_summaries = [p['summary'] for p in parts]
    agreeing_shards = sum(
        s.get('mean_same_attractor_distance') is not None
        and s.get('mean_wrong_meaning_distance') is not None
        and s['mean_same_attractor_distance'] < s['mean_wrong_meaning_distance']
        for s in shard_summaries
    )

    family_counts = [x['families'] for x in meanings]
    ranked = sorted(
        meanings,
        key=lambda x: (-x['convergence_advantage'], -x['families'], x['meaning'])
    )

    out = {
        'version': 4,
        'test_id': 8,
        'test': 'Reverse-family convergence through the corrected exact mirrored Man Grid',
        'status': 'complete',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'dependency': manifest['dependency'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': {
            'eligible_meanings_prepared': manifest['prepared']['eligible_meanings'],
            'meanings_evaluated': len(meanings),
            'classified_families_seen': manifest['prepared']['classified_families_seen'],
            'minimum_families_per_meaning': MIN_FAMILIES,
            'mean_families_per_meaning': round(statistics.mean(family_counts), 8) if family_counts else None,
            'median_families_per_meaning': round(statistics.median(family_counts), 8) if family_counts else None,
            'mean_same_meaning_attractor_distance': round(statistics.mean(same), 8) if same else None,
            'median_same_meaning_attractor_distance': round(statistics.median(same), 8) if same else None,
            'mean_wrong_meaning_control_distance': round(statistics.mean(wrong), 8) if wrong else None,
            'median_wrong_meaning_control_distance': round(statistics.median(wrong), 8) if wrong else None,
            'mean_convergence_advantage': round(statistics.mean(diffs), 8) if diffs else None,
            'relative_convergence_advantage': round(
                statistics.mean(diffs) / statistics.mean(wrong), 8
            ) if wrong and statistics.mean(wrong) else None,
            'paired_effect_dz': round(dz, 8) if dz is not None else None,
            'meanings_same_attractor_closer_than_wrong_control': sum(
                x['same_better_than_wrong'] for x in meanings
            ),
            'fraction_meanings_same_attractor_closer_than_wrong_control': round(
                sum(x['same_better_than_wrong'] for x in meanings) / len(meanings), 8
            ) if meanings else None,
            'mean_panel_attractor_to_corrected_test5_root_distance': round(
                statistics.mean(root), 8
            ) if root else None,
            'shards_agreeing_same_closer_than_wrong': agreeing_shards,
            'shard_outputs': [s['meanings'] for s in shard_summaries],
            'feature_distance_used_for_test8_scoring': False,
            'test4_result_used': False,
            'learned_historical_transform_used': False,
            'fixed_modern_language_attractor_used': False,
        },
        'shard_summaries': shard_summaries,
        'top_convergent_meanings': ranked[:250],
        'meanings': meanings,
        'evidence_boundary': manifest['evidence_boundary'],
    }
    write_json(OUT, out)
    print(json.dumps(out['summary'], ensure_ascii=False, indent=2), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('prepare')
    r = sub.add_parser('run')
    r.add_argument('--shard', type=int, required=True)
    sub.add_parser('merge')
    args = ap.parse_args()
    if args.cmd == 'prepare':
        prepare()
    elif args.cmd == 'run':
        run(args.shard)
    else:
        merge()


if __name__ == '__main__':
    main()
