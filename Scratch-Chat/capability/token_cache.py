"""Bounded-memory pre-tokenization of user-approved corpus into mmap-able files.

The binary format stores little-endian uint32 IDs and a SHA-256 manifest. Files
are ONLY produced from the user's prepared splits and project ByteBPE tokenizer.
"""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import os
from pathlib import Path
import sys

import torch
from capability.bpe import ByteBPE
from capability.pretrain import encode_record, file_hash

FORMAT = 'vardath-token-cache-v02'


def build_cache(*, corpus: Path, tokenizer_path: Path, output: Path) -> dict:
    if sys.byteorder != 'little' or array('I').itemsize != 4:
        raise RuntimeError('Token cache requires a 32-bit little-endian uint32 platform')
    output.mkdir(parents=True,exist_ok=True)
    tok=ByteBPE.load(tokenizer_path)
    manifest={'format':FORMAT, 'tokenizer_sha256':file_hash(tokenizer_path),
              'vocab_size':tok.vocab_size,'splits':{}}
    for split in ('train','validation','test'):
        input_path=corpus / f'{split}.jsonl'
        if not input_path.is_file():
            raise FileNotFoundError(input_path)
        temp=output/f'{split}.u32.tmp'
        target=output/f'{split}.u32'
        digest=hashlib.sha256()
        token_count=0
        record_count=0
        groups=set()
        try:
            with input_path.open(encoding='utf-8') as src, temp.open('wb') as out:
                for lineno,line in enumerate(src,1):
                    if not line.strip():
                        continue
                    record=json.loads(line)
                    if record.get('split') and record['split'] != split:
                        raise ValueError(f'Split mismatch at {input_path}:{lineno}')
                    tokens=encode_record(record,tok)
                    if any(i<0 or i>=tok.vocab_size for i in tokens):
                        raise ValueError('Invalid token ID')
                    blob=array('I', tokens).tobytes()
                    out.write(blob)
                    digest.update(blob)
                    token_count+=len(tokens)
                    record_count+=1
                    groups.add(record.get('group',''))
            if not token_count:
                raise ValueError(f'{split} split empty; add data before building token cache')
            os.replace(temp,target)
        finally:
            if temp.exists():
                temp.unlink()
        manifest['splits'][split] = {'file':target.name,
            'tokens':token_count,'records':record_count,'groups':len(groups),
            'source_sha256':file_hash(input_path),
            'binary_sha256':digest.hexdigest(), 'bytes':target.stat().st_size}
    temp=output/'metadata.json.tmp'
    temp.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    os.replace(temp,output/'metadata.json')
    return manifest


def load_cache(*, cache_dir: Path, corpus: Path, tokenizer_path: Path,
               split: str, validate_hash: bool=True) -> tuple[torch.Tensor,dict]:
    if split not in {'train','validation','test'}:
        raise ValueError('Split must be train, validation or test')
    metadata=json.loads((cache_dir/'metadata.json').read_text(encoding='utf-8'))
    if metadata.get('format')!=FORMAT or metadata.get('tokenizer_sha256')!=file_hash(tokenizer_path):
        raise ValueError('Token cache format/tokenizer mismatch; rebuild cache')
    info=metadata['splits'][split]
    source=corpus/(split+'.jsonl')
    binary=cache_dir/info['file']
    if not source.is_file() or file_hash(source)!=info['source_sha256']:
        raise ValueError(f'Source corpus {split} changed; rebuild cache')
    if not binary.is_file() or binary.stat().st_size!=info['tokens']*4 or binary.stat().st_size!=info['bytes']:
        raise ValueError(f'Token cache {split} is missing or truncated')
    if validate_hash and file_hash(binary)!=info['binary_sha256']:
        raise ValueError(f'Token cache {split} is corrupt or modified')
    mmap=torch.from_file(str(binary),shared=False,size=info['tokens'],dtype=torch.int32)
    return mmap, {'records':info['records'],'tokens':info['tokens'],'groups':info['groups']}


def main():
    p=argparse.ArgumentParser(description='Stream licensed corpus to memory-mapped training tokens')
    p.add_argument('--corpus',type=Path,default=Path('data/prepared'))
    p.add_argument('--tokenizer',type=Path,default=Path('data/tokenizer-bpe.json'))
    p.add_argument('--output',type=Path,default=Path('data/token-cache'))
    a=p.parse_args()
    print(json.dumps(build_cache(corpus=a.corpus,tokenizer_path=a.tokenizer,output=a.output),indent=2))

if __name__=='__main__':
    main()
