#!/usr/bin/env python3
import argparse,csv,json,math,re,time,urllib.parse,urllib.request
from collections import defaultdict
from pathlib import Path
UA='VardathLadderSkyV2/1.0 (public research; GitHub Actions)'
WORK=Path('research/masonic_ladder_sky_v2_work'); OUT=Path('research/masonic_ladder_sky_v2_results')
SHARDS=[
('freemasonry symbols','fraternal symbols'),('masonic symbols','religious symbols'),('freemason symbols','allegorical symbols'),('masonic tracing board','religious diagram'),('freemason tracing board','symbolic diagram'),('masonic emblem','religious emblem'),('freemasonry emblem','occult emblem'),('masonic chart','symbolic chart'),('freemasonry chart','allegorical chart'),('masonic allegory','religious allegory'),('freemasonry allegory','mystical allegory'),('masonic print','symbolic print'),('freemasonry print','religious print'),('masonic engraving','symbolic engraving'),('freemasonry engraving','religious engraving'),('masonic ritual','ritual diagram'),('freemasonry ritual','ceremonial symbolism'),('masonic degree','degree chart'),('freemasonry degree','initiation symbolism'),('masonic lodge symbolism','fraternal lodge symbolism')]
MASON=re.compile(r'\b(?:free\s*mason(?:ry|s)?|masonic)\b',re.I)
LADDER=re.compile(r"\b(?:ladder|ladders|stair|stairs|stairway|staircase|steps|rung|rungs|ascent|ascending|jacob'?s ladder)\b",re.I)
SKY=re.compile(r'\b(?:sky|heaven|heavens|heavenly|star|stars|stellar|sun|solar|moon|lunar|celestial|firmament|zodiac|constellation|constellations|cloud|clouds|vault|canopy|astral)\b',re.I)
STRUCT=re.compile(r'\b(?:rail|rails|rung|rungs|crossbar|crossbars|parallel|grid|gridded|lattice|mesh|net|network|interlace|interlaced|woven|crossing|crossings|transverse|framework|trellis)\b',re.I)
AXIS=re.compile(r'\b(?:pillar|pillars|column|columns|rod|staff|tree|tower|obelisk|axis|axial)\b',re.I)
NEG={k:re.compile(v,re.I) for k,v in {
'portrait':r'\b(?:portrait|portraits|bust|busts)\b','horse':r'\b(?:horse|horses|equestrian)\b','furniture':r'\b(?:furniture|chair|chairs|table|tables)\b','garment':r'\b(?:garment|garments|costume|costumes|dress)\b','landscape':r'\b(?:landscape|landscapes|scenery)\b'}.items()}

def getj(url,tries=10):
    err=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode('utf8','replace'))
        except Exception as e:
            err=e; time.sleep(min(40,4*(i+1)))
    raise RuntimeError(f'fetch failed {err}')

def year(text):
    ys=[int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)',text)]; return min(ys) if ys else None

def wbin(n): return '0-39' if n<40 else '40-79' if n<80 else '80-159' if n<160 else '160-319' if n<320 else '320+'

def record(p,cohort,q):
    title=p.get('title',''); revs=p.get('revisions') or []; text=''
    if revs:text=((revs[0].get('slots',{}).get('main',{}) or {}).get('content','') or '')
    ii=(p.get('imageinfo') or [{}])[0]; combined=re.sub(r'\s+',' ',title+' | '+text); wc=len(re.findall(r'\b\w+\b',combined)); y=year(text)
    return {'id':p.get('pageid'),'cohort':cohort,'query':q,'title':title,'text':combined[:5000],'url':'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe=':/()_,.-'),'image_url':ii.get('thumburl') or ii.get('url') or '','year':y,'word_count':wc,'word_bin':wbin(wc),'ladder':bool(LADDER.search(combined)),'sky':bool(SKY.search(combined)),'structure':bool(STRUCT.search(combined)),'axis':bool(AXIS.search(combined)),'negative':{k:bool(rx.search(combined)) for k,rx in NEG.items()}}

def search(q,cohort,limit=100):
    out=[]; offset=0
    while len(out)<limit:
        params={'action':'query','format':'json','formatversion':'2','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':50,'gsroffset':offset,'prop':'imageinfo|revisions','iiprop':'url','iiurlwidth':640,'rvprop':'content','rvslots':'main','origin':'*'}
        data=getj('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)); pages=data.get('query',{}).get('pages',[])
        if not pages:break
        for p in pages:
            r=record(p,cohort,q); s=r['title']+' '+r['text']
            if cohort=='target' and not MASON.search(s):continue
            if cohort=='control' and MASON.search(s):continue
            out.append(r)
            if len(out)>=limit:break
        cont=data.get('continue',{}).get('gsroffset')
        if cont is None:break
        offset=cont; time.sleep(.12)
    return out

def run_shard(i):
    tq,cq=SHARDS[i]; t=search(tq,'target'); c=search(cq,'control'); WORK.mkdir(parents=True,exist_ok=True)
    (WORK/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'target_query':tq,'control_query':cq,'target_n':len(t),'control_n':len(c),'records':t+c},ensure_ascii=False),encoding='utf8')
    print(json.dumps({'shard':i,'target':len(t),'control':len(c),'target_ladder':sum(r['ladder'] for r in t),'control_ladder':sum(r['ladder'] for r in c)}))

def dedupe(rs):
    seen=set();out=[]
    for r in rs:
        key=(r['cohort'],r['id'])
        if key in seen:continue
        seen.add(key);out.append(r)
    return out

def match_case_controls(cases,controls):
    groups=defaultdict(list)
    for r in controls:groups[r['word_bin']].append(r)
    mc=[];mn=[];used=set()
    for x in sorted(cases,key=lambda r:(r['word_bin'],r['year'] or 9999,r['id'])):
        best=None;score=None
        for y in groups[x['word_bin']]:
            if y['id'] in used:continue
            d=250 if x['year'] is None or y['year'] is None else abs(x['year']-y['year']); s=(d,abs(x['word_count']-y['word_count']),y['id'])
            if score is None or s<score:score=s;best=y
        if best is not None:used.add(best['id']);mc.append(x);mn.append(best)
    return mc,mn

def lc(n,k):
    if k<0 or k>n:return -1e300
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)

def fisher(a,b,c,d):
    r1=a+b;r2=c+d;c1=a+c;n=r1+r2;lo=max(0,c1-r2);hi=min(r1,c1)
    def lp(x):return lc(c1,x)+lc(n-c1,r1-x)-lc(n,r1)
    o=lp(a);vals=[lp(x) for x in range(lo,hi+1) if lp(x)<=o+1e-12];m=max(vals);return min(1,sum(math.exp(v-m) for v in vals)*math.exp(m))

def stat(name,a,b,pred):
    x=sum(pred(r) for r in a);y=sum(pred(r) for r in b);ra=x/len(a) if a else 0;rb=y/len(b) if b else 0;rr=ra/rb if rb else (float('inf') if ra else 1.0);return {'test':name,'a_n':len(a),'b_n':len(b),'a_hits':x,'b_hits':y,'a_rate':ra,'b_rate':rb,'rr':rr,'p':fisher(x,len(a)-x,y,len(b)-y) if a and b else 1.0}

def bh(rows):
    order=sorted(range(len(rows)),key=lambda i:rows[i]['p']);prev=1;m=len(rows)
    for rev,idx in enumerate(reversed(order),1):rank=m-rev+1;q=min(prev,rows[idx]['p']*m/rank);rows[idx]['q']=q;prev=q

def merge():
    fs=sorted(WORK.glob('shard-*.json'))
    if len(fs)!=20:raise SystemExit(f'need 20 shards, got {len(fs)}')
    payload=[json.loads(p.read_text()) for p in fs];rs=dedupe([r for p in payload for r in p['records']]);target=[r for r in rs if r['cohort']=='target'];control=[r for r in rs if r['cohort']=='control'];cases=[r for r in target if r['ladder']];non=[r for r in target if not r['ladder']];mc,mn=match_case_controls(cases,non);control_ladder=[r for r in control if r['ladder']];ec,enc=match_case_controls(mc,control_ladder)
    tests=[stat('PRIMARY celestial: Masonic ladder vs Masonic non-ladder',mc,mn,lambda r:r['sky']),stat('structure: Masonic ladder vs Masonic non-ladder',mc,mn,lambda r:r['structure']),stat('celestial+structure: Masonic ladder vs Masonic non-ladder',mc,mn,lambda r:r['sky'] and r['structure']),stat('axis: Masonic ladder vs Masonic non-ladder',mc,mn,lambda r:r['axis']),stat('celestial+axis: Masonic ladder vs Masonic non-ladder',mc,mn,lambda r:r['sky'] and r['axis'])]
    if ec and enc:tests.append(stat('external celestial: Masonic ladder vs non-Masonic ladder',ec,enc,lambda r:r['sky']))
    for k in NEG:tests.append(stat('negative '+k,mc,mn,lambda r,k=k:r['negative'][k]))
    bh(tests);OUT.mkdir(parents=True,exist_ok=True)
    conclusive=len(mc)>=25
    summary={'status':'complete','protocol':'masonic-ladder-sky-v2','shards':20,'unique_records':len(rs),'target_records':len(target),'control_records':len(control),'masonic_ladder_records':len(cases),'matched_primary_pairs':len(mc),'control_ladder_records':len(control_ladder),'minimum_pairs_required':25,'conclusive_sample_size':conclusive,'tests':tests,'shard_counts':[{'shard':p['shard'],'target_n':p['target_n'],'control_n':p['control_n']} for p in payload]}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    with open(OUT/'tests.csv','w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(tests[0]));w.writeheader();w.writerows(tests)
    ex=sorted(mc,key=lambda r:(-(int(r['sky'])+int(r['structure'])+int(r['axis'])),r['year'] or 9999,r['title']))
    with open(OUT/'examples.csv','w',newline='',encoding='utf8') as f:
        fields=['id','title','year','ladder','sky','structure','axis','url','image_url','query'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in ex])
    pri=tests[0]; verdict='conclusive sample' if conclusive else 'UNDERPOWERED: fewer than 25 matched Masonic ladder records'
    (OUT/'report.md').write_text(f"# Masonic ladder / sky / lattice validation v2 — results\n\n20 preregistered broad-corpus Wikimedia Commons shards.\n\nUnique records: {len(rs)}. Masonic target records: {len(target)}. Masonic ladder/ascent records: {len(cases)}. Matched primary pairs: {len(mc)}.\n\nSample-size rule: {verdict}.\n\nPrimary celestial context: {pri['a_hits']}/{pri['a_n']} ({100*pri['a_rate']:.2f}%) ladder vs {pri['b_hits']}/{pri['b_n']} ({100*pri['b_rate']:.2f}%) matched Masonic non-ladder; RR {pri['rr']:.2f}x; Fisher p={pri['p']:.4g}; BH q={pri['q']:.4g}.\n\nSee tests.csv for secondary endpoints.\n",encoding='utf8')
    print(json.dumps(summary,indent=2))

def main():
    ap=argparse.ArgumentParser();s=ap.add_subparsers(dest='cmd',required=True);x=s.add_parser('shard');x.add_argument('--id',type=int,required=True);s.add_parser('merge');s.add_parser('validate');a=ap.parse_args()
    if a.cmd=='validate':assert len(SHARDS)==20;print('validated 20 broad-corpus shards')
    elif a.cmd=='shard':run_shard(a.id)
    else:merge()
if __name__=='__main__':main()
