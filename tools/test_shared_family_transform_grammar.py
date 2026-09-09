#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, random, statistics, subprocess, sys
from functools import lru_cache
from pathlib import Path
try:
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable,'-m','pip','install','numpy'])
    import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phonetic-cross-family-proto-meaning.json'
OUTJ=ROOT/'data/phonetic-shared-family-transform.json'
OUTM=ROOT/'data/phonetic-shared-family-transform.md'
RNG=random.Random(137)
CELLS=tuple(f'{r}{c}' for r in 'ABCD' for c in range(1,5))
OPS=(('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True))
OPNAMES=tuple(x[0] for x in OPS)
OPMAP={name:(pl,ma,rv) for name,pl,ma,rv in OPS}
SLOTS=('Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian')
ASSIGN=np.array(list(itertools.product(range(8),repeat=5)),dtype=np.uint8)

def feat(c): return ('ABCD'.index(c[0]),int(c[1])-1)
def sim_raw(a,b):
    n,m=len(a),len(b); dp=[[0.0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0]=i
    for j in range(m+1): dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            ra,ca=feat(a[i-1]); rb,cb=feat(b[j-1])
            sub=0.0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
            dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+sub)
    return max(0.0,1-dp[n][m]/max(n,m,1))
def transform(p,pl=False,ma=False,rv=False):
    cm=(2,1,0,3) if pl else (0,1,2,3); rm=(0,3,2,1) if ma else (0,1,2,3)
    q=tuple('ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p)
    return q[::-1] if rv else q
@lru_cache(maxsize=1_500_000)
def tsim(path,target,opi):
    _,pl,ma,rv=OPS[opi]
    return sim_raw(transform(path,pl,ma,rv),target)

def slotform(data,m,slot):
    for f in data['meanings'][m]['forms']:
        if f['family']==slot or (slot=='Proto-Uralic' and f['family'].startswith('Proto-Uralic')): return f
    raise KeyError((m,slot))

def candidate_paths(form_paths):
    targets=tuple(tuple(x) for x in form_paths)
    def score(p): return sum(max(tsim(p,t,o) for o in range(8)) for t in targets)/len(targets)
    beam=[((c,),score((c,))) for c in CELLS]; cand=[]
    for L in range(1,7):
        beam=sorted(beam,key=lambda x:x[1],reverse=True)[:120]
        if L>=2: cand += [p for p,_ in beam[:40]]
        if L==6: break
        beam=[(p+(c,),score(p+(c,))) for p,_ in beam for c in CELLS]
    cand += list(targets)
    return list(dict.fromkeys(cand))

# Cache the expensive per-meaning surface. Key is the five source meaning labels, one per family.
SURFACE_CACHE={}
def meaning_surface(data, combo):
    if combo in SURFACE_CACHE: return SURFACE_CACHE[combo]
    forms=[slotform(data,m,s) for m,s in zip(combo,SLOTS)]
    targets=[tuple(f['path']) for f in forms]
    cand=candidate_paths(targets)
    C=len(cand)
    score=np.empty((C,5,8),dtype=np.float32)
    for ci,p in enumerate(cand):
        for fi,t in enumerate(targets):
            for oi in range(8): score[ci,fi,oi]=tsim(p,t,oi)
    best_scores=np.empty(len(ASSIGN),dtype=np.float32)
    best_idx=np.empty(len(ASSIGN),dtype=np.uint16)
    chunk=4096
    for lo in range(0,len(ASSIGN),chunk):
        a=ASSIGN[lo:lo+chunk]
        acc=np.zeros((len(a),C),dtype=np.float32)
        for fi in range(5): acc += score[:,fi,:][:,a[:,fi]].T
        idx=acc.argmax(axis=1); best_idx[lo:lo+len(a)]=idx
        best_scores[lo:lo+len(a)]=acc[np.arange(len(a)),idx]/5.0
    SURFACE_CACHE[combo]=(best_scores,best_idx,cand,forms,score)
    return SURFACE_CACHE[combo]

def fit_joint(data,mapping=None,details=True):
    meanings=list(data['meanings'])
    surfaces=[]
    for m in meanings:
        combo=tuple(m if mapping is None else mapping[s][m] for s in SLOTS)
        surfaces.append((m,combo,meaning_surface(data,combo)))
    totals=np.zeros(len(ASSIGN),dtype=np.float32)
    for _,_,surf in surfaces: totals += surf[0]
    totals/=len(meanings); ai=int(totals.argmax()); mean=float(totals[ai])
    ops={s:OPNAMES[int(ASSIGN[ai,fi])] for fi,s in enumerate(SLOTS)}
    if not details: return mean,ops,{}
    detail={}
    for m,combo,(best_scores,best_idx,cand,forms,score) in surfaces:
        ci=int(best_idx[ai]); p=cand[ci]; aligns=[]
        for fi,(slot,f) in enumerate(zip(SLOTS,forms)):
            oi=int(ASSIGN[ai,fi])
            aligns.append({'family':slot,'form':f['form'],'operator':OPNAMES[oi],'score':round(float(score[ci,fi,oi]),6),'path':f['path']})
        detail[m]={'hidden_path':list(p),'mean_fit':round(float(best_scores[ai]),6),'alignments':aligns}
    return mean,ops,detail

data=json.loads(SRC.read_text(encoding='utf-8'))
obs,ops,detail=fit_joint(data)
meanings=list(data['meanings']); perm=[]
for i in range(200):
    mapping={}
    for slot in SLOTS:
        z=meanings[:]; RNG.shuffle(z); mapping[slot]=dict(zip(meanings,z))
    s,_,_=fit_joint(data,mapping,False); perm.append(s)
    if (i+1)%20==0: print(f'null {i+1}/200; cached meaning surfaces={len(SURFACE_CACHE)}',flush=True)
p=(sum(x>=obs for x in perm)+1)/(len(perm)+1)
res={'version':2,'research_boundary':'This test asks whether each proto-family can be described by one shared bridge transformation reused across multiple meanings. A positive result would support a recurring family-level transformation grammar, not prove deliberate engineering or a single historical Proto-World language.','method':{'meanings':meanings,'families':list(SLOTS),'operators':list(OPNAMES),'shared_operator_constraint':'one fixed operator per family across all meanings','operator_assignments':32768,'permutation_controls':len(perm),'shuffle':'meaning labels independently within family','optimization':'cached dynamic-programming similarities plus NumPy-vectorized exhaustive operator evaluation; statistical search space unchanged'},'summary':{'observed_joint_fit':round(obs,6),'permutation_mean':round(statistics.mean(perm),6),'permutation_sd':round(statistics.stdev(perm),6),'delta_vs_permutation':round(obs-statistics.mean(perm),6),'p_ge_observed':round(p,6)},'family_operators':ops,'meanings':detail}
OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Shared family transformation grammar test','',res['research_boundary'],'',f"Observed shared-grammar fit: **{obs:.3f}**",f"Shuffled-meaning fit: **{statistics.mean(perm):.3f} ± {statistics.stdev(perm):.3f}**",f"Δ **{obs-statistics.mean(perm):+.3f}**, permutation p **{p:.4f}**",'','## Best fixed operator per family']
for fam,op in ops.items(): lines.append(f'- {fam}: **{op}**')
for m,x in detail.items():
    lines += ['',f"## {m.title()}",f"Hidden path: **{' → '.join(x['hidden_path'])}** · mean fit **{x['mean_fit']:.3f}**"]
    for a in x['alignments']: lines.append(f"- {a['family']} {a['form']}: {a['score']:.3f} via {a['operator']}")
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(res['summary'],indent=2))
