"""Make a transparent toy chat pilot from the original 51 manually written pairs.

This is only a pipeline demonstration; it is not a general training corpus.
"""
from pathlib import Path
import argparse
import json
import random


def prepare(source:Path,out:Path,seed:int=2026):
    records=[json.loads(line) for line in source.read_text(encoding='utf8').splitlines() if line.strip()]
    for rec in records:
        if 'messages' not in rec:raise ValueError('Expected chat messages')
    random.Random(seed).shuffle(records)
    n=len(records)
    if n<20:raise ValueError('Need at least twenty distinct chats to form pilot splits')
    out.mkdir(parents=True,exist_ok=True)
    cuts=(n*7//10,n*85//100)
    pools={'train':records[:cuts[0]],'validation':records[cuts[0]:cuts[1]],'test':records[cuts[1]:]}
    for split,pool in pools.items():
        with (out/(split+'.jsonl')).open('w',encoding='utf8') as f:
            for index,rec in enumerate(pool):
                f.write(json.dumps({'messages':rec['messages'],'split':split,'group':f'original-starter-{records.index(rec)}'},ensure_ascii=False)+'\n')
    return {k:len(v) for k,v in pools.items()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=Path('data/starter.jsonl'))
    p.add_argument('--out',type=Path,default=Path('data/instruct-pilot'))
    args=p.parse_args()
    print(json.dumps(prepare(args.source,args.out),indent=2))

if __name__=='__main__':main()
