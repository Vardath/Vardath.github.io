#!/usr/bin/env python3
import argparse, csv, hashlib, json, math, re, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

USER_AGENT = 'VardathCosmologyCorpus/1.0 (public research; GitHub Actions)'
OUTROOT = Path('research/masonic_alchemy_corpus_results')
WORK = Path('research/masonic_alchemy_corpus_work')

SHARDS = [
    {'id':0,'channel':'commons','tradition':'masonic','target':'freemasonry','control':'heraldry'},
    {'id':1,'channel':'commons','tradition':'masonic','target':'masonic','control':'fraternal order'},
    {'id':2,'channel':'commons','tradition':'masonic','target':'freemason','control':'architectural drawing'},
    {'id':3,'channel':'commons','tradition':'masonic','target':'masonic lodge','control':'ceremonial dress'},
    {'id':4,'channel':'commons','tradition':'masonic','target':'masonic symbolism','control':'Christian symbolism'},
    {'id':5,'channel':'commons','tradition':'alchemy','target':'alchemy','control':'historical chemistry'},
    {'id':6,'channel':'commons','tradition':'alchemy','target':'alchemical','control':'astronomy'},
    {'id':7,'channel':'commons','tradition':'alchemy','target':'alchemist','control':'botany'},
    {'id':8,'channel':'commons','tradition':'alchemy','target':'alchemical manuscript','control':'medical illustration'},
    {'id':9,'channel':'commons','tradition':'alchemy','target':'alchemical illustration','control':'emblem book'},
    {'id':10,'channel':'openlibrary','tradition':'masonic','target':'subject:freemasonry','control':'subject:heraldry'},
    {'id':11,'channel':'openlibrary','tradition':'masonic','target':'freemasonry','control':'fraternal organizations'},
    {'id':12,'channel':'openlibrary','tradition':'masonic','target':'subject:freemasons','control':'architecture'},
    {'id':13,'channel':'openlibrary','tradition':'masonic','target':'masonic','control':'ceremonial dress'},
    {'id':14,'channel':'openlibrary','tradition':'masonic','target':'masonic symbolism','control':'christian symbolism'},
    {'id':15,'channel':'openlibrary','tradition':'alchemy','target':'subject:alchemy','control':'subject:chemistry'},
    {'id':16,'channel':'openlibrary','tradition':'alchemy','target':'alchemy','control':'astronomy'},
    {'id':17,'channel':'openlibrary','tradition':'alchemy','target':'subject:alchemists','control':'botany'},
    {'id':18,'channel':'openlibrary','tradition':'alchemy','target':'alchemical','control':'medicine'},
    {'id':19,'channel':'openlibrary','tradition':'alchemy','target':'alchemist','control':'emblems'},
]

MOTIFS = {
 'axis':[r'\baxis\b',r'\baxial\b',r'\bpillar(?:s)?\b',r'\bcolumn(?:s)?\b',r'\bstaff\b',r'\brod\b',r'\bpole\b',r'\btree\b',r'\btower\b',r'\bobelisk\b',r'\bmountain\b',r'vertical support'],
 'gate_ladder':[r'\bgate(?:s)?\b',r'\bdoor(?:s)?\b',r'\bportal(?:s)?\b',r'\barch(?:es)?\b',r'\bthreshold\b',r'\bladder(?:s)?\b',r'\bstair(?:s|way)?\b',r'\bsteps?\b',r'\bpassage\b',r'\bentrance\b'],
 'serpent_braid':[r'\bserpent(?:s)?\b',r'\bsnake(?:s)?\b',r'\bdragon(?:s)?\b',r'\bouroboros\b',r'\buroboros\b',r'\bcaduceus\b',r'\bentwin(?:e|ed|ing)\b',r'\bintertwin(?:e|ed|ing)\b',r'\bbraid(?:ed|ing|s)?\b',r'\bplait(?:ed|ing|s)?\b'],
 'enclosure':[r'\bcircle\b',r'\bcircular\b',r'\bring(?:s)?\b',r'\bglobe\b',r'\bsphere\b',r'\begg\b',r'\boval\b',r'\bmandorla\b',r'\bhalo\b',r'\benclos(?:e|ed|ure)\b',r'\bboundary\b'],
 'node_radiance':[r'\beye(?:s)?\b',r'all[- ]seeing eye',r'eye of providence',r'\bstar(?:s)?\b',r'\bsun\b',r'\bmoon\b',r'solar (?:disc|disk)',r'lunar (?:disc|disk)',r'\brosette\b',r'\bradiant\b',r'\bradiance\b',r'\brays?\b',r'\bjewel\b',r'\bflame\b',r'central light'],
 'four_eight':[r'\bfourfold\b',r'\bfour[- ]part\b',r'\bquadripartite\b',r'\bquatrefoil\b',r'\bsquare\b',r'\bquadrate\b',r'\beightfold\b',r'\boctagon(?:al)?\b',r'eight[- ]point(?:ed)?',r'eight[- ]ray(?:ed)?',r'eight[- ]lobed'],
 'water_vessel':[r'\bwater\b',r'\briver(?:s)?\b',r'\bsea\b',r'\bocean\b',r'\bfountain\b',r'\bvessel\b',r'\bcup\b',r'\bchalice\b',r'\bflask\b',r'\bretort\b',r'\balembic\b',r'\bbath\b'],
 'paired_polarity':[r'\bpair(?:ed|s)?\b',r'\btwin(?:s)?\b',r'\bdouble\b',r'\boppos(?:e|ed|ing|ite)\b',r'sun (?:and|&) moon',r'moon (?:and|&) sun',r'king (?:and|&) queen',r'queen (?:and|&) king',r'male (?:and|&) female',r'female (?:and|&) male',r'two pillars?',r'two columns?',r'black (?:and|&) white',r'white (?:and|&) black']
}
NEGATIVE = {
 'portrait':[r'\bportrait(?:s)?\b',r'\bbust(?:s)?\b'],
 'horse':[r'\bhorse(?:s)?\b',r'\bequestrian\b'],
 'music':[r'\bmusical instrument(?:s)?\b',r'\bviolin\b',r'\bharp\b',r'\blute\b'],
 'furniture':[r'\bfurniture\b',r'\bchair(?:s)?\b',r'\btable(?:s)?\b'],
 'landscape':[r'\blandscape(?:s)?\b',r'\bscenery\b'],
 'garment':[r'\bgarment(?:s)?\b',r'\bcostume(?:s)?\b',r'\bdress\b']
}
RX={k:re.compile('|'.join(v),re.I) for k,v in MOTIFS.items()}
NRX={k:re.compile('|'.join(v),re.I) for k,v in NEGATIVE.items()}
TARGET_LABEL_RX=re.compile(r'\b(?:free\s*mason(?:ry|s)?|masonic|alchemy|alchemical|alchemist(?:s)?)\b',re.I)
MASONIC_RX=re.compile(r'\b(?:free\s*mason(?:ry|s)?|masonic)\b',re.I)
ALCHEMY_RX=re.compile(r'\b(?:alchemy|alchemical|alchemist(?:s)?)\b',re.I)

PAIRS = {
 'axis+gate_ladder':('axis','gate_ladder'),
 'enclosure+node_radiance':('enclosure','node_radiance'),
 'four_eight+node_radiance':('four_eight','node_radiance'),
 'axis+paired_polarity':('axis','paired_polarity'),
 'serpent_braid+axis':('serpent_braid','axis'),
 'water_vessel+enclosure':('water_vessel','enclosure'),
 'paired_polarity+node_radiance':('paired_polarity','node_radiance'),
}

def fetch_json(url, tries=4):
    err=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=45) as r:
                return json.loads(r.read().decode('utf-8','replace'))
        except Exception as e:
            err=e; time.sleep(1.5*(i+1))
    raise RuntimeError(f'fetch failed {url}: {err}')

def year_from_text(text):
    m=re.search(r'\|\s*date\s*=\s*[^\n]*?\b(1[0-9]{3}|20[0-2][0-9])\b',text,re.I)
    if m: return int(m.group(1))
    ys=[int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)',text)]
    return min(ys) if ys else None

def century_bin(y):
    if y is None:return 'unknown'
    if y<1500:return 'pre1500'
    c=(y//100)*100
    return f'{c}s'

def word_bin(n):
    if n<40:return '000-039'
    if n<80:return '040-079'
    if n<160:return '080-159'
    if n<320:return '160-319'
    return '320+'

def flags_for(text):
    f={k:bool(rx.search(text)) for k,rx in RX.items()}
    n={k:bool(rx.search(text)) for k,rx in NRX.items()}
    return f,n

def make_record(source,channel,tradition,cohort,rid,title,text,url,image_url='',year=None,query=''):
    text=re.sub(r'\s+',' ',text or '').strip(); title=(title or '').strip(); scoring=(title+' | '+text).lower()
    f,n=flags_for(scoring); wc=len(re.findall(r'\b\w+\b',scoring))
    return {'source':source,'channel':channel,'tradition':tradition,'cohort':cohort,'id':str(rid),'title':title,'text':text[:2500],'url':url,'image_url':image_url,'year':year,'century_bin':century_bin(year),'word_count':wc,'word_bin':word_bin(wc),'query':query,'flags':f,'negative':n,'family_count':sum(f.values())}

def commons_search(query,tradition,cohort,limit=300):
    out=[]; offset=0
    while len(out)<limit:
        params={'action':'query','format':'json','formatversion':'2','generator':'search','gsrsearch':query,'gsrnamespace':'6','gsrlimit':min(50,limit-len(out)),'gsroffset':offset,'prop':'imageinfo|revisions','iiprop':'url','iiurlwidth':'640','rvprop':'content','rvslots':'main','origin':'*'}
        data=fetch_json('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)); pages=data.get('query',{}).get('pages',[])
        if not pages:break
        for p in pages:
            title=p.get('title',''); revs=p.get('revisions') or []; wt=''
            if revs: wt=((revs[0].get('slots',{}).get('main',{}) or {}).get('content','') or '')
            ii=(p.get('imageinfo') or [{}])[0]; url='https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe=':/()_,.-'); image=ii.get('thumburl') or ii.get('url') or ''
            rec=make_record('Wikimedia Commons','commons',tradition,cohort,p.get('pageid',''),title,wt,url,image,year_from_text(wt),query); combined=title+' '+wt
            if cohort=='control' and TARGET_LABEL_RX.search(combined):continue
            if cohort=='target':
                rx=MASONIC_RX if tradition=='masonic' else ALCHEMY_RX
                if not rx.search(combined):continue
            out.append(rec)
            if len(out)>=limit:break
        cont=data.get('continue',{})
        if 'gsroffset' not in cont:break
        offset=cont['gsroffset']; time.sleep(0.15)
    return out

def openlibrary_search(query,tradition,cohort,limit=400):
    out=[]; page=1
    while len(out)<limit and page<=8:
        fields='key,title,subtitle,subject,author_name,first_publish_year,cover_i'; params={'q':query,'fields':fields,'limit':min(100,limit-len(out)),'page':page}
        data=fetch_json('https://openlibrary.org/search.json?'+urllib.parse.urlencode(params)); docs=data.get('docs') or []
        if not docs:break
        for d in docs:
            title=d.get('title') or ''; subtitle=d.get('subtitle') or ''; subjects=d.get('subject') or []
            if isinstance(subjects,str):subjects=[subjects]
            body=' | '.join([subtitle]+[str(x) for x in subjects[:80]]); combined=title+' | '+body
            if cohort=='control' and TARGET_LABEL_RX.search(combined):continue
            if cohort=='target':
                rx=MASONIC_RX if tradition=='masonic' else ALCHEMY_RX
                if not rx.search(combined):continue
            key=d.get('key') or ''; y=d.get('first_publish_year')
            try:y=int(y) if y is not None else None
            except:y=None
            cover=d.get('cover_i'); image=f'https://covers.openlibrary.org/b/id/{cover}-M.jpg' if cover else ''; url='https://openlibrary.org'+key if key.startswith('/') else 'https://openlibrary.org/search?q='+urllib.parse.quote(query)
            out.append(make_record('Open Library','openlibrary',tradition,cohort,key,title,body,url,image,y,query))
            if len(out)>=limit:break
        page+=1; time.sleep(0.15)
    return out

def dedupe(records):
    seen=set();out=[]
    for r in records:
        key=(r['source'],r['id'] or hashlib.sha1((r['title']+'|'+r['url']).encode()).hexdigest())
        if key in seen:continue
        seen.add(key);out.append(r)
    return out

def run_shard(i):
    cfg=SHARDS[i]; fn=commons_search if cfg['channel']=='commons' else openlibrary_search; lim=300 if cfg['channel']=='commons' else 400
    target=fn(cfg['target'],cfg['tradition'],'target',lim); control=fn(cfg['control'],cfg['tradition'],'control',lim)
    payload={'protocol':'masonic-alchemy-v1','shard':i,'config':cfg,'counts':{'target':len(target),'control':len(control)},'records':target+control}
    WORK.mkdir(parents=True,exist_ok=True); p=WORK/f'shard-{i:02d}.json'; p.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf8'); print(json.dumps({'shard':i,'config':cfg,'counts':payload['counts']},indent=2))

def near_match(records):
    groups=defaultdict(lambda:{'target':[],'control':[]})
    for r in records:groups[(r['channel'],r['tradition'],r['word_bin'])][r['cohort']].append(r)
    mt=[];mc=[]
    for key,g in groups.items():
        targets=sorted(g['target'],key=lambda r:(r['source'],r['id'])); controls=list(g['control']); used=set()
        for t in targets:
            best=None;bestscore=None
            for j,c in enumerate(controls):
                if j in used:continue
                ty=t['year'];cy=c['year']
                if ty is None and cy is None: yd=0
                elif ty is None or cy is None: yd=250
                else: yd=abs(ty-cy)
                samecent=0 if t['century_bin']==c['century_bin'] else 1
                score=(samecent,yd,hashlib.sha1((c['source']+c['id']).encode()).hexdigest())
                if bestscore is None or score<bestscore:bestscore=score;best=j
            if best is not None:used.add(best);mt.append(t);mc.append(controls[best])
    return mt,mc

def logcomb(n,k):
    if k<0 or k>n:return float('-inf')
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)

def fisher_two_sided(a,b,c,d):
    r1=a+b;r2=c+d;c1=a+c;n=r1+r2;lo=max(0,c1-r2);hi=min(r1,c1)
    def lp(x):return logcomb(c1,x)+logcomb(n-c1,r1-x)-logcomb(n,r1)
    obs=lp(a); vals=[lp(x) for x in range(lo,hi+1) if lp(x)<=obs+1e-12]
    if not vals:return 1.0
    m=max(vals);return min(1.0,sum(math.exp(v-m) for v in vals)*math.exp(m))

def effect(a,n1,b,n2):
    p1=a/n1 if n1 else 0;p2=b/n2 if n2 else 0;rr=(p1/p2) if p2 else (float('inf') if p1 else 1.0);aa=a+0.5;bb=n1-a+0.5;cc=b+0.5;dd=n2-b+0.5;orr=(aa*dd)/(bb*cc);return p1,p2,rr,orr,fisher_two_sided(a,n1-a,b,n2-b)

def bh(rows):
    m=len(rows);order=sorted(range(m),key=lambda i:rows[i]['p']);qs=[1.0]*m;prev=1.0
    for rank_rev,idx in enumerate(reversed(order),1):
        rank=m-rank_rev+1;q=min(prev,rows[idx]['p']*m/rank);qs[idx]=q;prev=q
    for r,q in zip(rows,qs):r['q']=q

def test_stat(name,t,c,pred):
    a=sum(1 for r in t if pred(r));b=sum(1 for r in c if pred(r));p1,p2,rr,orr,p=effect(a,len(t),b,len(c));return {'test':name,'target_n':len(t),'control_n':len(c),'target_hits':a,'control_hits':b,'target_rate':p1,'control_rate':p2,'rr':rr,'or':orr,'p':p}

def merge():
    files=sorted(WORK.glob('shard-*.json'))
    if len(files)!=20:raise SystemExit(f'Need 20 shard files, got {len(files)}')
    payloads=[json.loads(p.read_text(encoding='utf8')) for p in files];records=dedupe([r for x in payloads for r in x['records']]);t,c=near_match(records);tests=[]
    tests.append(test_stat('PRIMARY >=3 predicted families',t,c,lambda r:r['family_count']>=3));tests.append(test_stat('>=2 predicted families',t,c,lambda r:r['family_count']>=2));tests.append(test_stat('>=4 predicted families',t,c,lambda r:r['family_count']>=4))
    for trad in ['masonic','alchemy']:
        tt=[r for r in t if r['tradition']==trad];cc=[r for r in c if r['tradition']==trad];tests.append(test_stat(f'{trad}: >=3 predicted families',tt,cc,lambda r:r['family_count']>=3))
        for k in MOTIFS:tests.append(test_stat(f'{trad}: motif {k}',tt,cc,lambda r,k=k:r['flags'][k]))
        for label,(a,b) in PAIRS.items():tests.append(test_stat(f'{trad}: pair {label}',tt,cc,lambda r,a=a,b=b:r['flags'][a] and r['flags'][b]))
    for k in NEGATIVE:tests.append(test_stat(f'negative {k}',t,c,lambda r,k=k:r['negative'][k]))
    bh(tests);byname={r['test']:r for r in tests};motif_rows=[r for r in tests if ': motif ' in r['test']];pair_rows=[r for r in tests if ': pair ' in r['test']];neg_rows=[r for r in tests if r['test'].startswith('negative ')];source_counts=Counter((r['channel'],r['tradition'],r['cohort']) for r in records);ex=sorted(t,key=lambda r:(-r['family_count'],r['tradition'],r['channel'],r['title']))[:80]
    OUTROOT.mkdir(parents=True,exist_ok=True);(OUTROOT/'shards').mkdir(exist_ok=True)
    for p in files:(OUTROOT/'shards'/p.name).write_text(p.read_text(encoding='utf8'),encoding='utf8')
    def wcsv(path,rows,fields):
        with open(path,'w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in rows])
    fields=['test','target_n','control_n','target_hits','control_hits','target_rate','control_rate','rr','or','p','q'];wcsv(OUTROOT/'all_tests.csv',tests,fields);wcsv(OUTROOT/'motif_stats.csv',motif_rows,fields);wcsv(OUTROOT/'pair_stats.csv',pair_rows,fields);wcsv(OUTROOT/'negative_controls.csv',neg_rows,fields)
    exfields=['source','channel','tradition','id','title','year','family_count','url','image_url']+list(MOTIFS);exrows=[]
    for r in ex:d={k:r.get(k,'') for k in exfields};d.update(r['flags']);exrows.append(d)
    wcsv(OUTROOT/'examples.csv',exrows,exfields)
    summary={'protocol':'masonic-alchemy-v1','status':'complete','shards':20,'raw_records':len(records),'matched_target':len(t),'matched_control':len(c),'raw_counts':{'|'.join(k):v for k,v in source_counts.items()},'primary':byname['PRIMARY >=3 predicted families'],'tests':tests,'shard_counts':[x['counts'] for x in payloads]};(OUTROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    def pct(x):return f'{100*x:.2f}%'
    primary=summary['primary'];lines=['# Freemason + Alchemical Visual Grammar Test — Results','','**Protocol:** preregistered before acquisition; 20 GitHub shards.','','## Corpus','',f'- {len(records):,} unique records after cross-shard deduplication.',f'- {len(t):,} matched target records and {len(c):,} matched controls used in the primary analysis.','- Sources: Wikimedia Commons visual/file metadata and Open Library document metadata.','','## Primary preregistered endpoint','',f"Records with >=3 predicted Vardath families: **{primary['target_hits']}/{primary['target_n']} ({pct(primary['target_rate'])}) target** vs **{primary['control_hits']}/{primary['control_n']} ({pct(primary['control_rate'])}) control**.",f"Risk ratio **{primary['rr']:.2f}x**; odds ratio **{primary['or']:.2f}**; Fisher p={primary['p']:.3g}; BH-FDR q={primary['q']:.3g}.",'','## Tradition-specific package density','']
    for trad in ['masonic','alchemy']:
        r=byname[f'{trad}: >=3 predicted families'];lines += [f"- **{trad.title()}**: {pct(r['target_rate'])} target vs {pct(r['control_rate'])} control; RR {r['rr']:.2f}x; q={r['q']:.3g}."]
    lines += ['','## Strongest predicted motif families by tradition','']
    for trad in ['masonic','alchemy']:
        subset=sorted([r for r in motif_rows if r['test'].startswith(trad+':')],key=lambda r:(-(r['rr'] if math.isfinite(r['rr']) else 999),r['q']));lines.append(f'### {trad.title()}')
        for r in subset[:6]:lines.append(f"- {r['test'].split('motif ',1)[1]}: {pct(r['target_rate'])} vs {pct(r['control_rate'])}; RR {r['rr']:.2f}x; q={r['q']:.3g}")
        lines.append('')
    lines += ['## Predicted pairings','']
    for trad in ['masonic','alchemy']:
        lines.append(f'### {trad.title()}');subset=sorted([r for r in pair_rows if r['test'].startswith(trad+':')],key=lambda r:(r['q'],-(r['rr'] if math.isfinite(r['rr']) else 999)))
        for r in subset:lines.append(f"- {r['test'].split('pair ',1)[1]}: {pct(r['target_rate'])} vs {pct(r['control_rate'])}; RR {r['rr']:.2f}x; q={r['q']:.3g}")
        lines.append('')
    lines += ['## Negative controls','']
    for r in neg_rows:lines.append(f"- {r['test'].replace('negative ','')}: {pct(r['target_rate'])} vs {pct(r['control_rate'])}; RR {r['rr']:.2f}x; q={r['q']:.3g}")
    lines += ['','## Interpretation boundary','','This is a metadata/text-annotation corpus test of symbolic package structure. It can show whether Masonic/alchemical records are unusually rich in the predeclared Vardath projection families relative to neighboring controls. It cannot establish that the traditions encode the Vardath physical cosmology, and it does not replace an image-level blinded test. Retrieval and cataloguing language remain potential confounds.',''];(OUTROOT/'2026-09-13_report.md').write_text('\n'.join(lines),encoding='utf8');print(json.dumps({'unique':len(records),'matched':len(t),'primary':primary},indent=2))

def validate():
    assert len(SHARDS)==20 and [x['id'] for x in SHARDS]==list(range(20));assert len(MOTIFS)==8 and len(NEGATIVE)>=5;print('validated',len(SHARDS),'shards',len(MOTIFS),'motif families')

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');s=sub.add_parser('shard');s.add_argument('--id',type=int,required=True);sub.add_parser('merge');a=ap.parse_args()
    if a.cmd=='validate':validate()
    elif a.cmd=='shard':run_shard(a.id)
    else:merge()
if __name__=='__main__':main()
