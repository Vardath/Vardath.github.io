#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, gzip, io, json, os, re, sqlite3, statistics, unicodedata, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import man_grid_exact_v4 as V
import man_grid_exact_data as D

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
T1 = ROOT / 'data' / 'man-grid-original-phonetics-exact-v3.json'
N = 50
SOURCE_RUN = 34609281179
RAW = os.environ.get('WIKTEXTRACT_URL', 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP = 'https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
MAX_CONCEPTS = int(os.environ.get('MAX_CONCEPTS', '12000'))
MIN_LANGUAGES = int(os.environ.get('MIN_LANGUAGES', '5'))
MIN_FAMILIES = int(os.environ.get('MIN_FAMILIES', '3'))
GAP = 0.70
SKIP = set("/[](){}<>ˈˌːˑ.·‿#_=+~ |\t\r\n")
CELL_RE = re.compile(r'-R(\d+)-C(\d+)$')


def read_gz(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def write_gz(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def layer_specs(spec):
    return [*spec['upper'], *spec['lower']]


def cell_rc(cell):
    m = CELL_RE.search(cell)
    if not m:
        raise RuntimeError(f'cannot parse Man Grid cell: {cell}')
    return tuple(map(int, m.groups()))


def one_way_mirror_grid_distance(ga, gb, spec, from_side='L', to_side='R'):
    pa = ga['all_left'] if from_side == 'L' else ga['all_right']
    pb = gb['all_right'] if to_side == 'R' else gb['all_left']
    layers = layer_specs(spec)
    if len(pa) != 10 or len(pb) != 10 or len(layers) != 10:
        raise RuntimeError('expected ten exact mirrored Man Grid layers')
    vals = []
    for ca, cb, layer in zip(pa, pb, layers):
        ra, xa = cell_rc(ca)
        rb, xb = cell_rc(cb)
        rd = abs(ra - rb) / max(1, int(layer['rows']) - 1)
        cd = abs(xa - xb) / max(1, int(layer['columns']) - 1)
        vals.append((rd + cd) / 2.0)
    return statistics.mean(vals)


def mirror_grid_distance_from_grids(ga, gb, spec):
    lr = one_way_mirror_grid_distance(ga, gb, spec, 'L', 'R')
    rl = one_way_mirror_grid_distance(ga, gb, spec, 'R', 'L')
    return (lr + rl) / 2.0


def mirror_grid_distance(a, b, model):
    return mirror_grid_distance_from_grids(
        model['params'][a]['grid'],
        model['params'][b]['grid'],
        model['grid'],
    )


def mirror_seqdist(a, b, model):
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
            sub = mirror_grid_distance(x, y, model)
            nd[j] = min(dp[j] + GAP, nd[j - 1] + GAP, dp[j - 1] + sub)
        dp = nd
    return min(1.0, dp[m] / max(len(a), len(b)))


def build_mirror_model():
    spec, params, langs, projection, coverage = D.load_phoible()
    t1 = read_json(T1)
    roots = t1['original_phoneme_inventory']
    root_ids = [r['parameter_id'] for r in roots if r['parameter_id'] in params]
    if len(root_ids) != len(roots):
        missing = [r['parameter_id'] for r in roots if r['parameter_id'] not in params]
        raise RuntimeError(f'Test 1 root inventory does not fully resolve against pinned PHOIBLE: {missing[:8]}')

    nearest = {}
    for pid, p in params.items():
        nearest[pid] = min(
            root_ids,
            key=lambda q: (
                mirror_grid_distance_from_grids(p['grid'], params[q]['grid'], spec),
                q,
            ),
        )

    byfirst = defaultdict(list)
    for pid, p in params.items():
        nm = unicodedata.normalize('NFC', p['name'])
        if nm and not any(ch.isspace() for ch in nm):
            byfirst[nm[0]].append((nm, pid))
    for k in byfirst:
        byfirst[k].sort(key=lambda x: (-len(x[0]), x[0], x[1]))

    model = {
        'version': 4,
        'test': 5,
        'metric_version': 'exact-mirror-man-grid-50',
        'grid': spec,
        'params': {
            pid: {
                'name': p['name'],
                'features': p['features'],
                'grid': p['grid'],
            }
            for pid, p in params.items()
        },
        'root_ids': root_ids,
        'nearest_root': nearest,
        'phoible_commit': D.PH,
        'coverage': coverage,
        'calculation': {
            'phoneme_snap_metric': 'mean normalized row/column distance across all 10 exact mirrored Man Grid layers',
            'sequence_substitution_metric': 'same exact 10-layer mirrored-grid metric',
            'mirror_directions': ['LEFT->RIGHT', 'RIGHT->LEFT'],
            'aggregation': 'equal-weight mean across 10 layers and both mirror directions',
            'insert_delete_gap': GAP,
            'transformative_circle_operator': None,
            'circle_boundary': 'No circle transformation is assumed because no operator has been learned from evidence.',
            'feature_distance_used_for_test5_reconstruction': False,
        },
    }
    return model, byfirst


def tokenize_ipa(raw, model, byfirst):
    s = unicodedata.normalize('NFC', str(raw or '').strip())
    nearest = model['nearest_root']
    out, i, unknown = [], 0, 0
    while i < len(s):
        ch = s[i]
        if ch in SKIP or ch.isspace():
            i += 1
            continue
        hit = None
        for nm, pid in byfirst.get(ch, []):
            if s.startswith(nm, i):
                hit = (nm, pid)
                break
        if hit:
            rid = nearest[hit[1]]
            if not out or out[-1] != rid:
                out.append(rid)
            i += len(hit[0])
            continue
        if unicodedata.combining(ch):
            i += 1
            continue
        unknown += 1
        i += 1
    return tuple(out), unknown


def family_map():
    p = WORK / 'asjp-languages.csv'
    if not p.exists():
        urllib.request.urlretrieve(ASJP, p)
    iso, name = {}, {}
    with p.open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            fam = (
                r.get('Glottolog_Family')
                or r.get('Family')
                or r.get('family')
                or r.get('Classification')
                or 'Unclassified'
            ).strip() or 'Unclassified'
            code = (r.get('ISO639P3code') or r.get('ISO639P3') or '').strip()
            nm = (r.get('Name') or '').strip().lower()
            if code:
                iso[code] = fam
            if nm:
                name[nm] = fam
    return iso, name


def init_db():
    db = WORK / 'test5-mirror-lexicon.sqlite3'
    if db.exists():
        db.unlink()
    c = sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=OFF')
    c.execute('PRAGMA temp_store=MEMORY')
    c.executescript(
        '''
        CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,word TEXT,concept TEXT,seq TEXT);
        CREATE INDEX lex_concept ON lex(concept);
        CREATE INDEX lex_family ON lex(family);
        '''
    )
    return c


def prepare50():
    model, byfirst = build_mirror_model()
    write_gz(WORK / 'model.json.gz', model)
    iso, names = family_map()
    con = init_db()
    cur = con.cursor()
    batch = []
    stats = Counter()
    req = urllib.request.Request(RAW, headers={'User-Agent': 'Vardath-ManGrid-Test5-Mirror/5.0'})

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
            word = str(o.get('word') or '').strip()
            if not lc or not word:
                continue
            fam = iso.get(lc) or names.get(ln.lower()) or 'Unclassified'

            seqs = []
            for raw in V.get_ipa(o)[:3]:
                q, unknown = tokenize_ipa(raw, model, byfirst)
                stats['ipa_unknown_symbols'] += unknown
                if len(q) >= 2 and q not in seqs:
                    seqs.append(q)

            concepts = []
            for g in V.get_glosses(o)[:8]:
                c = V.norm_text(g)
                if c and c not in concepts:
                    concepts.append(c)
                if len(concepts) >= 4:
                    break

            if seqs and concepts:
                stats['entries_with_mirror_grid_mappable_ipa'] += 1
                for concept in concepts:
                    for q in seqs[:2]:
                        batch.append((lc, ln, fam, word, concept, ' '.join(q)))

            if len(batch) >= 15000:
                cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)', batch)
                batch.clear()

            if stats['dictionary_entries'] % 500000 == 0:
                con.commit()
                print(
                    json.dumps(
                        {
                            'entries': stats['dictionary_entries'],
                            'mirror_mappable': stats['entries_with_mirror_grid_mappable_ipa'],
                        }
                    ),
                    flush=True,
                )

    if batch:
        cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)', batch)
    con.commit()

    stats['languages'] = con.execute('SELECT COUNT(DISTINCT lang_code) FROM lex').fetchone()[0]
    stats['families'] = con.execute(
        "SELECT COUNT(DISTINCT family) FROM lex WHERE family!='Unclassified'"
    ).fetchone()[0]

    concepts = list(
        con.execute(
            '''
            SELECT concept,COUNT(DISTINCT lang_code),COUNT(DISTINCT family)
            FROM lex WHERE family!='Unclassified'
            GROUP BY concept
            HAVING COUNT(DISTINCT lang_code)>=? AND COUNT(DISTINCT family)>=?
            ORDER BY COUNT(DISTINCT family) DESC,COUNT(DISTINCT lang_code) DESC,concept
            LIMIT ?''',
            (MIN_LANGUAGES, MIN_FAMILIES, MAX_CONCEPTS),
        )
    )

    shards = [[] for _ in range(N)]
    seen = set()
    for rank, (concept, nlang, nfam) in enumerate(concepts):
        fc = defaultdict(Counter)
        lcmap = defaultdict(Counter)
        for fam, code, lang, seq, n in con.execute(
            "SELECT family,lang_code,lang,seq,COUNT(*) FROM lex "
            "WHERE concept=? AND family!='Unclassified' "
            "GROUP BY family,lang_code,lang,seq",
            (concept,),
        ):
            q = tuple(seq.split())
            fc[fam][q] += int(n)
            lcmap[(code, lang, fam)][q] += int(n)

        item = {
            'rank': rank,
            'meaning': concept,
            'languages': int(nlang),
            'families_reported': int(nfam),
            'family_sequences': {
                fam: [[list(q), n] for q, n in cnt.items()] for fam, cnt in fc.items()
            },
            'language_sequences': [
                {
                    'code': k[0],
                    'name': k[1],
                    'family': k[2],
                    'sequences': [[list(q), n] for q, n in cnt.items()],
                }
                for k, cnt in lcmap.items()
            ],
        }

        if concept in seen:
            raise SystemExit(f'duplicate meaning in source corpus: {concept}')
        seen.add(concept)
        shards[V.h64('mirror-test5-meaning', concept) % N].append(item)

    for p in WORK.glob('lexical-shard-*.json.gz'):
        p.unlink()
    for i, rows in enumerate(shards):
        write_gz(WORK / f'lexical-shard-{i:02d}.json.gz', rows)

    manifest = {
        'version': 4,
        'status': 'prepared',
        'test': 5,
        'shards': N,
        'grid_cells': model['grid']['counts']['total_cells'],
        'all_rectangles_mirrored': True,
        'test1_phonemes': len(model['root_ids']),
        'source': {'wiktextract': RAW, 'phoible_commit': model['phoible_commit']},
        'scan': dict(stats),
        'eligible_meaning_groups': len(concepts),
        'lexical_shard_sizes': [len(x) for x in shards],
        'test5_shard50': {
            'source_run_id': SOURCE_RUN,
            'rerun_shards': N,
            'same_source_corpus_as_test4': True,
            'same_dictionary_source_family_as_test4': True,
            'source_meanings': len(concepts),
            'unique_meanings': len(seen),
            'test4_prior_used_in_scoring': False,
            'reason_test4_prior_excluded': 'Test 4 was feature-distance scored; Test 5 is rebuilt cleanly through exact mirrored-grid geometry.',
        },
        'calculation': model['calculation'],
        'execution': {
            'version': 'exact-v4-test5-mirror-grid-shard50',
            'tests': '5',
            'shards_per_test': N,
            'partition': 'deterministic disjoint meaning ownership across 50 shards, never repeated full tests',
            'merge_requires_all_50': True,
            'workflow_custom_timeout_minutes': None,
            'invalid_old_mapping_reused': False,
            'feature_distance_used_for_test5_reconstruction': False,
            'mirror_grid_metric_used_for_phoneme_snap': True,
            'mirror_grid_metric_used_for_sequence_scoring': True,
        },
    }
    write_json(WORK / 'prepared-manifest.json', manifest)
    print(
        json.dumps(
            {
                'status': 'prepared',
                'source_meanings': len(concepts),
                'shards': N,
                'sizes': [len(x) for x in shards],
                'metric': model['calculation']['sequence_substitution_metric'],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


def install_mirror_metric():
    V.seqdist = mirror_seqdist


def run50(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..49')
    install_mirror_metric()
    model = V.load_model()
    items = read_gz(WORK / f'lexical-shard-{shard:02d}.json.gz')
    entries = []
    for item in items:
        e = V.entry_from_item(item, model, prior=None)
        if e:
            e['calculation_metric'] = 'exact_mirror_man_grid_10_layer_bilateral'
            e['test4_prior_used'] = False
            entries.append(e)
    control = V.wrong_meaning_control(entries, model)
    write_gz(
        V.result_path(5, shard),
        {
            'test': 5,
            'shard': shard,
            'input': len(items),
            'entries': entries,
            'control': control,
            'calculation_metric': 'exact_mirror_man_grid_10_layer_bilateral',
            'feature_distance_used_for_reconstruction': False,
        },
    )


def merge50():
    parts = [read_gz(V.result_path(5, i)) for i in range(N)]
    entries = []
    for p in parts:
        entries.extend(p.get('entries', []))
    entries.sort(key=lambda e: (-e.get('confidence', 0), -e.get('families', 0), e['meaning']))
    controls = [p.get('control') for p in parts if p.get('control')]
    manifest = read_json(WORK / 'prepared-manifest.json')

    out = {
        'version': 4,
        'test_id': 5,
        'test': 'Full original-language dictionary reconstruction through the exact mirrored Man Grid',
        'status': 'complete',
        'shards': N,
        'rerun': '50-shard-mirror-grid',
        'source_test1': 'data/man-grid-original-phonetics-exact-v3.json',
        'test4_dependency_note': 'Test 4 established the lexical stage, but its feature-distance candidate forms are not used as priors in this clean mirror-grid Test 5 rerun.',
        'grid': {
            'cells': 1074,
            'all_rectangles_mirrored': True,
            'layers_per_side': 10,
            'transformative_circle_operator': None,
        },
        'calculation': manifest['calculation'],
        'summary': {
            'entries': len(entries),
            'shard_outputs': [len(p.get('entries', [])) for p in parts],
            'shards_real_better_than_control': sum(bool(c.get('real_better')) for c in controls),
            'feature_distance_used_for_test5_reconstruction': False,
            'mirror_grid_used_for_phoneme_snap': True,
            'mirror_grid_used_for_sequence_scoring': True,
        },
        'entries': entries,
        'execution': manifest['execution'],
        'evidence_boundary': 'Experimental dictionary reconstruction under the exact mirrored Man Grid hypothesis; not proof of a literal single prehistoric world language.',
    }
    out_path = ROOT / 'data' / 'man-grid-test-05-exact-v4.json'
    write_json(out_path, out)
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
        prepare50()
    elif a.cmd == 'run':
        run50(a.shard)
    else:
        merge50()


if __name__ == '__main__':
    main()
