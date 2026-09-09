#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import random
import statistics
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/phonetic-cross-family-proto-meaning.json'
OUTJ = ROOT / 'data/phonetic-extended-operator-classes.json'
OUTM = ROOT / 'data/phonetic-extended-operator-classes.md'
RNG = random.Random(137)

SLOTS = ['Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian']
BASE_OPS = [
    ('identity',False,False,False),
    ('reverse',False,False,True),
    ('place',True,False,False),
    ('reverse+place',True,False,True),
    ('manner',False,True,False),
    ('reverse+manner',False,True,True),
    ('place+manner',True,True,False),
    ('reverse+place+manner',True,True,True),
]
NEW_CLASSES = ['metathesis','acrophonic','clipblend','resegmentation']
CLASS_NAMES = [x[0] for x in BASE_OPS] + NEW_CLASSES


def feat(c: str):
    return ('ABCD'.index(c[0]), int(c[1]) - 1)

@lru_cache(maxsize=None)
def sim_cached(a_t: tuple[str,...], b_t: tuple[str,...]) -> float:
    a=list(a_t); b=list(b_t)
    n,m=len(a),len(b)
    dp=[[0.0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0]=float(i)
    for j in range(m+1): dp[0][j]=float(j)
    for i in range(1,n+1):
        for j in range(1,m+1):
            ra,ca=feat(a[i-1]); rb,cb=feat(b[j-1])
            sub=0.0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6.0
            dp[i][j]=min(dp[i-1][j]+1.0, dp[i][j-1]+1.0, dp[i-1][j-1]+sub)
    return max(0.0, 1.0-dp[n][m]/max(n,m,1))

def transform_base(p, pl=False, ma=False, rv=False):
    cm=[2,1,0,3] if pl else [0,1,2,3]
    rm=[0,3,2,1] if ma else [0,1,2,3]
    q=['ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p]
    return q[::-1] if rv else q


def uniq(paths):
    out=[]; seen=set()
    for p in paths:
        t=tuple(p)
        if t and t not in seen:
            seen.add(t); out.append(list(t))
    return out


def metathesis_variants(p):
    # Linguistically conservative proxy: one local transposition, with distance <=2.
    n=len(p); out=[]
    for i in range(n):
        for j in range(i+1,min(n,i+3)):
            q=p[:]; q[i],q[j]=q[j],q[i]; out.append(q)
    return uniq(out or [p])


def anagram_ceiling_variants(p):
    # Diagnostic ceiling only, NOT part of the fitted operator bank.
    # For these short bridge paths the exact unique permutation set is tractable.
    if len(p)>7:
        return metathesis_variants(p)
    return [list(x) for x in set(itertools.permutations(p))]


def acrophonic_variants(p):
    # Experimental proxy for phrase-initial compression: split the path into 2..4
    # non-empty ordered chunks and retain the first state of each chunk.
    n=len(p); out=[]
    for k in range(2,min(4,n)+1):
        for cuts in itertools.combinations(range(1,n),k-1):
            starts=(0,)+cuts
            out.append([p[i] for i in starts])
    return uniq(out or [p])


def clipblend_variants(p):
    # Retain a prefix and suffix, allowing the middle to disappear; models a
    # clipping/blending family rather than claiming a specific historical event.
    n=len(p); out=[]
    for left in range(1,n):
        for right in range(1,n-left+1):
            q=p[:left] + p[n-right:]
            if 2 <= len(q) < n:
                out.append(q)
    # Also ordinary prefix/suffix clipping of length >=2.
    for k in range(2,n):
        out.append(p[:k]); out.append(p[n-k:])
    return uniq(out or [p])


def resegmentation_variants(p):
    # Boundary-shift proxy for a single lexical path: cyclic boundary rotations
    # and moving one edge state across the boundary.
    n=len(p); out=[]
    for k in range(1,n): out.append(p[k:]+p[:k])
    if n>=3:
        out.append(p[1:]+[p[0]])
        out.append([p[-1]]+p[:-1])
    return uniq(out or [p])


def class_variants(name, p):
    for nm,pl,ma,rv in BASE_OPS:
        if name==nm:
            return [transform_base(p,pl,ma,rv)]
    if name=='metathesis': return metathesis_variants(p)
    if name=='acrophonic': return acrophonic_variants(p)
    if name=='clipblend': return clipblend_variants(p)
    if name=='resegmentation': return resegmentation_variants(p)
    raise KeyError(name)


def slotform(data,m,slot):
    for f in data['meanings'][m]['forms']:
        if f['family']==slot or (slot=='Proto-Uralic' and f['family'].startswith('Proto-Uralic')):
            return f
    raise KeyError((m,slot))


data=json.loads(SRC.read_text(encoding='utf-8'))
meanings=list(data['meanings'])
forms={(slot,m):slotform(data,m,slot) for slot in SLOTS for m in meanings}

# Precompute every source-form/operator-class/target-form score exactly once.
# New classes can have many variants, but the expensive edit similarities are cached.
scores={}
variant_counts={}
anagram_ceiling={}
for sslot in SLOTS:
    for sm in meanings:
        src=forms[(sslot,sm)]['path']
        for cls in CLASS_NAMES:
            vs=class_variants(cls,src)
            variant_counts[(sslot,sm,cls)] = len(vs)
            for tslot in SLOTS:
                if tslot==sslot: continue
                for tm in meanings:
                    tgt=forms[(tslot,tm)]['path']
                    scores[(sslot,sm,tslot,tm,cls)] = max(sim_cached(tuple(v),tuple(tgt)) for v in vs)
        # unrestricted anagram is a diagnostic ceiling and never enters model selection
        av=anagram_ceiling_variants(src)
        for tslot in SLOTS:
            if tslot==sslot: continue
            for tm in meanings:
                tgt=forms[(tslot,tm)]['path']
                anagram_ceiling[(sslot,sm,tslot,tm)] = max(sim_cached(tuple(v),tuple(tgt)) for v in av)

ordered_pairs=[(a,b) for a in SLOTS for b in SLOTS if a!=b]

# Descriptive same-vs-wrong signal for each operator class.
class_summary={}
for cls in CLASS_NAMES:
    same=[]; wrong=[]
    for a,b in ordered_pairs:
        for m in meanings:
            same.append(scores[(a,m,b,m,cls)])
            for wm in meanings:
                if wm!=m: wrong.append(scores[(a,m,b,wm,cls)])
    class_summary[cls]={
        'same_mean':round(statistics.mean(same),6),
        'wrong_mean':round(statistics.mean(wrong),6),
        'uplift':round(statistics.mean(same)-statistics.mean(wrong),6),
    }

# Leave-one-meaning-out generalization test.
# For each ordered family pair and held-out concept, choose ONE operator class from
# the other meanings, then score the held-out same-meaning form. This directly
# tests reusable transformations without exhaustive 12^5 family assignments.
def cv_score(mapping=None):
    vals=[]; chosen=[]
    for a,b in ordered_pairs:
        for held in meanings:
            train=[m for m in meanings if m!=held]
            best_cls=max(CLASS_NAMES,key=lambda cls: statistics.mean(
                scores[(a,m,b,(mapping[b][m] if mapping else m),cls)] for m in train
            ))
            target_m=(mapping[b][held] if mapping else held)
            s=scores[(a,held,b,target_m,best_cls)]
            vals.append(s); chosen.append((a,b,held,best_cls,s))
    return statistics.mean(vals), chosen

obs, chosen=cv_score()
identity_vals=[scores[(a,m,b,m,'identity')] for a,b in ordered_pairs for m in meanings]
identity_mean=statistics.mean(identity_vals)
oracle_vals=[max(scores[(a,m,b,m,cls)] for cls in CLASS_NAMES) for a,b in ordered_pairs for m in meanings]
oracle_mean=statistics.mean(oracle_vals)
anagram_vals=[anagram_ceiling[(a,m,b,m)] for a,b in ordered_pairs for m in meanings]
anagram_mean=statistics.mean(anagram_vals)

# 100,000 cached permutation controls. Each target family receives an independent
# meaning permutation; all similarities are table lookups, so statistical power is
# increased without recomputing transformations or edit distances.
NNULL=100000
perm=[]
for _ in range(NNULL):
    mapping={}
    for slot in SLOTS:
        z=meanings[:]; RNG.shuffle(z); mapping[slot]=dict(zip(meanings,z))
    s,_=cv_score(mapping)
    perm.append(s)
perm_mean=statistics.mean(perm); perm_sd=statistics.stdev(perm)
p=(sum(x>=obs for x in perm)+1)/(NNULL+1)

# Summarize which classes actually generalize most often.
counts={cls:0 for cls in CLASS_NAMES}
heldout_detail=[]
for a,b,m,cls,s in chosen:
    counts[cls]+=1
    heldout_detail.append({'source_family':a,'target_family':b,'meaning':m,'selected_class':cls,'heldout_score':round(s,6)})

# New-class-only comparison, selected on training concepts and tested held out.
def cv_score_subset(classes, mapping=None):
    vals=[]
    for a,b in ordered_pairs:
        for held in meanings:
            train=[m for m in meanings if m!=held]
            best_cls=max(classes,key=lambda cls: statistics.mean(
                scores[(a,m,b,(mapping[b][m] if mapping else m),cls)] for m in train
            ))
            tm=(mapping[b][held] if mapping else held)
            vals.append(scores[(a,held,b,tm,best_cls)])
    return statistics.mean(vals)
new_obs=cv_score_subset(NEW_CLASSES)
base_obs=cv_score_subset([x[0] for x in BASE_OPS])

res={
    'version':1,
    'research_boundary':(
        'The four added classes are operational proxies over the existing 4x4 bridge paths. '
        'Metathesis is a local transposition model; acrophonic compression approximates retaining '
        'initial states from hypothesized chunks because the current proto-word dataset has no phrase '
        'boundaries; clipping/blending removes medial material or keeps word edges; resegmentation is '
        'approximated by boundary rotations. A positive result would show predictive structure under '
        'these operators, not prove a particular prehistoric derivation, Proto-World, or deliberate language engineering.'
    ),
    'method':{
        'families':SLOTS,
        'meanings':meanings,
        'operator_classes':CLASS_NAMES,
        'new_classes':NEW_CLASSES,
        'validation':'leave-one-meaning-out; operator class selected on other meanings for each ordered family pair',
        'permutation_controls':NNULL,
        'null':'independent within-target-family meaning-label permutations; cached exact score table',
        'anagram_ceiling':'exact unrestricted unique permutations for paths of length <=7; diagnostic only, excluded from model selection'
    },
    'summary':{
        'heldout_operator_bank_score':round(obs,6),
        'identity_heldout_same_mean':round(identity_mean,6),
        'oracle_same_mean_ceiling':round(oracle_mean,6),
        'unrestricted_anagram_same_mean_ceiling':round(anagram_mean,6),
        'baseline_classes_cv_score':round(base_obs,6),
        'new_classes_cv_score':round(new_obs,6),
        'permutation_mean':round(perm_mean,6),
        'permutation_sd':round(perm_sd,6),
        'delta_vs_permutation':round(obs-perm_mean,6),
        'p_ge_observed':round(p,6),
    },
    'class_same_vs_wrong':class_summary,
    'selected_class_counts':counts,
    'heldout_details':heldout_detail,
    'variant_counts':{'min':min(variant_counts.values()),'max':max(variant_counts.values()),'mean':round(statistics.mean(variant_counts.values()),3)}
}
OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')

lines=[
    '# Extended lexical operator-class test','',res['research_boundary'],'',
    '## Held-out result','',
    f"Full 12-class held-out score: **{obs:.3f}**",
    f"Baseline 8-class held-out score: **{base_obs:.3f}**",
    f"New four-class held-out score: **{new_obs:.3f}**",
    f"Identity same-meaning baseline: **{identity_mean:.3f}**",
    f"Oracle same-meaning ceiling: **{oracle_mean:.3f}**",
    f"Unrestricted-anagram diagnostic ceiling: **{anagram_mean:.3f}**",
    f"Shuffled held-out score: **{perm_mean:.3f} ± {perm_sd:.3f}**",
    f"Δ vs null **{obs-perm_mean:+.3f}**, permutation p **{p:.6f}**",'',
    '## Same-meaning versus wrong-meaning by class',''
]
for cls in CLASS_NAMES:
    x=class_summary[cls]
    lines.append(f"- {cls}: same {x['same_mean']:.3f}, wrong {x['wrong_mean']:.3f}, Δ {x['uplift']:+.3f}")
lines += ['', '## Classes selected by leave-one-meaning-out validation','']
for cls,n in sorted(counts.items(),key=lambda x:(-x[1],x[0])):
    lines.append(f'- {cls}: {n}')
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(res['summary'],indent=2))
