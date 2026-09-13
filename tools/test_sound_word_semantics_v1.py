#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,io,json,math,statistics,unicodedata,urllib.request
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E, man_grid_exact_data as D
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/sound-word-semantics-v1-work'
PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data/sound-word-semantics-v1.json'
SHARDS=20
RES=list(range(3,24))
CAND=list(range(3,22))
BOUND=[22,23]
NEG=15
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-SoundWordSemantics/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8-sig')
def dumpgz(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(x,f,separators=(',',':'))
def loadgz(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)
def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)
def signp(k,n):return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def prepare():
    _,params,_,_,cov=D.load_phoible();P=FB.fit(params)
    phones=[];alias={}
    for pid in sorted(params):
        p=params[pid];idx=len(phones);phones.append({'pid':pid,'name':p['name'],'c':FB.project(p['features'],P)})
        alias.setdefault(canon(p['name']),idx)
    lang_rows=list(csv.DictReader(io.StringIO(fetch('languages.csv'))))
    langs={r['ID']:{'id':r['ID'],'name':r['Name'],'family':r.get('Family') or 'Unknown','subfamily':r.get('Subfamily') or ''} for r in lang_rows}
    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('Name') or r['ID']) for r in csv.DictReader(io.StringIO(fetch('parameters.csv')))}
    raw=list(csv.DictReader(io.StringIO(fetch('forms.csv')))); token_total=token_mapped=forms_total=0
    best={}; mapped_forms=0
    for r in raw:
        lid,con=(r.get('Language_ID') or '').strip(),(r.get('Parameter_ID') or '').strip()
        if lid not in langs or not con:continue
        toks=[x for x in (r.get('Segments') or '').split() if x];forms_total+=1;token_total+=len(toks)
        if not toks or len(toks)>15:continue
        seq=[];ok=True
        for t in toks:
            q=alias.get(canon(t));token_mapped+=int(q is not None)
            if q is None:ok=False;break
            seq.append(q)
        if not ok:continue
        mapped_forms+=1;key=(lid,con);cand=(len(seq),r.get('ID') or '',seq)
        if key not in best or cand[:2]<best[key][:2]:best[key]=cand
    forms=defaultdict(dict)
    for (lid,con),(_,_,seq) in best.items():forms[lid][con]=seq
    langs={k:v for k,v in langs.items() if k in forms and len(forms[k])>=200}
    forms={k:forms[k] for k in langs}
    all_lids=sorted(langs);all_cons=sorted({c for x in forms.values() for c in x})
    plan={}
    for lid in all_lids:
        L=langs[lid];fc=set(forms[lid])
        same=[]
        for z in all_lids:
            if z==lid or langs[z]['family']!=L['family']:continue
            ov=len(fc&set(forms[z]));same.append((0 if langs[z]['subfamily']==L['subfamily'] else 1,-ov,D.h64('lexsem-same',lid,z),z))
        same_ref=min(same)[-1] if same else None
        fam_best={}
        for z in all_lids:
            if z==lid or langs[z]['family']==L['family']:continue
            fam=langs[z]['family'];ov=len(fc&set(forms[z]));k=(-ov,D.h64('lexsem-blocked-lang',lid,z),z)
            if fam not in fam_best or k<fam_best[fam]:fam_best[fam]=k
        blocked=[x[-1] for x in sorted(fam_best.values(),key=lambda q:(D.h64('lexsem-blocked-fam',lid,langs[q[-1]]['family']),q))[:3]]
        plan[lid]={'shard':D.h64('lexsem-shard',lid)%SHARDS,'same_ref':same_ref,'blocked_refs':blocked}
    x={'version':1,'source':{'phoible_commit':D.PH,'northeuralex_commit':NE_SHA},'phoible_coverage':cov,
       'phones':phones,'languages':langs,'forms':forms,'concept_labels':labels,'concepts':all_cons,'plan':plan,
       'counts':{'languages':len(langs),'concepts':len(all_cons),'raw_forms':forms_total,'mapped_forms':mapped_forms,'canonical_forms':sum(len(v) for v in forms.values()),'token_total':token_total,'token_mapped':token_mapped},
       'resolutions':RES,'candidate':CAND,'boundary':BOUND,'negatives':NEG,
       'protocol':{
        'question':'Does the successive phonetic-grid code carry word-level semantic/concept information?',
        'representation':'Only pronunciation is encoded. NorthEuraLex concept labels never affect the phonetic grid or segment coordinates.',
        'task':'For each held-out target-language word, rank its true concept against 15 deterministic wrong concepts using cross-language word-form distance.',
        'within_family':'Reference language is excluded target language, preferring same subfamily then same family. This tests genealogical lexical transmission.',
        'family_blocked':'Three deterministic reference languages from three different families are used; the target family is entirely excluded. This tests sound-meaning signal beyond shared family ancestry.',
        'controls':'Meaning-label pseudo-positive null; same-capacity random segment-to-cell geometry; raw segment-identity edit-distance ceiling.',
        'support':'Semantic support requires real-grid top1 and pairwise AUC above the label null with positive differences in >=15/20 shards and one-sided sign p<0.05. Geometry support additionally requires real grid above random-cell coding by the same rule.',
        'progression':'A meaning-refinement progression requires positive correlation between grid resolution and true-concept top1 in >=15/20 shards with one-sided sign p<0.05.',
        'interpretation':'Success means pronunciation retains information useful for recovering independently defined word meanings. It does not imply that meaning was historically generated by the grid.'}}
    dumpgz(PREP,x);print(json.dumps(x['counts'],indent=2))

def qlookup(phones,n,random=False):
    out=[]
    for i,p in enumerate(phones):
        if random:
            z=D.h64('lexsem-random-cell',n,p['pid'])%(n*n);out.append((z//n,z%n))
        else:
            x,y=p['c'];out.append((min(n-1,int(x*n)),min(n-1,int(y*n))))
    return out

def edit(a,b,lookup=None,n=None,raw=False):
    if not a or not b:return 1.0
    prev=list(range(len(b)+1))
    den=2*max(1,(n or 2)-1)
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
    p=ds[pos];lt=sum(d<p-1e-12 for j,d in enumerate(ds) if j!=pos);eq=sum(abs(d-p)<=1e-12 for j,d in enumerate(ds) if j!=pos)
    auc=sum((1.0 if p<d-1e-12 else .5 if abs(p-d)<=1e-12 else 0.0) for j,d in enumerate(ds) if j!=pos)/(len(ds)-1)
    top=0.0 if lt else 1.0/(eq+1);rank=1+lt+.5*eq
    return auc,top,1.0/rank
def agg0():return {'cases':0,'auc':0.0,'top1':0.0,'mrr':0.0}
def adda(a,m):
    a['cases']+=1;a['auc']+=m[0];a['top1']+=m[1];a['mrr']+=m[2]
def avg(a):return {k:(a[k]/a['cases'] if k!='cases' and a['cases'] else a[k]) for k in a}

def cases_for(lid,mode,x):
    forms=x['forms'];p=x['plan'][lid];target=forms[lid]
    refs=[p['same_ref']] if mode=='within_family' and p['same_ref'] else (p['blocked_refs'] if mode=='family_blocked' else [])
    refs=[r for r in refs if r in forms]
    if not refs:return []
    refpool={c:[forms[r][c] for r in refs if c in forms[r]] for c in x['concepts']};refpool={c:v for c,v in refpool.items() if v}
    pool=sorted(set(target)&set(refpool));out=[]
    for tc in pool:
        neg=[c for c in pool if c!=tc];neg=sorted(neg,key=lambda c:(D.h64('lexsem-neg',mode,lid,tc,c),c))[:NEG]
        if len(neg)<NEG:continue
        cs=[tc,*neg];pseudo=1+(D.h64('lexsem-pseudo',mode,lid,tc)%NEG)
        out.append((target[tc],[refpool[c] for c in cs],pseudo))
    return out

def eval_cases(cases,lookup,n,raw=False):
    real,label=agg0(),agg0()
    for tgt,refs,pseudo in cases:
        ds=[min(edit(tgt,z,lookup,n,raw) for z in zs) for zs in refs]
        adda(real,metrics(ds,0));adda(label,metrics(ds,pseudo))
    return real,label

def shard(i):
    x=loadgz(PREP);lids=[l for l,p in x['plan'].items() if p['shard']==i];modes=['within_family','family_blocked']
    built={m:[] for m in modes}
    for lid in lids:
        for m in modes:built[m].extend(cases_for(lid,m,x))
    out={'shard':i,'languages':lids,'case_counts':{m:len(built[m]) for m in modes},'raw':{},'resolutions':{}}
    for m in modes:
        r,z=eval_cases(built[m],None,None,True);out['raw'][m]={'real':r,'label_null':z}
    for n in RES:
        rl=qlookup(x['phones'],n,False);rr=qlookup(x['phones'],n,True);out['resolutions'][str(n)]={}
        for m in modes:
            a,z=eval_cases(built[m],rl,n,False);b,_=eval_cases(built[m],rr,n,False)
            out['resolutions'][str(n)][m]={'real':a,'label_null':z,'random_cells':b}
    WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02}.json').write_text(json.dumps(out,separators=(',',':')))
    print({'shard':i,'languages':len(lids),'cases':out['case_counts']})

def rank(v):
    o=sorted(range(len(v)),key=lambda i:v[i]);r=[0.0]*len(v);i=0
    while i<len(o):
        j=i+1
        while j<len(o) and v[o[j]]==v[o[i]]:j+=1
        q=(i+j+1)/2
        for k in range(i,j):r[o[k]]=q
        i=j
    return r
def rho(a,b):
    a,b=rank(a),rank(b);ma,mb=statistics.mean(a),statistics.mean(b);da=sum((x-ma)**2 for x in a);db=sum((x-mb)**2 for x in b)
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(da*db) if da and db else 0.0
def pooled(ss,path):
    a=agg0()
    for s in ss:
        q=s
        for k in path:q=q[k]
        for k in a:a[k]+=q[k]
    return avg(a)
def shardmean(s,path):
    q=s
    for k in path:q=q[k]
    return avg(q)
def support(ss,mode,n,a,b,metric='top1'):
    dif=[]
    for s in ss:
        A=shardmean(s,['resolutions',str(n),mode,a]);B=shardmean(s,['resolutions',str(n),mode,b])
        if A['cases'] and B['cases']:dif.append(A[metric]-B[metric])
    wins=sum(x>0 for x in dif);return {'mean_difference':statistics.mean(dif) if dif else None,'wins':wins,'valid_shards':len(dif),'sign_p':signp(wins,len(dif)),'supported':bool(dif and statistics.mean(dif)>0 and wins>=15 and signp(wins,len(dif))<.05)}

def merge():
    x=loadgz(PREP);ss=[json.loads((WORK/f'result-{i:02}.json').read_text()) for i in range(SHARDS)];modes=['within_family','family_blocked'];summary={}
    for m in modes:
        traj=[]
        for n in RES:
            row={'n':n,'real':pooled(ss,['resolutions',str(n),m,'real']),'label_null':pooled(ss,['resolutions',str(n),m,'label_null']),'random_cells':pooled(ss,['resolutions',str(n),m,'random_cells'])}
            row['semantic_top1']=support(ss,m,n,'real','label_null','top1');row['semantic_auc']=support(ss,m,n,'real','label_null','auc');row['geometry_top1']=support(ss,m,n,'real','random_cells','top1');traj.append(row)
        onset=next((r['n'] for r in traj if r['n'] in CAND and r['semantic_top1']['supported'] and r['semantic_auc']['supported']),None)
        gonset=next((r['n'] for r in traj if r['n'] in CAND and r['geometry_top1']['supported']),None)
        peak=max((r for r in traj if r['n'] in CAND),key=lambda r:r['real']['top1'])['n']
        rhos=[]
        for s in ss:
            ys=[shardmean(s,['resolutions',str(n),m,'real'])['top1'] for n in CAND]
            if any(ys):rhos.append(rho(CAND,ys))
        rw=sum(v>0 for v in rhos);rp=signp(rw,len(rhos));progress=bool(rhos and statistics.mean(rhos)>0 and rw>=15 and rp<.05)
        raw=pooled(ss,['raw',m,'real']);rawnull=pooled(ss,['raw',m,'label_null'])
        summary[m]={'semantic_onset':onset,'geometry_onset':gonset,'peak_resolution':peak,'trajectory':traj,'raw_identity':raw,'raw_label_null':rawnull,'rho_resolution_top1_mean':statistics.mean(rhos) if rhos else None,'rho_positive_shards':rw,'rho_valid_shards':len(rhos),'rho_sign_p':rp,'meaning_refinement_progression_supported':progress}
    out={'version':1,'status':'complete','test':'sound sequence -> word concept/meaning across successive phonetic grids','source':x['source'],'counts':x['counts'],'shards':SHARDS,'negatives_per_case':NEG,'method':x['protocol'],'results':summary,'boundary':'22x22 and 23x23 are continuation checks only; onset/peak claims are restricted to 3x3 through 21x21.'}
    OUT.write_text(json.dumps(out,indent=2));print(json.dumps({m:{k:v for k,v in summary[m].items() if k not in {'trajectory'}} for m in modes},indent=2))

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True);s.add_parser('prepare');q=s.add_parser('shard');q.add_argument('--id',type=int,required=True);s.add_parser('merge');a=p.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
