#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, math, urllib.request
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/'data/man-grid-structure-v1.json'
PH='5c477f1934f57b3c1a16168fadc08e83dbc03362'
PHBASE=f'https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/'

def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf-8','ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big')

def fetch_text(url,retries=4):
    last=None
    for _ in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Vardath-ManGrid-Exact/3.0'})
            with urllib.request.urlopen(req,timeout=120) as r:return r.read().decode('utf-8-sig')
        except Exception as e:last=e
    raise RuntimeError(f'failed to fetch {url}: {last}')

def load_phoible():
    spec=json.loads(GRID.read_text(encoding='utf-8'));ids=E.all_cell_ids(spec)
    if spec.get('counts',{}).get('total_cells')!=1074 or len(ids)!=1074 or len(set(ids))!=1074:raise RuntimeError('Man Grid spec is not the exact 1,074-cell mirrored structure')
    for cid in ids:
        if E.mirror_cell(E.mirror_cell(cid) or '')!=cid:raise RuntimeError(f'bad mirror address {cid}')
    pt=fetch_text(PHBASE+'parameters.csv');lt=fetch_text(PHBASE+'languages.csv');vt=fetch_text(PHBASE+'values.csv')
    rows=[];all_params={}
    for r in csv.DictReader(io.StringIO(pt)):
        pid=(r.get('ID') or '').strip();name=(r.get('Name') or '').strip()
        if pid and name:
            rows.append(r);all_params[pid]={'id':pid,'name':name,'class':(r.get('SegmentClass') or '').strip(),'features':E.vec(r)}
    P=E.fit_projection(rows)
    langs={}
    for r in csv.DictReader(io.StringIO(lt)):
        lid=(r.get('ID') or '').strip();fam=(r.get('Family_Name') or '').strip() or 'Unclassified'
        if lid:langs[lid]={'id':lid,'name':(r.get('Name') or '').strip(),'iso':(r.get('ISO639P3code') or '').strip(),'family':fam,'inventory':set()}
    value_rows=accepted=0
    for r in csv.DictReader(io.StringIO(vt)):
        value_rows+=1;lid=(r.get('Language_ID') or '').strip();pid=(r.get('Parameter_ID') or '').strip()
        if lid not in langs or pid not in all_params or str(r.get('Marginal') or '').lower()=='true':continue
        p=all_params[pid]
        if p['class'].lower()=='tone' or abs(p['features'][E.FEATURES.index('tone')])>.25:continue
        langs[lid]['inventory'].add(pid);accepted+=1
    all_langs=len(langs);langs={k:v for k,v in langs.items() if v['family']!='Unclassified' and len(v['inventory'])>=10}
    used=sorted({p for l in langs.values() for p in l['inventory'] if p in all_params});params={p:all_params[p] for p in used}
    for p in params:params[p]['grid']=E.grid_paths(params[p]['features'],P,spec)
    coverage={'all_phoible_parameters':len(all_params),'research_segments':len(params),'all_languages':all_langs,'eligible_languages':len(langs),'value_rows':value_rows,'accepted_inventory_rows':accepted,'families':len({l['family'] for l in langs.values()})}
    return spec,params,langs,P,coverage

def language_centroid(lang,params):return E.centroid([params[p]['features'] for p in lang['inventory'] if p in params])
def fit_sibling_axis(langs,params):
    by=defaultdict(list);cents={}
    for lid,l in langs.items():
        c=language_centroid(l,params)
        if c:cents[lid]=c;by[l['family']].append(lid)
    residual=[]
    for lids in by.values():
        if len(lids)<2:continue
        fc=E.centroid([cents[x] for x in lids]);residual.extend(E.sub(cents[x],fc) for x in lids)
    C=E.covariance(residual);axis,_=E.eig(C,[math.sin((i+1)*.913)+.25 for i in range(len(E.FEATURES))]) if C else ([1.0]+[0.0]*(len(E.FEATURES)-1),0.0)
    o=axis[E.FEATURES.index('front')]-axis[E.FEATURES.index('back')]+axis[E.FEATURES.index('coronal')]-axis[E.FEATURES.index('dorsal')]
    return ([-x for x in axis] if o<0 else axis),cents

def assign_branches(langs,params):
    axis,cents=fit_sibling_axis(langs,params);by=defaultdict(list)
    for lid,l in langs.items():by[l['family']].append(lid)
    branches={};eligible=[]
    for fam,lids in by.items():
        if len(lids)<2:continue
        fc=E.centroid([cents[x] for x in lids]);scores=sorted((E.dot(E.sub(cents[lid],fc),axis),lid) for lid in lids);mid=len(scores)//2
        for j,(_,lid) in enumerate(scores):branches[lid]='L' if j<mid else 'R'
        if any(branches[x]=='L' for x in lids) and any(branches[x]=='R' for x in lids):eligible.append(fam)
    return branches,sorted(eligible),axis

def consensus_inventory(lids,langs,ratio=.5):
    if not lids:return set()
    c=defaultdict(int)
    for lid in lids:
        for p in langs[lid]['inventory']:c[p]+=1
    need=max(1,math.ceil(len(lids)*ratio));return {p for p,n in c.items() if n>=need}

def mutual_pairs(A,B,params):
    A=sorted(p for p in A if p in params);B=sorted(p for p in B if p in params)
    if not A or not B:return []
    ba={a:min(B,key=lambda b:(E.dist(params[a]['features'],params[b]['features']),b)) for a in A};ab={b:min(A,key=lambda a:(E.dist(params[b]['features'],params[a]['features']),a)) for b in B}
    return [(a,b,E.dist(params[a]['features'],params[b]['features'])) for a,b in ba.items() if ab.get(b)==a]
