#!/usr/bin/env python3
"""Aggregate benchmark for the experimental 3–4–5 phonetic pyramid codec."""
from __future__ import annotations
import csv, io, json, math, urllib.request
from collections import defaultdict
from pathlib import Path

PH="5c477f1934f57b3c1a16168fadc08e83dbc03362"
BASE=f"https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/"
ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'data/phonetic-benchmark-languages.csv'
OUT=ROOT/'data/pyramid-benchmark-summary.json'
FEATURES=["tone","stress","syllabic","short","long","consonantal","sonorant","continuant","delayedRelease","approximant","tap","trill","nasal","lateral","labial","round","labiodental","coronal","anterior","distributed","strident","dorsal","high","low","front","back","tense","retractedTongueRoot","advancedTongueRoot","periodicGlottalSource","epilaryngealSource","spreadGlottis","constrictedGlottis","fortis","raisedLarynxEjective","loweredLarynxImplosive","click"]
PRIMARY={"syllabic","consonantal","sonorant","continuant","labial","coronal","dorsal","high","low","front","back"}

def get(name):
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"Vardath-Pyramid-Benchmark/1.1"})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read().decode('utf-8-sig')

def fnum(v):
    if v in (None,'','0','N'):return 0.0
    s=c=0
    for x in str(v).split(','):
        if x=='+':s+=1;c+=1
        elif x=='-':s-=1;c+=1
    return s/c if c else 0.0

def plus(v):return fnum(v)>.25

def classify(p):
    sc=(p.get('SegmentClass') or '').lower()
    if sc=='tone' or plus(p.get('tone')):return None
    if sc=='vowel' or (plus(p.get('syllabic')) and not plus(p.get('consonantal'))):
        vert=fnum(p.get('high'))-fnum(p.get('low')); horiz=fnum(p.get('front'))-fnum(p.get('back'))
        if vert>=0:return 'A1' if horiz>=0 else 'A3'
        return 'A2' if horiz>=0 else 'A4'
    row='B' if plus(p.get('sonorant')) else ('C' if plus(p.get('continuant')) else 'D')
    places=[('1',fnum(p.get('labial'))),('2',fnum(p.get('coronal'))),('3',fnum(p.get('dorsal')))]
    places.sort(key=lambda x:x[1],reverse=True)
    return row+(places[0][0] if places[0][1]>.25 else '4')

def fd(a,b):
    num=den=0.0
    for f in FEATURES:
        w=2.0 if f in PRIMARY else 1.0
        num+=w*(abs(fnum(a.get(f))-fnum(b.get(f)))/2);den+=w
    return num/den if den else 1.0

def latent(p):
    c=classify(p)
    if not c:return None
    ri='ABCD'.index(c[0]);ci=int(c[1])-1
    if c[0]=='A':
        dx=max(-1,min(1,(fnum(p.get('back'))-fnum(p.get('front')))/2))
        dy=max(-1,min(1,(fnum(p.get('low'))-fnum(p.get('high')))/2))
    else:
        lab,cor,dor=fnum(p.get('labial')),fnum(p.get('coronal')),fnum(p.get('dorsal'))
        dx=max(-1,min(1,(dor-lab+.35*(dor-cor))/2))
        dy=max(-1,min(1,(fnum(p.get('continuant'))-fnum(p.get('sonorant'))+.35*fnum(p.get('delayedRelease')))/2))
    return ((ci+.5+.42*dx)/4,(ri+.5+.42*dy)/4)

def cell(p,n):
    q=latent(p)
    if not q:return None
    x,y=q
    col=min(n-1,int(max(0,min(.999999,x))*n));row=min(n-1,int(max(0,min(.999999,y))*n))
    return row*n+col

def nearest(src,targets):return min(targets,key=lambda p:fd(src,p)) if targets else None

def route(src,targets,mode):
    if mode=='plain':
        b=nearest(src,targets);return b,bool(b),None
    if mode in ('5','4','3'):
        n=int(mode);cs=[p for p in targets if cell(p,n)==cell(src,n)]
        return (nearest(src,cs) if cs else None),bool(cs),n
    for n in (5,4,3):
        cs=[p for p in targets if cell(p,n)==cell(src,n)]
        if cs:return nearest(src,cs),True,n
    b=nearest(src,targets);return b,False,None

def load():
    langs=list(csv.DictReader(io.StringIO(get('languages.csv'))))
    params=list(csv.DictReader(io.StringIO(get('parameters.csv'))))
    vals=list(csv.DictReader(io.StringIO(get('values.csv'))))
    lang_iso={r.get('ID'):(r.get('ISO639P3code') or '').strip() for r in langs}
    pmap={r.get('ID'):r for r in params}
    inv_phones=defaultdict(list);inv_iso={}
    for v in vals:
        pid=v.get('Parameter_ID');iid=v.get('Inventory_ID');lid=v.get('Language_ID');p=pmap.get(pid)
        if not iid or not p:continue
        if lid and iid not in inv_iso:inv_iso[iid]=lang_iso.get(lid,'')
        if classify(p):inv_phones[iid].append(p)
    by_iso=defaultdict(list)
    for iid,ps in inv_phones.items():
        iso=inv_iso.get(iid,'')
        if iso and ps:by_iso[iso].append((iid,ps))
    return by_iso

def main():
    canonical=[r for r in csv.DictReader(CANON.open(encoding='utf-8')) if r.get('canonical','').lower()=='true']
    names={r['iso']:r.get('name',r['iso']) for r in canonical}
    by_iso=load();inventories={};missing=[]
    for iso in names:
        opts=by_iso.get(iso,[])
        if not opts:missing.append(iso);continue
        inventories[iso]=max(opts,key=lambda x:len(x[1]))[1]
    isos=sorted(inventories);modes=['plain','5','4','3','adaptive']
    agg={m:defaultdict(float) for m in modes};pair_wins={m:0 for m in modes};rt_wins={m:0 for m in modes}
    adaptive_layers={'5':0,'4':0,'3':0,'fallback':0};pairs=0
    for a in isos:
        srcs=inventories[a]
        for b in isos:
            if a==b:continue
            tgts=inventories[b];pairs+=1;pairmeans={};rtmeans={}
            for m in modes:
                fds=[];rtds=[];covered=outputs=exact=returned=rtexact=0
                for p in srcs:
                    q,cov,layer=route(p,tgts,m)
                    if cov:covered+=1
                    if m=='adaptive':adaptive_layers[str(layer) if layer else 'fallback']+=1
                    if not q:continue
                    outputs+=1;d=fd(p,q);fds.append(d)
                    if p.get('Name')==q.get('Name'):exact+=1
                    back,_,_=route(q,srcs,m)
                    if back:
                        returned+=1;rd=fd(p,back);rtds.append(rd)
                        if p.get('Name')==back.get('Name'):rtexact+=1
                z=agg[m];z['source_phones']+=len(srcs);z['coverage']+=covered;z['outputs']+=outputs;z['exact']+=exact;z['forward_loss_sum']+=sum(fds);z['forward_loss_n']+=len(fds);z['returned']+=returned;z['roundtrip_exact']+=rtexact;z['return_loss_sum']+=sum(rtds);z['return_loss_n']+=len(rtds)
                pairmeans[m]=sum(fds)/len(fds) if fds else math.inf
                rtmeans[m]=sum(rtds)/len(rtds) if rtds else math.inf
            pair_wins[min(modes,key=lambda m:pairmeans[m])]+=1
            rt_wins[min(modes,key=lambda m:rtmeans[m])]+=1
    strategies={}
    for m in modes:
        z=agg[m];n=z['source_phones'] or 1
        strategies[m]={
            'source_phone_tests':int(z['source_phones']),'same_region_coverage':int(z['coverage']),'coverage_rate':z['coverage']/n,
            'outputs':int(z['outputs']),'exact_forward':int(z['exact']),'exact_forward_rate':z['exact']/n,
            'mean_forward_loss':z['forward_loss_sum']/z['forward_loss_n'] if z['forward_loss_n'] else None,
            'roundtrip_returned':int(z['returned']),'roundtrip_exact':int(z['roundtrip_exact']),'roundtrip_exact_rate':z['roundtrip_exact']/n,
            'mean_roundtrip_loss':z['return_loss_sum']/z['return_loss_n'] if z['return_loss_n'] else None,
            'pairwise_forward_wins':pair_wins[m],'pairwise_roundtrip_wins':rt_wins[m]
        }
    OUT.write_text(json.dumps({
        'benchmark_version':2,'phoible_commit':PH,'canonical_languages_requested':len(names),
        'canonical_languages_with_phoible_inventory':len(isos),'missing_canonical_isos':missing,'ordered_language_pairs':pairs,
        'strategy_order':modes,'strategies':strategies,'adaptive_route_counts':adaptive_layers,
        'interpretation':'Experimental codec benchmark. Lower feature loss is better; coverage and round-trip exact recovery must be considered together. This does not establish linguistic universality.'
    },indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'languages':len(isos),'pairs':pairs,'missing':len(missing)},indent=2))
if __name__=='__main__':main()
