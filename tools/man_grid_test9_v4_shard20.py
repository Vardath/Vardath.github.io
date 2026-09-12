#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
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
SOURCE_DIR = ROOT / 'data' / 'test9-source'
WORK = ROOT / 'data' / 'man-grid-test9-exact-v4-work'
OUT = ROOT / 'data' / 'man-grid-test-09-exact-v4.json'
TEST6 = ROOT / 'data' / 'man-grid-test-06-exact-v4.json'
TEST7 = ROOT / 'data' / 'man-grid-test-07-exact-v4.json'
TEST8 = ROOT / 'data' / 'man-grid-test-08-exact-v4.json'
N = 20
SOURCE_RUN = 34660500756
SOURCE_BASE_ARTIFACT_ID = 10287516871
SOURCE_MERGED_ARTIFACT_ID = 10288413679
RAW = os.environ.get('WIKTEXTRACT_URL', 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
GAP = T5.GAP
MIN_TEST6_SHARED = 10
MIN_SHARD_MEANINGS = 8
MIN_PROFILE_MAGNITUDE = 0.002
MIN_FAMILIES_FOR_AXIS = 6
TOP_ANCHORS_PER_BRANCH = 12
DIM = 20


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


def validate_sources(test5, model, test6, test7, test8):
    if test5.get('status') != 'complete' or test5.get('test_id') != 5 or int(test5.get('shards', 0)) != 50:
        raise RuntimeError('corrected Test 5 is not complete')
    s5 = test5.get('summary', {})
    c5 = test5.get('calculation', {})
    if s5.get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('Test 5 source is not the corrected mirror-grid reconstruction')
    if not s5.get('mirror_grid_used_for_phoneme_snap') or not s5.get('mirror_grid_used_for_sequence_scoring'):
        raise RuntimeError('Test 5 source does not verify mirror-grid phoneme snap/scoring')
    if c5.get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('Test 5 metadata does not exclude feature distance')
    if int(model.get('grid', {}).get('counts', {}).get('total_cells', 0)) != 1074:
        raise RuntimeError('model is not the exact 1,074-cell mirrored Man Grid')
    if len(model.get('root_ids', [])) != 36:
        raise RuntimeError('model does not contain the corrected 36-root inventory')
    if model.get('calculation', {}).get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('downloaded model is not corrected mirror-grid Test 5 model')

    for tid, obj in ((6, test6), (7, test7), (8, test8)):
        if obj.get('test_id') != tid or obj.get('status') != 'complete' or int(obj.get('shards', 0)) != 20:
            raise RuntimeError(f'corrected Test {tid} dependency is not complete')
    if test6.get('calculation', {}).get('feature_distance_used_for_test6_scoring') is not False:
        raise RuntimeError('Test 6 is not corrected mirror-grid scoring')
    if test7.get('calculation', {}).get('feature_distance_used_for_test7_scoring') is not False:
        raise RuntimeError('Test 7 is not corrected mirror-grid scoring')
    if test8.get('calculation', {}).get('feature_distance_used_for_test8_scoring') is not False:
        raise RuntimeError('Test 8 is not corrected mirror-grid scoring')


def build_byfirst(model):
    byfirst = defaultdict(list)
    for pid, p in model['params'].items():
        nm = unicodedata.normalize('NFC', p['name'])
        if nm and not any(ch.isspace() for ch in nm):
            byfirst[nm[0]].append((nm, pid))
    for k in byfirst:
        byfirst[k].sort(key=lambda x: (-len(x[0]), x[0], x[1]))
    return byfirst


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
            nd[j] = min(dp[j] + GAP, nd[j - 1] + GAP, dp[j - 1] + costs[x][y])
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


def parse_cell(cell):
    try:
        tail = cell.rsplit('-R', 1)[1]
        r, c = tail.split('-C', 1)
        return int(r), int(c)
    except Exception as e:
        raise RuntimeError(f'cannot parse exact Man Grid cell {cell!r}') from e


def layer_shapes(model):
    layers = model.get('grid', {}).get('layers', [])
    shapes = []
    for layer in layers:
        if layer.get('type') == 'circle':
            continue
        if 'rows' in layer and 'columns' in layer:
            shapes.append((int(layer['rows']), int(layer['columns'])))
    if len(shapes) != 10:
        shapes = [(4,4),(7,5),(10,5),(7,4),(5,5),(6,5),(11,5),(17,4),(21,5),(25,5)]
    return shapes


def signed_substitution_vector(root_pid, lang_pid, model, shapes):
    rg = model['params'][root_pid]['grid']
    lg = model['params'][lang_pid]['grid']
    rp = rg['all_left']
    lp = lg['all_right']
    if len(rp) != 10 or len(lp) != 10:
        raise RuntimeError('root parameter does not have all 10 exact mirrored layer coordinates')
    out = []
    for i, (rc, lc) in enumerate(zip(rp, lp)):
        rr, cr = parse_cell(rc)
        rl, cl = parse_cell(lc)
        rows, cols = shapes[i]
        out.extend(((rl - rr) / max(1, rows - 1), (cl - cr) / max(1, cols - 1)))
    return out


def optimal_alignment(root, lang, costs):
    root, lang = tuple(root), tuple(lang)
    n, m = len(root), len(lang)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * GAP
        bt[i][0] = 'D'
    for j in range(1, m + 1):
        dp[0][j] = j * GAP
        bt[0][j] = 'I'
    priority = {'S':0,'D':1,'I':2}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opts = [
                (dp[i-1][j-1] + costs[root[i-1]][lang[j-1]], 'S'),
                (dp[i-1][j] + GAP, 'D'),
                (dp[i][j-1] + GAP, 'I'),
            ]
            val, op = min(opts, key=lambda x: (x[0], priority[x[1]]))
            dp[i][j] = val
            bt[i][j] = op
    pairs = []
    i, j = n, m
    while i or j:
        op = bt[i][j]
        if op == 'S':
            pairs.append((root[i-1], lang[j-1]))
            i -= 1
            j -= 1
        elif op == 'D':
            i -= 1
        elif op == 'I':
            j -= 1
        else:
            break
    pairs.reverse()
    return pairs


def mean_vec(vs):
    if not vs:
        return None
    return [statistics.mean(v[i] for v in vs) for i in range(len(vs[0]))]


def vdot(a, b):
    return sum(x*y for x, y in zip(a, b))


def vnorm(a):
    return math.sqrt(vdot(a, a))


def unit(a):
    n = vnorm(a)
    if not n:
        return None
    return [x/n for x in a]


def family_balanced_axis(language_profiles):
    fam = defaultdict(list)
    for p in language_profiles:
        fam[p['family']].append(p['direction'])
    family_rows = []
    for f, vs in sorted(fam.items()):
        u = unit(mean_vec(vs))
        if u is not None:
            family_rows.append({'family': f, 'direction': u, 'languages': len(vs)})
    if len(family_rows) < MIN_FAMILIES_FOR_AXIS:
        return None

    x = unit([sum(abs(r['direction'][i]) for r in family_rows) + (i+1)*1e-12 for i in range(DIM)])
    if x is None:
        return None
    for _ in range(80):
        y = [0.0] * DIM
        for r in family_rows:
            d = r['direction']
            q = vdot(d, x)
            for i in range(DIM):
                y[i] += q * d[i]
        y = unit(y)
        if y is None:
            return None
        if abs(vdot(x, y)) > 0.999999999:
            x = y
            break
        x = y

    total_energy = sum(vdot(r['direction'], r['direction']) for r in family_rows)
    axis_energy = sum(vdot(r['direction'], x) ** 2 for r in family_rows)
    explained = axis_energy / total_energy if total_energy else 0.0
    projs = [(r['family'], vdot(r['direction'], x), r['languages']) for r in family_rows]
    pos = [p for p in projs if p[1] >= 0]
    neg = [p for p in projs if p[1] < 0]
    if not pos or not neg:
        return None
    separation = statistics.mean(p[1] for p in pos) - statistics.mean(p[1] for p in neg)

    return {
        'axis': x,
        'families': [
            {'family': f, 'projection': round(q, 8), 'languages': n}
            for f, q, n in sorted(projs, key=lambda z: (-abs(z[1]), z[0]))
        ],
        'family_count': len(family_rows),
        'axis_explained_fraction': explained,
        'positive_family_count': len(pos),
        'negative_family_count': len(neg),
        'mean_branch_separation': separation,
    }


def wrong_meaning(meaning_keys, pos, lang_code, meaning):
    if len(meaning_keys) < 2:
        return meaning
    off = 1 + (V.h64('test9-wrong-meaning', lang_code, meaning) % (len(meaning_keys)-1))
    return meaning_keys[(pos[meaning] + off) % len(meaning_keys)]


def prepare():
    model_path = SRC_WORK / 'model.json.gz'
    if not model_path.exists():
        raise RuntimeError('corrected Test 5 model artifact is missing')
    model = read_gz(model_path)
    test5 = read_json(find_test5_json())
    test6 = read_json(TEST6)
    test7 = read_json(TEST7)
    test8 = read_json(TEST8)
    validate_sources(test5, model, test6, test7, test8)

    root_ids = set(model['root_ids'])
    roots = {}
    for e in test5.get('entries', []):
        meaning = str(e.get('meaning') or '').strip()
        seq = tuple(e.get('seq') or [])
        if meaning and seq and all(x in root_ids for x in seq):
            roots[meaning] = list(seq)
    if len(roots) != 12000:
        raise RuntimeError(f'expected 12,000 corrected Test 5 meanings, found {len(roots)}')

    supported = {
        str(x.get('meaning')) for x in test8.get('meanings', [])
        if x.get('same_better_than_wrong')
    }

    lang_meta = {}
    for x in test6.get('languages', []):
        if int(x.get('shared_meanings', 0)) < MIN_TEST6_SHARED:
            continue
        code = str(x.get('code') or '').strip()
        if not code:
            continue
        lang_meta[code] = {
            'name': x.get('name') or code,
            'family': x.get('family') or 'Unclassified',
            'test6_shared_meanings': int(x.get('shared_meanings', 0)),
            'test6_similarity': float(x.get('similarity', 0.0)),
            'test6_control_advantage': float(x.get('control_advantage', 0.0)),
        }
    if not lang_meta:
        raise RuntimeError('Test 6 supplied no candidate languages')

    test7_families = {
        str(x.get('family')): {
            'enrichment_score': float(x.get('enrichment_score', 0.0)),
            'similarity': float(x.get('similarity', 0.0)),
            'heldout_meanings': int(x.get('heldout_meanings', 0)),
        }
        for x in test7.get('families', [])
    }

    WORK.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / 'model.json.gz', model)
    write_gz(WORK / 'roots.json.gz', {
        'entries': roots,
        'test8_supported_meanings': sorted(supported),
        'test6_languages': lang_meta,
        'test7_families': test7_families,
    })

    byfirst = build_byfirst(model)
    iso, names = T5.family_map()
    db = WORK / 'test9-attested.sqlite3'
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('PRAGMA temp_store=MEMORY')
    con.executescript('''
      CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,concept TEXT,seq TEXT);
      CREATE INDEX lex_concept ON lex(concept);
      CREATE INDEX lex_lang ON lex(lang_code);
    ''')
    cur = con.cursor()
    batch = []
    stats = Counter()
    req = urllib.request.Request(RAW, headers={'User-Agent':'Vardath-ManGrid-Test9-Mirror/9.0'})

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
            if lc not in lang_meta or not ln:
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
            fam = iso.get(lc) or names.get(ln.lower()) or lang_meta[lc]['family'] or 'Unclassified'
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

    shards = [[] for _ in range(N)]
    q = '''
      SELECT concept,lang_code,MAX(lang),MAX(family),seq,COUNT(*)
      FROM lex
      GROUP BY concept,lang_code,seq
      ORDER BY concept,lang_code,seq
    '''
    current_meaning = None
    current_lang = None
    meaning_rec = None
    lang_rec = None

    def finish_lang():
        nonlocal lang_rec, meaning_rec
        if lang_rec is not None and meaning_rec is not None:
            meaning_rec['languages'].append(lang_rec)
        lang_rec = None

    def finish_meaning():
        nonlocal meaning_rec
        finish_lang()
        if meaning_rec is not None and meaning_rec['languages']:
            sid = V.h64('test9-meaning', meaning_rec['meaning']) % N
            shards[sid].append(meaning_rec)
        meaning_rec = None

    for concept, code, name, family, seq, count in con.execute(q):
        if concept != current_meaning:
            finish_meaning()
            current_meaning = concept
            current_lang = None
            meaning_rec = {
                'meaning': concept,
                'root': roots[concept],
                'test8_supported': concept in supported,
                'languages': [],
            }
        if code != current_lang:
            finish_lang()
            current_lang = code
            meta = lang_meta.get(code, {})
            lang_rec = {
                'code': code,
                'name': name or meta.get('name') or code,
                'family': family or meta.get('family') or 'Unclassified',
                'test6_shared_meanings': meta.get('test6_shared_meanings', 0),
                'test6_similarity': meta.get('test6_similarity', 0.0),
                'seqs': [],
            }
        lang_rec['seqs'].append([seq.split(), int(count)])
    finish_meaning()

    for i, rows in enumerate(shards):
        rows.sort(key=lambda x: x['meaning'])
        write_gz(WORK / f'meaning-shard-{i:02d}.json.gz', rows)

    stats['candidate_languages_from_test6'] = len(lang_meta)
    stats['test8_supported_meanings'] = len(supported)
    stats['meanings_with_attested_candidate_evidence'] = sum(len(x) for x in shards)
    stats['attested_candidate_codes_observed'] = con.execute('SELECT COUNT(DISTINCT lang_code) FROM lex').fetchone()[0]

    manifest = {
        'version': 4,
        'test_id': 9,
        'test': 'Data-driven sibling-language anchor discovery through the corrected exact mirrored Man Grid',
        'status': 'prepared',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'dependency': {
            'test5': 'corrected 50-shard mirror-grid dictionary and exact model',
            'test6': 'corrected attested-language candidate pool and language-level root similarity',
            'test7': 'corrected held-out family enrichment context',
            'test8': 'corrected reverse-family convergence support by meaning',
            'test4': 'not used; Test 4 is treated as the incomplete precursor to corrected Test 5',
        },
        'scan': dict(stats),
        'meaning_shard_sizes': [len(x) for x in shards],
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': {
            'metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'language_form_selection': 'per-language per-meaning medoid under corrected mirror-grid sequence distance',
            'branch_profile': 'optimal root-to-language sequence alignment; every aligned phoneme substitution contributes signed normalized row/column movement on each of the ten exact mirrored rectangular layers, yielding a 20-dimensional Grid displacement profile',
            'discovery': 'languages are summarized within families; equal-weight family direction profiles define an uncentred principal bipolar axis through the corrected Test 5 root. Branch A/B labels are exchangeable signs, not predefined languages.',
            'candidate_pool': 'all corrected Test 6 attested languages with >=10 shared Test 5 meanings; no language is hard-coded as an anchor',
            'test8_use': 'primary branch profiles use meanings that independently beat the wrong-meaning convergence control in corrected Test 8',
            'test7_use': 'family enrichment is attached only as context after branch discovery and does not determine the axis',
            'wrong_meaning_control': 'recompute each language displacement profile against deterministic different Test 5 meanings in the same shard, preserving observed language forms',
            'feature_distance_used_for_test9_scoring': False,
            'test4_result_used': False,
            'occitan_or_indonesian_hard_coded': False,
            'central_circle_operator_used': False,
        },
        'execution': {
            'version': 'exact-v4-test9-mirror-grid-shard20',
            'shards_per_test': N,
            'partition': 'deterministic disjoint meaning ownership across 20 shards; every shard independently discovers its two-branch axis',
            'merge_requires_all_20': True,
            'workflow_custom_timeout_minutes': None,
        },
        'evidence_boundary': 'Test 9 is an unsupervised structural anchor-discovery test. Two opposite labels are exchangeable and describe the strongest bipolar displacement axis found in the corrected Man Grid. A stable anchor pair can support a sibling-branch model but does not by itself establish genealogy, chronology, geography, or literal descent.',
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


def build_profiles(rows, model, roots_payload):
    costs = substitution_costs(model)
    shapes = layer_shapes(model)
    by_lang_real = defaultdict(list)
    by_lang_wrong = defaultdict(list)
    lang_meta = {}
    meaning_keys = sorted(r['meaning'] for r in rows)
    pos = {m:i for i,m in enumerate(meaning_keys)}
    roots_by_meaning = {r['meaning']: r['root'] for r in rows}
    supported = set(roots_payload['test8_supported_meanings'])

    for r in rows:
        meaning = r['meaning']
        if meaning not in supported:
            continue
        root = tuple(r['root'])
        for lr in r['languages']:
            cnt = Counter({tuple(seq): int(n) for seq, n in lr['seqs']})
            mm = medoid(cnt, costs)
            if not mm:
                continue
            lang_seq = tuple(mm[0])
            pairs = optimal_alignment(root, lang_seq, costs)
            vecs = [signed_substitution_vector(a, b, model, shapes) for a,b in pairs]
            mv = mean_vec(vecs)
            if mv is None:
                continue
            code = lr['code']
            by_lang_real[code].append(mv)

            wm = wrong_meaning(meaning_keys, pos, code, meaning)
            wroot = tuple(roots_by_meaning[wm])
            wpairs = optimal_alignment(wroot, lang_seq, costs)
            wvecs = [signed_substitution_vector(a, b, model, shapes) for a,b in wpairs]
            wmv = mean_vec(wvecs)
            if wmv is not None:
                by_lang_wrong[code].append(wmv)

            lang_meta[code] = {
                'code': code,
                'name': lr['name'],
                'family': lr['family'] or 'Unclassified',
                'test6_shared_meanings': int(lr.get('test6_shared_meanings',0)),
                'test6_similarity': float(lr.get('test6_similarity',0.0)),
            }

    def finalize(store):
        out = []
        for code, vs in store.items():
            if len(vs) < MIN_SHARD_MEANINGS:
                continue
            raw = mean_vec(vs)
            mag = vnorm(raw)
            direction = unit(raw)
            if direction is None or mag < MIN_PROFILE_MAGNITUDE:
                continue
            rec = dict(lang_meta[code])
            rec.update({
                'shard_meanings': len(vs),
                'profile_magnitude': mag,
                'profile': raw,
                'direction': direction,
            })
            out.append(rec)
        return out

    return finalize(by_lang_real), finalize(by_lang_wrong)


def rank_anchors(profiles, axis, branch_sign, roots_payload):
    fam_context = roots_payload.get('test7_families', {})
    rows = []
    for p in profiles:
        projection = vdot(p['direction'], axis)
        signed = branch_sign * projection
        if signed <= 0:
            continue
        overall_cov = int(p['test6_shared_meanings'])
        shard_cov = int(p['shard_meanings'])
        coverage_factor = min(1.0, math.sqrt(max(1, overall_cov) / 1000.0))
        shard_factor = min(1.0, math.sqrt(max(1, shard_cov) / 40.0))
        magnitude_factor = min(1.0, p['profile_magnitude'] / 0.06)
        score = signed * coverage_factor * shard_factor * magnitude_factor
        fc = fam_context.get(p['family'], {})
        rows.append({
            'code': p['code'],
            'name': p['name'],
            'family': p['family'],
            'branch_projection': round(projection, 8),
            'branch_alignment': round(signed, 8),
            'anchor_score': round(score, 8),
            'shard_meanings': shard_cov,
            'test6_shared_meanings': overall_cov,
            'test6_similarity': round(float(p['test6_similarity']), 8),
            'profile_magnitude': round(p['profile_magnitude'], 8),
            'test7_family_enrichment_score': round(float(fc.get('enrichment_score',0.0)),8) if fc else None,
        })
    rows.sort(key=lambda x: (-x['anchor_score'], -x['test6_shared_meanings'], x['code']))
    return rows[:TOP_ANCHORS_PER_BRANCH]


def run(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..19')
    model = read_gz(WORK / 'model.json.gz')
    roots_payload = read_gz(WORK / 'roots.json.gz')
    rows = read_gz(WORK / f'meaning-shard-{shard:02d}.json.gz')

    real_profiles, wrong_profiles = build_profiles(rows, model, roots_payload)
    real_axis = family_balanced_axis(real_profiles)
    wrong_axis = family_balanced_axis(wrong_profiles)
    if real_axis is None:
        raise RuntimeError(f'Test 9 shard {shard} has insufficient real family profile structure')
    if wrong_axis is None:
        raise RuntimeError(f'Test 9 shard {shard} has insufficient control family profile structure')

    axis = real_axis['axis']
    a = rank_anchors(real_profiles, axis, +1, roots_payload)
    b = rank_anchors(real_profiles, axis, -1, roots_payload)

    posthoc = {}
    for code in ('oci', 'id', 'ind'):
        matches = [p for p in real_profiles if p['code'] == code]
        if matches:
            p = matches[0]
            posthoc[code] = {
                'name': p['name'],
                'family': p['family'],
                'projection': round(vdot(p['direction'], axis), 8),
                'shard_meanings': p['shard_meanings'],
            }

    summary = {
        'test': 9,
        'shard': shard,
        'meanings_owned': len(rows),
        'languages_profiled': len(real_profiles),
        'families_profiled': real_axis['family_count'],
        'real_axis_explained_fraction': round(real_axis['axis_explained_fraction'], 8),
        'wrong_meaning_axis_explained_fraction': round(wrong_axis['axis_explained_fraction'], 8),
        'real_stronger_than_wrong': real_axis['axis_explained_fraction'] > wrong_axis['axis_explained_fraction'],
        'real_branch_separation': round(real_axis['mean_branch_separation'], 8),
        'wrong_branch_separation': round(wrong_axis['mean_branch_separation'], 8),
        'branch_a_top': a[0] if a else None,
        'branch_b_top': b[0] if b else None,
    }
    write_gz(WORK / f't09-result-{shard:02d}.json.gz', {
        'test': 9,
        'shard': shard,
        'summary': summary,
        'axis': [round(x, 12) for x in axis],
        'family_axis': real_axis['families'],
        'branch_a_anchors': a,
        'branch_b_anchors': b,
        'posthoc_previous_hypothesis': posthoc,
        'calculation_metric': 'exact_mirror_man_grid_10_layer_signed_displacement',
        'feature_distance_used_for_scoring': False,
    })
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def merge():
    manifest = read_json(WORK / 'prepared-manifest.json')
    parts = []
    for i in range(N):
        p = WORK / f't09-result-{i:02d}.json.gz'
        if not p.exists():
            raise RuntimeError(f'missing Test 9 shard {i}')
        parts.append(read_gz(p))

    ref = parts[0]['axis']
    aligned = []
    a_votes = Counter()
    b_votes = Counter()
    lang_proj_a = defaultdict(list)
    lang_proj_b = defaultdict(list)
    lang_score_a = defaultdict(list)
    lang_score_b = defaultdict(list)
    lang_meta = {}

    for p in parts:
        axis = list(p['axis'])
        flip = vdot(axis, ref) < 0
        if flip:
            axis = [-x for x in axis]
            branch_a = p['branch_b_anchors']
            branch_b = p['branch_a_anchors']
        else:
            branch_a = p['branch_a_anchors']
            branch_b = p['branch_b_anchors']

        for rank, r in enumerate(branch_a):
            a_votes[r['code']] += TOP_ANCHORS_PER_BRANCH - rank
            proj = -r['branch_projection'] if flip else r['branch_projection']
            lang_proj_a[r['code']].append(proj)
            lang_score_a[r['code']].append(r['anchor_score'])
            lang_meta[r['code']] = r
        for rank, r in enumerate(branch_b):
            b_votes[r['code']] += TOP_ANCHORS_PER_BRANCH - rank
            proj = -r['branch_projection'] if flip else r['branch_projection']
            lang_proj_b[r['code']].append(proj)
            lang_score_b[r['code']].append(r['anchor_score'])
            lang_meta[r['code']] = r

        aligned.append({'shard': p['shard'], 'flipped_for_merge': flip, 'axis': axis})

    def aggregate_branch(votes, proj_store, score_store):
        rows = []
        for code, vote in votes.items():
            meta = lang_meta[code]
            ps = proj_store.get(code, [])
            ss = score_store.get(code, [])
            rows.append({
                'code': code,
                'name': meta['name'],
                'family': meta['family'],
                'weighted_shard_votes': vote,
                'shards_in_top_anchors': len(ps),
                'top_anchor_fraction': round(len(ps) / N, 8),
                'mean_signed_projection': round(statistics.mean(ps), 8) if ps else None,
                'mean_anchor_score_when_ranked': round(statistics.mean(ss), 8) if ss else None,
                'test6_shared_meanings': meta['test6_shared_meanings'],
                'test6_similarity': meta['test6_similarity'],
                'test7_family_enrichment_score': meta.get('test7_family_enrichment_score'),
            })
        rows.sort(key=lambda x: (-x['weighted_shard_votes'], -x['top_anchor_fraction'], -abs(x['mean_signed_projection'] or 0), -x['test6_shared_meanings'], x['code']))
        return rows

    branch_a = aggregate_branch(a_votes, lang_proj_a, lang_score_a)
    branch_b = aggregate_branch(b_votes, lang_proj_b, lang_score_b)
    final_axis = unit(mean_vec([x['axis'] for x in aligned])) or ref

    prior = defaultdict(list)
    for p in parts:
        flip = vdot(p['axis'], ref) < 0
        for code, rec in p.get('posthoc_previous_hypothesis', {}).items():
            q = -float(rec['projection']) if flip else float(rec['projection'])
            prior[code].append(q)
    prior_out = {
        code: {
            'shards_observed': len(v),
            'mean_projection_on_discovered_axis': round(statistics.mean(v), 8),
            'branch': 'A' if statistics.mean(v) >= 0 else 'B',
        }
        for code, v in sorted(prior.items())
    }

    real_frac = [p['summary']['real_axis_explained_fraction'] for p in parts]
    wrong_frac = [p['summary']['wrong_meaning_axis_explained_fraction'] for p in parts]
    real_sep = [p['summary']['real_branch_separation'] for p in parts]
    wrong_sep = [p['summary']['wrong_branch_separation'] for p in parts]

    out = {
        'version': 4,
        'test_id': 9,
        'test': 'Data-driven sibling-language anchor discovery through the corrected exact mirrored Man Grid',
        'status': 'complete',
        'shards': N,
        'source_test5_run': SOURCE_RUN,
        'dependency': manifest['dependency'],
        'grid': manifest['grid'],
        'calculation': manifest['calculation'],
        'summary': {
            'shards_completed': N,
            'shards_real_axis_stronger_than_wrong_meaning_control': sum(p['summary']['real_stronger_than_wrong'] for p in parts),
            'mean_real_axis_explained_fraction': round(statistics.mean(real_frac), 8),
            'mean_wrong_meaning_axis_explained_fraction': round(statistics.mean(wrong_frac), 8),
            'mean_real_branch_separation': round(statistics.mean(real_sep), 8),
            'mean_wrong_branch_separation': round(statistics.mean(wrong_sep), 8),
            'branch_a_anchor': branch_a[0] if branch_a else None,
            'branch_b_anchor': branch_b[0] if branch_b else None,
            'branch_labels_exchangeable': True,
            'feature_distance_used_for_test9_scoring': False,
            'test4_result_used': False,
            'occitan_or_indonesian_hard_coded': False,
            'central_circle_operator_used': False,
        },
        'final_axis': [round(x, 12) for x in final_axis],
        'branch_a_ranking': branch_a,
        'branch_b_ranking': branch_b,
        'posthoc_previous_occitan_indonesian_hypothesis': prior_out,
        'shard_summaries': [p['summary'] for p in parts],
        'execution': manifest['execution'],
        'prepared': manifest['scan'],
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
