#!/usr/bin/env python3
# Strict literal phoneme-reversal search with vertical-language follow-up.
# workflow-trigger: v1
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from pathlib import Path

import man_grid_exact_data as D
import man_grid_exact_engine as E

ROOT=Path(__file__).resolve().parents[1]
LINKED=ROOT/'data/three-way-linked-language-test-v1.json'
OUT=ROOT/'data/strict-literal-reverse-vertical-v1.json'
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'
NEG=20
PERMS=5000
MIN_SHARED=250
STRICT_MAX=0.25
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

    def strict_hit(a,b):
        rev=edit(list(reversed(a)),b);direct=edit(a,b)
        return rev,direct,(rev<=STRICT_MAX and direct-rev>=MIN_REVERSE_GAIN and abs(len(a)-len(b))<=1)

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
            rev,direct,hit=strict_hit(A,B)
            pool=[z for z in shared if z!=c and abs(len(clean[b][z]['seq'])-len(A))<=1]
            pool=sorted(pool,key=lambda z:(D.h64('strict-neg',a,b,c,z),z))[:NEG]
            ctr=[]
            for z in pool:
                rr,dd,hh=strict_hit(A,clean[b][z]['seq'])
                ctr.append({'d':rr,'hit':hh})
            null_hit=mean([1.0 if q['hit'] else 0.0 for q in ctr]) if ctr else 0.0
            rows.append({'concept_id':c,'concept':labels.get(c,c),
                         'reverse_distance':rev,'direct_distance':direct,'reverse_gain':direct-rev,
                         'strict_hit':hit,'control_hit_rate':null_hit,
                         'a_form':clean[a][c]['form'],'a_segments':clean[a][c]['segments'],
                         'b_form':clean[b][c]['form'],'b_segments':clean[b][c]['segments'],
                         '_control_hits':[q['hit'] for q in ctr]})
        hits=sum(r['strict_hit'] for r in rows);expected=sum(r['control_hit_rate'] for r in rows)
        pairs.append({'LR':a,'RL':b,'languages':[resolved[a]['dataset_name'],resolved[b]['dataset_name']],
                      'shared_concepts':len(rows),'strict_hits':hits,'control_expected_hits':expected,
                      'hit_excess':hits-expected,'_rows':rows})

    if not pairs:raise RuntimeError('No eligible horizontal pairs')
    pairs.sort(key=lambda q:(q['hit_excess'],q['strict_hits']),reverse=True)
    best=pairs[0]

    # Search-corrected null: one length-matched wrong meaning per concept, then choose the
    # best apparent LTR/RTL pair exactly as in the observed search.
    null_best=[]
    for p in range(PERMS):
        excesses=[]
        for q in pairs:
            fake=0
            for r in q['_rows']:
                h=r['_control_hits']
                if h:fake+=1 if h[D.h64('strict-perm',p,q['LR'],r['concept_id'])%len(h)] else 0
            expected=sum(r['control_hit_rate'] for r in q['_rows'])
            excesses.append(fake-expected)
        null_best.append(max(excesses))
    search_p=(1+sum(x>=best['hit_excess'] for x in null_best))/(PERMS+1)

    # Freeze strict hits from winning horizontal pair before Korean lookup.
    frozen=[r for r in best['_rows'] if r['strict_hit']]
    frozen_ids=[r['concept_id'] for r in frozen]

    vertical=[]
    for kiso in tb:
        usable=[c for c in frozen_ids if c in clean[kiso]]
        rows=[]
        for c in usable:
            A=clean[best['LR']][c]['seq']
            B=clean[best['RL']][c]['seq']
            K=clean[kiso][c]['seq']
            # The horizontal core can be represented in either direction; the vertical word
            # is allowed top->bottom or bottom->top. No other transform is permitted.
            true=min(edit(K,A),edit(list(reversed(K)),A),edit(K,B),edit(list(reversed(K)),B))
            pool=[z for z in clean[kiso] if z!=c and abs(len(clean[kiso][z]['seq'])-len(K))<=1]
            pool=sorted(pool,key=lambda z:(D.h64('strict-vert-neg',kiso,c,z),z))[:NEG]
            ctr=[]
            for z in pool:
                Z=clean[kiso][z]['seq']
                ctr.append(min(edit(Z,A),edit(list(reversed(Z)),A),edit(Z,B),edit(list(reversed(Z)),B)))
            null=mean(ctr) if ctr else 1.0
            rows.append({'concept_id':c,'concept':labels.get(c,c),'vertical_best_distance':true,
                         'wrong_meaning_distance':null,'vertical_advantage':null-true,
                         'vertical_strict_match':true<=STRICT_MAX,
                         'vertical_form':clean[kiso][c]['form'],'vertical_segments':clean[kiso][c]['segments'],
                         '_controls':ctr})
        wins=sum(r['vertical_advantage']>0 for r in rows)
        strict=sum(r['vertical_strict_match'] for r in rows)
        # Permutation from precomputed matched controls.
        pn=[]
        for p in range(PERMS):
            vals=[]
            for r in rows:
                ctr=r['_controls']
                if ctr:vals.append(ctr[D.h64('strict-vert-perm',p,kiso,r['concept_id'])%len(ctr)])
            pn.append(mean(vals) if vals else 1.0)
        obs=mean([r['vertical_best_distance'] for r in rows]) if rows else 1.0
        pp=(1+sum(x<=obs for x in pn))/(PERMS+1)
        vertical.append({'TB':kiso,'language':resolved[kiso]['dataset_name'],
                         'tested_horizontal_strict_hits':len(rows),'vertical_strict_matches':strict,
                         'mean_vertical_advantage':mean([r['vertical_advantage'] for r in rows]) if rows else None,
                         'advantage_wins':wins,'sign_p':signp(wins,len(rows)) if rows else 1.0,
                         'permutation_p':pp,'_rows':rows})

    # Clean private controls and expose strongest examples.
    for q in pairs:
        raw=q.pop('_rows')
        for r in raw:r.pop('_control_hits',None)
        q['strict_examples']=[r for r in raw if r['strict_hit']]
    selected=pairs[0]
    selected['search_corrected_p']=search_p
    selected['strict_threshold']={'max_normalized_edit':STRICT_MAX,'min_reverse_gain':MIN_REVERSE_GAIN,'max_length_difference':1}
    for q in vertical:
        raw=q.pop('_rows')
        for r in raw:r.pop('_controls',None)
        q['best_examples']=sorted(raw,key=lambda r:r['vertical_advantage'],reverse=True)[:30]

    out={
      'version':1,'status':'complete',
      'test':'Strict literal same-meaning phone reversal with vertical follow-up',
      'source':{'NorthEuraLex_commit':NE_SHA,'PHOIBLE_commit':D.PH},
      'question':'Do same-meaning LTR and RTL words preserve nearly the same phone skeleton in literal reverse order, and do the same concepts also match in Korean under either vertical direction?',
      'design':{
        'phone_equivalence':'Exact normalized phone = cost 0. Phones with identical 11 primary PHOIBLE place/manner feature signatures = cost 0.25. Any other substitution = cost 1. Insert/delete = cost 1.',
        'strict_reversal':f'Reversed LTR vs RTL normalized edit distance <= {STRICT_MAX}, reversal must improve on direct order by >= {MIN_REVERSE_GAIN}, and word lengths may differ by at most one phone.',
        'semantic_controls':f'Each same-meaning comparison uses up to {NEG} length-matched wrong RTL meanings.',
        'search_correction':f'{PERMS} null universes repeat the best-LTR-language search using the same controls.',
        'vertical':'Only concepts that pass the strict horizontal reversal rule are frozen. Korean may be read top->bottom or bottom->top and compared with either horizontal orientation; no reflection/rotation or learned transform is allowed.',
        'vertical_controls':f'Korean same-meaning forms are compared with up to {NEG} length-matched wrong Korean meanings and {PERMS} null draws.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'resolved_languages':resolved,'horizontal_pairs':len(pairs),'permutations':PERMS},
      'horizontal_ranking':pairs,
      'selected_horizontal_pair':selected,
      'vertical_followup':vertical,
      'support_rule':'A three-way result requires search-corrected horizontal p<0.05 plus vertical permutation p<0.05 on the frozen strict reversal concepts.'
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'selected_horizontal_pair':selected,'vertical_followup':vertical},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
