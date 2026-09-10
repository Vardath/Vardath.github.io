#!/usr/bin/env python3
from __future__ import annotations

import argparse,gzip,hashlib,json,math,random,statistics
from collections import Counter
from pathlib import Path
import reconstruct_original_language_all_dictionaries as core

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'full-occitan-indonesian-candidate-shards'
OUTDIR=ROOT/'data'/'full-candidate-validation-shards'
OUT=ROOT/'data'/'full-candidate-validation.json'
CANDIDATE=ROOT/'data'/'full-occitan-indonesian-candidate-language.json'
ORIGINAL=ROOT/'data'/'phonetic-original-language-dictionary.json'
BENCH=ROOT/'data'/'phonetic-benchmark-summary.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
GRID_OPS=['id','row_mirror','col_mirror','both_mirror','transpose','transpose_row','transpose_col','transpose_both']

def load_gz(p):
    with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)

def med(rows):
    c=Counter({tuple(p.split()):int(n) for p,n in rows});m=core.medoid(c);return m[0] if m else None

def fam_map(item):
    out={}
    for f,rows in item['family_paths'].items():
        p=med(rows)
        if p:out[f]=p
    return out

def anchor(item,which):
    rows=item[f'{which}_paths'];return med(rows) if rows else None

def reconstruct_weighted(fam,occ=None,ind=None):
    if len(fam)<core.MIN_FAMILIES:return None
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
        fs=[core.bestfit(c,t)[0] for t in reps];base=statistics.mean(fs)
        of=core.bestfit(c,occ)[0] if occ else None;inf=core.bestfit(c,ind)[0] if ind else None
        if occ and ind:score=.70*base+.15*of+.15*inf
        elif occ:score=.70*base+.30*of
        elif ind:score=.70*base+.30*inf
        else:score=base
        score-=.012*abs(len(c)-median);key=(score,base,-len(c),c)
        if best is None or key>best[0]:best=(key,c)
    return best[1] if best else None

def reconstruct_unanchored(fam):
    r=core.reconstruct(fam);return r[2] if r else None

def stable_int(s):return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8],'big')

def wrong_maps(items):
    oc=[];ind=[]
    for x in items:
        o=anchor(x,'occitan');i=anchor(x,'indonesian')
        if o:oc.append((x['meaning'],o))
        if i:ind.append((x['meaning'],i))
    oc.sort();ind.sort()
    def shift(rows,k):
        if not rows:return {}
        n=len(rows);k%=n
        if k==0 and n>1:k=1
        out={}
        for j,(m,_) in enumerate(rows):
            q=(j+k)%n
            if n>1 and rows[q][0]==m:q=(q+1)%n
            out[m]=rows[q][1]
        return out
    return shift(oc,137),shift(ind,271)

def norm(v):
    s=sum(v);return [x/s for x in v] if s else [0.0]*256

def cosine(a,b):
    d=sum(x*y for x,y in zip(a,b));aa=sum(x*x for x in a);bb=sum(y*y for y in b)
    return d/math.sqrt(aa*bb) if aa and bb else 0.0

def jsd(a,b):
    m=[(x+y)/2 for x,y in zip(a,b)]
    def kl(x,y):return sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q)
    return .5*kl(a,m)+.5*kl(b,m)

def overlap(a,b,k=32):
    A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]);B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k]);return len(A&B)/k

def pscore(a,b):return .55*cosine(a,b)+.30*(1-min(1,jsd(a,b)))+.15*overlap(a,b)

def idxop(i,op):
    a,b=divmod(i,16);ar,ac=divmod(a,4);br,bc=divmod(b,4);cell=lambda r,c:r*4+c
    if op=='id':na,nb=a,b
    elif op=='row_mirror':na,nb=cell(3-ar,ac),cell(3-br,bc)
    elif op=='col_mirror':na,nb=cell(ar,3-ac),cell(br,3-bc)
    elif op=='both_mirror':na,nb=cell(3-ar,3-ac),cell(3-br,3-bc)
    elif op=='transpose':na,nb=b,a
    elif op=='transpose_row':na,nb=cell(3-br,bc),cell(3-ar,ac)
    elif op=='transpose_col':na,nb=cell(br,3-bc),cell(ar,3-ac)
    elif op=='transpose_both':na,nb=cell(3-br,3-bc),cell(3-ar,3-ac)
    else:raise ValueError(op)
    return na*16+nb

def transform(v,op):
    z=[0.0]*256
    for i,x in enumerate(v):z[idxop(i,op)]+=x
    return z

def best_forward(source,target):return max((pscore(transform(source,o),target),o) for o in GRID_OPS)

def profile(paths):
    c=[0.0]*256
    for p in paths:
        for a,b in zip(p,p[1:]):
            if a in CELLS and b in CELLS:c[CELLS.index(a)*16+CELLS.index(b)]+=1
    return norm(c)

def langs():
    b=json.loads(BENCH.read_text(encoding='utf-8'))
    return {r['iso']:{'name':r['name'],'family':r.get('family','Unclassified') or 'Unclassified','p':norm(list(map(float,r['sample_counts'])))} for r in b['languages']}

def paired(rows,a,b):
    vals=[r[a]-r[b] for r in rows if r.get(a) is not None and r.get(b) is not None]
    return {'n':len(vals),'mean_difference':statistics.mean(vals) if vals else None,'median_difference':statistics.median(vals) if vals else None,'wins':sum(x>0 for x in vals),'losses':sum(x<0 for x in vals),'ties':sum(x==0 for x in vals)}

def boot(vals,seed,draws=10000):
    if not vals:return None
    rng=random.Random(seed);n=len(vals);means=[]
    for _ in range(draws):means.append(sum(vals[rng.randrange(n)] for _ in range(n))/n)
    means.sort();return [means[int(.025*(draws-1))],means[int(.975*(draws-1))]]

def mean(rows,key):
    v=[r[key] for r in rows if r.get(key) is not None];return statistics.mean(v) if v else None

def shard(i):
    cand=json.loads(CANDIDATE.read_text(encoding='utf-8'));orig=json.loads(ORIGINAL.read_text(encoding='utf-8'))
    ci={e['meaning']:e for e in cand['entries']};oi={e['meaning']:e for e in orig['entries']}
    all_items=[]
    for j in range(N):all_items+=load_gz(WORK/f'shard-{j:02d}.json.gz')
    wrong_oc,wrong_ind=wrong_maps(all_items);items=load_gz(WORK/f'shard-{i:02d}.json.gz');L=langs()
    occfam=L.get('oci',{}).get('family');indfam=L.get('ind',{}).get('family');anchor_fams={x for x in (occfam,indfam) if x}
    desc=[];hold=[];cp=[];rp=[]
    for item in items:
        m=item['meaning'];ce=ci.get(m);oe=oi.get(m)
        if not ce or not oe:continue
        fam=fam_map(item)
        if len(fam)<core.MIN_FAMILIES:continue
        cpath=tuple(ce['path']);rpath=tuple(oe['path']);reps=list(fam.values());o=anchor(item,'occitan');d=anchor(item,'indonesian')
        cov='both' if o and d else ('occitan' if o else ('indonesian' if d else 'none'))
        desc.append({'meaning':m,'coverage':cov,'candidate_family_fit':ce['family_fit'],'root_family_fit':statistics.mean(core.bestfit(rpath,t)[0] for t in reps),'candidate_root_similarity':core.sim(cpath,rpath),'candidate_correct_occitan_fit':core.bestfit(cpath,o)[0] if o else None,'candidate_wrong_occitan_fit':core.bestfit(cpath,wrong_oc[m])[0] if o and m in wrong_oc else None,'candidate_correct_indonesian_fit':core.bestfit(cpath,d)[0] if d else None,'candidate_wrong_indonesian_fit':core.bestfit(cpath,wrong_ind[m])[0] if d and m in wrong_ind else None})
        cp.append(cpath);rp.append(rpath)
        if cov=='none' or stable_int(m)%3!=0:continue
        eligible=[f for f in sorted(fam) if f not in anchor_fams]
        if not eligible:continue
        hf=eligible[stable_int('held:'+m)%len(eligible)];target=fam[hf];train={f:p for f,p in fam.items() if f!=hf}
        if len(train)<core.MIN_FAMILIES:continue
        a=reconstruct_weighted(train,o,d);u=reconstruct_unanchored(train);s=reconstruct_weighted(train,wrong_oc.get(m) if o else None,wrong_ind.get(m) if d else None)
        if a and u and s:hold.append({'meaning':m,'coverage':cov,'held_family':hf,'anchored':core.bestfit(a,target)[0],'unanchored':core.bestfit(u,target)[0],'shuffled':core.bestfit(s,target)[0]})
    cprof=profile(cp);rprof=profile(rp);targets=[]
    for j,iso in enumerate(sorted(L)):
        if j%N!=i or iso in {'oci','ind'}:continue
        t=L[iso];cs,co=best_forward(cprof,t['p']);rs,ro=best_forward(rprof,t['p']);targets.append({'iso':iso,'name':t['name'],'family':t['family'],'anchor_family':t['family'] in anchor_fams,'candidate':cs,'root':rs,'candidate_operator':co,'root_operator':ro})
    OUTDIR.mkdir(parents=True,exist_ok=True);payload={'shard':i,'entries':len(desc),'holdout_examples':hold,'benchmark_targets':targets,'descriptive':desc,'anchor_families':sorted(anchor_fams)}
    (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8');print(json.dumps({'shard':i,'entries':len(desc),'holdout':len(hold),'benchmark_targets':len(targets)}),flush=True)

def merge():
    xs=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)];desc=[r for x in xs for r in x['descriptive']];hold=[r for x in xs for r in x['holdout_examples']];targets=[r for x in xs for r in x['benchmark_targets']];anchor_fams=sorted({f for x in xs for f in x.get('anchor_families',[])})
    coverage={}
    for cov in ('both','occitan','indonesian','none'):
        rows=[r for r in desc if r['coverage']==cov];cf=mean(rows,'candidate_family_fit');rf=mean(rows,'root_family_fit');coverage[cov]={'n':len(rows),'candidate_family_fit':cf,'root_family_fit':rf,'candidate_minus_root_family_fit':cf-rf if rows else None,'candidate_root_similarity':mean(rows,'candidate_root_similarity')}
    anchor_specific={'occitan_correct_minus_shuffled':paired([r for r in desc if r['candidate_correct_occitan_fit'] is not None],'candidate_correct_occitan_fit','candidate_wrong_occitan_fit'),'indonesian_correct_minus_shuffled':paired([r for r in desc if r['candidate_correct_indonesian_fit'] is not None],'candidate_correct_indonesian_fit','candidate_wrong_indonesian_fit')}
    bycov={}
    for cov in ('both','occitan','indonesian'):
        rows=[r for r in hold if r['coverage']==cov];bycov[cov]={'n':len(rows),'anchored_mean':mean(rows,'anchored'),'unanchored_mean':mean(rows,'unanchored'),'shuffled_mean':mean(rows,'shuffled'),'anchored_minus_unanchored':paired(rows,'anchored','unanchored'),'anchored_minus_shuffled':paired(rows,'anchored','shuffled')}
    au=[r['anchored']-r['unanchored'] for r in hold];ash=[r['anchored']-r['shuffled'] for r in hold]
    independent={'n':len(hold),'anchored_mean':mean(hold,'anchored'),'unanchored_mean':mean(hold,'unanchored'),'shuffled_mean':mean(hold,'shuffled'),'anchored_minus_unanchored':paired(hold,'anchored','unanchored'),'anchored_minus_unanchored_bootstrap_95':boot(au,73001),'anchored_minus_shuffled':paired(hold,'anchored','shuffled'),'anchored_minus_shuffled_bootstrap_95':boot(ash,73002),'by_anchor_coverage':bycov}
    nonfam=[r for r in targets if not r['anchor_family']];all_diff=[r['candidate']-r['root'] for r in targets];nf_diff=[r['candidate']-r['root'] for r in nonfam]
    benchmark={'all_non_anchor_languages':{'n':len(targets),'candidate_mean':mean(targets,'candidate'),'root_mean':mean(targets,'root'),'candidate_minus_root':paired(targets,'candidate','root'),'bootstrap_95':boot(all_diff,74001)},'excluding_occitan_and_indonesian_families':{'n':len(nonfam),'candidate_mean':mean(nonfam,'candidate'),'root_mean':mean(nonfam,'root'),'candidate_minus_root':paired(nonfam,'candidate','root'),'bootstrap_95':boot(nf_diff,74002)},'anchor_families_excluded':anchor_fams}
    famdiff=[r['candidate_family_fit']-r['root_family_fit'] for r in desc];same={'n':len(desc),'candidate_family_fit':mean(desc,'candidate_family_fit'),'root_family_fit':mean(desc,'root_family_fit'),'candidate_minus_root_family_fit':statistics.mean(famdiff) if famdiff else None,'candidate_root_path_similarity':mean(desc,'candidate_root_similarity'),'by_anchor_coverage':coverage}
    auci=independent['anchored_minus_unanchored_bootstrap_95'];asci=independent['anchored_minus_shuffled_bootstrap_95'];supports=bool(independent['n'] and independent['anchored_mean']>independent['unanchored_mean'] and independent['anchored_mean']>independent['shuffled_mean'] and auci and auci[0]>0 and asci and asci[0]>0)
    result={'version':1,'test':'Full 12,000-word Occitan-Indonesian constrained candidate validation — 20 shards','shards':N,'design':{'primary_test':'For a deterministic one-third subset of meanings with at least one Occitan/Indonesian anchor, hold out one non-anchor language family before reconstruction. Compare correct anchors, no extra anchors, and wrong-meaning shuffled anchors, then score only against the held-out family.','null':'Anchor availability is preserved but each available Occitan/Indonesian anchor path is deterministically reassigned from a different meaning. The same grid machinery and weights are used.','unanchored_control':'Same Man-grid reconstruction machinery from remaining family medoids with no extra Occitan/Indonesian anchor weighting.','secondary_tests':'Completed candidate versus original 12,000-word root on same-meaning family fit and canonical transition profiles, including targets outside both anchor families.','predeclared_success_rule':'Primary anchor evidence is positive only if correct-anchor held-out mean exceeds both unanchored and shuffled-anchor means and both paired bootstrap 95% intervals are entirely above zero.','no_custom_timeout':True},'primary_independent_family_holdout':independent,'same_mean_descriptive':same,'anchor_specific_descriptive':anchor_specific,'canonical_profile_comparison':benchmark,'verdict':{'supports_extra_anchor_value_on_independent_families':supports,'note':'This tests whether extra Occitan/Indonesian constraints improve prediction of withheld non-anchor family evidence under the Man-grid model. It does not by itself establish historical chronology, geography, or descent.'}}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'primary_n':independent['n'],'anchored':independent['anchored_mean'],'unanchored':independent['unanchored_mean'],'shuffled':independent['shuffled_mean'],'au_ci':auci,'ash_ci':asci,'supports':supports,'benchmark_non_anchor_family_candidate':benchmark['excluding_occitan_and_indonesian_families']['candidate_mean'],'benchmark_non_anchor_family_root':benchmark['excluding_occitan_and_indonesian_families']['root_mean']},indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__':main()
