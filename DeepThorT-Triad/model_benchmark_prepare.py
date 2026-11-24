"""Explicit, separate download of pinned experimental model files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parent
PROFILES=json.loads((ROOT/'benchmarks/profiles.json').read_text())
CONFIGS={'config.json','generation_config.json','tokenizer.json','tokenizer_config.json',
         'added_tokens.json','special_tokens_map.json','merges.txt','vocab.json'}
LIMIT=8*1024**3

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('profile',choices=PROFILES)
    parser.add_argument('--download',action='store_true',required=True)
    args=parser.parse_args()
    spec=PROFILES[args.profile]
    repo,rev=spec['repo'],spec['revision']
    with urlopen('https://huggingface.co/api/models/'+repo+'/revision/'+rev+'?blobs=true',timeout=60) as response:
        metadata=json.loads(response.read(4*1024**2))
    if metadata.get('sha')!=rev:raise SystemExit('Unexpected model revision')
    siblings={r['rfilename']:r for r in metadata['siblings']}
    names=set(spec['weights'])|(CONFIGS & siblings.keys())
    if not {'config.json','tokenizer.json','tokenizer_config.json'}<=names or not set(spec['weights'])<=siblings.keys():
        raise SystemExit('Incomplete model repository')
    if sum(siblings[n]['size'] for n in names)>LIMIT:raise SystemExit('Download exceeds profile budget')
    base=ROOT/'benchmark-local/models'/repo
    for name in sorted(names):
        meta=siblings[name]
        size=meta['size']; expected=(meta.get('lfs') or {}).get('sha256')
        path=base/name; path.parent.mkdir(parents=True,exist_ok=True)
        def fingerprint(p):
            with p.open('rb') as stream:
                if expected:return hashlib.file_digest(stream,'sha256').hexdigest()
                h=hashlib.sha1()
                h.update(('blob '+str(p.stat().st_size)+'\0').encode())
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
                return h.hexdigest()
        wanted=expected or meta.get('blobId')
        if not wanted:raise SystemExit('Missing expected file fingerprint')
        if path.exists() and path.stat().st_size==size and fingerprint(path)==wanted:continue
        part=path.with_suffix(path.suffix+'.part')
        print('Downloading pinned',name,size,flush=True)
        with urlopen(Request('https://huggingface.co/'+repo+'/resolve/'+rev+'/'+name),timeout=120) as r,part.open('wb') as stream:
            written=0
            for block in iter(lambda:r.read(1024*1024),b''):
                written+=len(block)
                if written>size:raise ValueError('Unexpected file size')
                stream.write(block)
        if part.stat().st_size!=size or fingerprint(part)!=wanted:raise ValueError('Model fingerprint mismatch')
        os.replace(part,path)
    print('Experimental model prepared separately:',args.profile)

if __name__=='__main__':main()
