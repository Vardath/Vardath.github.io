"""Provenance-aware, deterministic, leakage-resistant corpus preparation.

Inputs are explicitly listed in a manifest; never silently scrape, collect personal
files, or train on unlicensed documents. Only source formats TXT/MD/JSONL are read.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {'.txt', '.md', '.jsonl'}
VALID_SPLITS = {'train', 'validation', 'test'}


def canonical(text: str) -> str:
    # Normalize representation without destroying line structure needed for code.
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '')


def fingerprint(text: str) -> str:
    return hashlib.sha256(' '.join(text.split()).encode('utf-8')).hexdigest()


def stable_split(group: str, seed: int, validation: float, test: float) -> str:
    h = hashlib.sha256(f'{seed}/{group}'.encode('utf-8')).digest()
    value = int.from_bytes(h[:8], 'big') / float(2**64)
    if value < test:
        return 'test'
    if value < test + validation:
        return 'validation'
    return 'train'


def _flatten_messages(messages: list[dict[str, Any]]) -> str:
    lines = []
    for msg in messages:
        role = msg.get('role')
        if role not in {'user', 'assistant', 'system'}:
            raise ValueError(f'Unsupported message role: {role!r}')
        content = msg.get('content')
        if not isinstance(content, str) or not content.strip():
            raise ValueError('Each message must have nonempty string content')
        # Role markers are kept visible in corpus for later SFT formatting.
        lines.append(f'<|{role}|>\n{canonical(content)}')
    return '\n'.join(lines) + '\n<|end|>'


def _load_entry(entry: dict, root: Path) -> list[dict]:
    rel = entry.get('path')
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError('Every manifest entry needs a path')
    path = (root / rel).resolve()
    if not path.is_file():
        raise ValueError(f'Source does not exist: {path}')
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f'Unsupported source type {path.suffix}: {path}')
    source_name = entry.get('source')
    license_name = entry.get('license')
    if not source_name or not license_name:
        raise ValueError(f'Missing source attribution or license for {rel}')
    if entry.get('permission_to_train') is not True:
        raise ValueError(f'Explicit permission_to_train=true required for {rel}')
    source_ref = str(entry.get('source_url', 'local file (user provided)'))
    if path.suffix.lower() == '.jsonl':
        records = []
        for line_no, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if isinstance(obj.get('messages'), list):
                messages = obj['messages']
                text = _flatten_messages(messages)
                kind = 'chat'
            elif isinstance(obj.get('text'), str):
                text = canonical(obj['text'])
                messages = None
                kind = 'text'
            else:
                raise ValueError(f'{rel}:{line_no} needs text or messages')
            record = {'text': text, 'kind': kind, 'source': source_name,
                      'source_url': source_ref, 'license': license_name,
                      'group': str(obj.get('group') or f'{rel}:{line_no}'),
                      'origin': f'{rel}:{line_no}'}
            if messages is not None:
                record['messages'] = messages
            records.append(record)
        return records
    text = canonical(path.read_text(encoding='utf-8-sig'))
    return [{'text': text, 'kind': 'text', 'source': source_name,
             'source_url': source_ref, 'license': license_name,
             'group': str(entry.get('group') or rel), 'origin': rel}]


def prepare(manifest: Path, output: Path, *, seed: int = 2026,
            validation: float = 0.08, test: float = 0.08,
            min_chars: int = 10) -> dict:
    """Create train/validation/test JSONL and auditable provenance report.

    Split before any later document chunking; all examples with a group remain in
    the same split. Exact duplicates are removed before splitting.
    """
    if not (0 <= test < 1 and 0 <= validation < 1 and test + validation < 1):
        raise ValueError('Invalid validation/test fractions')
    config = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(config.get('sources'), list) or not config['sources']:
        raise ValueError('Manifest needs nonempty sources array')
    roots = manifest.parent
    output.mkdir(parents=True, exist_ok=True)
    records, seen = [], set()
    counts = Counter()
    group_split = {}
    source_register = []
    for entry in config['sources']:
        source_register.append({k:entry.get(k) for k in ('path','source','source_url','license','permission_to_train')})
        for record in _load_entry(entry, roots):
            counts['received'] += 1
            if len(record['text'].strip()) < min_chars:
                counts['too_short'] += 1
                continue
            fp = fingerprint(record['text'])
            if fp in seen:
                counts['exact_duplicates'] += 1
                continue
            seen.add(fp)
            record['sha256'] = fp
            record['id'] = fp[:16]
            group = record['group']
            if group not in group_split:
                group_split[group] = stable_split(group, seed, validation, test)
            record['split'] = group_split[group]
            records.append(record)
    if not records:
        raise ValueError('No usable records (check minimum length and input files)')
    # Never silently fall back to mixing a validation set into training. Empty
    # splits should be fixed by supplying more independent groups.
    for split in ('train', 'validation', 'test'):
        selected = sorted((r for r in records if r['split'] == split), key=lambda r: r['id'])
        with (output / f'{split}.jsonl').open('w', encoding='utf-8') as f:
            for record in selected:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        counts[split] = len(selected)
        counts[f'{split}_chars'] = sum(len(r['text']) for r in selected)
    counts['unique'] = len(records)
    report = {'schema_version': 1, 'seed': seed,
              'manifest': manifest.name, 'records': dict(counts),
              'sources': source_register,
              'warnings': [f'{x} split is empty; add more independent documents or conversations'
                           for x in ('train', 'validation', 'test') if not counts[x]],
              'rules': ['only manifest-listed sources', 'explicit permission and license',
                        'exact content deduplication', 'stable split by group before chunking',
                        'no automatic online collection']}
    (output / 'provenance_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
