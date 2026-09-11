#!/usr/bin/env python3
from __future__ import annotations

import argparse, gzip, json
from pathlib import Path

import man_grid_exact_v4 as V

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
N = 50
SOURCE_RUN = 34609281179


def read_gz(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def write_gz(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def prepare50():
    source = []
    for i in range(20):
        p = WORK / f'lexical-shard-{i:02d}.json.gz'
        if not p.exists():
            raise SystemExit(f'missing source base shard: {p}')
        source.extend(read_gz(p))

    # Repartition the exact same Test-4 corpus into 50 deterministic,
    # disjoint meaning-owned shards. This is not 50 repetitions.
    shards = [[] for _ in range(N)]
    seen = set()
    for item in source:
        meaning = item['meaning']
        if meaning in seen:
            raise SystemExit(f'duplicate meaning in source corpus: {meaning}')
        seen.add(meaning)
        shards[V.h64('meaning', meaning) % N].append(item)

    for p in WORK.glob('lexical-shard-*.json.gz'):
        p.unlink()
    for i, rows in enumerate(shards):
        write_gz(WORK / f'lexical-shard-{i:02d}.json.gz', rows)

    manifest_path = WORK / 'prepared-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['shards'] = N
    manifest['lexical_shard_sizes'] = [len(x) for x in shards]
    manifest['test5_shard50'] = {
        'source_run_id': SOURCE_RUN,
        'source_shards': 20,
        'rerun_shards': N,
        'same_source_corpus_as_test4': True,
        'source_meanings': len(source),
        'unique_meanings': len(seen),
    }
    execution = dict(manifest.get('execution') or {})
    execution.update({
        'version': 'exact-v4-test5-shard50',
        'tests': '5',
        'shards_per_test': N,
        'partition': 'deterministic disjoint meaning ownership across 50 shards, never repeated full tests',
        'merge_requires_all_50': True,
        'workflow_custom_timeout_minutes': None,
        'invalid_old_mapping_reused': False,
    })
    execution.pop('merge_requires_all_20', None)
    manifest['execution'] = execution
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    if len(shards) != N or sum(map(len, shards)) != len(source):
        raise SystemExit('50-shard repartition validation failed')
    print(json.dumps({
        'status': 'prepared',
        'source_run_id': SOURCE_RUN,
        'source_meanings': len(source),
        'shards': N,
        'sizes': [len(x) for x in shards],
    }, ensure_ascii=False, indent=2))


def run50(shard):
    if not 0 <= shard < N:
        raise SystemExit('shard must be 0..49')
    V.N = N
    V.test5(shard)


def merge50():
    parts = [read_gz(V.result_path(5, i)) for i in range(N)]
    entries = []
    for p in parts:
        entries.extend(p.get('entries', []))
    entries.sort(key=lambda e: (-e.get('confidence', 0), -e.get('families', 0), e['meaning']))
    controls = [p.get('control') for p in parts if p.get('control')]
    manifest = json.loads((WORK / 'prepared-manifest.json').read_text(encoding='utf-8'))
    out = {
        'version': 4,
        'test_id': 5,
        'status': 'complete',
        'shards': N,
        'rerun': '50-shard',
        'source_test4': 'data/man-grid-test-04-exact-v4.json',
        'source_base_run_id': SOURCE_RUN,
        'grid': {'cells': 1074, 'all_rectangles_mirrored': True},
        'summary': {
            'entries': len(entries),
            'shard_outputs': [len(p.get('entries', [])) for p in parts],
            'shards_real_better_than_control': sum(bool(c.get('real_better')) for c in controls),
        },
        'entries': entries,
        'execution': manifest['execution'],
    }
    out_path = ROOT / 'data' / 'man-grid-test-05-exact-v4.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out['summary'], ensure_ascii=False, indent=2))


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
