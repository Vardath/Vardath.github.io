#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, random, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phonetic-cross-family-proto-meaning.json'
OUTJ=ROOT/'data/phonetic-shared-family-transform.json'
OUTM=ROOT/'data/phonetic-shared-family-transform.md'
RNG=random.Random(137)
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
OPS=[('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]
SLOTS=['Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian']

def feat(c): return ('ABCD'.index(c[0]),int(c[1])-1)
def sim(a,b):
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
    cm=[2,1,0,3] if pl else [0,1,2,3]; rm=[0,3,2,1] if ma else [0,1,2,3]
    q=['ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p]
    return q[::-1] if rv else q
OPMAP={name:(pl,ma,rv) for name,pl,ma,rv in OPS}

def slotform(data,m,slot):
    for f in data['meanings'][m]['forms']:
        if f['family']==slot or (slot=='Proto-Uralic' and f['family'].startswith('Proto-Uralic')):
            return f
    raise KeyError((m,slot))

def candidate_paths(forms):
    # Search small latent paths, independent of operator assignment.
    def score(p):
        vals=[]
        for f in forms:
            vals.append(max(sim(transform(p,*OPMAP[n]),f['path']) for n in OPMAP))
        return statistics.mean(vals)
    beam=[([c],score([c])) for c in CELLS]; cand=[]
    for L in range(1,7):
        beam=sorted(beam,key=lambda x:x[1],reverse=True)[:120]
        if L>=2: cand += [p for p,_ in beam[:40]]
        if L==6: break
        beam=[(p+[c],score(p+[c])) for p,_ in beam for c in CELLS]
    # Include observed proto paths to avoid search artefacts.
    cand += [f['path'] for f in forms]
    uniq=[]; seen=set()
    for p in cand:
        k=tuple(p)
        if k not in seen: seen.add(k); uniq.append(p)
    return uniq

def fit_joint(data, mapping=None):
    meanings=list(data['meanings'])
    # mapping[slot][meaning] can remap meaning labels for nulls.
    forms_by_m={}
    for m in meanings:
        forms=[]
        for slot in SLOTS:
            src_m=m if mapping is None else mapping[slot][m]
            forms.append(slotform(data,src_m,slot))
        forms_by_m[m]=forms
    candidates={m:candidate_paths(forms_by_m[m]) for m in meanings}
    best_global=None
    # Exhaustively search one fixed operator per family: 8^5 = 32768.
    # For each assignment, choose the best latent path independently per meaning.
    for ops in itertools.product(list(OPMAP), repeat=len(SLOTS)):
        total=0.0; chosen={}
        for m in meanings:
            forms=forms_by_m[m]; bestp=None; bests=-1
            for p in candidates[m]:
                vals=[]
                for slot,op,f in zip(SLOTS,ops,forms):
                    vals.append(sim(transform(p,*OPMAP[op]),f['path']))
                s=statistics.mean(vals)
                if s>bests: bests=s; bestp=p
            total+=bests; chosen[m]=(bestp,bests)
        mean=total/len(meanings)
        if best_global is None or mean>best_global[0]: best_global=(mean,ops,chosen,forms_by_m)
    mean,ops,chosen,forms_by_m=best_global
    detail={}
    for m,(p,s) in chosen.items():
        aligns=[]
        for slot,op,f in zip(SLOTS,ops,forms_by_m[m]):
            aligns.append({'family':slot,'form':f['form'],'operator':op,'score':round(sim(transform(p,*OPMAP[op]),f['path']),6),'path':f['path']})
        detail[m]={'hidden_path':p,'mean_fit':round(s,6),'alignments':aligns}
    return mean,dict(zip(SLOTS,ops)),detail

data=json.loads(SRC.read_text(encoding='utf-8'))
obs,ops,detail=fit_joint(data)
meanings=list(data['meanings'])
perm=[]
# 200 nulls are enough for this expensive exhaustive joint fit; exact tail floor ~0.005.
for _ in range(200):
    mapping={}
    for slot in SLOTS:
        z=meanings[:]; RNG.shuffle(z); mapping[slot]=dict(zip(meanings,z))
    s,_,_=fit_joint(data,mapping)
    perm.append(s)
p=(sum(x>=obs for x in perm)+1)/(len(perm)+1)
res={
 'version':1,
 'research_boundary':'This test asks whether each proto-family can be described by one shared bridge transformation reused across multiple meanings. A positive result would support a recurring family-level transformation grammar, not prove deliberate engineering or a single historical Proto-World language.',
 'method':{'meanings':meanings,'families':SLOTS,'operators':[x[0] for x in OPS],'shared_operator_constraint':'one fixed operator per family across all meanings','permutation_controls':len(perm),'shuffle':'meaning labels independently within family'},
 'summary':{'observed_joint_fit':round(obs,6),'permutation_mean':round(statistics.mean(perm),6),'permutation_sd':round(statistics.stdev(perm),6),'delta_vs_permutation':round(obs-statistics.mean(perm),6),'p_ge_observed':round(p,6)},
 'family_operators':ops,
 'meanings':detail
}
OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Shared family transformation grammar test','',res['research_boundary'],'',f"Observed shared-grammar fit: **{obs:.3f}**",f"Shuffled-meaning fit: **{statistics.mean(perm):.3f} ± {statistics.stdev(perm):.3f}**",f"Δ **{obs-statistics.mean(perm):+.3f}**, permutation p **{p:.4f}**",'','## Best fixed operator per family']
for fam,op in ops.items(): lines.append(f'- {fam}: **{op}**')
for m,x in detail.items():
    lines += ['',f"## {m.title()}",f"Hidden path: **{' → '.join(x['hidden_path'])}** · mean fit **{x['mean_fit']:.3f}**"]
    for a in x['alignments']: lines.append(f"- {a['family']} {a['form']}: {a['score']:.3f} via {a['operator']}")
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(res['summary'],indent=2))
