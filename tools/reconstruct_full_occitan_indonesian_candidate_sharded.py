#!/usr/bin/env python3
"""Full 20-shard Occitan+Indonesian constrained candidate-language reconstruction.

This deliberately does NOT use forms from the existing 12,000-word reconstructed
language. It re-scans the same complete Wiktextract corpus and reconstructs the
same eligible meaning space from source evidence.

For every meaning:
  * build one medoid path per independent language family (base evidence);
  * separately recover Occitan and Indonesian medoid paths when available;
  * generate the same fixed Man-grid candidate pool used by the original model;
  * score candidates against family evidence, while giving Occitan/Indonesian
    extra weight as the two predeclared split anchors discovered by the pilot;
  * when neither anchor is available, fall back to family-balanced reconstruction
    rather than inventing a word.

Execution is 20 deterministic shards. The output is a complete candidate lexicon
for every eligible meaning that can be reconstructed from the multilingual corpus.
"""
from __future__ import annotations
import argparse,gzip,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
import reconstruct_original_language_all_dictionaries as core

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'full-occitan-indonesian-candidate-shards'
WORK.mkdir(parents=True,exist_ok=True)
N=20
OUT=ROOT/'data'/'full-occitan-indonesian-candidate-language.json'
REPORT=ROOT/'data'/'full-occitan-indonesian-candidate-results.json'

OCC={'oc','oci'}; IND={'id','ind'}

def dg(p,o):
    with gzip.open(p,'wt',encoding='utf-8',compresslevel=6) as f: json.dump(o,f,ensure_ascii=False,separators=(',',':'))
def lg(p):
    with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)

def med(rows):
    c=Counter({tuple(p.split()):int(n) for p,n in rows});m=core.medoid(c);return m[0] if m else None

def prepare():
    con,stats,langs=core.ingest_all()
    hist=core.word_level_historical_audit(con)
    q="""SELECT concept,COUNT(DISTINCT lang_code),COUNT(DISTINCT family) FROM lex
         WHERE family!='Unclassified' GROUP BY concept HAVING COUNT(DISTINCT lang_code)>=?
         AND COUNT(DISTINCT family)>=? ORDER BY COUNT(DISTINCT family) DESC,
         COUNT(DISTINCT lang_code) DESC LIMIT ?"""
    concepts=list(con.execute(q,(core.MIN_LANGUAGES,core.MIN_FAMILIES,core.MAX_CONCEPTS)))
    shards=[[] for _ in range(N)]
    for ix,(concept,nlang,nfam) in enumerate(concepts):
        fam=defaultdict(Counter)
        for f,p,n in con.execute("SELECT family,path,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,path",(concept,)):
            fam[f][p]+=int(n)
        occ=Counter();ind=Counter()
        for lc,p,n in con.execute("SELECT lang_code,path,COUNT(*) FROM lex WHERE concept=? GROUP BY lang_code,path",(concept,)):
            if lc in OCC:occ[p]+=int(n)
            if lc in IND:ind[p]+=int(n)
        item={'meaning':concept,'languages':int(nlang),'families_reported':int(nfam),
              'family_paths':{f:[[p,int(n)] for p,n in c.items()] for f,c in fam.items()},
              'occitan_paths':[[p,int(n)] for p,n in occ.items()],
              'indonesian_paths':[[p,int(n)] for p,n in ind.items()]}
        shards[ix%N].append(item)
    man={'version':1,'shards':N,'eligible_meanings':len(concepts),'scan':dict(stats),
         'historical_word_regression':hist,
         'design':{'meaning_space':'same eligibility rules as the 12,000-word all-dictionary reconstruction',
                   'old_dictionary_forms_used':False,
                   'base_weight':0.70,'anchor_weight_each_when_both':0.15,
                   'single_anchor_weight':0.30,
                   'no_anchor_rule':'family-balanced reconstruction only; no invented anchor form',
                   'operators':core.CLASSES,
                   'candidate_generation':'same fixed Man-grid candidate pool as original full-dictionary model'}}
    (WORK/'manifest.json').write_text(json.dumps(man,indent=2),encoding='utf-8')
    for i,s in enumerate(shards):dg(WORK/f'shard-{i:02d}.json.gz',s)
    print(json.dumps({'phase':'prepare','eligible':len(concepts),'sizes':[len(s) for s in shards]}),flush=True)

def reconstruct(item):
    fam={}
    for f,rows in item['family_paths'].items():
        m=med(rows)
        if m:fam[f]=m
    if len(fam)<core.MIN_FAMILIES:return None
    occ=med(item['occitan_paths']) if item['occitan_paths'] else None
    ind=med(item['indonesian_paths']) if item['indonesian_paths'] else None
    reps=list(fam.values());freq=Counter(reps);pool=[];seen=set()
    for p,_ in freq.most_common(40):
        for cls in ('identity','metathesis','resegmentation','clipblend','acrophonic'):
            for v in core.variants(cls,p):
                if 2<=len(v)<=12 and v not in seen:seen.add(v);pool.append(v)
    for p in (occ,ind):
        if p:
            for cls in ('identity','metathesis','resegmentation','clipblend','acrophonic'):
                for v in core.variants(cls,p):
                    if 2<=len(v)<=12 and v not in seen:seen.add(v);pool.append(v)
    if not pool:return None
    median=statistics.median(map(len,reps));best=None
    for c in pool:
        ffits=[core.bestfit(c,t)[0] for t in reps];base=statistics.mean(ffits)
        of=core.bestfit(c,occ)[0] if occ else None; inf=core.bestfit(c,ind)[0] if ind else None
        if occ and ind: score=.70*base+.15*of+.15*inf
        elif occ: score=.70*base+.30*of
        elif ind: score=.70*base+.30*inf
        else: score=base
        score-=.012*abs(len(c)-median)
        key=(score,base,-len(c),c)
        if best is None or key>best[0]:best=(key,c,base,of,inf,ffits)
    _,cand,base,of,inf,ffits=best
    form=''.join(core.PHONE[x] for x in cand)
    return {'meaning':item['meaning'],'form':form,'ipa':f'/{form}/','path':list(cand),
            'languages':item['languages'],'families':len(fam),'family_fit':round(base,5),
            'occitan_fit':None if of is None else round(of,5),'indonesian_fit':None if inf is None else round(inf,5),
            'anchor_coverage':'both' if occ and ind else ('occitan' if occ else ('indonesian' if ind else 'none'))}

def shard(i):
    items=lg(WORK/f'shard-{i:02d}.json.gz');out=[]
    for j,x in enumerate(items,1):
        r=reconstruct(x)
        if r:out.append(r)
        if j%50==0:print(json.dumps({'shard':i,'processed':j,'of':len(items),'output':len(out)}),flush=True)
    dg(WORK/f'result-{i:02d}.json.gz',{'shard':i,'input':len(items),'entries':out})
    print(json.dumps({'phase':'shard','shard':i,'entries':len(out)}),flush=True)

def merge():
    man=json.loads((WORK/'manifest.json').read_text())
    entries=[];counts=[]
    for i in range(N):
        r=lg(WORK/f'result-{i:02d}.json.gz');entries+=r['entries'];counts.append({'shard':i,'input':r['input'],'output':len(r['entries'])})
    entries.sort(key=lambda x:x['meaning'])
    cov=Counter(x['anchor_coverage'] for x in entries)
    famfit=statistics.mean(x['family_fit'] for x in entries) if entries else 0
    payload={'version':1,'title':'Full Occitan-Indonesian constrained candidate language — 20 shards',
             'research_boundary':'Experimental reconstruction. Occitan and Indonesian are predeclared anchor languages; all remaining meanings use multilingual family evidence. Existing reconstructed word forms were not used to choose candidate words.',
             'method':man['design'],'summary':{'entries':len(entries),'eligible_meanings':man['eligible_meanings'],'shards':N,
             'anchor_coverage':dict(cov),'mean_family_fit':round(famfit,6)},'entries':entries}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    REPORT.write_text(json.dumps({'test':'full 20-shard Occitan-Indonesian constrained candidate reconstruction','summary':payload['summary'],'scan':man['scan'],'shard_counts':counts,'design':man['design']},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':'merge',**payload['summary']}),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='phase',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
    if a.phase=='prepare':prepare()
    elif a.phase=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
