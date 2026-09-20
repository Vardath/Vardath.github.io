#!/usr/bin/env python3
# Strict literal phoneme-reversal search with vertical-language follow-up.
# sensitivity sweep v1
# workflow-trigger: sensitivity-v3-500
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from pathlib import Path

import man_grid_exact_data as D
import man_grid_exact_engine as E

ROOT=Path(__file__).resolve().parents[1]
LINKED=ROOT/'data/three-way-linked-language-test-v1.json'
OUT=ROOT/'data/strict-literal-reverse-vertical-sensitivity-v1.json'
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'
NEG=20
PERMS=500
MIN_SHARED=250
STRICT_MAX=0.25
THRESHOLDS=[0.25,0.3333333333,0.40,0.50]
MIN_REVERSE_GAIN=0.15
PRIMARY=[E.FEATURES.index(f) for f in E.FEATURES if f in E.PRIMARY]

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-StrictReverseVertical/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8-sig')

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def bare(s):
    # Strip suprasegmental/secondary marks that should not turn the same core phone
    # into a different segment for the exact-symbol tier.
    s=unicodedata.normalize('NFD',canon(s))
    drop=set('ːˑˈˌʰʷʲˠˤ̥̬̹̜̟̠̩̯̃̈')
    return unicodedata.normalize('NFC',''.join(ch for ch in s if ch not in drop and not unicodedata.combining(ch)))

def signp(k,n):
    return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def mean(xs):return statistics.mean(xs) if xs else None

def main():
    _,params,_,_,cov=D.load_phoible()
    pids=sorted(params)
    alias={}; meta=[]
    for i,pid in enumerate(pids):
        p=params[pid]
        alias.setdefault(canon(p['name']),i)
        meta.append({'name':canon(p['name']),'bare':bare(p['name']),
                     'sig':tuple(round(p['features'][j],3) for j in PRIMARY)})

    linked=json.loads(LINKED.read_text(encoding='utf8'))
    wanted={}
    for direction in ('LR','RL','TB'):
        for x in linked['coverage']['eligible_members'][direction]:
            if x['iso']=='okm':continue
            wanted[x['iso']]={'iso':x['iso'],'name':x['name'],'direction':direction}

    lrows=list(csv.DictReader(io.StringIO(fetch('languages.csv'))))
    def normname(s):
        return ''.join(c for c in unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode('ascii').lower() if c.isalnum())
    aliases={'cym':['welsh'],'dan':['danish'],'fin':['finnish'],'heb':['hebrew'],'isl':['icelandic'],
             'kor':['korean'],'nob':['norwegianbokmal'],'nor':['norwegian'],'swe':['swedish']}
    resolved={}
    for iso,w in wanted.items():
        rr=None
        for r in lrows:
            vals=[str(v).strip().lower() for v in r.values() if v is not None]
            if iso.lower() in vals:rr=r;break
        if rr is None:
            targets={normname(w['name']),*(normname(z) for z in aliases.get(iso,[]))}
            rr=next((r for r in lrows if normname(r.get('Name','')) in targets),None)
        if rr:
            resolved[iso]={**w,'id':rr['ID'],'dataset_name':rr.get('Name') or w['name'],
                           'family':rr.get('Family') or 'Unknown'}

    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('Name') or r['ID'])
            for r in csv.DictReader(io.StringIO(fetch('parameters.csv')))}
    ids={x['id']:iso for iso,x in resolved.items()}
    forms={iso:{} for iso in resolved}
    for r in csv.DictReader(io.StringIO(fetch('forms.csv'))):
        lid=(r.get('Language_ID') or '').strip()
        if lid not in ids:continue
        con=(r.get('Parameter_ID') or '').strip()
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if not con or not toks or len(toks)>18:continue
        seq=[];ok=True
        for t in toks:
            j=alias.get(canon(t))
            if j is None:ok=False;break
            seq.append(j)
        if not ok:continue
        iso=ids[lid]
        cand=(len(seq),r.get('ID') or '',seq,(r.get('Form') or r.get('Value') or '').strip(),(r.get('Segments') or '').strip())
        if con not in forms[iso] or cand[:2]<forms[iso][con][:2]:forms[iso][con]=cand
    clean={iso:{c:{'seq':v[2],'form':v[3],'segments':v[4]} for c,v in fd.items()} for iso,fd in forms.items()}

    def subcost(a,b):
        A=meta[a];B=meta[b]
        if A['bare']==B['bare']:return 0.0
        if A['sig']==B['sig']:return 0.25
        return 1.0

    def edit(a,b):
        if not a or not b:return 1.0
        prev=[float(j) for j in range(len(b)+1)]
        for i,x in enumerate(a,1):
            cur=[float(i)]+[0.0]*len(b)
            for j,y in enumerate(b,1):
                cur[j]=min(prev[j]+1,cur[j-1]+1,prev[j-1]+subcost(x,y))
            prev=cur
        return prev[-1]/max(len(a),len(b))

    def score_pair(a,b):
        rev=edit(list(reversed(a)),b);direct=edit(a,b)
        return rev,direct

    lr=[i for i,x in resolved.items() if x['direction']=='LR']
    rl=[i for i,x in resolved.items() if x['direction']=='RL']
    tb=[i for i,x in resolved.items() if x['direction']=='TB']
    pairs=[]
    for a in lr:
      for b in rl:
        shared=sorted(set(clean[a])&set(clean[b]))
        if len(shared)<MIN_SHARED:continue
        rows=[]
        for c in shared:
            A=clean[a][c]['seq'];B=clean[b][c]['seq']
            rev,direct=score_pair(A,B)
            pool=[z for z in shared if z!=c and abs(len(clean[b][z]['seq'])-len(A))<=1]
            pool=sorted(pool,key=lambda z:(D.h64('strict-neg',a,b,c,z),z))[:NEG]
            ctr=[]
            for z in pool:
                rr,dd=score_pair(A,clean[b][z]['seq'])
                ctr.append({'d':rr,'gain':dd-rr,'lendiff':abs(len(A)-len(clean[b][z]['seq']))})
            rows.append({'concept_id':c,'concept':labels.get(c,c),
                         'reverse_distance':rev,'direct_distance':direct,'reverse_gain':direct-rev,
                         'length_difference':abs(len(A)-len(B)),
                         'a_form':clean[a][c]['form'],'a_segments':clean[a][c]['segments'],
                         'b_form':clean[b][c]['form'],'b_segments':clean[b][c]['segments'],
                         '_controls':ctr})
        pairs.append({'LR':a,'RL':b,'languages':[resolved[a]['dataset_name'],resolved[b]['dataset_name']],
                      'shared_concepts':len(rows),'_rows':rows})
    if not pairs:raise RuntimeError('No eligible horizontal pairs')
    sweeps=[]
    for threshold in THRESHOLDS:
        scored=[]
        for q in pairs:
            hits=0; expected=0.0
            for r in q['_rows']:
                hit=(r['reverse_distance']<=threshold and r['reverse_gain']>=MIN_REVERSE_GAIN and r['length_difference']<=1)
                r.setdefault('_hits',{})[str(threshold)]=hit
                ctr=r['_controls']
                rates=[1.0 if (z['d']<=threshold and z['gain']>=MIN_REVERSE_GAIN and z['lendiff']<=1) else 0.0 for z in ctr]
                r.setdefault('_ctrl_hit_vectors',{})[str(threshold)]=rates
                hits+=1 if hit else 0
                expected+=mean(rates) if rates else 0.0
            scored.append({'pair':q,'hits':hits,'expected':expected,'excess':hits-expected})
        scored.sort(key=lambda x:(x['excess'],x['hits']),reverse=True)
        best=scored[0]
        null_best=[]
        for p in range(PERMS):
            vals=[]
            for z in scored:
                fake=0.0
                for r in z['pair']['_rows']:
                    h=r['_ctrl_hit_vectors'][str(threshold)]
                    if h:fake+=h[D.h64('strict-sweep',threshold,p,z['pair']['LR'],r['concept_id'])%len(h)]
                vals.append(fake-z['expected'])
            null_best.append(max(vals))
        sp=(1+sum(x>=best['excess'] for x in null_best))/(PERMS+1)

        hitrows=[r for r in best['pair']['_rows'] if r['_hits'][str(threshold)]]
        hitids=[r['concept_id'] for r in hitrows]
        vertical=[]
        for kiso in tb:
            usable=[c for c in hitids if c in clean[kiso]]
            vrows=[]
            for c in usable:
                A=clean[best['pair']['LR']][c]['seq'];B=clean[best['pair']['RL']][c]['seq'];K=clean[kiso][c]['seq']
                true=min(edit(K,A),edit(list(reversed(K)),A),edit(K,B),edit(list(reversed(K)),B))
                pool=[z for z in clean[kiso] if z!=c and abs(len(clean[kiso][z]['seq'])-len(K))<=1]
                pool=sorted(pool,key=lambda z:(D.h64('strict-sweep-vert-neg',threshold,kiso,c,z),z))[:NEG]
                ctr=[]
                for z in pool:
                    Z=clean[kiso][z]['seq']
                    ctr.append(min(edit(Z,A),edit(list(reversed(Z)),A),edit(Z,B),edit(list(reversed(Z)),B)))
                vrows.append({'concept_id':c,'concept':labels.get(c,c),'distance':true,
                              'wrong_meaning_distance':mean(ctr) if ctr else 1.0,
                              'advantage':(mean(ctr)-true) if ctr else 0.0,
                              'strict_vertical_match':true<=threshold,
                              'vertical_form':clean[kiso][c]['form'],'vertical_segments':clean[kiso][c]['segments'],
                              '_ctr':ctr})
            if vrows:
                obs=mean([r['distance'] for r in vrows]);pn=[]
                for p in range(PERMS):
                    draws=[]
                    for r in vrows:
                        cvec=r['_ctr']
                        if cvec:draws.append(cvec[D.h64('strict-sweep-vert',threshold,p,kiso,r['concept_id'])%len(cvec)])
                    pn.append(mean(draws) if draws else 1.0)
                pp=(1+sum(x<=obs for x in pn))/(PERMS+1)
            else:pp=1.0
            for r in vrows:r.pop('_ctr',None)
            vertical.append({'language':resolved[kiso]['dataset_name'],'tested_hits':len(vrows),
                             'strict_vertical_matches':sum(r['strict_vertical_match'] for r in vrows),
                             'mean_advantage':mean([r['advantage'] for r in vrows]) if vrows else None,
                             'advantage_wins':sum(r['advantage']>0 for r in vrows),'permutation_p':pp,
                             'best_examples':sorted(vrows,key=lambda r:r['advantage'],reverse=True)[:20]})
        sweeps.append({'threshold':threshold,'min_reverse_gain':MIN_REVERSE_GAIN,
                       'best_pair':best['pair']['languages'],'shared_concepts':best['pair']['shared_concepts'],
                       'strict_hits':best['hits'],'control_expected_hits':best['expected'],'hit_excess':best['excess'],
                       'search_corrected_p':sp,
                       'examples':[{'concept':r['concept'],'ltr_form':r['a_form'],'ltr_segments':r['a_segments'],
                                    'rtl_form':r['b_form'],'rtl_segments':r['b_segments'],
                                    'reverse_distance':r['reverse_distance'],'reverse_gain':r['reverse_gain']}
                                   for r in sorted(hitrows,key=lambda r:(r['reverse_distance'],-r['reverse_gain']))[:40]],
                       'vertical_followup':vertical})

    # BH correction across the four threshold sensitivity checks.
    order=sorted(range(len(sweeps)),key=lambda i:sweeps[i]['search_corrected_p'])
    qvals=[1.0]*len(sweeps);running=1.0
    for rank,i in reversed(list(enumerate(order,1))):
        running=min(running,sweeps[i]['search_corrected_p']*len(sweeps)/rank)
        qvals[i]=running
    for i,q in enumerate(qvals):sweeps[i]['BH_q_across_thresholds']=q

    out={
      'version':1,'status':'complete',
      'test':'Strict literal reversal threshold sensitivity with vertical follow-up',
      'source':{'NorthEuraLex_commit':NE_SHA,'PHOIBLE_commit':D.PH},
      'question':'Does the literal same-meaning reversal result appear only at a particular strictness cutoff, or persist as the strict phone-edit threshold is relaxed?',
      'design':{
        'phone_equivalence':'Exact normalized phone costs 0; identical 11-primary-feature PHOIBLE class costs 0.25; all other substitutions and insert/delete cost 1.',
        'thresholds':THRESHOLDS,
        'min_reverse_gain':MIN_REVERSE_GAIN,
        'controls':f'Up to {NEG} length-matched wrong meanings per concept; {PERMS} search-corrected null universes at every threshold.',
        'multiple_threshold_control':'Benjamini-Hochberg q-values are reported across the four predeclared thresholds.',
        'vertical':'At each threshold, only horizontal hits passing that threshold are frozen before Korean is tested; Korean may be direct or reversed but receives no other transform.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'horizontal_pairs':len(pairs),'permutations':PERMS},
      'sweeps':sweeps
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
