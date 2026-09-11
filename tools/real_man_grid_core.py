#!/usr/bin/env python3
"""Shared continuous-coordinate engine for the source-traced Man Grid tool.

This module intentionally mirrors the live web tool rather than the retired 4x4/16-state
proxy. Source phonemes are embedded from PHOIBLE feature vectors into the 716x910 canvas,
snapped to the traced line geometry, and the only built-in geometric transform is the
web tool's vertical fold x' = 2*axis-x, y'=y.
"""
from __future__ import annotations

import csv, io, json, math, re, statistics, unicodedata, urllib.request
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / 'phonetic-historical-grid-data.json'
ENCODER = ROOT / 'data' / 'real-man-grid-encoder.json'
W, H, AXIS = 716.0, 910.0, 358.0
PH = '5c477f1934f57b3c1a16168fadc08e83dbc03362'
PHURL = f'https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/parameters.csv'
FEATURES = [
    'syllabic','consonantal','sonorant','continuant','delayedRelease','approximant',
    'nasal','lateral','labial','round','labiodental','coronal','anterior','distributed',
    'strident','dorsal','high','low','front','back','spreadGlottis','constrictedGlottis'
]
IGNORE = set(' /[](){}ˈˌ.‿#|·0123456789')


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent':'Vardath-real-man-grid/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode('utf-8-sig')


def fnum(v) -> float:
    if v in (None, '', '0', 'N', 'NA', 'n/a'):
        return 0.0
    vals=[]
    for x in str(v).split(','):
        x=x.strip()
        if x=='+': vals.append(1.0)
        elif x=='-': vals.append(-1.0)
        elif x in ('0','N',''): vals.append(0.0)
    return statistics.mean(vals) if vals else 0.0


def _power_top2(rows):
    """Top two PCA loading vectors for standardized rows, pure Python and deterministic."""
    n=len(rows); d=len(rows[0])
    means=[sum(r[j] for r in rows)/n for j in range(d)]
    sds=[]
    for j in range(d):
        v=sum((r[j]-means[j])**2 for r in rows)/max(1,n-1)
        sds.append(math.sqrt(v) or 1.0)
    z=[[ (r[j]-means[j])/sds[j] for j in range(d)] for r in rows]
    cov=[[0.0]*d for _ in range(d)]
    for r in z:
        for a in range(d):
            ra=r[a]
            for b in range(a,d): cov[a][b]+=ra*r[b]
    den=max(1,n-1)
    for a in range(d):
        for b in range(a,d):
            cov[a][b]/=den; cov[b][a]=cov[a][b]
    vecs=[]
    A=[row[:] for row in cov]
    for k in range(2):
        v=[0.0]*d; v[k%d]=1.0
        for j in range(d): v[j]+=((j+1)*(k+3)%17)/100.0
        for _ in range(250):
            w=[sum(A[i][j]*v[j] for j in range(d)) for i in range(d)]
            norm=math.sqrt(sum(x*x for x in w)) or 1.0
            w=[x/norm for x in w]
            if sum((w[j]-v[j])**2 for j in range(d)) < 1e-20:
                v=w;break
            v=w
        m=max(range(d), key=lambda j: abs(v[j]))
        if v[m]<0: v=[-x for x in v]
        lam=sum(v[i]*sum(A[i][j]*v[j] for j in range(d)) for i in range(d))
        vecs.append(v)
        for i in range(d):
            for j in range(d): A[i][j]-=lam*v[i]*v[j]
    return means,sds,vecs,z


def _nearest_on_segment(px,py,s):
    x1,y1,x2,y2=map(float,s); dx=x2-x1;dy=y2-y1
    den=dx*dx+dy*dy
    if den<=1e-12:return x1,y1,(px-x1)**2+(py-y1)**2
    t=((px-x1)*dx+(py-y1)*dy)/den;t=max(0.0,min(1.0,t))
    x=x1+t*dx;y=y1+t*dy
    return x,y,(px-x)**2+(py-y)**2


def snap_to_trace(x,y,segments):
    best=None
    for s in segments:
        q=_nearest_on_segment(x,y,s)
        if best is None or q[2]<best[2]: best=q
    return best[0],best[1]


def build_encoder(force=False):
    if ENCODER.exists() and not force:
        return json.loads(ENCODER.read_text(encoding='utf-8'))
    params=[]
    for p in csv.DictReader(io.StringIO(_fetch(PHURL))):
        name=(p.get('Name') or '').strip()
        if not name: continue
        v=[fnum(p.get(f)) for f in FEATURES]
        if any(abs(x)>1e-12 for x in v): params.append((name,v))
    uniq={}
    for name,v in params: uniq.setdefault(unicodedata.normalize('NFC',name),v)
    names=sorted(uniq)
    rows=[uniq[n] for n in names]
    means,sds,vecs,z=_power_top2(rows)
    pcs=[]
    for zr in z: pcs.append((sum(a*b for a,b in zip(zr,vecs[0])),sum(a*b for a,b in zip(zr,vecs[1]))))
    xs=sorted(p[0] for p in pcs);ys=sorted(p[1] for p in pcs)
    def quant(a,q):
        if not a:return 0.0
        pos=(len(a)-1)*q;i=int(pos);f=pos-i
        return a[i]*(1-f)+a[min(i+1,len(a)-1)]*f
    xlo,xhi=quant(xs,.02),quant(xs,.98);ylo,yhi=quant(ys,.02),quant(ys,.98)
    if xhi<=xlo:xlo,xhi=min(xs),max(xs)
    if yhi<=ylo:ylo,yhi=min(ys),max(ys)
    segments=json.loads(TRACE.read_text(encoding='utf-8'))
    coords={}
    for name,(a,b) in zip(names,pcs):
        nx=max(0,min(1,(a-xlo)/(xhi-xlo or 1)));ny=max(0,min(1,(b-ylo)/(yhi-ylo or 1)))
        x=12+nx*(W-24);y=12+(1-ny)*(H-24)
        sx,sy=snap_to_trace(x,y,segments)
        coords[name]=[round(sx,4),round(sy,4)]
    encoder={
        'version':1,'tool':'source-traced continuous Man Grid','width':W,'height':H,'axis':AXIS,
        'trace_file':TRACE.name,'trace_segments':len(segments),'phoible_commit':PH,'features':FEATURES,
        'embedding':'standardized PHOIBLE feature PCA(2), deterministic sign; 2-98% scale; nearest-point snap to traced line segments',
        'transform':"tool_fold: x'=2*axis-x, y'=y; token order unchanged",
        'pca':{'mean':means,'sd':sds,'pc1':vecs[0],'pc2':vecs[1],'clip':[xlo,xhi,ylo,yhi]},
        'segments':coords,
    }
    ENCODER.parent.mkdir(parents=True,exist_ok=True)
    ENCODER.write_text(json.dumps(encoder,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return encoder


class Encoder:
    def __init__(self,data=None):
        self.data=data or build_encoder();self.coords={unicodedata.normalize('NFC',k):tuple(v) for k,v in self.data['segments'].items()}
        self.axis=float(self.data['axis']);self.width=float(self.data['width']);self.height=float(self.data['height'])
        self.by_first={}
        for s in self.coords:
            if not s:continue
            self.by_first.setdefault(s[0],[]).append(s)
        for k in self.by_first:self.by_first[k].sort(key=lambda s:(-len(s),s))
        self._spatial={};self._bucket=32.0
        for name,(x,y) in self.coords.items():
            self._spatial.setdefault((int(x//self._bucket),int(y//self._bucket)),[]).append((name,(x,y)))
    def tokenize(self,ipa):
        s=unicodedata.normalize('NFC',str(ipa or '')).strip();out=[];i=0
        while i<len(s):
            ch=s[i]
            if ch in IGNORE or ch.isspace():i+=1;continue
            found=None
            for tok in self.by_first.get(ch,()):
                if s.startswith(tok,i):found=tok;break
            if found is not None:
                out.append(found);i+=len(found);continue
            i+=1
        return out
    def path(self,ipa):
        return [self.coords[t] for t in self.tokenize(ipa) if t in self.coords]
    def fold(self,path):
        return [(2*self.axis-x,y) for x,y in path]
    def nearest_segment(self,p):
        x,y=p;bx=int(x//self._bucket);by=int(y//self._bucket);cand=[]
        for r in range(0,24):
            for dx in range(-r,r+1):
                for dy in range(-r,r+1):
                    if r and abs(dx)!=r and abs(dy)!=r: continue
                    cand.extend(self._spatial.get((bx+dx,by+dy),()))
            if cand: break
        if not cand: cand=list(self.coords.items())
        return min(cand,key=lambda kv:(kv[1][0]-x)**2+(kv[1][1]-y)**2)[0]


def point_dist(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])/math.hypot(W,H)

@lru_cache(maxsize=1_000_000)
def _path_sim_cached(a,b):
    A=[(a[i],a[i+1]) for i in range(0,len(a),2)];B=[(b[i],b[i+1]) for i in range(0,len(b),2)]
    return path_similarity(A,B)

def path_key(path):
    return tuple(round(v,3) for p in path for v in p)

def path_similarity(a,b):
    if not a or not b:return 0.0
    n,m=len(a),len(b);gap=.42
    dp=[j*gap for j in range(m+1)]
    for i in range(1,n+1):
        nd=[i*gap]+[0.0]*m
        for j in range(1,m+1):
            sub=point_dist(a[i-1],b[j-1])
            nd[j]=min(dp[j]+gap,nd[j-1]+gap,dp[j-1]+sub)
        dp=nd
    cost=dp[m]/max(n,m)
    return max(0.0,1.0-cost)

def sim(a,b):return _path_sim_cached(path_key(a),path_key(b))

def best_orientation(path,target,enc):
    direct=sim(path,target);folded=sim(enc.fold(path),target)
    return (folded,'fold') if folded>direct else (direct,'identity')

def medoid(paths,enc,allow_fold=False):
    if not paths:return None
    items=paths[:];candidates=[];seen=set()
    for p in items:
        k=path_key(p)
        if k not in seen:seen.add(k);candidates.append(p)
    if len(candidates)>32:candidates=candidates[:32]
    best=None
    for p in candidates:
        vals=[]
        for q in items:vals.append(best_orientation(p,q,enc)[0] if allow_fold else sim(p,q))
        sc=statistics.mean(vals);key=(sc,-len(p),tuple(path_key(p)))
        if best is None or key>best[0]:best=(key,p,sc)
    return best[1],best[2]

def latent_barycenter(family_paths,enc,iterations=2):
    vals=list(family_paths.values())
    if not vals:return None
    ref=medoid(vals,enc,allow_fold=True)[0]
    segments=json.loads(TRACE.read_text(encoding='utf-8'));ops={}
    for _ in range(iterations):
        buckets=[[] for _ in ref]
        for name,p0 in family_paths.items():
            p=enc.fold(p0) if sim(enc.fold(p0),ref)>sim(p0,ref) else p0
            ops[name]='fold' if p is not p0 else 'identity'
            n,m=len(ref),len(p);gap=.42
            dp=[[0.0]*(m+1) for _ in range(n+1)];bt=[[None]*(m+1) for _ in range(n+1)]
            for i in range(1,n+1):dp[i][0]=i*gap;bt[i][0]=(i-1,0)
            for j in range(1,m+1):dp[0][j]=j*gap;bt[0][j]=(0,j-1)
            for i in range(1,n+1):
                for j in range(1,m+1):
                    opts=[(dp[i-1][j]+gap,(i-1,j)),(dp[i][j-1]+gap,(i,j-1)),(dp[i-1][j-1]+point_dist(ref[i-1],p[j-1]),(i-1,j-1))]
                    dp[i][j],bt[i][j]=min(opts,key=lambda x:x[0])
            i,j=n,m
            while i or j:
                pi,pj=bt[i][j]
                if pi==i-1 and pj==j-1 and i>0 and j>0:buckets[i-1].append(p[j-1])
                i,j=pi,pj
        nr=[]
        for old,b in zip(ref,buckets):
            if not b:nr.append(old);continue
            x=statistics.mean(p[0] for p in b);y=statistics.mean(p[1] for p in b)
            nr.append(snap_to_trace(x,y,segments)[:2])
        ref=nr
    fits={name:best_orientation(ref,p,enc)[0] for name,p in family_paths.items()}
    return ref,ops,fits
