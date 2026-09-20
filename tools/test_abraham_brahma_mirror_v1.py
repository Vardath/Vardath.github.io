#!/usr/bin/env python3
# workflow-trigger: v2-100k
# Focused Abraham/Brahma/Bharata/Mahabharata mirror test against empirical phonetic nulls.
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path

import man_grid_exact_data as D
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/abraham-brahma-mirror-test-v1.json'
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'
K=24
NULLS=100000
OPS=['reverse','reflect_x','reflect_y','rotate180','reverse_reflect_x','reverse_reflect_y','reverse_rotate180']

CANDIDATES=[
 {'a':'Abraham','b':'Brahma','a_ipa':'/ʔabraːhaːm/','b_ipa':'/bɾɐɦmɑː/',
  'a_tokens':['ʔ','a','b','r','aː','h','aː','m'],
  'b_tokens':['b','ɾ','ɐ','ɦ','m','ɑː'],
  'semantic_relation':'broad creator/progenitor association, not lexical synonymy'},
 {'a':'Abraham','b':'Brahman','a_ipa':'/ʔabraːhaːm/','b_ipa':'/bɾɐɦmɐn̪/',
  'a_tokens':['ʔ','a','b','r','aː','h','aː','m'],
  'b_tokens':['b','ɾ','ɐ','ɦ','m','ɐ','n̪'],
  'semantic_relation':'broad origin/expansion/progenitor association, not lexical synonymy'},
 {'a':'Abraham','b':'Bharata','a_ipa':'/ʔabraːhaːm/','b_ipa':'/bʱɐɾɐt̪ɐ/',
  'a_tokens':['ʔ','a','b','r','aː','h','aː','m'],
  'b_tokens':['bʱ','ɐ','ɾ','ɐ','t̪','ɐ'],
  'semantic_relation':'no established same meaning; included because user recalled a Bharata/Mahabharata-like form'},
 {'a':'Abraham','b':'Mahabharata','a_ipa':'/ʔabraːhaːm/','b_ipa':'/mɐɦɑːbʱɑːɾɐt̪ɐ/',
  'a_tokens':['ʔ','a','b','r','aː','h','aː','m'],
  'b_tokens':['m','ɐ','ɦ','ɑː','bʱ','ɑː','ɾ','ɐ','t̪','ɐ'],
  'semantic_relation':'no established same meaning; included as the likely Mahabharata/Maharata recollection'}
]

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-AbrahamBrahmaMirror/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8-sig')

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def base(s):
    s=canon(s).replace('ː','')
    return ''.join(ch for ch in unicodedata.normalize('NFD',s) if not unicodedata.combining(ch))

def resample(points,k=K):
    if not points:return ()
    if len(points)==1:return tuple(points[0] for _ in range(k))
    out=[]
    for j in range(k):
        u=j*(len(points)-1)/(k-1)
        i=min(len(points)-2,int(u));f=u-i
        a,b=points[i],points[i+1]
        out.append((a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f))
    return tuple(out)

def transform(path,op):
    q=path
    if op.startswith('reverse'):q=tuple(reversed(q))
    if 'reflect_x' in op:q=tuple((1-x,y) for x,y in q)
    elif 'reflect_y' in op:q=tuple((x,1-y) for x,y in q)
    elif 'rotate180' in op:q=tuple((1-x,1-y) for x,y in q)
    return q

def dist(a,b):
    return sum(math.hypot(x[0]-y[0],x[1]-y[1]) for x,y in zip(a,b))/len(a)

def best_mirror(a,b):
    vals=[(dist(transform(a,op),b),op) for op in OPS]
    return min(vals)

def build_phonetics():
    _,params,_,_,cov=D.load_phoible();P=FB.fit(params)
    coords=[];alias={};bybase=defaultdict(list)
    for pid in sorted(params):
        p=params[pid];idx=len(coords);coords.append(FB.project(p['features'],P))
        n=canon(p['name']);alias.setdefault(n,idx);bybase[base(n)].append(idx)
    def idx(tok):
        n=canon(tok)
        if n in alias:return alias[n]
        b=base(n)
        if b in bybase:return bybase[b][0]
        # simple source-normalization fallbacks
        fall={'r':'ɾ','h':'ɦ','n̪':'n','t̪':'t','bʱ':'b','ɑ':'a','ɐ':'a'}
        if n in fall:
            z=canon(fall[n])
            if z in alias:return alias[z]
            bz=base(z)
            if bz in bybase:return bybase[bz][0]
        raise KeyError(f'No PHOIBLE mapping for {tok!r}')
    return coords,idx,cov

def load_null_pool(coords,idx):
    langs={r['ID']:{'name':r['Name'],'family':r.get('Family') or 'Unknown'} for r in csv.DictReader(io.StringIO(fetch('languages.csv')))}
    pool=[]
    for r in csv.DictReader(io.StringIO(fetch('forms.csv'))):
        lid=(r.get('Language_ID') or '').strip();con=(r.get('Parameter_ID') or '').strip()
        if lid not in langs or not con or langs[lid]['family'] in ('Unknown','Unclassified',''):continue
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if len(toks)<3 or len(toks)>12:continue
        seq=[];ok=True
        for t in toks:
            try:seq.append(idx(t))
            except KeyError:ok=False;break
        if not ok:continue
        path=resample([coords[j] for j in seq])
        pool.append({'lid':lid,'family':langs[lid]['family'],'concept':con,'len':len(seq),'path':path})
    return pool

def deterministic_null(pool,la,lb,tag):
    A=[x for x in pool if abs(x['len']-la)<=1]
    B=[x for x in pool if abs(x['len']-lb)<=1]
    if not A or not B:raise RuntimeError('empty null stratum')
    vals=[];rows=[]
    for k in range(NULLS):
        # independent deterministic selection, rejecting same-family/same-concept pairs
        ia=D.h64('abb-null-a',tag,k)%len(A)
        ib=D.h64('abb-null-b',tag,k)%len(B)
        a=A[ia];b=B[ib]
        tries=0
        while (a['family']==b['family'] or a['concept']==b['concept']) and tries<50:
            ib=(ib+1+D.h64('abb-null-step',tag,k,tries)%max(1,len(B)-1))%len(B)
            b=B[ib];tries+=1
        if a['family']==b['family'] or a['concept']==b['concept']:continue
        d,op=best_mirror(a['path'],b['path']);vals.append(d)
        if len(rows)<20:rows.append({'distance':d,'operator':op,'len_a':a['len'],'len_b':b['len']})
    return vals,rows

def main():
    coords,idx,cov=build_phonetics();pool=load_null_pool(coords,idx)
    results=[]
    null_sets=[]
    for c in CANDIDATES:
        pa=resample([coords[idx(t)] for t in c['a_tokens']])
        pb=resample([coords[idx(t)] for t in c['b_tokens']])
        direct=dist(pa,pb);md,op=best_mirror(pa,pb)
        null,_=deterministic_null(pool,len(c['a_tokens']),len(c['b_tokens']),c['b'])
        p=(1+sum(x<=md for x in null))/(len(null)+1)
        pct=sum(x<=md for x in null)/len(null)
        results.append({**{k:v for k,v in c.items() if k not in ('a_tokens','b_tokens')},
                        'phone_lengths':[len(c['a_tokens']),len(c['b_tokens'])],
                        'direct_distance':direct,'best_mirror_distance':md,'best_mirror_operator':op,
                        'mirror_gain_vs_direct':direct-md,'matched_length_null_n':len(null),
                        'null_mean_best_mirror_distance':statistics.mean(null),
                        'null_median_best_mirror_distance':statistics.median(null),
                        'individual_empirical_p':p,'null_fraction_as_close_or_closer':pct})
        null_sets.append(null)
    results.sort(key=lambda x:x['best_mirror_distance'])
    best=results[0]
    best_index=next(i for i,c in enumerate(CANDIDATES) if c['b']==best['b'])
    # Family-wise correction for looking at all four remembered candidates:
    # each null universe contributes the best (smallest) matched-length mirror distance across all four strata.
    n=min(map(len,null_sets));minnull=[min(ns[j] for ns in null_sets) for j in range(n)]
    family_p=(1+sum(x<=best['best_mirror_distance'] for x in minnull))/(n+1)

    out={
      'version':1,'status':'complete','test':'Abraham/Brahma/Bharata/Mahabharata focused mirror test',
      'question':'Are the recalled Abraham/Brahma/Bharata/Mahabharata sound correspondences unusually close under the previously defined phonetic mirror operations?',
      'sources':{
        'Abraham':'Biblical Hebrew /ʔabraːhaːm/ (Wiktionary)',
        'Brahma':'Classical Sanskrit /bɾɐɦ.mɑː/ (Wiktionary/Kaikki)',
        'Brahman':'Classical Sanskrit /bɾɐɦ.mɐn̪/ (Wiktionary)',
        'Bharata':'Classical Sanskrit /bʱɐ.ɾɐ.t̪ɐ/ (Wiktionary)',
        'Mahabharata':'Classical Sanskrit /mɐ.ɦɑː.bʱɑː.ɾɐ.t̪ɐ/ (Wiktionary)',
        'empirical_null':f'NorthEuraLex {NE_SHA}, PHOIBLE {D.PH}'},
      'design':{
        'candidate_freeze':'All four candidate pronunciations and all seven mirror operators are fixed before scoring.',
        'operators':OPS,
        'distance':'Pronunciations are mapped to the frozen PHOIBLE continuous phonetic field, resampled to 24 rank positions, and compared by mean Euclidean path distance.',
        'operation_search_control':'Every null pair receives the same privilege as the candidate: its score is the best of all seven non-identity mirror operations.',
        'null':f'For each candidate, {NULLS} NorthEuraLex word pairs from different language families and different meanings are sampled with each word length matched to within ±1 phones.',
        'multiple_candidate_control':'The overall p-value compares the best of the four recalled candidates with the best of four matched null strata in each null universe.',
        'semantic_boundary':'The statistics test phonetic/mirror unusualness only. Historical or semantic relatedness is not inferred from phonetic closeness.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'north_euralex_mapped_pool':len(pool),'nulls_per_candidate':NULLS,'candidate_pairs':len(CANDIDATES)},
      'results':results,
      'best_recalled_candidate':best,
      'familywise_best_of_four_empirical_p':family_p,
      'interpretation_rule':{
        'strong':'Family-wise p<0.05 would mean at least one recalled candidate is unusually mirror-close compared with length-matched unrelated cross-family word pairs, after controlling both mirror-operation and four-candidate search.',
        'weak':'An individual p<0.05 but family-wise p>=0.05 is a candidate-specific lead that does not survive the four-pair search correction.',
        'negative':'Family-wise p>=0.05 means the remembered resemblance is not unusual enough under this phonetic mirror metric to distinguish it from chance cross-family word pairs.'
      }
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
