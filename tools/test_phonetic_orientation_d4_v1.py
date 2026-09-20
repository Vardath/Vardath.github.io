#!/usr/bin/env python3
from __future__ import annotations
import json, math
from collections import defaultdict
from pathlib import Path
import man_grid_exact_data as D
import test_phonetic_square_sequence_v2 as B

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/phonetic-orientation-d4-v1.json'
RES=list(range(3,22))
FOLDS=20

# Transform TARGET coordinates into SOURCE coordinates.
TRANSFORMS={
 'identity':lambda x,y:(x,y),
 'mirror_lr':lambda x,y:(1-x,y),
 'mirror_tb':lambda x,y:(x,1-y),
 'rot180':lambda x,y:(1-x,1-y),
 'transpose':lambda x,y:(y,x),
 'anti_diagonal':lambda x,y:(1-y,1-x),
 'rot90_cw':lambda x,y:(1-y,x),
 'rot270_cw':lambda x,y:(y,1-x),
}
TN=list(TRANSFORMS)

def tc(c,t):
    x,y=TRANSFORMS[t](*c)
    return max(0.0,min(.999999,x)),max(0.0,min(.999999,y))

def cell(c,n):
    return int(max(0,min(.999999,c[0]))*n),int(max(0,min(.999999,c[1]))*n)

def empty():
    return {'src':0,'out':0,'heldout_sum':0.0}

def add(a,b):
    a['src']+=b['src'];a['out']+=b['out'];a['heldout_sum']+=b['heldout_sum']

def one_way(A,Bset,Q,n,t,transform_source=False,transform_target=True):
    A=sorted(A & Q.keys()); Bs=sorted(Bset & Q.keys())
    m=empty();m['src']=len(A)
    buckets=defaultdict(list)
    for b in Bs:
        bc=tc(Q[b]['c'],t) if transform_target else Q[b]['c']
        buckets[cell(bc,n)].append(b)
    for a in A:
        ac=tc(Q[a]['c'],t) if transform_source else Q[a]['c']
        cand=buckets.get(cell(ac,n),[])
        if not cand: continue
        b=min(cand,key=lambda q:(B.pd(Q[a]['features'],Q[q]['features']),q))
        m['out']+=1
        m['heldout_sum']+=B.hd(Q[a]['features'],Q[b]['features'])
    return m

def oriented_bidir(A,Bset,Q,n,t):
    # B is the transformed side in both directions:
    # A -> t(B), and t(B) -> A.
    m=empty()
    add(m,one_way(A,Bset,Q,n,t,False,True))
    add(m,one_way(Bset,A,Q,n,t,True,False))
    return m

def score(m):
    cov=m['out']/m['src'] if m['src'] else 0.0
    loss=m['heldout_sum']/m['out'] if m['out'] else 1.0
    sim=max(0.0,1.0-loss)
    f1=(2*cov*sim/(cov+sim)) if cov+sim else 0.0
    return {'coverage':cov,'heldout_loss':loss,'balanced':f1,'sources':m['src'],'outputs':m['out']}

def binom_tail(k,n):
    if n<=0:return 1.0
    return sum(math.comb(n,i) for i in range(k,n+1))/(2**n)

def best_name(metrics):
    # identity wins exact ties, preventing non-identity claims from numerical ties.
    return max(TN,key=lambda t:(metrics[t]['balanced'], metrics[t]['coverage'], -metrics[t]['heldout_loss'], t=='identity'))

def load():
    _,Q,L,_,cov=D.load_phoible()
    P=B.fit(Q)
    for q in Q.values():q['c']=B.proj(q['features'],P)
    branches,eligible=B.branches(L,Q)
    for lid,b in branches.items():
        if lid in L:L[lid]['branch']=b
    by=defaultdict(list)
    for lid,l in L.items():by[l['family']].append(lid)
    structures={}
    for fam in eligible:
        s=B.struct(fam,by[fam],L,Q)
        if s and s['A'] and s['B']:structures[fam]=s
    return Q,L,by,structures,cov

def main():
    Q,L,by,S,cov=load()
    families=sorted(S)
    shard={f:D.h64('d4-orientation-v1',f)%FOLDS for f in families}

    # Precompute family x resolution x orientation metrics once.
    FM={}
    for fam in families:
        A,C=S[fam]['A'],S[fam]['B']
        FM[fam]={}
        for n in RES:
            FM[fam][n]={}
            for t in TN:
                FM[fam][n][t]=oriented_bidir(A,C,Q,n,t)

    # Descriptive pooled performance for all families.
    pooled={}
    for n in RES:
        pooled[n]={}
        for t in TN:
            z=empty()
            for f in families:add(z,FM[f][n][t])
            pooled[n][t]=score(z)

    folds=[]
    per_resolution={n:{'wins':0,'ties':0,'delta_sum':0.0,'selected':defaultdict(int),
                       'control_delta_sum':0.0} for n in RES}
    for fold in range(FOLDS):
        train=[f for f in families if shard[f]!=fold]
        test=[f for f in families if shard[f]==fold]
        fr={'fold':fold,'train_families':len(train),'test_families':len(test),'resolutions':{}}
        for n in RES:
            tr={}
            for t in TN:
                z=empty()
                for f in train:add(z,FM[f][n][t])
                tr[t]=score(z)
            chosen=best_name(tr)

            def agg(fs,t):
                z=empty()
                for f in fs:add(z,FM[f][n][t])
                return score(z)
            sel=agg(test,chosen); ident=agg(test,'identity')
            ctrl_name=TN[D.h64('d4-control-v1',fold,n)%len(TN)]
            ctrl=agg(test,ctrl_name)
            delta=sel['balanced']-ident['balanced']
            cdelta=ctrl['balanced']-ident['balanced']
            pr=per_resolution[n]
            pr['selected'][chosen]+=1;pr['delta_sum']+=delta;pr['control_delta_sum']+=cdelta
            if delta>1e-12:pr['wins']+=1
            elif abs(delta)<=1e-12:pr['ties']+=1
            fr['resolutions'][str(n)]={
                'selected':chosen,'train_selected':tr[chosen],
                'test_selected':sel,'test_identity':ident,
                'delta_balanced_vs_identity':delta,
                'random_control':ctrl_name,'test_random_control':ctrl,
                'random_delta_vs_identity':cdelta
            }
        folds.append(fr)

    resolution_summary={}
    supported=0
    for n in RES:
        p=per_resolution[n]
        mean_delta=p['delta_sum']/FOLDS
        wins=p['wins']
        signp=binom_tail(wins,FOLDS)
        ok=(wins>=15 and signp<.05 and mean_delta>0)
        supported+=int(ok)
        resolution_summary[str(n)]={
            'pooled':pooled[n],
            'pooled_best':best_name(pooled[n]),
            'cv_selection_counts':dict(p['selected']),
            'cv_test_wins_vs_identity':wins,
            'cv_test_ties_vs_identity':p['ties'],
            'cv_test_sign_p':signp,
            'cv_mean_balanced_delta_vs_identity':mean_delta,
            'random_control_mean_delta_vs_identity':p['control_delta_sum']/FOLDS,
            'replicated_nonidentity_advantage':ok
        }

    # Exploratory named-language probe. This does not test writing direction:
    # it only asks whether one PHOIBLE inventory is better aligned to the
    # consensus of other members of its PHOIBLE family under D4 transforms.
    probes=[]
    needles=('korean','mandarin','chinese','cantonese','yue')
    for lid,l in sorted(L.items(),key=lambda kv:(kv[1]['name'],kv[0])):
        nm=(l.get('name') or '').lower()
        if not any(x in nm for x in needles):continue
        others=[x for x in by[l['family']] if x!=lid]
        row={'id':lid,'name':l['name'],'family':l['family'],'same_family_others':len(others)}
        if not others:
            row['status']='no same-family PHOIBLE comparator; not scored'
            probes.append(row);continue
        C=B.cons(others,L)
        A=set(l['inventory'])
        rr={}
        for n in (4,8,16,21):
            vals={}
            for t in TN:vals[t]=score(oriented_bidir(C,A,Q,n,t))
            best=best_name(vals)
            rr[str(n)]={'best':best,'best_score':vals[best],
                        'identity':vals['identity'],
                        'delta_vs_identity':vals[best]['balanced']-vals['identity']['balanced']}
        row['status']='exploratory inventory-family probe only'
        row['resolutions']=rr
        probes.append(row)

    overall_support=(supported>=14)
    result={
      'version':1,'status':'complete',
      'test':'D4 orientation of the successive phonetic square bridge',
      'source':{'dataset':'PHOIBLE CLDF','commit':D.PH},
      'question':'Does rotating or reflecting one language-side of the phonetic plane improve held-out related-family translation beyond the ordinary orientation?',
      'transforms':{
        'identity':'(x,y)',
        'mirror_lr':'(1-x,y)','mirror_tb':'(x,1-y)','rot180':'(1-x,1-y)',
        'transpose':'(y,x)','anti_diagonal':'(1-y,1-x)',
        'rot90_cw':'(1-y,x)','rot270_cw':'(y,1-x)'
      },
      'method':{
        'resolutions':'3x3 through 21x21, same continuous primary-feature plane as the existing square-sequence test',
        'projection_features':B.PN,
        'heldout_features':[E for E in B.E.FEATURES if E not in B.PRIMARY and E not in {'tone','stress'}] if hasattr(B,'PRIMARY') else [B.E.FEATURES[i] for i in B.HI],
        'evidence':'Within-family sibling-branch consensus inventories; unrelated script labels are not used.',
        'cross_validation':'20 deterministic family-blocked folds. For each resolution, choose one D4 transform using the other 19 folds, then compare it with fixed identity on the held-out fold.',
        'score':'Harmonic mean of same-cell coverage and (1 - held-out residual-feature loss).',
        'control':'A deterministic random D4 transform per held-out fold/resolution.',
        'support_rule':'A resolution replicates only with >=15/20 held-out-fold wins over identity, one-sided sign p<0.05, and positive mean balanced-score delta. A general orientation effect requires replication at >=14/19 resolutions.',
        'important_boundary':'This tests phonetic-coordinate orientation. It does not by itself test visual writing direction or Hangul/Hanzi layout.'
      },
      'coverage':{'families':len(families),'folds':FOLDS,'segments':cov['research_segments'],'eligible_languages':cov['eligible_languages']},
      'summary':{
        'replicated_resolutions':supported,'candidate_resolutions':len(RES),
        'general_nonidentity_orientation_supported':overall_support,
        'pooled_identity_best_resolutions':sum(best_name(pooled[n])=='identity' for n in RES),
        'pooled_nonidentity_best_resolutions':sum(best_name(pooled[n])!='identity' for n in RES)
      },
      'resolutions':resolution_summary,
      'named_language_probe':probes,
      'folds':folds
    }
    OUT.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result['coverage'],indent=2))
    print(json.dumps(result['summary'],indent=2))
    print('RESOLUTION_SUMMARY')
    for n in RES:
        x=resolution_summary[str(n)]
        print(n,x['pooled_best'],x['cv_selection_counts'],x['cv_test_wins_vs_identity'],
              round(x['cv_mean_balanced_delta_vs_identity'],8),x['replicated_nonidentity_advantage'])
    print('NAMED_PROBE')
    print(json.dumps(probes,indent=2))

if __name__=='__main__':main()
