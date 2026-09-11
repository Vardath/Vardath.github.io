#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, math, statistics, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/'data/man-grid-structure-v1.json'
PH='5c477f1934f57b3c1a16168fadc08e83dbc03362'
PHBASE=f'https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/'
FEATURES=[
 'tone','stress','syllabic','short','long','consonantal','sonorant','continuant','delayedRelease','approximant','tap','trill','nasal','lateral','labial','round','labiodental','coronal','anterior','distributed','strident','dorsal','high','low','front','back','tense','retractedTongueRoot','advancedTongueRoot','periodicGlottalSource','epilaryngealSource','spreadGlottis','constrictedGlottis','fortis','raisedLarynxEjective','loweredLarynxImplosive','click']


def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf-8','ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big')


def fetch_text(url,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Vardath-ManGrid-V2/1.0'})
            with urllib.request.urlopen(req,timeout=120) as r:return r.read().decode('utf-8-sig')
        except Exception as e:last=e
    raise RuntimeError(f'failed to fetch {url}: {last}')


def fnum(v):
    if v is None or v in ('','0','N'):return 0.0
    n=c=0
    for x in str(v).split(','):
        if x=='+':n+=1;c+=1
        elif x=='-':n-=1;c+=1
    return n/c if c else 0.0


def vec(row):return [fnum(row.get(k)) for k in FEATURES]

def dist(a,b):
    if not a or not b:return 1e9
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/len(a))

def centroid(vs):
    if not vs:return []
    n=len(vs);m=len(vs[0]);return [sum(v[j] for v in vs)/n for j in range(m)]

def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a);return [x/n for x in a] if n else [0.0]*len(a)

def covariance(rows):
    if not rows:return []
    m=len(rows[0]);mu=centroid(rows);c=[[0.0]*m for _ in range(m)];den=max(1,len(rows)-1)
    for r in rows:
        z=[r[j]-mu[j] for j in range(m)]
        for i in range(m):
            zi=z[i]
            for j in range(i,m):c[i][j]+=zi*z[j]
    for i in range(m):
        for j in range(i,m):
            c[i][j]/=den;c[j][i]=c[i][j]
    return c

def matvec(M,v):return [sum(a*b for a,b in zip(r,v)) for r in M]

def power_pc(M,seed=1,orth=None,iters=120):
    m=len(M);v=[(((i+1)*(seed*17+11))%29)-14 for i in range(m)];v=unit(v)
    orth=orth or []
    for _ in range(iters):
        w=matvec(M,v)
        for o in orth:
            q=dot(w,o);w=[x-q*y for x,y in zip(w,o)]
        u=unit(w)
        if norm([x-y for x,y in zip(u,v)])<1e-10:v=u;break
        v=u
    return v

def fit_projection(segment_vectors):
    ids=sorted(segment_vectors);raw=[segment_vectors[i] for i in ids];m=len(FEATURES)
    means=[statistics.mean(r[j] for r in raw) for j in range(m)]
    sds=[]
    for j in range(m):
        s=statistics.pstdev(r[j] for r in raw);sds.append(s if s>1e-9 else 1.0)
    Z=[[(r[j]-means[j])/sds[j] for j in range(m)] for r in raw]
    C=covariance(Z);pc1=power_pc(C,1);pc2=power_pc(C,2,[pc1])
    # deterministic signs: front/back loads orient x; syllabic/consonantal loads orient y when possible.
    def load(pc,names):return sum(pc[FEATURES.index(k)] for k in names if k in FEATURES)
    if load(pc1,['front','labial'])-load(pc1,['back','dorsal'])<0:pc1=[-x for x in pc1]
    if load(pc2,['syllabic','sonorant'])-load(pc2,['consonantal'])<0:pc2=[-x for x in pc2]
    ps=[]
    for z in Z:ps.append((dot(z,pc1),dot(z,pc2)))
    xmin=min(x for x,y in ps);xmax=max(x for x,y in ps);ymin=min(y for x,y in ps);ymax=max(y for x,y in ps)
    return {'means':means,'sds':sds,'pc1':pc1,'pc2':pc2,'bounds':[xmin,xmax,ymin,ymax]}

def project(v,P):
    z=[(v[j]-P['means'][j])/P['sds'][j] for j in range(len(v))]
    x=dot(z,P['pc1']);y=dot(z,P['pc2']);xmin,xmax,ymin,ymax=P['bounds']
    xx=(x-xmin)/(xmax-xmin) if xmax>xmin else .5;yy=(y-ymin)/(ymax-ymin) if ymax>ymin else .5
    return max(0,min(1,xx)),max(0,min(1,yy))

def cell(layer,x,y,side=None):
    c=min(layer['columns'],int(max(0,min(.999999,x))*layer['columns'])+1)
    r=min(layer['rows'],int(max(0,min(.999999,y))*layer['rows'])+1)
    return f"{layer['id']}-{side}-R{r}-C{c}" if side else f"{layer['id']}-R{r}-C{c}"

def grid_paths(v,P,spec):
    x,y=project(v,P)
    lower=[cell(layer,x,y) for layer in reversed(spec['lower'])]  # D5 -> D1, toward circle
    upper_l=[cell(layer,x,y,'L') for layer in reversed(spec['upper'])] # U5 -> U1, away from circle
    upper_r=[cell(layer,x,y,'R') for layer in reversed(spec['upper'])]
    return {'x':x,'y':y,'lower':lower,'upper_left':upper_l,'upper_right':upper_r}

def load_phoible():
    spec=json.loads(GRID.read_text(encoding='utf-8'))
    if spec['counts']['total_cells']!=691:raise RuntimeError('Man Grid spec is not the 691-cell exact structure')
    pt=fetch_text(PHBASE+'parameters.csv');lt=fetch_text(PHBASE+'languages.csv');vt=fetch_text(PHBASE+'values.csv')
    params={};names={}
    for r in csv.DictReader(io.StringIO(pt)):
        pid=(r.get('ID') or '').strip();name=(r.get('Name') or '').strip()
        if not pid or not name:continue
        params[pid]={'id':pid,'name':name,'class':(r.get('SegmentClass') or '').strip(),'features':vec(r)};names[name]=pid
    langs={}
    for r in csv.DictReader(io.StringIO(lt)):
        lid=(r.get('ID') or '').strip();fam=(r.get('Family_Name') or '').strip() or 'Unclassified'
        if lid:langs[lid]={'id':lid,'name':(r.get('Name') or '').strip(),'iso':(r.get('ISO639P3code') or '').strip(),'family':fam,'inventory':set()}
    for r in csv.DictReader(io.StringIO(vt)):
        lid=(r.get('Language_ID') or '').strip();pid=(r.get('Parameter_ID') or '').strip()
        if lid not in langs or pid not in params:continue
        if str(r.get('Marginal') or '').lower()=='true':continue
        p=params[pid]
        if p['class'].lower()=='tone' or abs(p['features'][FEATURES.index('tone')])>.25:continue
        langs[lid]['inventory'].add(pid)
    langs={k:v for k,v in langs.items() if v['family']!='Unclassified' and len(v['inventory'])>=10}
    used=sorted({p for l in langs.values() for p in l['inventory'] if p in params})
    params={p:params[p] for p in used}
    P=fit_projection({p:params[p]['features'] for p in params})
    for p in params:params[p]['grid']=grid_paths(params[p]['features'],P,spec)
    return spec,params,langs,P

def language_centroid(lang,params):return centroid([params[p]['features'] for p in lang['inventory'] if p in params])

def fit_sibling_axis(langs,params):
    by=defaultdict(list)
    cents={}
    for lid,l in langs.items():
        c=language_centroid(l,params)
        if c:cents[lid]=c;by[l['family']].append(lid)
    residual=[]
    for fam,lids in by.items():
        if len(lids)<2:continue
        fc=centroid([cents[x] for x in lids])
        residual.extend(sub(cents[x],fc) for x in lids)
    C=covariance(residual);axis=power_pc(C,7) if C else [1.0]+[0.0]*(len(FEATURES)-1)
    # deterministic sign using front/back and coronal/dorsal loads.
    orient=axis[FEATURES.index('front')]-axis[FEATURES.index('back')]+axis[FEATURES.index('coronal')]-axis[FEATURES.index('dorsal')]
    if orient<0:axis=[-x for x in axis]
    return axis,cents

def assign_branches(langs,params):
    axis,cents=fit_sibling_axis(langs,params);by=defaultdict(list)
    for lid,l in langs.items():by[l['family']].append(lid)
    branches={};eligible=[]
    for fam,lids in by.items():
        if len(lids)<2:continue
        fc=centroid([cents[x] for x in lids]);scores=[]
        for lid in lids:scores.append((dot(sub(cents[lid],fc),axis),lid))
        scores.sort(key=lambda z:(z[0],z[1]));mid=len(scores)//2
        for j,(_,lid) in enumerate(scores):branches[lid]='L' if j<mid else 'R'
        if any(branches[x]=='L' for x in lids) and any(branches[x]=='R' for x in lids):eligible.append(fam)
    return branches,sorted(eligible),axis

def consensus_inventory(lids,langs,ratio=.5):
    if not lids:return set()
    c=defaultdict(int)
    for lid in lids:
        for p in langs[lid]['inventory']:c[p]+=1
    need=max(1,math.ceil(len(lids)*ratio))
    return {p for p,n in c.items() if n>=need}

def mutual_pairs(A,B,params):
    A=sorted(p for p in A if p in params);B=sorted(p for p in B if p in params)
    if not A or not B:return []
    ba={a:min(B,key=lambda b:(dist(params[a]['features'],params[b]['features']),b)) for a in A}
    ab={b:min(A,key=lambda a:(dist(params[b]['features'],params[a]['features']),a)) for b in B}
    out=[]
    for a,b in ba.items():
        if ab.get(b)==a:out.append((a,b,dist(params[a]['features'],params[b]['features'])))
    return out
