#!/usr/bin/env python3
"""Batch-prefetch transport for the frozen waterborne-child v2 merge."""
import json
import test_waterborne_child_fingertrap_v2 as core
import run_waterborne_child_fingertrap_v1_resilient as transport
import run_waterborne_child_fingertrap_v2_fast as fast

def run():
    paths=sorted(core.WORK.glob('shard-*.json'))
    if len(paths)!=20: raise SystemExit(f'need 20 shard files, found {len(paths)}')
    payloads=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
    bykey={}
    for sh in payloads:
        for r in sh['rows']:
            title=r.get('en_title')
            if not title: continue
            key=('q',r.get('qid')) if r.get('qid') else ('t',core.norm(title))
            bykey.setdefault(key,{'title':title,'qid':r.get('qid')})
    print(json.dumps({'batch_prefetch_candidates':len(bykey),'batch_size':20}),flush=True)
    fetched=transport.paced_fetch_en_extracts([r['title'] for r in bykey.values()])
    byq={}; byt={}
    for rec in fetched.values():
        x=dict(rec); x['extract']=(x.get('extract') or '')[:core.MAX_CHARS]
        if x.get('qid'): byq[x['qid']]=x
        byt[core.norm(x.get('title') or '')]=x
    cache={}
    for r in bykey.values():
        x=byq.get(r.get('qid')) if r.get('qid') else None
        if not x: x=byt.get(core.norm(r['title']))
        cache[core.norm(r['title'])]=x
    unresolved=sum(v is None for v in cache.values())
    print(json.dumps({'batch_prefetch_resolved':len(cache)-unresolved,'batch_prefetch_unresolved':unresolved}),flush=True)
    core.fetch_extract=lambda title: cache.get(core.norm(title))
    fast.fast_merge(workers=1)

if __name__=='__main__': run()
