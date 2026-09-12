#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == 'tools' else Path('/mnt/data')
SOURCE_DIR = ROOT / 'data' / 'test11-source'
WORK = ROOT / 'data' / 'man-grid-test11-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-11-exact-v4.json'
TEST9_PATH = ROOT / 'data' / 'man-grid-test-09-exact-v4.json'

N = 20
GAP = 0.70
LAMBDAS = [0.0, 0.10, 0.25, 0.50, 1.0, 2.0]
CV_FOLDS = 3
MIN_FAMILIES = 3
MIN_BRANCH_FAMILIES = 1
RESAMPLE_RUNS = 3

# Exact aggregate recovered from the completed Test 10 calculations after the
# GitHub artifact-upload naming bug prevented the 20 shard files from merging.
# These values are used only to set the Test 11 design boundary: the specific
# Tamil/Serbo-Croatian pair receives zero privileged weight. Test 11 does not
# use these numbers as a scoring target.
TEST10_ACTUAL = {
    'source_run': 34678815939,
    'status': '20 calculations completed; merge blocked by artifact upload-format bug',
    'meanings_tested': 2483,
    'mean_parent_to_test5_root_distance': 0.27190,
    'mean_random_pair_parent_to_root_distance': 0.25930,
    'mean_parent_to_heldout_distance': 0.32332,
    'mean_random_parent_to_heldout_distance': 0.31464,
    'real_beats_random_root_fraction': 1148 / 2483,
    'real_beats_random_heldout_fraction': 1089 / 2483,
    'shards_real_root_better_than_random': 3,
    'shards_real_heldout_better_than_random': 2,
    'specific_anchor_pair_privileged': False,
}


def h64(*parts):
    b = '\x1f'.join(map(str, parts)).encode('utf-8', 'ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8], 'big')


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


def layer_specs(spec):
    return [*spec['upper'], *spec['lower']]


def parse_cell(cell):
    try:
        tail = cell.rsplit('-R', 1)[1]
        r, c = tail.split('-C', 1)
        return int(r), int(c)
    except Exception as e:
        raise RuntimeError(f'cannot parse exact Man Grid cell {cell!r}') from e


def one_way_mirror_grid_distance(ga, gb, spec, from_side='L', to_side='R'):
    pa = ga['all_left'] if from_side == 'L' else ga['all_right']
    pb = gb['all_right'] if to_side == 'R' else gb['all_left']
    layers = layer_specs(spec)
    if len(pa) != 10 or len(pb) != 10 or len(layers) != 10:
        raise RuntimeError('expected ten exact mirrored Man Grid layers')
    vals = []
    for ca, cb, layer in zip(pa, pb, layers):
        ra, xa = parse_cell(ca)
        rb, xb = parse_cell(cb)
        rd = abs(ra - rb) / max(1, int(layer['rows']) - 1)
        cd = abs(xa - xb) / max(1, int(layer['columns']) - 1)
        vals.append((rd + cd) / 2.0)
    return statistics.mean(vals)


def mirror_grid_distance(a, b, model):
    ga = model['params'][a]['grid']
    gb = model['params'][b]['grid']
    spec = model['grid']
    lr = one_way_mirror_grid_distance(ga, gb, spec, 'L', 'R')
    rl = one_way_mirror_grid_distance(ga, gb, spec, 'R', 'L')
    return (lr + rl) / 2.0


def substitution_costs(model):
    ids = list(model['root_ids'])
    return {a: {b: mirror_grid_distance(a, b, model) for b in ids} for a in ids}


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
            nd[j] = min(dp[j] + GAP, nd[j - 1] + GAP, dp[j - 1] + costs[x][y])
        dp = nd
    return min(1.0, dp[m] / max(len(a), len(b)))


def weighted_medoid(rows, costs, limit=32):
    cnt = Counter()
    for seq, weight in rows:
        cnt[tuple(seq)] += float(weight)
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
            i -= 1
            j -= 1
        elif op == 'up':
            out.append((a[i - 1], None))
            i -= 1
        else:
            out.append((None, b[j - 1]))
            j -= 1
    out.reverse()
    return out


def infer_midpoint(a, b, model, costs):
    roots = list(model['root_ids'])
    parent = []
    for x, y in align_sequences(a, b, costs):
        if x is None:
            parent.append(y)
        elif y is None:
            parent.append(x)
        elif x == y:
            parent.append(x)
        else:
            q = min(
                roots,
                key=lambda r: (
                    costs[r][x] * costs[r][x] + costs[r][y] * costs[r][y],
                    max(costs[r][x], costs[r][y]),
                    abs(costs[r][x] - costs[r][y]),
                    r,
                ),
            )
            parent.append(q)
    return tuple(parent)


def ipa(seq, model):
    return '/' + ''.join(str(model['params'][p]['name']) for p in seq) + '/'


def family_key(code, family):
    family = str(family or '').strip()
    if not family or family == 'Unclassified':
        return '@' + str(code)
    return family


def branch_support_from_test9(test9):
    support = defaultdict(lambda: [0.0, 0.0])
    meta = {}
    for side_idx, key in enumerate(('branch_a_ranking', 'branch_b_ranking')):
        for rec in test9.get(key, []):
            fk = family_key(rec.get('code'), rec.get('family'))
            votes = float(rec.get('weighted_shard_votes') or 0.0)
            support[fk][side_idx] += votes
            meta[fk] = {'family': rec.get('family') or 'Unclassified', 'example_code': rec.get('code')}
    out = {}
    for fk, (a, b) in sorted(support.items()):
        total = a + b
        if total <= 0 or a == b:
            continue
        out[fk] = {
            'sign': 1 if a > b else -1,
            'strength': abs(a - b) / total,
            'a_votes': a,
            'b_votes': b,
            **meta.get(fk, {}),
        }
    return out


def shuffled_branch_support(branch_support):
    keys = sorted(branch_support)
    positives = sum(1 for k in keys if branch_support[k]['sign'] > 0)
    ordered = sorted(keys, key=lambda k: (h64('test11-shuffled-axis', k), k))
    out = {}
    for i, k in enumerate(ordered):
        rec = dict(branch_support[k])
        rec['sign'] = 1 if i < positives else -1
        out[k] = rec
    return out


def load_languages():
    files = sorted(SOURCE_DIR.glob('language-shard-*.json.gz'))
    if len(files) != 20:
        raise RuntimeError(f'expected 20 corrected Test 6 language shards, found {len(files)}')
    rows = []
    for p in files:
        rows.extend(read_gz(p))
    return rows


def validate_sources(model, roots_payload, test9):
    if int(model.get('grid', {}).get('counts', {}).get('total_cells', 0)) != 1074:
        raise RuntimeError('source model is not the exact 1,074-cell mirrored Man Grid')
    if len(model.get('root_ids', [])) != 36:
        raise RuntimeError('source model does not contain corrected 36-root inventory')
    if roots_payload.get('test_id') != 5 or len(roots_payload.get('entries', {})) != 12000:
        raise RuntimeError('corrected Test 5 root dictionary is incomplete')
    if test9.get('status') != 'complete' or test9.get('test_id') != 9 or int(test9.get('shards', 0)) != 20:
        raise RuntimeError('corrected Test 9 output is incomplete')
    calc = test9.get('calculation', {})
    if calc.get('feature_distance_used_for_test9_scoring') is not False:
        raise RuntimeError('Test 9 did not exclude feature-space scoring')
    if calc.get('test4_result_used') is not False:
        raise RuntimeError('Test 9 reused invalid Test 4 output')
    if TEST10_ACTUAL['specific_anchor_pair_privileged'] is not False:
        raise RuntimeError('Test 10 outcome does not permit de-privileging the specific anchor pair')


def prepare():
    model = read_gz(SOURCE_DIR / 'model.json.gz')
    roots_payload = read_gz(SOURCE_DIR / 'test5-roots.json.gz')
    test9 = read_json(TEST9_PATH)
    validate_sources(model, roots_payload, test9)
    costs = substitution_costs(model)
    root_ids = set(model['root_ids'])
    roots = roots_payload['entries']
    branch_support = branch_support_from_test9(test9)
    shuffled_support = shuffled_branch_support(branch_support)
    languages = load_languages()

    grouped = defaultdict(lambda: defaultdict(list))
    language_forms = 0
    for lr in languages:
        code = str(lr['code'])
        fk = family_key(code, lr.get('family'))
        for meaning, variants in lr.get('meanings', {}).items():
            if meaning not in roots:
                continue
            med = weighted_medoid(variants, costs)
            if not med:
                continue
            if any(p not in root_ids for p in med):
                raise RuntimeError(f'non-root phoneme in {code}/{meaning}')
            grouped[meaning][fk].append((med, 1.0))
            language_forms += 1

    shards = [[] for _ in range(N)]
    family_rep_count = 0
    eligible = 0
    branch_eligible = 0
    for meaning in sorted(roots):
        fams = []
        for fk, seq_rows in sorted(grouped.get(meaning, {}).items()):
            med = weighted_medoid(seq_rows, costs)
            if not med:
                continue
            bs = branch_support.get(fk)
            fams.append({
                'family_key': fk,
                'seq': list(med),
                'branch_sign': int(bs['sign']) if bs else 0,
                'branch_strength': round(float(bs['strength']), 8) if bs else 0.0,
            })
        if len(fams) < MIN_FAMILIES:
            continue
        pos = sum(1 for f in fams if f['branch_sign'] > 0)
        neg = sum(1 for f in fams if f['branch_sign'] < 0)
        if pos >= MIN_BRANCH_FAMILIES and neg >= MIN_BRANCH_FAMILIES:
            branch_eligible += 1
        family_rep_count += len(fams)
        eligible += 1
        row = {'meaning': meaning, 'root': roots[meaning]['seq'], 'families': fams}
        shards[h64('test11-meaning', meaning) % N].append(row)

    for rows in shards:
        rows.sort(key=lambda x: x['meaning'])

    WORK.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / 'model.json.gz', model)
    for i, rows in enumerate(shards):
        write_gz(WORK / f'meaning-shard-{i}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 11,
        'test': 'Test 10-adapted branch-balanced candidate-language reconstruction',
        'status': 'prepared',
        'shards': N,
        'dependency': {
            'test10_actual_outcome': TEST10_ACTUAL,
            'test9': 'corrected 20-shard bipolar Man-Grid branch discovery; family branch support is aggregated from its data-driven shard rankings',
            'test6': 'corrected attested-language forms reused from the Test 6 base artifact',
            'test5': 'corrected 36-root mirror-grid representation; Test 5 root forms are evaluation targets only and do not construct Test 11 candidates',
            'test4': 'not used; Test 4 remains the incomplete precursor to corrected Test 5',
        },
        'adaptation_to_test10': {
            'specific_tamil_serbo_croatian_pair_privileged': False,
            'specific_anchor_pair_weight': 0.0,
            'reason': 'Test 10 found the discovered anchor pair beat wrong-meaning controls but lost overall to random same-meaning language-pair parents; Test 11 therefore treats the Test 9 bipolar structure only as soft family-level evidence.',
            'lambda_grid_includes_zero': True,
            'fallback_to_unconstrained_baseline': True,
        },
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': {
            'metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'family_equal_weighting': True,
            'unclassified_languages_as_independent_pseudofamilies': True,
            'baseline': 'mirror-grid medoid across one representative per family',
            'branch_constraint': 'soft minimax penalty on Test 9-supported positive and negative family sides; objective = equal-family mean distance + lambda * max(weighted branch-A mean distance, weighted branch-B mean distance)',
            'lambda_selection': f'{CV_FOLDS}-fold deterministic family cross-validation separately for each meaning over {LAMBDAS}; lambda=0 is always permitted',
            'candidate_pool': 'training family representatives plus branch-side medoids and their discrete mirrored-Man-Grid midpoint',
            'shuffled_axis_control': 'deterministic permutation of Test 9 family side labels preserving the global positive/negative counts and confidence strengths',
            'random_pair_control': 'deterministic same-meaning pair of training family representatives, converted to a discrete mirrored-Man-Grid midpoint',
            'final_candidate_rule': 'use branch-balanced candidate only when its cross-validated held-out-family distance beats both unconstrained baseline and shuffled-axis control; otherwise use unconstrained baseline',
            'test5_root_used_for_candidate_inference': False,
            'feature_distance_used_for_test11_scoring': False,
            'test4_result_used': False,
            'specific_test9_anchor_pair_special_weight': False,
            'central_circle_operator_used': False,
        },
        'prepared': {
            'attested_languages_loaded': len(languages),
            'attested_language_meaning_medoid_forms': language_forms,
            'eligible_meanings': eligible,
            'branch_eligible_meanings': branch_eligible,
            'family_representatives': family_rep_count,
            'test9_branch_supported_family_keys': len(branch_support),
            'meaning_shard_sizes': [len(x) for x in shards],
        },
        'execution': {
            'version': 'exact-v4-test11-adapted-branch-balanced-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint meaning ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 11 reconstructs a second full candidate lexicon while explicitly allowing the Test 9 branch constraint to collapse to zero after Test 10 rejected the specific anchor pair as privileged. Any branch benefit is provisional internal cross-validation and must be independently tested by Test 12. This test does not establish genealogy, chronology, homeland, or a central-circle transform.',
        'branch_support': branch_support,
        'shuffled_branch_support': shuffled_support,
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps({
        'test': 11,
        'eligible_meanings': eligible,
        'branch_eligible_meanings': branch_eligible,
        'languages': len(languages),
        'branch_supported_family_keys': len(branch_support),
        'shard_sizes': manifest['prepared']['meaning_shard_sizes'],
    }), flush=True)


def mean_dist(candidate, fams, costs):
    if not fams:
        return None
    return statistics.mean(seqdist(candidate, tuple(f['seq']), costs) for f in fams)


def branch_mean(candidate, fams, sign, branch_map, costs):
    vals = []
    weights = []
    for f in fams:
        rec = branch_map.get(f['family_key'])
        if not rec or int(rec['sign']) != sign:
            continue
        w = max(1e-9, float(rec.get('strength') or 0.0))
        vals.append(seqdist(candidate, tuple(f['seq']), costs))
        weights.append(w)
    if not vals:
        return None
    return sum(v*w for v, w in zip(vals, weights)) / sum(weights)


def candidate_pool(fams, branch_map, model, costs):
    uniq = {tuple(f['seq']) for f in fams}
    if not uniq:
        return []
    baseline = weighted_medoid([(s, 1.0) for s in uniq], costs)
    if baseline:
        uniq.add(tuple(baseline))
    pos = [f for f in fams if branch_map.get(f['family_key'], {}).get('sign') == 1]
    neg = [f for f in fams if branch_map.get(f['family_key'], {}).get('sign') == -1]
    if pos and neg:
        pa = weighted_medoid([(f['seq'], max(1e-9, float(branch_map[f['family_key']]['strength']))) for f in pos], costs)
        pb = weighted_medoid([(f['seq'], max(1e-9, float(branch_map[f['family_key']]['strength']))) for f in neg], costs)
        if pa:
            uniq.add(tuple(pa))
        if pb:
            uniq.add(tuple(pb))
        if pa and pb:
            uniq.add(infer_midpoint(pa, pb, model, costs))
    return sorted(uniq, key=lambda s: (len(s), s))


def choose_candidate(fams, branch_map, lam, model, costs):
    pool = candidate_pool(fams, branch_map, model, costs)
    if not pool:
        return None
    best = None
    for c in pool:
        overall = mean_dist(c, fams, costs)
        a = branch_mean(c, fams, +1, branch_map, costs)
        b = branch_mean(c, fams, -1, branch_map, costs)
        penalty = max(a, b) if a is not None and b is not None else 0.0
        objective = overall + float(lam) * penalty
        key = (objective, overall, penalty, len(c), c)
        if best is None or key < best[0]:
            best = (key, c, overall, a, b)
    return {
        'seq': best[1],
        'train_mean_distance': best[2],
        'branch_a_distance': best[3],
        'branch_b_distance': best[4],
    }


def cv_fold(family_key_value, meaning):
    return h64('test11-cv-family', meaning, family_key_value) % CV_FOLDS


def random_pair_candidate(train, meaning, fold, model, costs):
    ordered = sorted(train, key=lambda f: (h64('test11-random-pair', meaning, fold, f['family_key']), f['family_key']))
    if len(ordered) < 2:
        return None
    return infer_midpoint(ordered[0]['seq'], ordered[1]['seq'], model, costs)


def cv_scores(fams, branch_map, model, costs, meaning):
    lambda_scores = {lam: [] for lam in LAMBDAS}
    baseline_scores = []
    random_scores = []
    valid_folds = 0
    for fold in range(CV_FOLDS):
        held = [f for f in fams if cv_fold(f['family_key'], meaning) == fold]
        train = [f for f in fams if cv_fold(f['family_key'], meaning) != fold]
        if not held or len(train) < 2:
            continue
        valid_folds += 1
        base = choose_candidate(train, {}, 0.0, model, costs)
        if base:
            baseline_scores.append(mean_dist(base['seq'], held, costs))
        rp = random_pair_candidate(train, meaning, fold, model, costs)
        if rp:
            random_scores.append(mean_dist(rp, held, costs))
        for lam in LAMBDAS:
            cand = choose_candidate(train, branch_map, lam, model, costs)
            if cand:
                lambda_scores[lam].append(mean_dist(cand['seq'], held, costs))
    baseline = statistics.mean(baseline_scores) if baseline_scores else None
    random = statistics.mean(random_scores) if random_scores else None
    means = {
        lam: (statistics.mean(vals) if vals else None)
        for lam, vals in lambda_scores.items()
    }
    usable = [(score, lam) for lam, score in means.items() if score is not None]
    if usable:
        chosen_score, chosen_lambda = min(usable, key=lambda x: (x[0], x[1]))
    else:
        chosen_score, chosen_lambda = baseline, 0.0
    return {
        'valid_folds': valid_folds,
        'baseline': baseline,
        'random': random,
        'lambda_scores': means,
        'chosen_lambda': chosen_lambda,
        'chosen_score': chosen_score,
    }


def resample_stability(fams, branch_map, lam, full_seq, meaning, model, costs):
    vals = []
    for rep in range(RESAMPLE_RUNS):
        kept = [
            f for f in fams
            if (h64('test11-resample', meaning, rep, f['family_key']) % 5) != 0
        ]
        if len(kept) < 2:
            continue
        cand = choose_candidate(kept, branch_map, lam, model, costs)
        if cand:
            vals.append(seqdist(full_seq, cand['seq'], costs))
    return statistics.mean(vals) if vals else None


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
    rows = read_gz(WORK / f'meaning-shard-{shard}.json.gz')
    manifest = read_json(WORK / 'prepared-manifest.json')
    branch_map = manifest['branch_support']
    shuffled_map = manifest['shuffled_branch_support']
    costs = substitution_costs(model)
    out = []

    for row in rows:
        meaning = row['meaning']
        fams = row['families']
        baseline_cv = cv_scores(fams, {}, model, costs, meaning)
        actual_cv = cv_scores(fams, branch_map, model, costs, meaning)
        shuffled_cv = cv_scores(fams, shuffled_map, model, costs, meaning)

        base_full = choose_candidate(fams, {}, 0.0, model, costs)
        actual_full = choose_candidate(fams, branch_map, actual_cv['chosen_lambda'], model, costs)
        shuffled_full = choose_candidate(fams, shuffled_map, shuffled_cv['chosen_lambda'], model, costs)
        if not base_full:
            continue
        if not actual_full:
            actual_full = base_full
        if not shuffled_full:
            shuffled_full = base_full

        bcv = baseline_cv['baseline']
        acv = actual_cv['chosen_score']
        scv = shuffled_cv['chosen_score']
        branch_accepted = (
            bcv is not None and acv is not None and scv is not None and
            acv < bcv and acv < scv and actual_cv['chosen_lambda'] > 0.0
        )
        final = actual_full if branch_accepted else base_full
        final_lambda = actual_cv['chosen_lambda'] if branch_accepted else 0.0
        final_branch_map = branch_map if branch_accepted else {}

        root = tuple(row['root'])
        stability = resample_stability(fams, final_branch_map, final_lambda, final['seq'], meaning, model, costs)
        pos = sum(1 for f in fams if branch_map.get(f['family_key'], {}).get('sign') == 1)
        neg = sum(1 for f in fams if branch_map.get(f['family_key'], {}).get('sign') == -1)

        out.append({
            'meaning': meaning,
            'families': len(fams),
            'branch_a_families': pos,
            'branch_b_families': neg,
            'baseline_seq': list(base_full['seq']),
            'baseline_ipa': ipa(base_full['seq'], model),
            'branch_seq': list(actual_full['seq']),
            'branch_ipa': ipa(actual_full['seq'], model),
            'shuffled_seq': list(shuffled_full['seq']),
            'final_seq': list(final['seq']),
            'final_ipa': ipa(final['seq'], model),
            'branch_accepted': branch_accepted,
            'chosen_lambda': actual_cv['chosen_lambda'],
            'shuffled_chosen_lambda': shuffled_cv['chosen_lambda'],
            'cv_valid_folds': actual_cv['valid_folds'],
            'cv_baseline_heldout_distance': round(bcv, 8) if bcv is not None else None,
            'cv_branch_heldout_distance': round(acv, 8) if acv is not None else None,
            'cv_shuffled_heldout_distance': round(scv, 8) if scv is not None else None,
            'cv_random_pair_heldout_distance': round(actual_cv['random'], 8) if actual_cv['random'] is not None else None,
            'baseline_to_test5_root_distance': round(seqdist(base_full['seq'], root, costs), 8),
            'branch_to_test5_root_distance': round(seqdist(actual_full['seq'], root, costs), 8),
            'shuffled_to_test5_root_distance': round(seqdist(shuffled_full['seq'], root, costs), 8),
            'final_to_test5_root_distance': round(seqdist(final['seq'], root, costs), 8),
            'resample_stability_distance': round(stability, 8) if stability is not None else None,
        })

    if len(out) > 1:
        roots = {r['meaning']: tuple(r['root']) for r in rows}
        keys = sorted(roots)
        pos_map = {m: i for i, m in enumerate(keys)}
        for rec in out:
            m = rec['meaning']
            off = 1 + h64('test11-wrong-root', m) % (len(keys) - 1)
            wm = keys[(pos_map[m] + off) % len(keys)]
            rec['wrong_meaning'] = wm
            rec['final_to_wrong_meaning_test5_root_distance'] = round(
                seqdist(tuple(rec['final_seq']), roots[wm], costs), 8
            )

    def vals(key):
        return [x[key] for x in out if x.get(key) is not None]
    b = vals('cv_baseline_heldout_distance')
    a = vals('cv_branch_heldout_distance')
    s = vals('cv_shuffled_heldout_distance')
    r = vals('cv_random_pair_heldout_distance')
    summary = {
        'test': 11,
        'shard': shard,
        'meanings': len(out),
        'branch_accepted_meanings': sum(x['branch_accepted'] for x in out),
        'mean_cv_baseline_heldout_distance': round(statistics.mean(b), 8) if b else None,
        'mean_cv_branch_heldout_distance': round(statistics.mean(a), 8) if a else None,
        'mean_cv_shuffled_heldout_distance': round(statistics.mean(s), 8) if s else None,
        'mean_cv_random_pair_heldout_distance': round(statistics.mean(r), 8) if r else None,
        'mean_final_to_test5_root_distance': round(statistics.mean(vals('final_to_test5_root_distance')), 8) if out else None,
        'mean_baseline_to_test5_root_distance': round(statistics.mean(vals('baseline_to_test5_root_distance')), 8) if out else None,
        'mean_resample_stability_distance': round(statistics.mean(vals('resample_stability_distance')), 8) if vals('resample_stability_distance') else None,
    }
    write_gz(WORK / f't11-result-{shard}.json.gz', {
        'test': 11,
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
        p = WORK / f't11-result-{i}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 11 shard {i}')
        parts.append(read_gz(p))
    rows = [x for p in parts for x in p.get('meanings', [])]
    rows.sort(key=lambda x: x['meaning'])
    shard_summaries = [p['summary'] for p in parts]

    def vals(key):
        return [x[key] for x in rows if x.get(key) is not None]
    b = vals('cv_baseline_heldout_distance')
    a = vals('cv_branch_heldout_distance')
    s = vals('cv_shuffled_heldout_distance')
    r = vals('cv_random_pair_heldout_distance')
    fr = vals('final_to_test5_root_distance')
    br = vals('baseline_to_test5_root_distance')
    wr = vals('final_to_wrong_meaning_test5_root_distance')
    stab = vals('resample_stability_distance')

    comparable_ab = [(x['cv_branch_heldout_distance'], x['cv_baseline_heldout_distance']) for x in rows if x.get('cv_branch_heldout_distance') is not None and x.get('cv_baseline_heldout_distance') is not None]
    comparable_as = [(x['cv_branch_heldout_distance'], x['cv_shuffled_heldout_distance']) for x in rows if x.get('cv_branch_heldout_distance') is not None and x.get('cv_shuffled_heldout_distance') is not None]
    lam_counts = Counter(str(x['chosen_lambda']) for x in rows)

    summary = {
        'meanings_reconstructed': len(rows),
        'shards_completed': len(parts),
        'branch_accepted_meanings': sum(x['branch_accepted'] for x in rows),
        'branch_accepted_fraction': round(sum(x['branch_accepted'] for x in rows) / len(rows), 8) if rows else None,
        'lambda_distribution': dict(sorted(lam_counts.items(), key=lambda kv: float(kv[0]))),
        'mean_cv_baseline_heldout_distance': round(statistics.mean(b), 8) if b else None,
        'mean_cv_branch_heldout_distance': round(statistics.mean(a), 8) if a else None,
        'mean_cv_shuffled_heldout_distance': round(statistics.mean(s), 8) if s else None,
        'mean_cv_random_pair_heldout_distance': round(statistics.mean(r), 8) if r else None,
        'meanings_branch_beats_baseline_cv': sum(x < y for x, y in comparable_ab),
        'fraction_branch_beats_baseline_cv': round(sum(x < y for x, y in comparable_ab) / len(comparable_ab), 8) if comparable_ab else None,
        'meanings_branch_beats_shuffled_cv': sum(x < y for x, y in comparable_as),
        'fraction_branch_beats_shuffled_cv': round(sum(x < y for x, y in comparable_as) / len(comparable_as), 8) if comparable_as else None,
        'effect_dz_branch_vs_baseline_cv': round(paired_dz([x for x, _ in comparable_ab], [y for _, y in comparable_ab]), 8) if comparable_ab and paired_dz([x for x, _ in comparable_ab], [y for _, y in comparable_ab]) is not None else None,
        'effect_dz_branch_vs_shuffled_cv': round(paired_dz([x for x, _ in comparable_as], [y for _, y in comparable_as]), 8) if comparable_as and paired_dz([x for x, _ in comparable_as], [y for _, y in comparable_as]) is not None else None,
        'shards_branch_mean_better_than_baseline': sum(
            x['mean_cv_branch_heldout_distance'] is not None and x['mean_cv_baseline_heldout_distance'] is not None and
            x['mean_cv_branch_heldout_distance'] < x['mean_cv_baseline_heldout_distance']
            for x in shard_summaries
        ),
        'shards_branch_mean_better_than_shuffled': sum(
            x['mean_cv_branch_heldout_distance'] is not None and x['mean_cv_shuffled_heldout_distance'] is not None and
            x['mean_cv_branch_heldout_distance'] < x['mean_cv_shuffled_heldout_distance']
            for x in shard_summaries
        ),
        'mean_final_to_test5_root_distance': round(statistics.mean(fr), 8) if fr else None,
        'mean_baseline_to_test5_root_distance': round(statistics.mean(br), 8) if br else None,
        'mean_final_to_wrong_meaning_test5_root_distance': round(statistics.mean(wr), 8) if wr else None,
        'mean_resample_stability_distance': round(statistics.mean(stab), 8) if stab else None,
        'median_resample_stability_distance': round(statistics.median(stab), 8) if stab else None,
        'specific_test9_anchor_pair_special_weight': False,
        'test5_root_used_for_candidate_inference': False,
        'feature_distance_used_for_test11_scoring': False,
        'test4_result_used': False,
        'central_circle_operator_used': False,
    }

    out = {
        'version': 4,
        'test_id': 11,
        'test': manifest['test'],
        'status': 'complete',
        'shards': N,
        'dependency': manifest['dependency'],
        'adaptation_to_test10': manifest['adaptation_to_test10'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': summary,
        'shard_summaries': shard_summaries,
        'entries': rows,
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
    args = ap.parse_args()
    if args.cmd == 'prepare':
        prepare()
    elif args.cmd == 'run':
        run(args.shard)
    else:
        merge()


if __name__ == '__main__':
    main()
