"""Download and import pinned WikiText-2 Parquet data to Vardath Scratch Chat's text corpus.

Source: https://huggingface.co/datasets/Salesforce/wikitext/tree/main/wikitext-2-raw-v1
SHA-256 fingerprints are copied from the publisher's individual file pages.
Train, validation and test splits remain separated; no sample mixing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

from capability.wikitext import _stream_articles

BASE = 'https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-2-raw-v1/'
CHECKSUMS = {
    'train': 'e83889baabc497075506f91975be5fac0d45c5290b6b20582c8cd1e853d0c9f7',
    'validation': '204929b7ff9d6184953f867dedb860e40aa69c078fc1e54b3baaa8fb28511c4c',
    'test': '5f1bea067869d04849c0f975a2b29c4ff47d867f484f5010ea5e861eab246d91',
}
LICENSE_INFO = 'Publisher lists CC BY-SA 3.0 and GFDL. Confirm obligations before redistribution.'


def filename(split: str) -> str:
    if split not in CHECKSUMS: raise ValueError('Unexpected data split')
    return split + '-00000-of-00001.parquet'


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1048576), b''):
            digest.update(part)
    return digest.hexdigest()


def fetch(cache: Path):
    cache.mkdir(parents=True, exist_ok=True)
    for split, checksum in CHECKSUMS.items():
        dst = cache / filename(split)
        if dst.exists():
            if sha256_file(dst) != checksum: raise ValueError(f'Existing {split} file checksum mismatch')
            continue
        tmp = cache / (filename(split) + '.partial')
        url = BASE + filename(split)
        req = urllib.request.Request(url, headers={'User-Agent': 'Vardath-ScratchChat/0.7'})
        try:
            with urllib.request.urlopen(req, timeout=120) as response, tmp.open('wb') as f:
                while block := response.read(1048576):
                    f.write(block)
            if sha256_file(tmp) != checksum:
                raise ValueError(f'Publisher checksum mismatch: {split}')
            tmp.replace(dst)
        finally:
            tmp.unlink(missing_ok=True)


def convert(cache: Path, output: Path, *, row_reader=None, verify=True, min_chars=80):
    if row_reader is None:
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise RuntimeError('pip install pyarrow to read Parquet dataset') from exc
        def row_reader(path):
            for batch in pq.ParquetFile(path).iter_batches(batch_size=2048, columns=['text']):
                for text in batch.column(0).to_pylist():
                    yield {'text': text}
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = {}
    seen = {}
    with tempfile.TemporaryDirectory(prefix='.scratchchat-wiki-', dir=output.parent) as td:
        tmp = Path(td)
        for split in ('train', 'validation', 'test'):
            path = cache / filename(split)
            if verify and sha256_file(path) != CHECKSUMS[split]:
                raise ValueError(f'Checksum mismatch: {split}')
            count = 0
            with (tmp / f'{split}.jsonl').open('w', encoding='utf8') as out:
                for index, (title, text) in enumerate(_stream_articles(row_reader(path))):
                    if len(text) < min_chars: continue
                    fingerprint = hashlib.sha256(' '.join(text.split()).encode('utf8')).hexdigest()
                    previous = seen.get(fingerprint)
                    if previous is not None:
                        if previous != split:
                            raise ValueError(f'Cross-split text leakage: {title}')
                        continue
                    seen[fingerprint] = split
                    out.write(json.dumps({'id': fingerprint[:16], 'sha256': fingerprint,
                        'text': text + '\n', 'kind': 'text', 'split': split,
                        'group': f'wikitext-2:{split}:{index}',
                        'source': 'Salesforce/wikitext',
                        'source_url': 'https://huggingface.co/datasets/Salesforce/wikitext',
                        'license': 'CC BY-SA 3.0 / GFDL (publisher metadata)',
                        'origin': f'wikitext-2:{split}:{title}'}, ensure_ascii=False)+'\n')
                    count += 1
            if not count: raise ValueError(f'No usable articles in {split}')
            counts[split] = count
        report = {'dataset': 'Salesforce/wikitext wikitext-2-raw-v1',
                  'source_revision': 'main (SHA256-pinned)',
                  'sha256': CHECKSUMS, 'article_counts': counts,
                  'license_notice': LICENSE_INFO,
                  'limitations': ['Not conversational instruction data',
                                  'Insufficient alone for capable general-purpose AI']}
        (tmp / 'provenance_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        output.mkdir(parents=True,exist_ok=True)
        for name in ('train.jsonl','validation.jsonl','test.jsonl','provenance_report.json'):
            (tmp / name).replace(output / name)
        return report


def main(argv=None):
    p=argparse.ArgumentParser(description='Retrieve/import checksum-pinned WikiText-2 data')
    p.add_argument('--cache',type=Path,default=Path('data/wiki-parquet/downloads'))
    p.add_argument('--out',type=Path,default=Path('data/wiki-parquet/prepared'))
    p.add_argument('--skip-download',action='store_true')
    args=p.parse_args(argv)
    if not args.skip_download:fetch(args.cache)
    print(json.dumps(convert(args.cache,args.out),indent=2))


if __name__=='__main__':main()
