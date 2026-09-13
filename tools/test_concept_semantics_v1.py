#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,io,json,math,statistics,unicodedata,urllib.request
from collections import defaultdict
from pathlib import Path
import man_grid_exact_data as D
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/concept-semantics-v1-work'
PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data/concept-semantics-v1.json'
SHARDS=20
PRIMARY_KM=2000
SENS_KM=[1000,2000,3000]
NREF=5
NEG=15
GRID=20
MIN_CASES=25
MIN_FAMILIES=8
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-ConceptSemantics/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:
        return r.read().decode('utf-8-sig')

def dumpgz(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(x,f,separators=(',',':'))

def loadgz(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def truthy(s):
    return str(s or '').strip().lower() in {'1','true','t','yes','y'}

def signp(k,n):
    return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def hav(lat1,lon1,lat2,lon2):
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371.0088*2*math.asin(min(1.0,math.sqrt(a)))

def avgagg(a):
    n=a.get('cases',0)
    return {k:(v/n if k!='cases' and n else v) for k,v in a.items()}

def addagg(a,m):
    a['cases']+=1
    for k,v in m.items():a[k]+=v

def agg():
    return {'cases':0,'auc_real':0.0,'auc_label':0.0,'auc_random':0.0,'auc_raw':0.0,
            'top1_real':0.0,'top1_label':0.0,'top1_random':0.0,'top1_raw':0.0}

def prepare():
    _,params,_,_,cov=D.load_phoible()
    P=FB.fit(params)
    phones=[];alias={}
    for pid in sorted(params):
        p=params[pid];idx=len(phones)
        phones.append({'pid':pid,'name':p['name'],'c':FB.project(p['features'],P)})
        alias.setdefault(canon(p['name']),idx)

    lrows=list(csv.DictReader(io.StringIO(fetch('languages.csv'))))
    langs={}
    for r in lrows:
        try:lat=float(r['Latitude']);lon=float(r['Longitude'])
        except Exception:continue
        langs[r['ID']]={'id':r['ID'],'name':r['Name'],'family':(r.get('Family') or 'Unknown').strip(),
                        'subfamily':(r.get('Subfamily') or '').strip(),'lat':lat,'lon':lon}
    prows=list(csv.DictReader(io.StringIO(fetch('parameters.csv'))))
    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('NorthEuralex_Gloss') or r.get('Name') or r['ID']) for r in prows}

    raw=list(csv.DictReader(io.StringIO(fetch('forms.csv'))))
    counts={'raw_forms':0,'loan_forms_removed':0,'unmapped_forms':0,'mapped_nonloan_forms':0}
    best={}
    for r in raw:
        counts['raw_forms']+=1
        lid=(r.get('Language_ID') or '').strip();con=(r.get('Parameter_ID') or '').strip()
        if lid not in langs or not con:continue
        if truthy(r.get('Loan')):
            counts['loan_forms_removed']+=1;continue
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if not toks or len(toks)>15:
            counts['unmapped_forms']+=1;continue
        seq=[];ok=True
        for t in toks:
            q=alias.get(canon(t))
            if q is None:ok=False;break
            seq.append(q)
        if not ok:
            counts['unmapped_forms']+=1;continue
        counts['mapped_nonloan_forms']+=1
        cog=(r.get('Cognacy') or '').strip()
        key=(lid,con);cand=(len(seq),r.get('ID') or '',seq,cog)
        if key not in best or cand[:2]<best[key][:2]:best[key]=cand

    forms=defaultdict(dict)
    for (lid,con),(_,_,seq,cog) in best.items():
        forms[lid][con]={'seq':seq,'cog':cog}
    langs={k:v for k,v in langs.items() if k in forms and len(forms[k])>=200}
    forms={k:forms[k] for k in langs}
    concepts=sorted({c for d in forms.values() for c in d})
    counts.update({'languages':len(langs),'concepts':len(concepts),
                   'canonical_nonloan_forms':sum(len(v) for v in forms.values())})

    plan={}
    lids=sorted(langs)
    for lid in lids:
        L=langs[lid];fc=set(forms[lid]);by_t={}
        for th in SENS_KM:
            fam_best={}
            for z in lids:
                if z==lid or langs[z]['family']==L['family']:continue
                dz=hav(L['lat'],L['lon'],langs[z]['lat'],langs[z]['lon'])
                if dz < th:continue
                ov=len(fc & set(forms[z]));fam=langs[z]['family']
                key=(-ov,D.h64('concept-ref-lang',th,lid,z),z)
                if fam not in fam_best or key<fam_best[fam]:fam_best[fam]=key
            refs=[q[-1] for q in sorted(fam_best.values())[:NREF]]
            by_t[str(th)]=refs
        plan[lid]=by_t

    order=sorted(concepts,key=lambda c:(D.h64('concept-shard-order',c),c))
    concept_shard={c:i%SHARDS for i,c in enumerate(order)}
    shard_sizes=[sum(1 for c in concepts if concept_shard[c]==i) for i in range(SHARDS)]

    x={'version':1,'source':{'phoible_commit':D.PH,'northeuralex_commit':NE_SHA},
       'phoible_coverage':cov,'phones':phones,'languages':langs,'forms':forms,
       'concept_labels':labels,'concepts':concepts,'plan':plan,'concept_shard':concept_shard,
       'shard_sizes':shard_sizes,'counts':counts,
       'protocol':{
           'question':'Which individual concepts retain cross-family sound->meaning signal after explicit ancestry/loan/contact controls?',
           'primary_grid':'20x20, fixed from the prior pooled family-blocked run; no per-concept grid selection is allowed in the primary test.',
           'target_family_control':'All reference languages must belong to families different from the target family.',
           'loan_control':'NorthEuraLex forms with Loan=true are removed before canonical-form selection.',
           'cognacy_control':'For the true concept, reference forms sharing the non-empty NorthEuraLex Cognacy label with the target form are removed.',
           'geography_control':f'Primary comparisons require reference languages at least {PRIMARY_KM} km from the target; pooled sensitivity checks use {SENS_KM} km.',
           'reference_plan':f'Up to {NREF} reference languages from distinct unrelated families are chosen without using phonetic similarity, one per family, by whole-lexicon concept overlap and deterministic hash ties.',
           'task':f'For each target word, rank its true concept against {NEG} deterministic wrong concepts. Every candidate must have >=2 eligible reference forms.',
           'controls':'Pseudo-positive meaning-label null, same-capacity random segment-to-cell geometry, and raw segment-identity edit distance.',
           'concept_statistics':f'Aggregate cases by target family. A concept is eligible with >= {MIN_CASES} cases across >= {MIN_FAMILIES} target families. One-sided family sign tests are FDR-corrected across all eligible concepts.',
           'semantic_support':'Positive real-grid AUC minus pseudo-label AUC with BH-FDR q<0.05.',
           'geometry_support':'Positive real-grid AUC minus random-cell AUC with BH-FDR q<0.05.',
           'boundary':'Distance filtering reduces nearby contact but cannot prove the absence of ancient contact, unflagged borrowing, or convergent sound symbolism.'
       }}
    dumpgz(PREP,x);print(json.dumps(counts,indent=2));print({'shard_sizes':shard_sizes})

def qlookup(phones,n,random=False):
    out=[]
    for p in phones:
        if random:
            z=D.h64('concept-random-cell',n,p['pid'])%(n*n);out.append((z//n,z%n))
        else:
            x,y=p['c'];out.append((min(n-1,int(x*n)),min(n-1,int(y*n))))
    return out

def edit(a,b,lookup=None,n=None,raw=False):
    if not a or not b:return 1.0
    prev=list(range(len(b)+1));den=2*max(1,(n or 2)-1)
    for i,x in enumerate(a,1):
        cur=[i]+[0]*len(b)
        for j,y in enumerate(b,1):
            if x==y:sub=0.0
            elif raw:sub=1.0
            else:
                X,Y=lookup[x],lookup[y];sub=(abs(X[0]-Y[0])+abs(X[1]-Y[1]))/den
            cur[j]=min(prev[j]+1.0,cur[j-1]+1.0,prev[j-1]+sub)
        prev=cur
    return prev[-1]/max(len(a),len(b))

def metrics(ds,pos):
    p=ds[pos];others=[d for i,d in enumerate(ds) if i!=pos]
    lt=sum(d<p-1e-12 for d in others);eq=sum(abs(d-p)<=1e-12 for d in others)
    auc=sum(1.0 if p<d-1e-12 else .5 if abs(p-d)<=1e-12 else 0.0 for d in others)/len(others)
    top=0.0 if lt else 1.0/(eq+1)
    return auc,top

def pool_for(x,lid,th,cache):
    key=(lid,th)
    if key in cache:return cache[key]
    out=defaultdict(list)
    for r in x['plan'][lid][str(th)]:
        for c,f in x['forms'].get(r,{}).items():out[c].append(f)
    cache[key]=dict(out);return cache[key]

def make_case(x,lid,concept,th,cache):
    target=x['forms'].get(lid,{}).get(concept)
    if not target:return None
    pool=pool_for(x,lid,th,cache)
    if concept not in pool:return None
    tcog=target.get('cog') or ''
    true_refs=[f['seq'] for f in pool[concept] if not (tcog and f.get('cog') and f['cog']==tcog)]
    if len(true_refs)<2:return None
    avail=[c for c,fs in pool.items() if c!=concept and len(fs)>=2]
    neg=sorted(avail,key=lambda c:(D.h64('concept-neg',th,lid,concept,c),c))[:NEG]
    if len(neg)<NEG:return None
    candidates=[true_refs]+[[f['seq'] for f in pool[c]] for c in neg]
    pseudo=1+(D.h64('concept-pseudo',th,lid,concept)%NEG)
    return target['seq'],candidates,pseudo

def eval_case(case,real_lookup,random_lookup):
    tgt,cands,pseudo=case
    dr=[min(edit(tgt,z,real_lookup,GRID,False) for z in zs) for zs in cands]
    dn=[min(edit(tgt,z,random_lookup,GRID,False) for z in zs) for zs in cands]
    di=[min(edit(tgt,z,None,None,True) for z in zs) for zs in cands]
    ar,tr=metrics(dr,0);al,tl=metrics(dr,pseudo);an,tn=metrics(dn,0);ai,ti=metrics(di,0)
    return {'auc_real':ar,'auc_label':al,'auc_random':an,'auc_raw':ai,
            'top1_real':tr,'top1_label':tl,'top1_random':tn,'top1_raw':ti}

def concept_row(label,cases_by_family):
    total=agg();famrows=[]
    for fam,a in sorted(cases_by_family.items()):
        aa=avgagg(a);famrows.append((fam,aa));total['cases']+=a['cases']
        for k in total:
            if k!='cases':total[k]+=a[k]
    overall=avgagg(total);sem=[];geo=[]
    for fam,a in famrows:
        ds=a['auc_real']-a['auc_label'];dg=a['auc_real']-a['auc_random']
        if abs(ds)>1e-12:sem.append(ds)
        if abs(dg)>1e-12:geo.append(dg)
    eligible=overall['cases']>=MIN_CASES and len(famrows)>=MIN_FAMILIES
    sw=sum(d>0 for d in sem);gw=sum(d>0 for d in geo)
    return {'label':label,'cases':overall['cases'],'target_families':len(famrows),'metrics':overall,
            'semantic_auc_advantage':overall.get('auc_real',0)-overall.get('auc_label',0),
            'geometry_auc_advantage':overall.get('auc_real',0)-overall.get('auc_random',0),
            'raw_vs_real_auc':overall.get('auc_real',0)-overall.get('auc_raw',0),
            'semantic_family_wins':sw,'semantic_family_nonzero':len(sem),'semantic_p':signp(sw,len(sem)),
            'geometry_family_wins':gw,'geometry_family_nonzero':len(geo),'geometry_p':signp(gw,len(geo)),
            'eligible':eligible}

def shard(i):
    x=loadgz(PREP);concepts=[c for c in x['concepts'] if x['concept_shard'][c]==i]
    if not concepts:raise SystemExit(f'empty shard {i}')
    real=qlookup(x['phones'],GRID,False);rand=qlookup(x['phones'],GRID,True)
    cache={};rows={};sens={str(t):agg() for t in SENS_KM}
    for c in concepts:
        byfam=defaultdict(agg)
        for lid,L in x['languages'].items():
            case=make_case(x,lid,c,PRIMARY_KM,cache)
            if case:
                m=eval_case(case,real,rand);addagg(byfam[L['family']],m);addagg(sens[str(PRIMARY_KM)],m)
            for th in SENS_KM:
                if th==PRIMARY_KM:continue
                q=make_case(x,lid,c,th,cache)
                if q:addagg(sens[str(th)],eval_case(q,real,rand))
        rows[c]=concept_row(x['concept_labels'].get(c,c),byfam)
    out={'shard':i,'concept_count':len(concepts),'concepts':rows,'sensitivity':sens}
    WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02}.json').write_text(json.dumps(out,separators=(',',':')))
    print({'shard':i,'concepts':len(concepts),'eligible':sum(r['eligible'] for r in rows.values()),'primary_cases':sens[str(PRIMARY_KM)]['cases']})

def bh(rows,pkey,qkey):
    eligible=[(r[pkey],c,r) for c,r in rows.items() if r['eligible']]
    eligible.sort(key=lambda x:x[0]);m=len(eligible);qs=[1.0]*m;prev=1.0
    for j in range(m-1,-1,-1):
        p,_,_=eligible[j];q=min(prev,p*m/(j+1));qs[j]=q;prev=q
    for (_,c,r),q in zip(eligible,qs):r[qkey]=min(1.0,q)
    for c,r in rows.items():
        if not r['eligible']:r[qkey]=None

def merge():
    x=loadgz(PREP);ss=[json.loads((WORK/f'result-{i:02}.json').read_text()) for i in range(SHARDS)]
    if any(s['concept_count']<=0 for s in ss):raise SystemExit('empty concept shard')
    rows={};sensitivity={str(t):agg() for t in SENS_KM}
    for s in ss:
        for c,r in s['concepts'].items():
            if c in rows:raise SystemExit(f'duplicate concept {c}')
            rows[c]=r
        for th,a in s['sensitivity'].items():
            for k,v in a.items():sensitivity[th][k]+=v
    if set(rows)!=set(x['concepts']):raise SystemExit('concept coverage mismatch')
    bh(rows,'semantic_p','semantic_q');bh(rows,'geometry_p','geometry_q')
    for r in rows.values():
        r['semantic_supported_fdr']=bool(r['eligible'] and r['semantic_auc_advantage']>0 and r['semantic_q'] is not None and r['semantic_q']<.05)
        r['geometry_supported_fdr']=bool(r['eligible'] and r['geometry_auc_advantage']>0 and r['geometry_q'] is not None and r['geometry_q']<.05)
        r['both_supported_fdr']=r['semantic_supported_fdr'] and r['geometry_supported_fdr']
    eligible=[(c,r) for c,r in rows.items() if r['eligible']]
    pos=sum(r['semantic_auc_advantage']>0 for _,r in eligible);widespread_p=signp(pos,len(eligible))
    sem_supported=[(c,r) for c,r in eligible if r['semantic_supported_fdr']]
    geo_supported=[(c,r) for c,r in eligible if r['geometry_supported_fdr']]
    both=[(c,r) for c,r in eligible if r['both_supported_fdr']]
    top=sorted(eligible,key=lambda q:(-q[1]['semantic_auc_advantage'],-q[1]['metrics']['auc_real'],q[0]))[:30]
    bottom=sorted(eligible,key=lambda q:(q[1]['semantic_auc_advantage'],q[1]['metrics']['auc_real'],q[0]))[:30]
    top_supported=sorted(sem_supported,key=lambda q:(q[1]['semantic_q'],-q[1]['semantic_auc_advantage'],q[0]))[:50]
    sens={th:avgagg(a) for th,a in sensitivity.items()}
    out={'version':1,'status':'complete','test':'concept-by-concept residual sound -> meaning after family/loan/cognacy/geography controls',
         'source':x['source'],'counts':x['counts'],'shards':SHARDS,'shard_sizes':x['shard_sizes'],
         'primary_grid':GRID,'primary_distance_km':PRIMARY_KM,'sensitivity_distance_km':SENS_KM,
         'eligibility':{'min_cases':MIN_CASES,'min_target_families':MIN_FAMILIES},'protocol':x['protocol'],
         'summary':{'concepts_total':len(rows),'concepts_eligible':len(eligible),'eligible_positive_semantic_advantage':pos,
             'eligible_positive_fraction':pos/len(eligible) if eligible else None,'eligible_positive_sign_p':widespread_p,
             'semantic_supported_fdr':len(sem_supported),'geometry_supported_fdr':len(geo_supported),
             'both_semantic_and_geometry_supported_fdr':len(both),'sensitivity_pooled':sens,
             'top_semantic_advantage':[{'concept_id':c,**r} for c,r in top],
             'bottom_semantic_advantage':[{'concept_id':c,**r} for c,r in bottom],
             'strongest_fdr_supported':[{'concept_id':c,**r} for c,r in top_supported]},
         'concepts':rows,
         'interpretation_boundary':'A supported concept shows reproducible cross-family pronunciation/concept association after the explicit filters used here. It does not establish innate meaning, universal sound symbolism, or absence of ancient contact/unflagged borrowing.'}
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False))
    print(json.dumps({k:out['summary'][k] for k in ['concepts_total','concepts_eligible','eligible_positive_semantic_advantage','eligible_positive_fraction','eligible_positive_sign_p','semantic_supported_fdr','geometry_supported_fdr','both_semantic_and_geometry_supported_fdr']},indent=2))
    print('TOP',[(z['label'],round(z['semantic_auc_advantage'],4),z['semantic_q']) for z in out['summary']['strongest_fdr_supported'][:20]])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('cmd',choices=['prepare','shard','merge']);ap.add_argument('--id',type=int);a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='shard':
        if a.id is None or not (0<=a.id<SHARDS):raise SystemExit('--id 0..19 required')
        shard(a.id)
    else:merge()

if __name__=='__main__':main()
