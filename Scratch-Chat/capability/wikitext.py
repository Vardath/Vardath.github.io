"""Integrity-checked WikiText ZIP import, preserving the publisher's held-out splits.

No pretrained weights or external model APIs are used.  Dataset usage is distinct
from permission to redistribute trained outputs: check CC BY-SA 4.0 obligations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

DATASETS = {
    'wikitext-2-raw-v1': {
        'url': 'https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-raw-v1.zip',
        'sha256': 'ef7edb566e3e2b2d31b29c1fdb0c89a4cc683597484c3dc2517919c615435a11',
        'bytes': 4721645,
    },
    'wikitext-103-raw-v1': {
        'url': 'https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-raw-v1.zip',
        'sha256': '91c00ae287f0d699e18605c84afc9e45c192bc6b7797ff8837e5474655a33794',
        'bytes': 191984949,
    },
}
SPLITS = {'train': 'train', 'valid': 'validation', 'test': 'test'}
ARTICLE_RE = re.compile(r'^\s*=\s+([^=].*?)\s+=\s*$', re.MULTILINE)
LICENSE = 'CC BY-SA 4.0'
SOURCE = 'Salesforce WikiText / Stephen Merity et al. (2016)'


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fetch_archive(destination: Path, dataset: str = 'wikitext-2-raw-v1') -> Path:
    """Download a known release, atomically, with size and SHA-256 verification.

    When the publisher endpoint returns 403, download manually from a trusted
    source and pass its file path to `import` instead.  Do not bypass integrity.
    """
    meta = DATASETS[dataset]
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        verify_archive(destination, dataset)
        return destination
    partial = destination.with_name(destination.name + '.partial')
    try:
        req = urllib.request.Request(meta['url'], headers={'User-Agent': 'VardathScratchChat/0.3'})
        with urllib.request.urlopen(req, timeout=60) as resp, partial.open('wb') as out:
            while True:
                block = resp.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
        verify_archive(partial, dataset)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return destination


def verify_archive(path: Path, dataset: str) -> str:
    meta = DATASETS[dataset]
    if path.stat().st_size != meta['bytes']:
        raise ValueError(f'Wrong {dataset} archive size; expected {meta["bytes"]} bytes')
    got = digest_file(path)
    if got != meta['sha256']:
        raise ValueError(f'WikiText SHA-256 mismatch: got {got}; expected {meta["sha256"]}')
    if not zipfile.is_zipfile(path):
        raise ValueError('Expected a ZIP archive')
    return got


def _paragraph_articles(text: str):
    """Keep entire articles together. Never split a single article across sets."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        if text.strip():
            yield 'untitled', text.strip()
        return
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.start():end].strip()
        if body:
            yield match.group(1).strip(), body


def import_archive(archive: Path, output: Path, *, dataset: str = 'wikitext-2-raw-v1',
                   verify: bool = True, min_chars: int = 80) -> dict:
    if dataset not in DATASETS:
        raise ValueError(f'Unsupported dataset: {dataset}')
    if verify:
        verify_archive(archive, dataset)
    elif not zipfile.is_zipfile(archive):
        raise ValueError('Invalid ZIP archive')
    # Work in a temporary directory: never leave half-written evaluation splits.
    output_parent = output.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory(prefix='.wikitext-', dir=output_parent) as tmp:
        temp = Path(tmp)
        seen: dict[str, str] = {}
        counts = {}
        with zipfile.ZipFile(archive) as zf:
            for original_split, split in SPLITS.items():
                suffix = f'wiki.{original_split}.raw'
                matches = [name for name in zf.namelist() if name.endswith('/' + suffix) or name == suffix]
                if len(matches) != 1:
                    raise ValueError(f'Expected one {suffix} in ZIP, found {len(matches)}')
                with zf.open(matches[0]) as raw:
                    content = io.TextIOWrapper(raw, encoding='utf-8-sig').read()
                written = 0
                bytes_written = 0
                with (temp / (split + '.jsonl')).open('w', encoding='utf-8') as out:
                    for article_index, (title, text) in enumerate(_paragraph_articles(content)):
                        if len(text) < min_chars:
                            continue
                        fingerprint = hashlib.sha256(' '.join(text.split()).encode('utf-8')).hexdigest()
                        previous = seen.get(fingerprint)
                        if previous is not None:
                            if previous != split:
                                raise ValueError(f'Exact article leakage across {previous} and {split}: {title}')
                            continue
                        seen[fingerprint] = split
                        record = {
                            'id': fingerprint[:16], 'sha256': fingerprint,
                            'text': text + '\n', 'kind': 'text', 'group': f'{dataset}:{split}:{article_index}',
                            'source': SOURCE, 'source_url': DATASETS[dataset]['url'],
                            'license': LICENSE, 'split': split,
                            'origin': f'{dataset}:{split}:{title}',
                        }
                        out.write(json.dumps(record, ensure_ascii=False) + '\n')
                        written += 1
                        bytes_written += len(record['text'].encode('utf-8'))
                if written == 0:
                    raise ValueError(f'{split} contains no qualifying articles')
                counts[split] = {'articles': written, 'bytes_utf8': bytes_written}
        report = {
            'schema_version': 1, 'dataset': dataset, 'archive_sha256': digest_file(archive),
            'verified_against_publisher_checksum': verify, 'source': SOURCE,
            'license': LICENSE, 'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'dataset_card': 'https://huggingface.co/datasets/Salesforce/wikitext',
            'counts': counts, 'policy': 'Preserve publisher splits, article-level grouping, exact cross-split leakage rejection',
            'limitations': ['Wikipedia articles are not instruction-tuning data',
                            'WikiText-2 is too small for a general-purpose assistant',
                            'Near-duplicate detection is not yet implemented'],
        }
        (temp / 'provenance_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        output.mkdir(parents=True, exist_ok=True)
        for filename in ('train.jsonl', 'validation.jsonl', 'test.jsonl', 'provenance_report.json'):
            (temp / filename).replace(output / filename)
    return report



def _stream_articles(rows):
    """Assemble whole WikiText articles from the publisher's streaming rows."""
    title, parts, index = None, [], 0
    for row in rows:
        line = row.get('text', '')
        if not isinstance(line, str):
            raise ValueError('WikiText row must contain text')
        header = ARTICLE_RE.fullmatch(line.strip())
        if header and parts:
            yield title or f'untitled-{index}', '\n'.join(parts).strip()
            index += 1
            parts = []
        if header:
            title = header.group(1).strip()
        if line.strip():
            parts.append(line)
    if parts:
        yield title or f'untitled-{index}', '\n'.join(parts).strip()


def import_huggingface(output: Path, *, dataset: str = 'wikitext-2-raw-v1',
                       loader=None, min_chars: int = 80) -> dict:
    """Alternate source using Hugging Face datasets, preserving official splits.

    The datasets package is optional; `pip install -r requirements-datasets.txt`.
    By default data are streamed and never downloaded into this Git repository.
    """
    if dataset not in DATASETS:
        raise ValueError('Unsupported WikiText config')
    if loader is None:
        try:
            from datasets import load_dataset
        except ImportError as e:
            raise RuntimeError('Install optional dependency: pip install -r requirements-datasets.txt') from e
        loader = load_dataset
    split_map = {'train': 'train', 'validation': 'validation', 'test': 'test'}
    import tempfile
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hf-wikitext-', dir=output.parent) as temp_dir:
        temp = Path(temp_dir)
        seen = {}
        counts = {}
        for split, api_split in split_map.items():
            rows = loader('Salesforce/wikitext', dataset, split=api_split, streaming=True)
            written = 0
            size = 0
            with (temp / f'{split}.jsonl').open('w', encoding='utf-8') as out:
                for idx, (title, article) in enumerate(_stream_articles(rows)):
                    if len(article) < min_chars:
                        continue
                    digest = hashlib.sha256(' '.join(article.split()).encode('utf-8')).hexdigest()
                    old_split = seen.get(digest)
                    if old_split:
                        if old_split != split:
                            raise ValueError(f'Exact article leakage across {old_split} and {split}: {title}')
                        continue
                    seen[digest] = split
                    record = {
                        'id': digest[:16], 'sha256': digest, 'text': article+'\n',
                        'kind': 'text', 'group': f'{dataset}:{split}:{idx}',
                        'source': SOURCE, 'source_url': 'https://huggingface.co/datasets/Salesforce/wikitext',
                        'license': LICENSE, 'split': split,
                        'origin': f'{dataset}:{split}:{title}',
                    }
                    out.write(json.dumps(record, ensure_ascii=False)+'\n')
                    written += 1
                    size += len(record['text'].encode('utf-8'))
            if not written:
                raise ValueError(f'{split} contains no qualifying articles')
            counts[split] = {'articles': written, 'bytes_utf8': size}
        report = {
            'schema_version': 1, 'dataset': dataset,
            'publisher': 'Salesforce/wikitext',
            'acquisition': 'Hugging Face official datasets API, streaming',
            'source': SOURCE, 'license': LICENSE,
            'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'counts': counts, 'policy': 'Keep publisher splits, article grouping, fail on exact cross-split leakage',
            'limitations': ['Streaming dataset revision not yet pinned by content hash',
                            'WikiText is pretraining text, not instruction-tuning data',
                            'Near-duplicate detection not implemented'],
        }
        (temp / 'provenance_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        output.mkdir(parents=True, exist_ok=True)
        for name in ('train.jsonl', 'validation.jsonl', 'test.jsonl', 'provenance_report.json'):
            (temp / name).replace(output / name)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description='Import verified publisher WikiText data')
    p.add_argument('--dataset', choices=DATASETS, default='wikitext-2-raw-v1')
    p.add_argument('--archive', type=Path, default=Path('data/downloads/wikitext-2-raw-v1.zip'))
    p.add_argument('--out', type=Path, default=Path('data/wikitext2/prepared'))
    p.add_argument('--source', choices=('zip', 'hf'), default='hf', help='hf works if historic ZIP endpoint is blocked')
    p.add_argument('--download', action='store_true', help='Download/check archive before import (ZIP only)')
    args = p.parse_args(argv)
    if args.source == 'hf':
        report = import_huggingface(args.out, dataset=args.dataset)
    else:
        if args.download:
            fetch_archive(args.archive, args.dataset)
        report = import_archive(args.archive, args.out, dataset=args.dataset)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
