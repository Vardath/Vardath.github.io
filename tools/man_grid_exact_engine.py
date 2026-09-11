#!/usr/bin/env python3
from __future__ import annotations
import math, statistics

FEATURES=['tone','stress','syllabic','short','long','consonantal','sonorant','continuant','delayedRelease','approximant','tap','trill','nasal','lateral','labial','round','labiodental','coronal','anterior','distributed','strident','dorsal','high','low','front','back','tense','retractedTongueRoot','advancedTongueRoot','periodicGlottalSource','epilaryngealSource','spreadGlottis','constrictedGlottis','fortis','raisedLarynxEjective','loweredLarynxImplosive','click']
PRIMARY={'syllabic','consonantal','sonorant','continuant','labial','coronal','dorsal','high','low','front','back'}

def fnum(v):
    if v is None or v in ('','0','N'):return 0.0
    n=c=0
    for x in str(v).split(','):
        if x=='+':n+=1;c+=1
        elif x=='-':n-=1;c+=1
    return n/c if c else 0.0

def vec(row):return [fnum(row.get(k)) for k in FEATURES]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a)) or 1.0
def unit(a):
    n=norm(a);return [x/n for x in a]
def centroid(vs):
    if not vs:return []
    return [sum(v[j] for v in vs)/len(vs) for j in range(len(vs[0]))]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def matvec(M,v):return [dot(r,v) for r in M]

def dist(a,b):
    if not a or not b:return 1.0
    s=w=0.0
    for i,f in enumerate(FEATURES):
        q=2.0 if f in PRIMARY else 1.0
        s+=abs(a[i]-b[i])*q/2.0;w+=q
    return s/w if w else 1.0

def covariance(vs,m=None):
    if not vs:return []
    m=m or centroid(vs);d=len(m);C=[[0.0]*d for _ in range(d)];den=max(1,len(vs)-1)
    for v in vs:
        for i in range(d):
            a=v[i]-m[i]
            for j in range(i,d):C[i][j]+=a*(v[j]-m[j])
    for i in range(d):
        for j in range(i,d):C[i][j]/=den;C[j][i]=C[i][j]
    return C

def eig(C,seed,orth=None):
    v=unit(seed)
    for _ in range(100):
        z=matvec(C,v)
        if orth is not None:
            q=dot(z,orth);z=[x-q*orth[i] for i,x in enumerate(z)]
        z=unit(z);d=max(abs(z[i]-v[i]) for i in range(len(v)));v=z
        if d<1e-9:break
    return v,dot(v,matvec(C,v))

def pct(a,q):
    b=sorted(a)
    if not b:return 0.0
    p=(len(b)-1)*q;i=math.floor(p);f=p-i
    return b[i]*(1-f)+b[min(i+1,len(b)-1)]*f

def orient(axis,rows,kind):
    score=0.0
    for r in rows:
        v=vec(r)
        t=(fnum(r.get('back'))-fnum(r.get('front'))+.5*fnum(r.get('dorsal'))-.45*fnum(r.get('labial'))) if kind=='x' else (fnum(r.get('syllabic'))+.65*fnum(r.get('sonorant'))+.25*fnum(r.get('approximant'))-.5*fnum(r.get('consonantal')))
        score+=dot(v,axis)*t
    return [-x for x in axis] if score<0 else axis

def fit_projection(rows):
    vs=[vec(r) for r in rows];m=centroid(vs);C=covariance(vs,m);d=len(m)
    e1,lam=eig(C,[math.sin((i+1)*1.731)+.5 for i in range(d)])
    C2=[[C[i][j]-lam*e1[i]*e1[j] for j in range(d)] for i in range(d)]
    e2,_=eig(C2,[math.cos((i+1)*2.117)+.25 for i in range(d)],e1)
    ax=orient(e1,rows,'x');ay=orient(e2,rows,'y');xs=[];ys=[]
    for v in vs:
        z=[v[i]-m[i] for i in range(d)];xs.append(dot(z,ax));ys.append(dot(z,ay))
    return {'features':FEATURES,'mean':m,'axisX':ax,'axisY':ay,'x0':pct(xs,.01),'x1':pct(xs,.99),'y0':pct(ys,.01),'y1':pct(ys,.99),'method':'PHOIBLE full-feature PCA (2 components); axis signs fixed with independent place/backness and sonority/openness references'}

def project(v,P):
    z=[v[i]-P['mean'][i] for i in range(len(v))];sx=dot(z,P['axisX']);sy=dot(z,P['axisY'])
    x=(sx-P['x0'])/((P['x1']-P['x0']) or 1.0);y=(sy-P['y0'])/((P['y1']-P['y0']) or 1.0)
    return max(0.0,min(1.0,x)),max(0.0,min(1.0,y))

def cell(layer,x,y,side):
    x=max(0.0,min(.999999,x));y=max(0.0,min(.999999,y))
    c=min(layer['columns'],1+math.floor(x*layer['columns']));r=min(layer['rows'],1+math.floor((1-y)*layer['rows']))
    return f"{layer['id']}-{side}-R{r}-C{c}"

def map_vector(v,P,spec,side='L'):
    x,y=project(v,P);u=[cell(l,x,y,side) for l in spec['upper']];d=[cell(l,x,y,side) for l in spec['lower']]
    return {'x':x,'y':y,'side':side,'upper':u,'lower':d,'all':u+d}

def grid_paths(v,P,spec):
    L=map_vector(v,P,spec,'L');R=map_vector(v,P,spec,'R')
    return {'x':L['x'],'y':L['y'],'upper_left':L['upper'],'upper_right':R['upper'],'lower_left':L['lower'],'lower_right':R['lower'],'all_left':L['all'],'all_right':R['all']}

def all_cell_ids(spec):
    out=[]
    for l in [*spec['upper'],*spec['lower']]:
        for s in ('L','R'):
            for r in range(1,l['rows']+1):
                for c in range(1,l['columns']+1):out.append(f"{l['id']}-{s}-R{r}-C{c}")
    return out

def mirror_cell(cid):
    import re
    m=re.match(r'^([UD]\d+)-(L|R)-R(\d+)-C(\d+)$',cid)
    return None if not m else f"{m.group(1)}-{'R' if m.group(2)=='L' else 'L'}-R{m.group(3)}-C{m.group(4)}"

def inventory_distance(A,B,params):
    A=[p for p in A if p in params];B=[p for p in B if p in params]
    if not A or not B:return None
    ab=[min(dist(params[a]['features'],params[b]['features']) for b in B) for a in A]
    ba=[min(dist(params[b]['features'],params[a]['features']) for a in A) for b in B]
    return (statistics.mean(ab)+statistics.mean(ba))/2
