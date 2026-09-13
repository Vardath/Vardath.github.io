#!/usr/bin/env python3
import argparse, csv, json, math, re, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

UA='VardathLadderSkyTest/1.0 (public research; GitHub Actions)'
WORK=Path('research/masonic_ladder_sky_work')
OUT=Path('research/masonic_ladder_sky_results')

SHARDS=[
('masonic ladder','ladder engraving'),('freemason ladder','ladder illustration'),
('freemasonry ladder','ladder painting'),('masonic tracing board ladder','ladder allegory'),
('masonic symbols ladder','ladder emblem'),('masonic degree ladder','ladder manuscript'),
('masonic lodge ladder','ladder print'),('freemasons ladder','ladder symbol'),
('masonic ritual ladder','ladder iconography'),('masonic diagram ladder','ladder architecture'),
('masonic chart ladder','ladder drawing'),('freemason tracing board ladder','ladder woodcut'),
('freemasonry symbolism ladder','ladder etching'),('masonic allegory ladder','ladder poster'),
('masonic emblem ladder','ladder sculpture'),('masonic teaching ladder','ladder relief'),
('masonic degree chart ladder','ladder fresco'),('freemason symbolism ladder','ladder mosaic'),
('masonic board ladder','ladder diagram'),('freemasonry diagram ladder','ladder artwork')]

MASON=re.compile(r'\b(?:free\s*mason(?:ry|s)?|masonic)\b',re.I)
LADDER=re.compile(r'\b(?:ladder|ladders|stair|stairs|stairway|steps)\b',re.I)
SKY=re.compile(r'\b(?:sky|heaven|heavens|heavenly|star|stars|stellar|sun|moon|celestial|firmament|zodiac|constellation|constellations|cloud|clouds|vault|canopy)\b',re.I)
STRUCT=re.compile(r'\b(?:rail|rails|rung|rungs|crossbar|crossbars|parallel|grid|gridded|lattice|mesh|net|network|interlace|interlaced|woven|crossing|crossings|transverse)\b',re.I)
AXIS=re.compile(r'\b(?:pillar|pillars|column|columns|rod|staff|tree|tower|obelisk|axis|axial)\b',re.I)
NEG={
 'portrait':re.compile(r'\b(?:portrait|portraits|bust|busts)\b',re.I),
 'horse':re.compile(r'\b(?:horse|horses|equestrian)\b',re.I),
 'furniture':re.compile(r'\b(?:furniture|chair|chairs|table|tables)\b',re.I),
 'garment':re.compile(r'\b(?:garment|garments|costume|costumes|dress)\b',re.I),
 'landscape':re.compile(r'\b(?:landscape|landscapes|scenery)\b',re.I),
}

def getj(url,tries=9):
    err=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode('utf8','replace'))
        except Exception as e:
            err=e; time.sleep(min(45,5*(i+1)))
    raise RuntimeError(f'fetch failed: {err}')

def year(text):
    ys=[int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)',text)]
    return min(ys) if ys else None

def wbin(n):
    return '0-39' if n<40 else '40-79' if n<80 else '80-159' if n<160 else '160-319' if n<320 else '320+'

def rec(p,cohort,q):
    title=p.get('title',''); revs=p.get('revisions') or []; text=''
    if revs:text=((revs[0].get('slots',{}).get('main',{}) or {}).get('content','') or '')
    ii=(p.get('imageinfo') or [{}])[0]; combined=re.sub(r'\s+',' ',title+' | '+text)
    wc=len(re.findall(r'\b\w+\b',combined)); y=year(text)
    return {'id':p.get('pageid'),'cohort':cohort,'query':q,'title':title,'text':combined[:3000],
      'url':'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe=':/()_,.-'),
      'image_url':ii.get('thumburl') or ii.get('url') or '','year':y,'word_count':wc,'word_bin':wbin(wc),
      'sky':bool(SKY.search(combined)),'structure':bool(STRUCT.search(combined)),'axis':bool(AXIS.search(combined)),
      'negative':{k:bool(rx.search(combined)) for k,rx in NEG.items()}}

def search(q,cohort):
    params={'action':'query','format':'json','formatversion':'2','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':50,'prop':'imageinfo|revisions','iiprop':'url','iiurlwidth':640,'rvprop':'content','rvslots':'main','origin':'*'}
    data=getj('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)); out=[]
    for p in data.get('query',{}).get('pages',[]):
        r=rec(p,cohort,q); s=r['title']+' '+r['text']
        if not LADDER.search(s): continue
        if cohort=='target' and not MASON.search(s): continue
        if cohort=='control' and MASON.search(s): continue
        out.append(r)
    return out

def run_shard(i):
    tq,cq=SHARDS[i]; t=search(tq,'target'); c=search(cq,'control')
    WORK.mkdir(parents=True,exist_ok=True); p=WORK/f'shard-{i:02d}.json'
    p.write_text(json.dumps({'shard':i,'target_query':tq,'control_query':cq,'target_n':len(t),'control_n':len(c),'records':t+c},ensure_ascii=False),encoding='utf8')
    print(json.dumps({'shard':i,'target':len(t),'control':len(c)}))

def dedupe(rs):
    seen=set(); out=[]
    for r in rs:
        if r['id'] in seen:continue
        seen.add(r['id']); out.append(r)
    return out

def match(rs):
    t=[r for r in rs if r['cohort']=='target']; c=[r for r in rs if r['cohort']=='control']; groups=defaultdict(list)
    for r in c:groups[r['word_bin']].append(r)
    mt=[];mc=[];used=set()
    for x in sorted(t,key=lambda r:(r['word_bin'],r['year'] or 9999,r['id'])):
        pool=groups[x['word_bin']]; best=None;score=None
        for y in pool:
            if y['id'] in used:continue
            d=250 if x['year'] is None or y['year'] is None else abs(x['year']-y['year'])
            s=(d,abs(x['word_count']-y['word_count']),y['id'])
            if score is None or s<score:score=s;best=y
        if best is not None:used.add(best['id']);mt.append(x);mc.append(best)
    return mt,mc

def lc(n,k):
    if k<0 or k>n:return -1e300
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)

def fisher(a,b,c,d):
    r1=a+b;r2=c+d;c1=a+c;n=r1+r2;lo=max(0,c1-r2);hi=min(r1,c1)
    def lp(x):return lc(c1,x)+lc(n-c1,r1-x)-lc(n,r1)
    o=lp(a); vals=[lp(x) for x in range(lo,hi+1) if lp(x)<=o+1e-12];m=max(vals);return min(1,sum(math.exp(v-m) for v in vals)*math.exp(m))

def stat(name,t,c,pred):
    a=sum(pred(x) for x in t);b=sum(pred(x) for x in c);rt=a/len(t) if t else 0;rc=b/len(c) if c else 0
    rr=rt/rc if rc else (float('inf') if rt else 1.0);p=fisher(a,len(t)-a,b,len(c)-b)
    return {'test':name,'target_n':len(t),'control_n':len(c),'target_hits':a,'control_hits':b,'target_rate':rt,'control_rate':rc,'rr':rr,'p':p}

def bh(rows):
    m=len(rows);order=sorted(range(m),key=lambda i:rows[i]['p']);prev=1
    for rev,idx in enumerate(reversed(order),1):
        rank=m-rev+1;q=min(prev,rows[idx]['p']*m/rank);rows[idx]['q']=q;prev=q

def merge():
    fs=sorted(WORK.glob('shard-*.json'))
    if len(fs)!=20:raise SystemExit(f'need 20 shards, got {len(fs)}')
    payload=[json.loads(p.read_text()) for p in fs]; rs=dedupe([r for p in payload for r in p['records']]);t,c=match(rs)
    tests=[stat('PRIMARY celestial context',t,c,lambda r:r['sky']),stat('lattice structure',t,c,lambda r:r['structure']),stat('celestial + structure',t,c,lambda r:r['sky'] and r['structure']),stat('axis context',t,c,lambda r:r['axis']),stat('celestial + axis',t,c,lambda r:r['sky'] and r['axis'])]
    for k in NEG:tests.append(stat('negative '+k,t,c,lambda r,k=k:r['negative'][k]))
    bh(tests);OUT.mkdir(parents=True,exist_ok=True)
    summary={'status':'complete','shards':20,'unique_records':len(rs),'matched_target':len(t),'matched_control':len(c),'tests':tests,'shard_counts':[{'shard':p['shard'],'target_n':p['target_n'],'control_n':p['control_n']} for p in payload]}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    with open(OUT/'tests.csv','w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(tests[0]));w.writeheader();w.writerows(tests)
    ex=sorted(t,key=lambda r:(-(int(r['sky'])+int(r['structure'])+int(r['axis'])),r['title']))[:60]
    with open(OUT/'examples.csv','w',newline='',encoding='utf8') as f:
        fields=['id','title','year','sky','structure','axis','url','image_url','query'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in ex])
    pri=tests[0]
    report=f"""# Masonic ladder / sky / lattice test — results\n\n20 preregistered Wikimedia Commons shards.\n\nUnique records: {len(rs)}. Matched target/control pairs: {len(t)}.\n\nPrimary celestial context: {pri['target_hits']}/{pri['target_n']} ({100*pri['target_rate']:.2f}%) target vs {pri['control_hits']}/{pri['control_n']} ({100*pri['control_rate']:.2f}%) control; RR {pri['rr']:.2f}x; Fisher p={pri['p']:.4g}; BH q={pri['q']:.4g}.\n\nSee tests.csv for all secondary and negative-control endpoints.\n"""
    (OUT/'report.md').write_text(report,encoding='utf8');print(json.dumps(summary,indent=2))

def main():
    ap=argparse.ArgumentParser();s=ap.add_subparsers(dest='cmd',required=True);x=s.add_parser('shard');x.add_argument('--id',type=int,required=True);s.add_parser('merge');s.add_parser('validate');a=ap.parse_args()
    if a.cmd=='validate':assert len(SHARDS)==20;print('validated 20 shards')
    elif a.cmd=='shard':run_shard(a.id)
    else:merge()
if __name__=='__main__':main()
