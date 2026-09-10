#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,io,json,os,random,re,statistics,unicodedata,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
import reconstruct_original_language_all_dictionaries as core

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'historical-drift-shards'; PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data'/'historical-drift-20-shards.json'; N=20
RAW=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ROUTES={
 ('oc','pro'):('occitan','Old Occitan -> Modern Occitan'),('oci','pro'):('occitan','Old Occitan -> Modern Occitan'),
 ('pro','la'):('occitan','Latin -> Old Occitan'),('oc','la'):('occitan','Latin -> Modern Occitan'),('oci','la'):('occitan','Latin -> Modern Occitan'),
 ('ms','ms-cla'):('malayic','Classical Malay -> Malay'),('ms','ms-old'):('malayic','Old Malay -> Malay'),
 ('ms','poz-mly-pro'):('malayic','Proto-Malayic -> Malay'),('ms','poz-pro'):('malayic','Proto-Malayo-Polynesian -> Malay'),
 ('id','ms'):('malayic','Malay -> Indonesian'),('id','ms-cla'):('malayic','Classical Malay -> Indonesian'),
 ('id','ms-old'):('malayic','Old Malay -> Indonesian'),('id','poz-mly-pro'):('malayic','Proto-Malayic -> Indonesian'),
 ('id','poz-pro'):('malayic','Proto-Malayo-Polynesian -> Indonesian')}
TARGET={a for a,b in ROUTES}; CELLS=core.CELLS

def norm(s):
 s=unicodedata.normalize('NFKD',str(s or '')); return ''.join(c for c in s if not unicodedata.combining(c)).lower()
def clean(s):
 s=re.sub(r'^\*+','',str(s or '').strip()); s=re.sub(r'\([^)]*\)','',s); s=s.replace('[[','').replace(']]',''); return re.split(r'[,;/]',s,1)[0].strip()
def path(s):
 z=[]
 for ch in clean(s):
  c=core.token_cell(ch)
  if c and (not z or z[-1]!=c): z.append(c)
 return tuple(z)
def fold(*x): return int.from_bytes(hashlib.sha256('\x1f'.join(map(str,x)).encode()).digest()[:8],'big')%N
def concepts(o):
 z=[]
 for g in core.get_glosses(o)[:8]:
  c=core.concept_key(g)
  if c and c not in z:z.append(c)
  if len(z)==4:break
 return z

def source_term(t):
 n=str(t.get('name') or '').lower(); a=t.get('args') or {}
 if n in {'inh','inh+','inherited'}:
  return n,str(a.get('2') or a.get('source') or a.get('from') or '').strip(),str(a.get('tr') or a.get('transliteration') or a.get('3') or a.get('term') or '').strip()
 if n in {'m','m+'}:
  return n,str(a.get('1') or '').strip(),str(a.get('tr') or a.get('transliteration') or a.get('2') or '').strip()
 return n,'',''

def prepare():
 WORK.mkdir(parents=True,exist_ok=True); pairs=[]; seen=set(); stats=Counter(); pro_words=set(); pro_ipa=set()
 req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-historical-drift/1.0'})
 with urllib.request.urlopen(req) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
  for line in f:
   stats['dictionary_entries']+=1
   try:o=json.loads(line)
   except Exception:stats['json_errors']+=1;continue
   lc=str(o.get('lang_code') or '').strip()
   if lc=='pro':
    w=norm(o.get('word'))
    if w:pro_words.add(w)
    if any(len(core.ipa_path(x))>=2 for x in core.get_ipa(o)):pro_ipa.add(w)
   if lc not in TARGET:continue
   stats['target_'+lc]+=1; dform=clean(o.get('word')); dp=path(dform); cs=concepts(o)
   if len(dp)<2 or not cs:continue
   for t in o.get('etymology_templates') or []:
    rel,src,aform=source_term(t); meta=ROUTES.get((lc,src))
    if not meta or (rel in {'m','m+'} and src not in {'ms-old','ms-cla'}):continue
    ap=path(aform)
    if len(ap)<2:continue
    branch,route=meta
    for meaning in cs:
     p={'branch':branch,'route':route,'meaning':meaning,'ancestor_form':clean(aform),'descendant_form':dform,'ancestor_path':list(ap),'descendant_path':list(dp),'source_code':src,'relation':rel}
     k=(route,meaning,tuple(ap),tuple(dp))
     if k not in seen:seen.add(k);pairs.append(p)
   if stats['dictionary_entries']%1000000==0:print(json.dumps({'entries':stats['dictionary_entries'],'pairs':len(pairs)}),flush=True)
 for p in pairs:
  p['fold']=fold(p['route'],p['meaning'],p['ancestor_form'],p['descendant_form'])
  p['old_occitan_dictionary_attested']=norm(p['ancestor_form']) in pro_words if p['source_code']=='pro' else None
 stats['old_occitan_distinct_words']=len(pro_words);stats['old_occitan_words_with_ipa']=len(pro_ipa);stats['pairs']=len(pairs)
 rc=Counter(p['route'] for p in pairs);bc=Counter(p['branch'] for p in pairs)
 payload={'pairs':pairs,'source_audit':dict(stats),'route_counts':dict(rc),'branch_counts':dict(bc),'design':{
  'folds':20,'source':'complete English Wiktionary Wiktextract stream; explicit inherited/attested historical etymology forms only',
  'primary':'learn descendant-to-ancestor Man-grid cell correspondences on 19 folds and test reconstruction on the held-out fold',
  'null':'learn the identical correspondence model after rotating ancestor forms across meanings within each route',
  'secondary':'same-meaning comparison of older versus younger forms to the existing reconstructed root; descriptive because the root used the broad Wiktextract corpus',
  'representation':'ancestor and descendant spellings are passed through the same coarse 4x4 grapheme-to-gate encoder; this is a structural drift test, not a full historical IPA transcription',
  'no_custom_timeout':True}}
 with gzip.open(PREP,'wt',encoding='utf-8',compresslevel=6) as f:json.dump(payload,f,ensure_ascii=False,separators=(',',':'))
 print(json.dumps({'phase':'prepare','pairs':len(pairs),'routes':dict(rc),'branches':dict(bc),'audit':dict(stats)},ensure_ascii=False),flush=True)

def cost(a,b):
 ra,ca=core.feat(a);rb,cb=core.feat(b);return (abs(ra-rb)+abs(ca-cb))/6
def align(desc,anc):
 a=tuple(desc);b=tuple(anc);n=len(a);m=len(b);gap=.75;dp=[[0.]*(m+1) for _ in range(n+1)];bt=[[None]*(m+1) for _ in range(n+1)]
 for i in range(1,n+1):dp[i][0]=i*gap;bt[i][0]='D'
 for j in range(1,m+1):dp[0][j]=j*gap;bt[0][j]='I'
 for i in range(1,n+1):
  for j in range(1,m+1):
   opts=[(dp[i-1][j-1]+cost(a[i-1],b[j-1]),'M'),(dp[i-1][j]+gap,'D'),(dp[i][j-1]+gap,'I')]
   dp[i][j],bt[i][j]=min(opts,key=lambda x:(x[0],{'M':0,'D':1,'I':2}[x[1]]))
 out=[];i=n;j=m
 while i or j:
  q=bt[i][j]
  if q=='M':out.append((a[i-1],b[j-1]));i-=1;j-=1
  elif q=='D':out.append((a[i-1],None));i-=1
  else:out.append((None,b[j-1]));j-=1
 return list(reversed(out))
def learn(rows,shuffle=False):
 rows=sorted(rows,key=lambda r:(r['meaning'],r['ancestor_form'],r['descendant_form']));aa=[tuple(r['ancestor_path']) for r in rows]
 if shuffle and len(aa)>1:aa=aa[1:]+aa[:1]
 c={x:Counter({x:.25}) for x in CELLS}
 for r,anc in zip(rows,aa):
  for d,a in align(r['descendant_path'],anc):
   if d and a:c[d][a]+=1
 mp={}
 for d in CELLS:
  mx=max(c[d].values());opts=[a for a,n in c[d].items() if n==mx];mp[d]=d if d in opts else sorted(opts)[0]
 return mp
def apply(p,mp):
 z=[]
 for c in p:
  q=mp.get(c,c)
  if not z or z[-1]!=q:z.append(q)
 return tuple(z)
def roots():
 d=json.loads((ROOT/'data/phonetic-original-language-dictionary.json').read_text(encoding='utf-8'))
 return {core.concept_key(e.get('meaning','')):tuple(e.get('path') or ()) for e in d['entries'] if e.get('path')}

def shard(i):
 with gzip.open(PREP,'rt',encoding='utf-8') as f:p=json.load(f)
 R=roots();by=defaultdict(list)
 for x in p['pairs']:by[(x['branch'],x['route'])].append(x)
 out=[];maps=[]
 for (branch,route),rows in sorted(by.items()):
  train=[r for r in rows if r['fold']!=i];test=[r for r in rows if r['fold']==i]
  if len(train)<8 or not test:continue
  mp=learn(train);nm=learn(train,True);maps.append({'branch':branch,'route':route,'fold':i,'train':len(train),'test':len(test),'map':mp,'null_map':nm})
  test=sorted(test,key=lambda r:(r['meaning'],r['ancestor_form']));wrong=[tuple(r['ancestor_path']) for r in test]
  if len(wrong)>1:wrong=wrong[1:]+wrong[:1]
  for k,r in enumerate(test):
   a=tuple(r['ancestor_path']);d=tuple(r['descendant_path']);fs,fo=core.bestfit(d,a);ws,_=core.bestfit(d,wrong[k] if wrong else a);rr=R.get(core.concept_key(r['meaning']))
   z={'branch':branch,'route':route,'meaning':r['meaning'],'raw':core.sim(d,a),'learned':core.sim(apply(d,mp),a),'null':core.sim(apply(d,nm),a),'flex':fs,'wrong_flex':ws,'operator':fo,'ancestor_root':None,'descendant_root':None,'ancestor_root_bestfit':None,'descendant_root_bestfit':None,'old_occitan_dictionary_attested':r.get('old_occitan_dictionary_attested')}
   if rr:
    z['ancestor_root']=core.sim(a,rr);z['descendant_root']=core.sim(d,rr);z['ancestor_root_bestfit']=core.bestfit(a,rr)[0];z['descendant_root_bestfit']=core.bestfit(d,rr)[0]
   out.append(z)
 (WORK/f'result-{i:02d}.json').write_text(json.dumps({'shard':i,'rows':out,'maps':maps},ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'phase':'shard','shard':i,'rows':len(out),'routes':len(maps)}),flush=True)

def ci(v,seed):
 if not v:return [None,None]
 rng=random.Random(seed);n=len(v);x=[]
 for _ in range(4000):x.append(sum(v[rng.randrange(n)] for _ in range(n))/n)
 x.sort();return [x[99],x[3899]]
def summary(rows,seed):
 if not rows:return {'n':0}
 M=lambda k:statistics.mean(r[k] for r in rows);g=[r['learned']-r['raw'] for r in rows];vn=[r['learned']-r['null'] for r in rows];wf=[r['flex']-r['wrong_flex'] for r in rows];rr=[r for r in rows if r['ancestor_root'] is not None]
 o={'n':len(rows),'raw_similarity':M('raw'),'learned_reverse_similarity':M('learned'),'learned_gain':statistics.mean(g),'learned_gain_bootstrap_95':ci(g,seed+1),'shuffled_map_similarity':M('null'),'learned_minus_shuffled':statistics.mean(vn),'learned_minus_shuffled_bootstrap_95':ci(vn,seed+2),'best_flexible_similarity':M('flex'),'wrong_meaning_best_flexible_similarity':M('wrong_flex'),'matched_minus_wrong_flexible':statistics.mean(wf),'matched_minus_wrong_flexible_bootstrap_95':ci(wf,seed+3),'operator_counts':dict(Counter(r['operator'] for r in rows)),'root_matched_n':len(rr)}
 if rr:
  d=[r['ancestor_root']-r['descendant_root'] for r in rr];b=[r['ancestor_root_bestfit']-r['descendant_root_bestfit'] for r in rr]
  o.update({'ancestor_root_similarity':statistics.mean(r['ancestor_root'] for r in rr),'descendant_root_similarity':statistics.mean(r['descendant_root'] for r in rr),'ancestor_minus_descendant_root':statistics.mean(d),'ancestor_minus_descendant_root_bootstrap_95':ci(d,seed+4),'ancestor_root_bestfit':statistics.mean(r['ancestor_root_bestfit'] for r in rr),'descendant_root_bestfit':statistics.mean(r['descendant_root_bestfit'] for r in rr),'ancestor_minus_descendant_root_bestfit':statistics.mean(b),'ancestor_minus_descendant_root_bestfit_bootstrap_95':ci(b,seed+5)})
 a=[r for r in rows if r['old_occitan_dictionary_attested'] is not None]
 if a:o['old_occitan_dictionary_attestation']={'n':len(a),'attested':sum(bool(r['old_occitan_dictionary_attested']) for r in a)}
 return o

def merge():
 with gzip.open(PREP,'rt',encoding='utf-8') as f:p=json.load(f)
 rows=[];maps=[]
 for i in range(N):
  q=json.loads((WORK/f'result-{i:02d}.json').read_text(encoding='utf-8'));rows+=q['rows'];maps+=q['maps']
 br=defaultdict(list);rt=defaultdict(list)
 for r in rows:br[r['branch']].append(r);rt[r['route']].append(r)
 overall=summary(rows,8000);B={b:summary(x,9000+j*50) for j,(b,x) in enumerate(sorted(br.items()))};routes=[]
 for j,(name,x) in enumerate(sorted(rt.items())):
  s=summary(x,10000+j*50);s['route']=name;routes.append(s)
 pos=[]
 for s in routes:
  if s['n']>=30 and s['learned_gain_bootstrap_95'][0]>0 and s['learned_minus_shuffled_bootstrap_95'][0]>0:pos.append(s['route'])
 bp={b:bool(s['n']>=50 and s['learned_gain_bootstrap_95'][0]>0 and s['learned_minus_shuffled_bootstrap_95'][0]>0) for b,s in B.items()}
 rc=overall.get('ancestor_minus_descendant_root_bootstrap_95',[None,None])
 res={'version':1,'test':'Historical language drift / reverse-drift reconstruction — 20 deterministic folds','shards':20,'source_audit':p['source_audit'],'prepared_route_counts':p['route_counts'],'design':p['design'],'tested_pairs':len(rows),'overall':overall,'by_branch':B,'routes':routes,'fold_maps':maps,'verdict':{'supports_cross_validated_reversible_drift_overall':bool(len(rows)>=100 and overall['learned_gain_bootstrap_95'][0]>0 and overall['learned_minus_shuffled_bootstrap_95'][0]>0),'supports_cross_validated_reversible_drift_by_branch':bp,'positive_routes':pos,'older_forms_closer_to_existing_reconstructed_root_descriptively':bool(rc[0] is not None and rc[0]>0),'boundary':'Positive reverse-drift means historical change leaves learnable structure in this Man-grid encoding. It does not by itself identify the ultimate original language, date a split, or prove geography/descent.'}}
 OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'phase':'merge','tested_pairs':len(rows),'verdict':res['verdict'],'overall':overall},ensure_ascii=False,indent=2),flush=True)

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
 if a.cmd=='prepare':prepare()
 elif a.cmd=='shard':shard(a.id)
 else:merge()
if __name__=='__main__':main()
