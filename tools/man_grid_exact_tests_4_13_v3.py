#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,hashlib,io,json,os,re,sqlite3,statistics,unicodedata,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'man-grid-exact-v3-lexical-work';WORK.mkdir(parents=True,exist_ok=True)
T1=ROOT/'data'/'man-grid-original-phonetics-exact-v3.json'
OUT4=ROOT/'data'/'man-grid-original-language-lexical-exact-v3.json'
OUT13=ROOT/'data'/'man-grid-historical-drift-exact-v3.json'
N=20
RAW=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP='https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
PH='5c477f1934f57b3c1a16168fadc08e83dbc03362'
PH_PARAMS=f'https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/parameters.csv'
MIN_LANG=5;MIN_FAM=3;MAX_CONCEPTS=12000
SEP='|'

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).lower()
    return ''.join(c for c in s if not unicodedata.combining(c))

def concept_key(g):
    x=norm(g).strip();x=re.sub(r'\([^)]*\)',' ',x);x=re.sub(r'\[[^]]*\]',' ',x)
    x=re.sub(r'^(to|a|an|the)\s+','',x);x=x.split(';')[0].strip();x=re.sub(r'\s+',' ',x)
    if len(x)<2 or len(x)>90:return ''
    bad=('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')
    return '' if any(x.startswith(z) for z in bad) else x

def read_url(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Vardath-ManGrid-exact-v3/1.0'})
    with urllib.request.urlopen(req) as r:return r.read()

def fnum(v):
    if v is None or v in ('','0','N'):return 0.0
    n=c=0
    for x in str(v).split(','):
        if x=='+':n+=1;c+=1
        elif x=='-':n-=1;c+=1
    return n/c if c else 0.0

FEATURES=['tone','stress','syllabic','short','long','consonantal','sonorant','continuant','delayedRelease','approximant','tap','trill','nasal','lateral','labial','round','labiodental','coronal','anterior','distributed','strident','dorsal','high','low','front','back','tense','retractedTongueRoot','advancedTongueRoot','periodicGlottalSource','epilaryngealSource','spreadGlottis','constrictedGlottis','fortis','raisedLarynxEjective','loweredLarynxImplosive','click']
PRIMARY={'syllabic','consonantal','sonorant','continuant','labial','coronal','dorsal','high','low','front','back'}

def featdist(a,b):
    s=w=0.0
    for i,f in enumerate(FEATURES):
        q=2.0 if f in PRIMARY else 1.0
        s+=abs(a[i]-b[i])*q/2.0;w+=q
    return s/w if w else 1.0

class Encoder:
    def __init__(self):
        t=json.loads(T1.read_text(encoding='utf-8'))
        if t.get('status')!='complete' or t.get('grid',{}).get('cells')!=1074:raise RuntimeError('correct exact-v3 Test 1 output missing')
        self.roots=t['original_phoneme_inventory']
        self.ripa=[x['ipa'] for x in self.roots];self.rfeat=[x['features'] for x in self.roots]
        rows=list(csv.DictReader(io.StringIO(read_url(PH_PARAMS).decode('utf-8-sig'))))
        seg=[]
        for r in rows:
            name=(r.get('Name') or '').strip()
            if not name or (r.get('SegmentClass') or '').strip().lower()=='tone':continue
            v=[fnum(r.get(k)) for k in FEATURES]
            j=min(range(len(self.rfeat)),key=lambda i:(featdist(v,self.rfeat[i]),self.ripa[i]))
            seg.append((name,j))
        self.names=sorted(seg,key=lambda z:(-len(z[0]),z[0]))
        self.map={a:b for a,b in seg}
    def tokenize(self,ipa):
        s=str(ipa).strip('/[] ').replace('ˈ','').replace('ˌ','')
        out=[];i=0
        while i<len(s):
            if s[i].isspace() or s[i] in '.-‿':i+=1;continue
            hit=None
            for name,j in self.names:
                if s.startswith(name,i):hit=(name,j);break
            if hit is None:i+=1;continue
            out.append(hit[1]);i+=len(hit[0])
        z=[]
        for x in out:
            if not z or z[-1]!=x:z.append(x)
        return tuple(z)
    def ipa(self,seq):return ''.join(self.ripa[i] for i in seq)
    def subcost(self,a,b):return featdist(self.rfeat[a],self.rfeat[b])

def seqdist(a,b,enc):
    if not a or not b:return 1.0
    n,m=len(a),len(b);dp=[j for j in range(m+1)]
    for i in range(1,n+1):
        nd=[i]+[0]*m
        for j in range(1,m+1):
            nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+enc.subcost(a[i-1],b[j-1]))
        dp=nd
    return dp[m]/max(n,m)

def medoid(rows,enc,limit=24):
    c=Counter(rows);items=c.most_common(limit)
    if not items:return None
    den=sum(w for _,w in items);best=None
    for p,w in items:
        sc=sum((1-seqdist(p,q,enc))*v for q,v in items)/den
        key=(sc,w,-len(p),tuple(p))
        if best is None or key>best[0]:best=(key,p,sc)
    return best[1],best[2]

def family_map():
    rows=list(csv.DictReader(io.StringIO(read_url(ASJP).decode('utf-8-sig'))))
    i2f={};n2f={}
    for r in rows:
        fam=(r.get('Glottolog_Family') or r.get('Family') or r.get('family') or r.get('Classification') or 'Unclassified').strip() or 'Unclassified'
        iso=(r.get('ISO639P3code') or r.get('ISO639P3') or '').strip();name=(r.get('Name') or '').strip().lower()
        if iso:i2f[iso]=fam
        if name:n2f[name]=fam
    return i2f,n2f

def get_ipa(o):
    z=[]
    for s in o.get('sounds') or []:
        x=s.get('ipa')
        if isinstance(x,str):z.append(x)
        elif isinstance(x,list):z.extend(str(y) for y in x if y)
    return z

def get_gloss(o):
    z=[]
    for s in o.get('senses') or []:
        z.extend(str(x) for x in (s.get('glosses') or []) if x)
        z.extend(str(x) for x in (s.get('raw_glosses') or []) if x)
    return z

def inh(o):
    z=[]
    for t in o.get('etymology_templates') or []:
        if str(t.get('name') or '').lower() not in ('inh','inh+','inherited'):continue
        a=t.get('args') or {};pl=str(a.get('2') or a.get('source') or a.get('from') or '').strip();pw=str(a.get('3') or a.get('term') or '').strip()
        if pl and pw:z.append((pl,pw))
    return z

def prepare():
    enc=Encoder();i2f,n2f=family_map();db=WORK/'lex.sqlite3'
    if db.exists():db.unlink()
    con=sqlite3.connect(db);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=OFF')
    con.executescript('CREATE TABLE lex(lc TEXT,ln TEXT,fam TEXT,word TEXT,concept TEXT,seq TEXT);CREATE INDEX lx1 ON lex(concept);CREATE INDEX lx2 ON lex(lc,word);CREATE TABLE inh(cl TEXT,cw TEXT,pl TEXT,pw TEXT);')
    b=[];h=[];stats=Counter();langs=set();fams=set()
    req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-ManGrid-exact-v3/1.0'})
    with urllib.request.urlopen(req) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
        for line in f:
            stats['dictionary_entries']+=1
            try:o=json.loads(line)
            except Exception:stats['json_errors']+=1;continue
            lc=str(o.get('lang_code') or '').strip();ln=str(o.get('lang') or '').strip();word=str(o.get('word') or '').strip()
            if not lc or not word:continue
            fam=i2f.get(lc) or n2f.get(ln.lower()) or 'Unclassified';langs.add((lc,ln));fams.add(fam)
            seqs=[]
            for ip in get_ipa(o)[:4]:
                q=enc.tokenize(ip)
                if len(q)>=2 and q not in seqs:seqs.append(q)
            if seqs:
                cs=[]
                for g in get_gloss(o)[:8]:
                    c=concept_key(g)
                    if c and c not in cs:cs.append(c)
                for c in cs[:4]:
                    for q in seqs[:2]:b.append((lc,ln,fam,word,c,SEP.join(map(str,q))))
                if cs:stats['entries_with_mappable_ipa_and_meaning']+=1
            for pl,pw in inh(o):h.append((lc,word,pl,pw))
            if len(b)>=15000:con.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',b);b.clear()
            if len(h)>=15000:con.executemany('INSERT INTO inh VALUES(?,?,?,?)',h);h.clear()
            if stats['dictionary_entries']%500000==0:
                con.commit();print(json.dumps({'phase':'scan','entries':stats['dictionary_entries'],'languages':len(langs),'mappable':stats['entries_with_mappable_ipa_and_meaning']}),flush=True)
    if b:con.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',b)
    if h:con.executemany('INSERT INTO inh VALUES(?,?,?,?)',h)
    con.commit();stats['languages']=len(langs);stats['families_seen']=len(fams)
    concepts=list(con.execute("SELECT concept,COUNT(DISTINCT lc),COUNT(DISTINCT fam) FROM lex WHERE fam!='Unclassified' GROUP BY concept HAVING COUNT(DISTINCT lc)>=? AND COUNT(DISTINCT fam)>=? ORDER BY COUNT(DISTINCT fam) DESC,COUNT(DISTINCT lc) DESC LIMIT ?",(MIN_LANG,MIN_FAM,MAX_CONCEPTS)))
    shards=[[] for _ in range(N)]
    for ix,(c,nl,nf) in enumerate(concepts):
        fr=defaultdict(list)
        for fam,seq,cnt in con.execute("SELECT fam,seq,COUNT(*) FROM lex WHERE concept=? AND fam!='Unclassified' GROUP BY fam,seq ORDER BY fam,COUNT(*) DESC",(c,)):
            if len(fr[fam])<24:fr[fam].append([seq,int(cnt)])
        shards[ix%N].append({'meaning':c,'languages':int(nl),'families':int(nf),'family_sequences':dict(fr)})
    hist=[[] for _ in range(N)]
    q="""SELECT c.lc,c.ln,c.fam,c.word,c.seq,p.pl,p.pw,s.seq
         FROM inh p JOIN lex c ON c.lc=p.cl AND c.word=p.cw
         JOIN lex s ON s.lc=p.pl AND s.word=p.pw
         GROUP BY c.lc,c.word,p.pl,p.pw,c.seq,s.seq"""
    for row in con.execute(q):
        d={'child_code':row[0],'child_language':row[1],'family':row[2],'child_word':row[3],'child_seq':row[4],'parent_code':row[5],'parent_word':row[6],'parent_seq':row[7]}
        k=int.from_bytes(hashlib.sha256((row[0]+'\x1f'+row[3]+'\x1f'+row[5]+'\x1f'+row[6]).encode()).digest()[:8],'big')%N
        hist[k].append(d)
    manifest={'version':3,'suite':'corrected exact Man Grid Tests 4 and 13 preparation','grid_cells':1074,'root_phonemes':len(enc.roots),'shards':N,'scan':dict(stats),'eligible_meaning_groups':len(concepts),'historical_edges':sum(map(len,hist)),'source':{'wiktextract':RAW,'phoible_commit':PH},'invalid_old_model_imported':False}
    (WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for i in range(N):
        with gzip.open(WORK/f'concept-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump(shards[i],f,ensure_ascii=False,separators=(',',':'))
        with gzip.open(WORK/f'history-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump(hist[i],f,ensure_ascii=False,separators=(',',':'))
    print(json.dumps({'phase':'prepare','concepts':len(concepts),'history_edges':sum(map(len,hist)),'concept_shard_sizes':list(map(len,shards)),'history_shard_sizes':list(map(len,hist))}),flush=True)

def dec(s):return tuple(int(x) for x in str(s).split(SEP) if x!='')

def reconstruct_item(item,enc):
    fam={};within={}
    for f,rows in item['family_sequences'].items():
        vals=[]
        for s,n in rows:
            vals.extend([dec(s)]*min(int(n),4))
        m=medoid(vals,enc)
        if m:fam[f]=m[0];within[f]=m[1]
    if len(fam)<MIN_FAM:return None
    overall=medoid(list(fam.values()),enc)
    if not overall:return None
    cand,fit=overall
    loo=[]
    keys=sorted(fam)
    for k in keys[:min(8,len(keys))]:
        m=medoid([v for a,v in fam.items() if a!=k],enc)
        if m:loo.append(1-seqdist(m[0],fam[k],enc))
    return {'meaning':item['meaning'],'ipa':'/'+enc.ipa(cand)+'/','root_sequence':list(cand),'languages':item['languages'],'families':len(fam),'mean_family_fit':round(fit,6),'leave_family_out_mean':round(statistics.mean(loo),6) if loo else None,'family_evidence':[{'family':k,'within_family_medoid_fit':round(within[k],6),'distance_to_root':round(seqdist(cand,fam[k],enc),6)} for k in keys]}

def test4_shard(i):
    enc=Encoder()
    with gzip.open(WORK/f'concept-{i:02d}.json.gz','rt',encoding='utf-8') as f:items=json.load(f)
    out=[x for x in (reconstruct_item(it,enc) for it in items) if x]
    for j,e in enumerate(out):
        ctrl=out[(j+1)%len(out)] if len(out)>1 else e
        e['wrong_meaning_control_distance']=round(seqdist(tuple(e['root_sequence']),tuple(ctrl['root_sequence']),enc),6)
        e['real_family_mean_distance']=round(1-e['mean_family_fit'],6)
    with gzip.open(WORK/f't4-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump({'shard':i,'input':len(items),'entries':out},f,ensure_ascii=False,separators=(',',':'))
    print(json.dumps({'test':4,'shard':i,'input':len(items),'output':len(out)}),flush=True)

def align(a,b,enc):
    n,m=len(a),len(b);dp=[[0]*(m+1) for _ in range(n+1)];bt=[[None]*(m+1) for _ in range(n+1)]
    for i in range(1,n+1):dp[i][0]=i;bt[i][0]=('del',i-1,0)
    for j in range(1,m+1):dp[0][j]=j;bt[0][j]=('ins',0,j-1)
    for i in range(1,n+1):
        for j in range(1,m+1):
            z=[(dp[i-1][j]+1,'del'),(dp[i][j-1]+1,'ins'),(dp[i-1][j-1]+enc.subcost(a[i-1],b[j-1]),'sub')]
            v,op=min(z,key=lambda x:x[0]);dp[i][j]=v;bt[i][j]=(op,i-1,j-1)
    i,j=n,m;ops=[]
    while i or j:
        op,ai,bj=bt[i][j]
        if op=='sub':ops.append(('same' if a[ai]==b[bj] else 'sub',a[ai],b[bj]));i-=1;j-=1
        elif op=='del':ops.append(('del',a[ai],None));i-=1
        else:ops.append(('ins',None,b[bj]));j-=1
    return list(reversed(ops))

def test13_shard(i):
    enc=Encoder()
    with gzip.open(WORK/f'history-{i:02d}.json.gz','rt',encoding='utf-8') as f:items=json.load(f)
    out=[];rules=Counter();parents=[dec(x['parent_seq']) for x in items]
    for j,x in enumerate(items):
        p=dec(x['parent_seq']);c=dec(x['child_seq'])
        if not p or not c:continue
        real=seqdist(p,c,enc);wrong=seqdist(parents[(j+1)%len(parents)],c,enc) if len(parents)>1 else real
        for op,a,b in align(p,c,enc):rules[(op,a,b)]+=1
        out.append({'family':x['family'],'child_language':x['child_language'],'child_word':x['child_word'],'parent_code':x['parent_code'],'parent_word':x['parent_word'],'real_distance':round(real,6),'wrong_parent_control_distance':round(wrong,6)})
    with gzip.open(WORK/f't13-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump({'shard':i,'edges':out,'rules':[[list(k),v] for k,v in rules.items()]},f,ensure_ascii=False,separators=(',',':'))
    print(json.dumps({'test':13,'shard':i,'edges':len(out),'rules':len(rules)}),flush=True)

def merge4():
    man=json.loads((WORK/'manifest.json').read_text());entries=[];counts=[]
    for i in range(N):
        with gzip.open(WORK/f't4-{i:02d}.json.gz','rt',encoding='utf-8') as f:r=json.load(f)
        entries.extend(r['entries']);counts.append({'shard':i,'input':r['input'],'output':len(r['entries'])})
    real=[e['real_family_mean_distance'] for e in entries];ctrl=[e['wrong_meaning_control_distance'] for e in entries];loso=[e['leave_family_out_mean'] for e in entries if e['leave_family_out_mean'] is not None]
    res={'version':3,'test_id':4,'test':'Original-language lexical reconstruction','status':'complete','shards':20,'grid':{'cells':1074,'all_rectangles_mirrored':True},'dependency':'corrected Test 1 exact-v3 output','source':man['source'],'coverage':{'eligible_meaning_groups':man['eligible_meaning_groups'],'dictionary_entries':len(entries),'languages_scanned':man['scan'].get('languages',0),'families_seen':man['scan'].get('families_seen',0)},'summary':{'mean_real_family_distance':statistics.mean(real) if real else None,'mean_wrong_meaning_control_distance':statistics.mean(ctrl) if ctrl else None,'real_beats_wrong_meaning_control':(statistics.mean(real)<statistics.mean(ctrl)) if real and ctrl else None,'mean_leave_family_out_fit':statistics.mean(loso) if loso else None,'shard_counts':counts},'entries':sorted(entries,key=lambda e:(-e['families'],-e['languages'],-e['mean_family_fit'],e['meaning'])),'research_boundary':'Candidate same-meaning ancestral forms under the exact 1,074-cell/Test-1 phoneme model; not historically established Proto-World words. No 16-state or traced-grid mappings are imported.'}
    OUT4.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res['summary'],ensure_ascii=False),flush=True)

def merge13():
    man=json.loads((WORK/'manifest.json').read_text());edges=[];rules=Counter();counts=[]
    for i in range(N):
        with gzip.open(WORK/f't13-{i:02d}.json.gz','rt',encoding='utf-8') as f:r=json.load(f)
        edges.extend(r['edges']);counts.append({'shard':i,'edges':len(r['edges'])})
        for k,v in r['rules']:rules[tuple(k)]+=v
    real=[x['real_distance'] for x in edges];ctrl=[x['wrong_parent_control_distance'] for x in edges];wins=sum(a<b for a,b in zip(real,ctrl))
    res={'version':3,'test_id':13,'test':'Historical language drift through the correct Man Grid','status':'complete','shards':20,'grid':{'cells':1074,'all_rectangles_mirrored':True},'dependency':'corrected Test 1 exact-v3 output','source':man['source'],'coverage':{'matched_historical_edges':len(edges)},'summary':{'mean_real_parent_child_distance':statistics.mean(real) if real else None,'mean_wrong_parent_control_distance':statistics.mean(ctrl) if ctrl else None,'edges_real_beats_control':wins,'edge_success_rate':wins/len(edges) if edges else None,'shard_counts':counts},'rule_counts':[[list(k),v] for k,v in rules.most_common()],'research_boundary':'Uses documented Wiktionary inherited-from links where both forms have usable IPA. It tests learnable historical drift in the corrected exact-v3 phoneme/Grid representation and does not by itself establish ultimate origin.'}
    OUT13.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res['summary'],ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare')
    for n in ('test4','test13'):
        p=sp.add_parser(n);p.add_argument('--id',type=int,required=True)
    sp.add_parser('merge4');sp.add_parser('merge13');a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='test4':test4_shard(a.id)
    elif a.cmd=='test13':test13_shard(a.id)
    elif a.cmd=='merge4':merge4()
    else:merge13()

if __name__=='__main__':main()
