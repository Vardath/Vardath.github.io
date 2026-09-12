#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == 'tools' else Path('/mnt/data')
SOURCE_DIR = ROOT / 'data' / 'man-grid-test12-source'
WORK = ROOT / 'data' / 'man-grid-test12-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-12-exact-v4.json'
TEST11_PATH = ROOT / 'data' / 'man-grid-test-11-exact-v4.json'
N = 20
GAP = 0.70
ASJP_COMMIT = '012795349540ba0dabfdcf2be16f2e77622f62d6'
ASJP_BASE = f'https://raw.githubusercontent.com/lexibank/asjp/{ASJP_COMMIT}/cldf/'
ASJP_FILES = ('parameters.csv', 'languages.csv', 'forms.csv')
MIN_OVERLAP_CONCEPTS = 90
MIN_FULLY_MAPPED_FORMS = 10000


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


def download(url, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers={'User-Agent': 'Vardath-ManGrid-Test12/1.0'})
    with urllib.request.urlopen(req) as r, path.open('wb') as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def norm_symbol(s):
    return unicodedata.normalize('NFC', str(s or '').strip())


def layer_specs(spec):
    return [*spec['upper'], *spec['lower']]


def parse_cell(cell):
    tail = cell.rsplit('-R', 1)[1]
    r, c = tail.split('-C', 1)
    return int(r), int(c)


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


def weighted_medoid(seqs, costs):
    cnt = Counter(tuple(s) for s in seqs if s)
    items = list(cnt.items())
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


def paired_dz(real, ctrl):
    diffs = [b - a for a, b in zip(real, ctrl)]
    if len(diffs) < 2:
        return None
    sd = statistics.stdev(diffs)
    return statistics.mean(diffs) / sd if sd else None


def boolish_true(v):
    return str(v or '').strip().lower() in {'1', 'true', 'yes', 'y', 't'}


def validate_sources(model, test11):
    if int(model.get('grid', {}).get('counts', {}).get('total_cells', 0)) != 1074:
        raise RuntimeError('source model is not exact 1,074-cell mirrored Man Grid')
    if len(model.get('root_ids', [])) != 36:
        raise RuntimeError('source model does not contain corrected 36-root inventory')
    if test11.get('status') != 'complete' or test11.get('test_id') != 11 or int(test11.get('shards', 0)) != 20:
        raise RuntimeError('published Test 11 output is incomplete')
    s = test11.get('summary', {})
    if int(s.get('meanings_reconstructed', 0)) != 12000 or int(s.get('shards_completed', 0)) != 20:
        raise RuntimeError('Test 11 did not publish a complete 12,000-meaning reconstruction')
    calc = test11.get('calculation', {})
    if calc.get('feature_distance_used_for_test11_scoring') is not False:
        raise RuntimeError('Test 11 source used feature-space scoring')
    if calc.get('test4_result_used') is not False:
        raise RuntimeError('Test 11 source reused invalid Test 4')
    if calc.get('test5_root_used_for_candidate_inference') is not False:
        raise RuntimeError('Test 11 used Test 5 root for candidate inference')
    if calc.get('central_circle_operator_used') is not False:
        raise RuntimeError('Test 11 used an unsupported circle operator')


def load_asjp_parameters(path):
    out = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            name = str(row.get('Name') or '').lstrip('*').strip()
            if name:
                out[str(row['ID'])] = name
    return out


def load_asjp_languages(path):
    out = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            lid = str(row.get('ID') or '')
            if not lid:
                continue
            fam = str(row.get('Family') or '').strip() or 'Unclassified'
            out[lid] = {
                'id': lid,
                'name': row.get('Name') or lid,
                'family': fam,
                'glottocode': row.get('Glottocode') or '',
                'iso': row.get('ISO639P3code') or row.get('code_iso') or '',
            }
    return out


def build_exact_symbol_map(model):
    by_name = {}
    for pid, rec in model['params'].items():
        name = norm_symbol(rec.get('name'))
        if name:
            if name in by_name and by_name[name] != pid:
                raise RuntimeError(f'duplicate PHOIBLE symbol name in model: {name!r}')
            by_name[name] = pid
    return {name: model['nearest_root'][pid] for name, pid in by_name.items()}


def prepare():
    WORK.mkdir(parents=True, exist_ok=True)
    asjp_dir = WORK / 'asjp-v21'
    for fn in ASJP_FILES:
        download(ASJP_BASE + fn, asjp_dir / fn)

    model_path = SOURCE_DIR / 'model.json.gz'
    if not model_path.exists():
        raise RuntimeError('Test 11 base artifact model.json.gz is missing')
    model = read_gz(model_path)
    test11 = read_json(TEST11_PATH)
    validate_sources(model, test11)
    costs = substitution_costs(model)

    candidates = {}
    for e in test11.get('entries', []):
        candidates[str(e['meaning'])] = {
            'final_seq': e['final_seq'],
            'baseline_seq': e['baseline_seq'],
            'branch_seq': e['branch_seq'],
            'shuffled_seq': e['shuffled_seq'],
            'branch_accepted': bool(e['branch_accepted']),
            'chosen_lambda': e.get('chosen_lambda'),
        }

    param_names = load_asjp_parameters(asjp_dir / 'parameters.csv')
    concept_by_param = {pid: name for pid, name in param_names.items() if name in candidates}
    if len(concept_by_param) < MIN_OVERLAP_CONCEPTS:
        raise RuntimeError(f'only {len(concept_by_param)} ASJP concepts overlap frozen Test 11 meanings')
    languages = load_asjp_languages(asjp_dir / 'languages.csv')
    symbol_to_root = build_exact_symbol_map(model)

    forms = defaultdict(lambda: defaultdict(list))
    total_rows = 0
    nonloan_rows = 0
    overlap_rows = 0
    fully_mapped_rows = 0
    rejected_unmapped_rows = 0
    total_segment_tokens = 0
    mapped_segment_tokens = 0
    unmapped_token_counts = Counter()

    with open(asjp_dir / 'forms.csv', newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            total_rows += 1
            if boolish_true(row.get('Loan')):
                continue
            nonloan_rows += 1
            meaning = concept_by_param.get(str(row.get('Parameter_ID') or ''))
            if not meaning:
                continue
            overlap_rows += 1
            lid = str(row.get('Language_ID') or '')
            if lid not in languages:
                continue
            toks = [norm_symbol(x) for x in str(row.get('Segments') or '').split() if norm_symbol(x)]
            if not toks:
                continue
            total_segment_tokens += len(toks)
            seq = []
            ok = True
            for tok in toks:
                rid = symbol_to_root.get(tok)
                if rid is None:
                    unmapped_token_counts[tok] += 1
                    ok = False
                else:
                    mapped_segment_tokens += 1
                    seq.append(rid)
            if not ok:
                rejected_unmapped_rows += 1
                continue
            fully_mapped_rows += 1
            forms[lid][meaning].append(seq)

    if fully_mapped_rows < MIN_FULLY_MAPPED_FORMS:
        raise RuntimeError(f'only {fully_mapped_rows} ASJP forms map exactly into the mirrored-Man-Grid model')

    wrong_keys = sorted(concept_by_param.values())
    compact_candidates = {m: candidates[m] for m in wrong_keys}
    write_gz(WORK / 'model.json.gz', model)
    write_gz(WORK / 'candidates.json.gz', compact_candidates)

    shards = [[] for _ in range(N)]
    language_meaning_records = 0
    observed_families = set()
    observed_meanings = set()
    for lid in sorted(forms):
        meta = languages[lid]
        means = {}
        for meaning, seqs in sorted(forms[lid].items()):
            med = weighted_medoid(seqs, costs)
            if med:
                means[meaning] = list(med)
                observed_meanings.add(meaning)
        if not means:
            continue
        language_meaning_records += len(means)
        observed_families.add(meta['family'])
        rec = {**meta, 'meanings': means}
        shards[h64('test12-asjp-language', lid) % N].append(rec)

    for rows in shards:
        rows.sort(key=lambda x: x['id'])
    for i, rows in enumerate(shards):
        write_gz(WORK / f'asjp-language-shard-{i}.json.gz', rows)

    manifest = {
        'version': 4,
        'test_id': 12,
        'test': 'Independent validation of frozen Test 11 candidate reconstruction on ASJP v21 lexical forms',
        'status': 'prepared',
        'shards': N,
        'dependency': {
            'test11': 'frozen published 12,000-meaning candidate lexicon; no Test 12 evidence may modify it',
            'test10': 'carried only through Test 11 adaptation; no Tamil/Serbo-Croatian special weighting is introduced',
            'test4': 'not used',
        },
        'independent_source': {
            'dataset': 'ASJP Database CLDF v21',
            'commit': ASJP_COMMIT,
            'lexical_forms_used_by_test11_candidate_training': False,
            'concepts_available': len(param_names),
            'concepts_overlapping_test11': len(concept_by_param),
            'license': 'CC-BY-4.0',
        },
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': {
            'metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'asjp_segment_mapping': 'strict Unicode-NFC exact symbol match to pinned PHOIBLE segment names already present in the corrected Test 11 model, followed by that model\'s precomputed nearest 36-root mapping; any form containing an unmapped segment is rejected in full',
            'synonym_handling': 'per-language per-meaning mirror-grid medoid before validation',
            'loan_handling': 'ASJP forms marked Loan=true are excluded',
            'frozen_candidate': 'Test 11 final_seq; never refit or altered by Test 12 evidence',
            'no_branch_baseline': 'Test 11 baseline_seq',
            'shuffled_axis_control': 'Test 11 shuffled_seq generated from the deterministic shuffled family-axis control',
            'raw_branch_candidate': 'Test 11 branch_seq retained for diagnostic comparison',
            'wrong_meaning_control': 'deterministic different ASJP-overlap meaning using the frozen Test 11 final_seq',
            'primary_branch_question': 'on Test 11 meanings where branch_accepted=true, does frozen final_seq beat baseline_seq and shuffled_seq on independent ASJP lexical forms?',
            'feature_distance_used_for_test12_scoring': False,
            'test5_root_used_for_test12_scoring': False,
            'test4_result_used': False,
            'specific_test9_anchor_pair_special_weight': False,
            'central_circle_operator_used': False,
        },
        'prepared': {
            'asjp_form_rows_total': total_rows,
            'asjp_nonloan_rows': nonloan_rows,
            'asjp_overlap_rows': overlap_rows,
            'fully_mapped_form_rows': fully_mapped_rows,
            'rejected_unmapped_form_rows': rejected_unmapped_rows,
            'segment_tokens_total_in_overlap': total_segment_tokens,
            'segment_tokens_exactly_mapped': mapped_segment_tokens,
            'segment_token_mapping_fraction': round(mapped_segment_tokens / total_segment_tokens, 8) if total_segment_tokens else None,
            'languages_with_mapped_evidence': sum(len(x) for x in shards),
            'families_with_mapped_evidence': len(observed_families),
            'meanings_with_mapped_evidence': len(observed_meanings),
            'language_meaning_records': language_meaning_records,
            'language_shard_sizes': [len(x) for x in shards],
            'top_unmapped_segments': unmapped_token_counts.most_common(30),
        },
        'execution': {
            'version': 'exact-v4-test12-independent-asjp-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint ASJP language ownership across 20 shards',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 12 is an out-of-sample lexical validation of frozen Test 11 candidates against ASJP v21 forms that were not used to construct Test 11 lexical candidates. Shared family labels or language identities do not make the lexical forms training evidence. This test can validate or reject predictive phonetic structure under the exact mirrored-Man-Grid representation; it does not establish genealogy, chronology, homeland, or a central-circle transform.',
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps({'test': 12, **manifest['prepared'], 'overlap_concepts': len(concept_by_param)}, ensure_ascii=False), flush=True)


def add_metric(bucket, key, value):
    bucket[key + '_sum'] = bucket.get(key + '_sum', 0.0) + float(value)


def finalize_bucket(b):
    n = int(b.get('n', 0))
    out = {'n': n}
    for key in ('final', 'baseline', 'shuffled', 'branch', 'wrong'):
        out['mean_' + key] = round(b.get(key + '_sum', 0.0) / n, 8) if n else None
    out['final_beats_baseline'] = int(b.get('final_beats_baseline', 0))
    out['final_beats_shuffled'] = int(b.get('final_beats_shuffled', 0))
    out['final_beats_wrong'] = int(b.get('final_beats_wrong', 0))
    out['branch_n'] = int(b.get('branch_n', 0))
    bn = out['branch_n']
    out['branch_mean_final'] = round(b.get('branch_final_sum', 0.0) / bn, 8) if bn else None
    out['branch_mean_baseline'] = round(b.get('branch_baseline_sum', 0.0) / bn, 8) if bn else None
    out['branch_mean_shuffled'] = round(b.get('branch_shuffled_sum', 0.0) / bn, 8) if bn else None
    out['branch_final_beats_baseline'] = int(b.get('branch_final_beats_baseline', 0))
    out['branch_final_beats_shuffled'] = int(b.get('branch_final_beats_shuffled', 0))
    return out


def score_record(seq, cand, wrong_cand, costs):
    return {
        'final': seqdist(cand['final_seq'], seq, costs),
        'baseline': seqdist(cand['baseline_seq'], seq, costs),
        'shuffled': seqdist(cand['shuffled_seq'], seq, costs),
        'branch': seqdist(cand['branch_seq'], seq, costs),
        'wrong': seqdist(wrong_cand['final_seq'], seq, costs),
    }


def update_bucket(b, d, branch_accepted):
    b['n'] = b.get('n', 0) + 1
    for k, v in d.items():
        add_metric(b, k, v)
    b['final_beats_baseline'] = b.get('final_beats_baseline', 0) + int(d['final'] < d['baseline'])
    b['final_beats_shuffled'] = b.get('final_beats_shuffled', 0) + int(d['final'] < d['shuffled'])
    b['final_beats_wrong'] = b.get('final_beats_wrong', 0) + int(d['final'] < d['wrong'])
    if branch_accepted:
        b['branch_n'] = b.get('branch_n', 0) + 1
        b['branch_final_sum'] = b.get('branch_final_sum', 0.0) + d['final']
        b['branch_baseline_sum'] = b.get('branch_baseline_sum', 0.0) + d['baseline']
        b['branch_shuffled_sum'] = b.get('branch_shuffled_sum', 0.0) + d['shuffled']
        b['branch_final_beats_baseline'] = b.get('branch_final_beats_baseline', 0) + int(d['final'] < d['baseline'])
        b['branch_final_beats_shuffled'] = b.get('branch_final_beats_shuffled', 0) + int(d['final'] < d['shuffled'])


def wrong_meaning(meaning, keys):
    if len(keys) < 2:
        return None
    i = keys.index(meaning)
    off = 1 + h64('test12-wrong-meaning', meaning) % (len(keys) - 1)
    return keys[(i + off) % len(keys)]


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')
    model = read_gz(WORK / 'model.json.gz')
    candidates = read_gz(WORK / 'candidates.json.gz')
    langs = read_gz(WORK / f'asjp-language-shard-{shard}.json.gz')
    costs = substitution_costs(model)
    keys = sorted(candidates)
    wrong_map = {m: wrong_meaning(m, keys) for m in keys}

    overall = {}
    family_buckets = defaultdict(dict)
    meaning_buckets = defaultdict(dict)
    language_summaries = []

    for lr in langs:
        lb = {}
        for meaning, seq in lr.get('meanings', {}).items():
            cand = candidates.get(meaning)
            wm = wrong_map.get(meaning)
            if not cand or not wm:
                continue
            d = score_record(tuple(seq), cand, candidates[wm], costs)
            accepted = bool(cand.get('branch_accepted'))
            update_bucket(overall, d, accepted)
            update_bucket(family_buckets[lr['family']], d, accepted)
            update_bucket(meaning_buckets[meaning], d, accepted)
            update_bucket(lb, d, accepted)
        if lb.get('n', 0):
            language_summaries.append({
                'id': lr['id'], 'name': lr['name'], 'family': lr['family'],
                **finalize_bucket(lb),
            })

    summary = {
        'test': 12,
        'shard': shard,
        'languages': len(language_summaries),
        **finalize_bucket(overall),
    }
    write_gz(WORK / f't12-result-{shard}.json.gz', {
        'test': 12,
        'shard': shard,
        'summary': summary,
        'languages': language_summaries,
        'families': {k: finalize_bucket(v) for k, v in sorted(family_buckets.items())},
        'meanings': {k: finalize_bucket(v) for k, v in sorted(meaning_buckets.items())},
        'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps(summary), flush=True)


def combine_finalized(rows):
    b = {}
    for r in rows:
        n = int(r.get('n', 0))
        b['n'] = b.get('n', 0) + n
        for k in ('final', 'baseline', 'shuffled', 'branch', 'wrong'):
            v = r.get('mean_' + k)
            if v is not None:
                b[k + '_sum'] = b.get(k + '_sum', 0.0) + float(v) * n
        for k in ('final_beats_baseline', 'final_beats_shuffled', 'final_beats_wrong'):
            b[k] = b.get(k, 0) + int(r.get(k, 0))
        bn = int(r.get('branch_n', 0))
        b['branch_n'] = b.get('branch_n', 0) + bn
        for k in ('final', 'baseline', 'shuffled'):
            v = r.get('branch_mean_' + k)
            if v is not None:
                b['branch_' + k + '_sum'] = b.get('branch_' + k + '_sum', 0.0) + float(v) * bn
        for k in ('branch_final_beats_baseline', 'branch_final_beats_shuffled'):
            b[k] = b.get(k, 0) + int(r.get(k, 0))
    return finalize_bucket(b)


def mean_of(rows, key):
    vals = [float(r[key]) for r in rows if r.get(key) is not None]
    return statistics.mean(vals) if vals else None


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't12-result-{i}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 12 shard {i}')
        parts.append(read_gz(p))

    languages = [x for p in parts for x in p.get('languages', [])]
    family_rows = defaultdict(list)
    meaning_rows = defaultdict(list)
    for p in parts:
        for k, v in p.get('families', {}).items():
            family_rows[k].append(v)
        for k, v in p.get('meanings', {}).items():
            meaning_rows[k].append(v)
    families = {k: combine_finalized(v) for k, v in sorted(family_rows.items())}
    meanings = {k: combine_finalized(v) for k, v in sorted(meaning_rows.items())}
    overall = combine_finalized([p['summary'] for p in parts])

    lang_final = [x['mean_final'] for x in languages if x.get('mean_final') is not None]
    lang_base = [x['mean_baseline'] for x in languages if x.get('mean_final') is not None]
    lang_shuf = [x['mean_shuffled'] for x in languages if x.get('mean_final') is not None]
    lang_wrong = [x['mean_wrong'] for x in languages if x.get('mean_final') is not None]
    branch_langs = [x for x in languages if int(x.get('branch_n', 0)) > 0]
    bf = [x['branch_mean_final'] for x in branch_langs]
    bb = [x['branch_mean_baseline'] for x in branch_langs]
    bs = [x['branch_mean_shuffled'] for x in branch_langs]

    fam_values = list(families.values())
    meaning_values = list(meanings.values())
    branch_meaning_values = [v for v in meaning_values if int(v.get('branch_n', 0)) > 0]

    summary = {
        'shards_completed': len(parts),
        'independent_languages_scored': len(languages),
        'independent_families_scored': len(families),
        'independent_meanings_scored': len(meanings),
        'observation_weighted': overall,
        'language_equal_mean_final_distance': round(mean_of(languages, 'mean_final'), 8),
        'language_equal_mean_baseline_distance': round(mean_of(languages, 'mean_baseline'), 8),
        'language_equal_mean_shuffled_distance': round(mean_of(languages, 'mean_shuffled'), 8),
        'language_equal_mean_wrong_distance': round(mean_of(languages, 'mean_wrong'), 8),
        'language_effect_dz_final_vs_baseline': round(paired_dz(lang_final, lang_base), 8) if paired_dz(lang_final, lang_base) is not None else None,
        'language_effect_dz_final_vs_shuffled': round(paired_dz(lang_final, lang_shuf), 8) if paired_dz(lang_final, lang_shuf) is not None else None,
        'language_effect_dz_final_vs_wrong': round(paired_dz(lang_final, lang_wrong), 8) if paired_dz(lang_final, lang_wrong) is not None else None,
        'branch_subset_languages': len(branch_langs),
        'branch_subset_language_equal_final_distance': round(statistics.mean(bf), 8) if bf else None,
        'branch_subset_language_equal_baseline_distance': round(statistics.mean(bb), 8) if bb else None,
        'branch_subset_language_equal_shuffled_distance': round(statistics.mean(bs), 8) if bs else None,
        'branch_subset_language_effect_dz_final_vs_baseline': round(paired_dz(bf, bb), 8) if bf and paired_dz(bf, bb) is not None else None,
        'branch_subset_language_effect_dz_final_vs_shuffled': round(paired_dz(bf, bs), 8) if bf and paired_dz(bf, bs) is not None else None,
        'family_equal_mean_final_distance': round(mean_of(fam_values, 'mean_final'), 8),
        'family_equal_mean_baseline_distance': round(mean_of(fam_values, 'mean_baseline'), 8),
        'family_equal_mean_shuffled_distance': round(mean_of(fam_values, 'mean_shuffled'), 8),
        'meaning_equal_mean_final_distance': round(mean_of(meaning_values, 'mean_final'), 8),
        'meaning_equal_mean_baseline_distance': round(mean_of(meaning_values, 'mean_baseline'), 8),
        'meaning_equal_mean_shuffled_distance': round(mean_of(meaning_values, 'mean_shuffled'), 8),
        'meaning_equal_mean_wrong_distance': round(mean_of(meaning_values, 'mean_wrong'), 8),
        'branch_accepted_meanings_with_independent_evidence': len(branch_meaning_values),
        'branch_meaning_equal_final_distance': round(mean_of(branch_meaning_values, 'branch_mean_final'), 8) if branch_meaning_values else None,
        'branch_meaning_equal_baseline_distance': round(mean_of(branch_meaning_values, 'branch_mean_baseline'), 8) if branch_meaning_values else None,
        'branch_meaning_equal_shuffled_distance': round(mean_of(branch_meaning_values, 'branch_mean_shuffled'), 8) if branch_meaning_values else None,
        'shards_final_mean_better_than_baseline': sum(
            p['summary'].get('mean_final') is not None and p['summary']['mean_final'] < p['summary']['mean_baseline'] for p in parts
        ),
        'shards_final_mean_better_than_shuffled': sum(
            p['summary'].get('mean_final') is not None and p['summary']['mean_final'] < p['summary']['mean_shuffled'] for p in parts
        ),
        'shards_branch_final_mean_better_than_baseline': sum(
            p['summary'].get('branch_mean_final') is not None and p['summary']['branch_mean_final'] < p['summary']['branch_mean_baseline'] for p in parts
        ),
        'shards_branch_final_mean_better_than_shuffled': sum(
            p['summary'].get('branch_mean_final') is not None and p['summary']['branch_mean_final'] < p['summary']['branch_mean_shuffled'] for p in parts
        ),
        'feature_distance_used_for_test12_scoring': False,
        'test5_root_used_for_test12_scoring': False,
        'test4_result_used': False,
        'specific_test9_anchor_pair_special_weight': False,
        'central_circle_operator_used': False,
    }

    out = {
        'version': 4,
        'test_id': 12,
        'test': manifest['test'],
        'status': 'complete',
        'shards': N,
        'dependency': manifest['dependency'],
        'independent_source': manifest['independent_source'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'prepared': manifest['prepared'],
        'summary': summary,
        'shard_summaries': [p['summary'] for p in parts],
        'meaning_results': meanings,
        'family_results': families,
        'execution': manifest['execution'],
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
