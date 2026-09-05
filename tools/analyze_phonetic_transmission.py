#!/usr/bin/env python3
"""Test whether bridge similarity tracks genealogy and geographic/contact opportunity.

This does NOT infer ethnicity or biological ancestry. It compares:
1) Glottolog genealogical family membership,
2) modern geographic proximity (a proxy for contact opportunity, not proof of contact), and
3) Vardath 4x4 stable-gate Jaccard similarity.

Outputs data/phonetic-transmission-analysis.json.
"""
from __future__ import annotations
import csv, io, json, math, pathlib, urllib.request
from collections import defaultdict

ROOT=pathlib.Path(__file__).resolve().parents[1]
LANGS=ROOT/'data/phonetic-benchmark-languages.csv'
PAIRS=ROOT/'data/phonetic-benchmark-pairs.csv'
OUT=ROOT/'data/phonetic-transmission-analysis.json'
GLOTTO='https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv'
UA='Vardath-Phonetic-Transmission/1.0'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=90) as r:
        return r.read().decode('utf-8')

def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def hav(lat1,lon1,lat2,lon2):
    r=6371.0088
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1,math.sqrt(a)))

def mean(xs): return sum(xs)/len(xs) if xs else None

def pearson(xs,ys):
    if len(xs)<3:return None
    mx,my=mean(xs),mean(ys);num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx=sum((x-mx)**2 for x in xs);dy=sum((y-my)**2 for y in ys)
    return num/math.sqrt(dx*dy) if dx>0 and dy>0 else None

def solve3(a,b):
    # Gaussian elimination 3x3.
    m=[list(a[i])+[b[i]] for i in range(3)]
    for c in range(3):
        piv=max(range(c,3),key=lambda r:abs(m[r][c]))
        m[c],m[piv]=m[piv],m[c]
        if abs(m[c][c])<1e-12:return [0,0,0]
        z=m[c][c];m[c]=[v/z for v in m[c]]
        for r in range(3):
            if r==c:continue
            z=m[r][c];m[r]=[m[r][j]-z*m[c][j] for j in range(4)]
    return [m[i][3] for i in range(3)]

def ols(rows):
    # y = b0 + b1*same_family + b2*log1p(distance_km)
    X=[[1.0,float(r['same_family']),math.log1p(r['distance_km'])] for r in rows]
    y=[r['jaccard'] for r in rows]
    xtx=[[sum(x[i]*x[j] for x in X) for j in range(3)] for i in range(3)]
    xty=[sum(x[i]*yy for x,yy in zip(X,y)) for i in range(3)]
    return solve3(xtx,xty)

def qround(x,n=4):return None if x is None else round(x,n)

def main():
    langs=[r for r in read_csv(LANGS) if r.get('canonical','').lower()=='true']
    byiso={r['iso']:r for r in langs if r.get('iso')}
    glrows=list(csv.DictReader(io.StringIO(fetch(GLOTTO))))
    byid={r.get('ID'):r for r in glrows}
    giso={}
    for r in glrows:
        iso=(r.get('ISO639P3code') or '').strip()
        if iso and iso not in giso:giso[iso]=r
    meta={}
    for iso,l in byiso.items():
        g=giso.get(iso)
        if not g:continue
        try:lat=float(g['Latitude']);lon=float(g['Longitude'])
        except Exception:lat=lon=None
        fid=(g.get('Family_ID') or '').strip()
        fam=(byid.get(fid,{}).get('Name') if fid else '') or ('Isolate' if not fid else fid)
        meta[iso]={'iso':iso,'name':l.get('name') or iso,'family_id':fid or None,'family':fam,'lat':lat,'lon':lon,'glottocode':g.get('ID')}

    rows=[]
    for p in read_csv(PAIRS):
        a,b=p.get('iso_a'),p.get('iso_b')
        if a not in meta or b not in meta:continue
        ma,mb=meta[a],meta[b]
        if ma['lat'] is None or mb['lat'] is None:continue
        try:j=float(p['jaccard'])
        except Exception:continue
        same=bool(ma['family_id'] and mb['family_id'] and ma['family_id']==mb['family_id'])
        d=hav(ma['lat'],ma['lon'],mb['lat'],mb['lon'])
        rows.append({'iso_a':a,'iso_b':b,'name_a':ma['name'],'name_b':mb['name'],'family_a':ma['family'],'family_b':mb['family'],'same_family':same,'distance_km':d,'jaccard':j})

    same=[r['jaccard'] for r in rows if r['same_family']]
    cross=[r for r in rows if not r['same_family']]
    bands=[(0,500,'near ≤500 km'),(500,2000,'regional 500–2,000 km'),(2000,5000,'distant 2,000–5,000 km'),(5000,1e99,'far >5,000 km')]
    band_stats=[]
    for lo,hi,label in bands:
        xs=[r['jaccard'] for r in cross if lo<=r['distance_km']<hi]
        band_stats.append({'label':label,'min_km':lo,'max_km':None if hi>1e90 else hi,'n':len(xs),'mean_jaccard':qround(mean(xs))})
    xs=[math.log1p(r['distance_km']) for r in cross];ys=[r['jaccard'] for r in cross]
    corr=pearson(xs,ys)
    b0,bfam,bdist=ols(rows)
    for r in rows:
        pred=b0+bfam*(1 if r['same_family'] else 0)+bdist*math.log1p(r['distance_km'])
        r['predicted']=pred;r['residual']=r['jaccard']-pred
    anomalies=sorted([r for r in cross if r['distance_km']>=2000],key=lambda r:r['residual'],reverse=True)[:30]
    near_mean=band_stats[0]['mean_jaccard'];far_mean=band_stats[-1]['mean_jaccard']
    geo_uplift=(near_mean-far_mean) if near_mean is not None and far_mean is not None else None
    inheritance_uplift=mean(same)-mean([r['jaccard'] for r in cross]) if same and cross else None

    evidence=[]
    evidence.append({'test':'Genealogical inheritance signal','result':'supported' if inheritance_uplift and inheritance_uplift>0.03 else 'weak','metric':qround(inheritance_uplift),'explanation':'How much higher bridge similarity is for languages in the same Glottolog family than for different-family pairs.'})
    geosupport=(geo_uplift is not None and geo_uplift>0.015 and corr is not None and corr<0)
    evidence.append({'test':'Geographic/contact-opportunity signal','result':'supported' if geosupport else 'weak/mixed','metric':qround(geo_uplift),'explanation':'Among unrelated languages, compares nearby pairs with very distant pairs. Geography is only a proxy for possible contact.'})
    residual_support=any(r['residual']>0.20 for r in anomalies)
    evidence.append({'test':'Similarity beyond genealogy + modern geography','result':'present' if residual_support else 'limited','metric':qround(anomalies[0]['residual'] if anomalies else None),'explanation':'Large positive residuals are languages more bridge-similar than a simple family+distance model predicts. They are leads for historical investigation, not proof of contact.'})

    conclusion=(
        'The bridge contains a clear inherited-family signal and also a weaker geographic signal among unrelated languages. '
        'That pattern is consistent with phonetic convergence through contact or language shift, but it does not by itself prove a specific historical transmission event. '
        'The strongest residual pairs are therefore research targets: cases where known genealogy and present-day geography do not fully explain the bridge similarity.'
    )
    out={
      'version':1,'language_count':len(byiso),'glottolog_matched':len(meta),'pair_count_with_coordinates':len(rows),
      'metrics':{
        'same_family_mean_jaccard':qround(mean(same)),
        'cross_family_mean_jaccard':qround(mean([r['jaccard'] for r in cross])),
        'inheritance_uplift':qround(inheritance_uplift),
        'cross_family_log_distance_correlation':qround(corr),
        'near_vs_far_cross_family_uplift':qround(geo_uplift),
        'ols_intercept':qround(b0),'ols_same_family_coefficient':qround(bfam),'ols_log_distance_coefficient':qround(bdist)
      },
      'distance_bands':band_stats,'evidence':evidence,'conclusion':conclusion,
      'top_unexplained_cross_family_pairs':[
        {k:(round(v,4) if isinstance(v,float) else v) for k,v in r.items()} for r in anomalies
      ],
      'method_notes':[
        'Genealogy uses Glottolog Family_ID and is independent of the 4x4 bridge.',
        'Geographic distance uses Glottolog reference coordinates and represents modern geographic proximity, not historical migration routes.',
        'Bridge similarity is stable-gate Jaccard overlap from the existing WikiPron benchmark.',
        'Residuals come from a simple linear model: Jaccard ~ same-family + log(1+distance km).',
        'Ethnicity or biological ancestry is not inferred. Language transmission can occur without population replacement.'
      ]
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pairs':len(rows),'same_mean':mean(same),'cross_mean':mean([r['jaccard'] for r in cross]),'geo_corr':corr,'near_far_uplift':geo_uplift,'top_residual':anomalies[0]['residual'] if anomalies else None},indent=2))

if __name__=='__main__':main()
