#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import man_grid_exact_v4 as V
import man_grid_test5_v4_shard50 as T5

ROOT = Path(__file__).resolve().parents[1]
SRC_WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
SOURCE_DIR = ROOT / 'data' / 'test7-source'
WORK = ROOT / 'data' / 'man-grid-test7-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-07-exact-v4.json'
N = 20
SOURCE_RUN = 34660500756
SOURCE_BASE_ARTIFACT_ID = 10287516871
SOURCE_MERGED_ARTIFACT_ID = 10288413679
MIN_HELDOUT = 20
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


def predict_from_other_families(others, costs):
    unique = sorted(set(tuple(x) for x in others))
    if not unique:
        return None
    return min(
        unique,
        key=lambda c: (
            statistics.mean(seqdist(c, s, costs) for s in others),
            len(c),
            c,
        ),
    )


def prepare():
    model_path = SRC_WORK / 'model.json.gz'
    if not model_path.exists():
        raise RuntimeError('corrected Test 5 base artifact model.json.gz is missing')
    model = read_gz(model_path)
    test5 = read_json(find_test5_json())
    validate_corrected_test5(test5, model)

    root_ids = set(model['root_ids'])
    family_rows = defaultdict(list)
    total_evidence = 0
    meanings_with_four_plus_families = 0

    for e in test5.get('entries', []):
        meaning = e.get('meaning')
        evidence = []
        for x in e.get('family_evidence', []):
            fam = str(x.get('family') or '').strip()
            seq = tuple(x.get('seq') or [])
            if not fam or fam == 'Unclassified' or not seq:
                continue
            if any(p not in root_ids for p in seq):
                raise RuntimeError(f'non-root family evidence sequence in {meaning!r} / {fam!r}')
            evidence.append((fam, seq))
        if len(evidence) < 4:
            continue
        meanings_with_four_plus_families += 1
        for fam, target in evidence:
            others = [list(seq) for ofam, seq in evidence if ofam != fam]
            if len(others) < 3:
                continue
            family_rows[fam].append({
                'meaning': meaning,
                'target': list(target),
                'others': others,
                'other_family_count': len(others),
            })
            total_evidence += 1

    shards = [[] for _ in range(N)]
    for fam, rows in sorted(family_rows.items()):
        rows.sort(key=lambda r: r['meaning'])
        shard = V.h64('test7-family', fam) % N
        shards[shard].append({'family': fam, 'meanings': rows})

    WORK.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / 'model.json.gz', model)
    for i, rows in enumerate(shards):
        write_gz(WORK / f'family-shard-{i:02d}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 7,
        'test': 'Family enrichment / held-out family recoverability from the corrected Test 5 reconstruction',
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
            'families_with_any_eligible_evidence': len(family_rows),
            'heldout_family_meaning_rows': total_evidence,
            'meanings_with_at_least_four_classified_families': meanings_with_four_plus_families,
            'family_shard_sizes': [len(x) for x in shards],
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
            'heldout_prediction': 'for each meaning and target family, choose the medoid sequence among the other classified families using mirrored-grid sequence distance, then score that prediction against the held-out family sequence',
            'wrong_meaning_control': 'compare the same prediction against a deterministic different-meaning sequence from the same held-out family',
            'reference_control': 'also record distance from the prediction to one deterministic contributing other-family sequence from the same meaning',
            'gap_cost': GAP,
            'feature_distance_used_for_test7_scoring': False,
            'test4_result_used': False,
            'geographic_origin_inferred': False,
        },
        'execution': {
            'version': 'exact-v4-test7-mirror-grid-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint family ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 7 measures family-level enrichment/recoverability under the corrected mirrored-Man-Grid lexical metric. It does not by itself infer a geographic origin or prove genealogical descent.',
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')
    model = read_gz(WORK / 'model.json.gz')
    rows = read_gz(WORK / f'family-shard-{shard:02d}.json.gz')
    costs = substitution_costs(model)
    out = []

    for fr in rows:
        fam = fr['family']
        eligible = fr.get('meanings', [])
        targets = {r['meaning']: tuple(r['target']) for r in eligible}
        meanings = sorted(targets)
        if len(meanings) < MIN_HELDOUT:
            continue
        pos = {m: i for i, m in enumerate(meanings)}
        real = []
        wrong = []
        reference = []
        per_meaning = []

        for r in eligible:
            meaning = r['meaning']
            target = tuple(r['target'])
            others = [tuple(x) for x in r['others']]
            pred = predict_from_other_families(others, costs)
            if pred is None:
                continue
            rd = seqdist(pred, target, costs)
            offset = 1 + (V.h64('test7-wrong-meaning', fam, meaning) % (len(meanings) - 1))
            wrong_meaning = meanings[(pos[meaning] + offset) % len(meanings)]
            wd = seqdist(pred, targets[wrong_meaning], costs)
            ref = others[V.h64('test7-reference-family', fam, meaning) % len(others)]
            xd = seqdist(pred, ref, costs)
            real.append(rd)
            wrong.append(wd)
            reference.append(xd)
            if len(per_meaning) < 200:
                per_meaning.append({
                    'meaning': meaning,
                    'prediction': list(pred),
                    'heldout_target': list(target),
                    'heldout_distance': round(rd, 8),
                    'wrong_meaning': wrong_meaning,
                    'wrong_meaning_distance': round(wd, 8),
                    'contributing_other_families': len(others),
                })

        if len(real) < MIN_HELDOUT:
            continue
        mean_real = statistics.mean(real)
        mean_wrong = statistics.mean(wrong)
        mean_ref = statistics.mean(reference)
        adv = mean_wrong - mean_real
        out.append({
            'family': fam,
            'heldout_meanings': len(real),
            'mean_heldout_distance': round(mean_real, 8),
            'median_heldout_distance': round(statistics.median(real), 8),
            'similarity': round(1.0 - mean_real, 8),
            'wrong_meaning_distance': round(mean_wrong, 8),
            'control_advantage': round(adv, 8),
            'relative_advantage': round(adv / mean_wrong, 8) if mean_wrong else None,
            'other_family_reference_distance': round(mean_ref, 8),
            'real_better_than_wrong': mean_real < mean_wrong,
            'meanings_real_better_than_wrong': sum(a < b for a, b in zip(real, wrong)),
            'enrichment_score': round(adv * math.log1p(len(real)), 8),
            'examples': per_meaning,
        })

    out.sort(key=lambda e: (-e['enrichment_score'], -e['heldout_meanings'], e['family']))
    write_gz(WORK / f't07-result-{shard:02d}.json.gz', {
        'test': 7,
        'shard': shard,
        'families': out,
        'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps({'test': 7, 'shard': shard, 'families': len(out)}), flush=True)


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't07-result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 7 shard {i}')
        parts.append(read_gz(p))

    families = [x for p in parts for x in p.get('families', [])]
    families.sort(key=lambda e: (-e['enrichment_score'], -e['heldout_meanings'], e['family']))
    total = sum(x['heldout_meanings'] for x in families)
    weighted_real = (
        sum(x['mean_heldout_distance'] * x['heldout_meanings'] for x in families) / total
        if total else None
    )
    weighted_wrong = (
        sum(x['wrong_meaning_distance'] * x['heldout_meanings'] for x in families) / total
        if total else None
    )
    by_similarity = sorted(families, key=lambda e: (-e['similarity'], -e['heldout_meanings'], e['family']))
    by_coverage = sorted(families, key=lambda e: (-e['heldout_meanings'], -e['similarity'], e['family']))

    out = {
        'version': 4,
        'test_id': 7,
        'test': 'Family enrichment / held-out family recoverability from the corrected Test 5 reconstruction',
        'status': 'complete',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'dependency': manifest['dependency'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': {
            'families_ranked': len(families),
            'minimum_heldout_meanings': MIN_HELDOUT,
            'shard_outputs': [len(p.get('families', [])) for p in parts],
            'families_real_better_than_wrong_meaning_control': sum(x['real_better_than_wrong'] for x in families),
            'weighted_mean_heldout_distance': round(weighted_real, 8) if weighted_real is not None else None,
            'weighted_mean_wrong_meaning_distance': round(weighted_wrong, 8) if weighted_wrong is not None else None,
            'top_enriched_family': families[0] if families else None,
            'nearest_family_by_similarity': by_similarity[0] if by_similarity else None,
            'highest_coverage_family': by_coverage[0] if by_coverage else None,
            'feature_distance_used_for_test7_scoring': False,
            'test4_result_used': False,
            'geographic_origin_inferred': False,
        },
        'families': families,
        'rankings': {
            'by_similarity': [x['family'] for x in by_similarity],
            'by_coverage': [x['family'] for x in by_coverage],
        },
        'execution': manifest['execution'],
        'prepared': manifest['prepared'],
        'evidence_boundary': manifest['evidence_boundary'],
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
