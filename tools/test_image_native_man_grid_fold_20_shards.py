#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,io,json,math,os,re,statistics,unicodedata,urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
MODEL=ROOT/'data/man-grid-image-fold-model.json'
PREP=ROOT/'data/image-native-man-grid-fold-lexicon.json.gz'
OUTDIR=ROOT/'data/image-native-man-grid-fold-shards'
OUT=ROOT/'data/image-native-man-grid-fold-results.json'
N=20

# Deliberately broad, historically interesting test set. Matching is by code OR language name.
TARGETS={
 'occitan':({'oc','oci'},{'occitan'}),
 'indonesian':({'id','ind'},{'indonesian'}),
 'hebrew':({'he','heb'},{'hebrew'}),
 'sanskrit':({'sa','san'},{'sanskrit'}),
 'ancient_greek':({'grc'},{'ancient greek'}),
 'greek':({'el','ell'},{'greek','modern greek'}),
 'latin':({'la','lat'},{'latin'}),
 'arabic':({'ar','ara','arb'},{'arabic','standard arabic','modern standard arabic'}),
 'english':({'en','eng'},{'english'}),
 'spanish':({'es','spa'},{'spanish'}),
 'persian':({'fa','fas','per'},{'persian'}),
 'hindi':({'hi','hin'},{'hindi'}),
 'tamil':({'ta','tam'},{'tamil'}),
 'turkish':({'tr','tur'},{'turkish'}),
 'malay':({'ms','msa','zlm'},{'malay','malay (macrolanguage)'})
}

DROP=set(' /[](){}.,;:!?\"“”‘’ˈˌːˑ|‖=~')

def textnorm(s):
 s=unicodedata.normalize('NFKD',str(s)).lower()
 return ''.join(c for c in s if not unicodedata.combining(c))

def concept_key(g):
 x=textnorm(g).strip();x=re.sub(r'\([^)]*\)',' ',x);x=re.sub(r'\[[^]]*\]',' ',x)
 x=re.sub(r'^(to|a|an|the)\s+','',x);x=x.split(';')[0].strip();x=re.sub(r'\s+',' ',x)
 if len(x)<2 or len(x)>90:return ''
 if any(x.startswith(z) for z in ('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')):return ''
 return x

def ipa_tokens(s):
 # Raw IPA symbol sequence only. No 4x4/16-state/category mapping.
 s=unicodedata.normalize('NFKD',str(s).strip())
 out=[]
 for c in s:
  if c in DROP or unicodedata.combining(c):continue
  if c.isspace():continue
  out.append(c)
 return tuple(out)

def word_tokens(s):
 return tuple(c for c in textnorm(s) if c.isalpha())

def sounds(o):
 vals=[]
 for z in o.get('sounds') or []:
  x=z.get('ipa')
  if isinstance(x,str):vals.append(x)
  elif isinstance(x,list):vals.extend(str(y) for y in x if y)
 return vals

def glosses(o):
 vals=[]
 for s in o.get('senses') or []:
  vals.extend(str(x) for x in (s.get('glosses') or []) if x)
  vals.extend(str(x) for x in (s.get('raw_glosses') or []) if x)
 return vals

def canon_lang(o):
 lc=str(o.get('lang_code') or '').lower();ln=str(o.get('lang') or '').lower().strip()
 for k,(codes,names) in TARGETS.items():
  if lc in codes or ln in names:return k
 return ''

def edit_sim(a,b):
 a=tuple(a);b=tuple(b);n=len(a);m=len(b)
 if not n or not m:return 0.0
 dp=list(range(m+1))
 for i in range(1,n+1):
  nd=[i]+[0]*m
  for j in range(1,m+1):
   nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+(a[i-1]!=b[j-1]))
  dp=nd
 return max(0.0,1.0-dp[m]/max(n,m))

def prepare():
 if not MODEL.exists():raise SystemExit('missing image-native fold model')
 by=defaultdict(lambda:defaultdict(list));scanned=kept=0
 req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-image-native-man-grid/1.0'})
 with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
  for line in f:
   scanned+=1
   try:o=json.loads(line)
   except Exception:continue
   lang=canon_lang(o)
   if not lang:continue
   word=str(o.get('word') or '').strip()
   if not word:continue
   ipas=[]
   for ipa in sounds(o):
    t=ipa_tokens(ipa)
    if 2<=len(t)<=40 and t not in [tuple(x['ipa']) for x in ipas]:ipas.append({'raw':ipa,'ipa':list(t)})
   if not ipas:continue
   cs=[]
   for g in glosses(o)[:8]:
    c=concept_key(g)
    if c and c not in cs:cs.append(c)
   for c in cs[:5]:
    bucket=by[c][lang]
    for p in ipas[:3]:
     item={'word':word,'orth':list(word_tokens(word)),'ipa':p['ipa'],'ipa_raw':p['raw']}
     if item not in bucket and len(bucket)<8:bucket.append(item);kept+=1
 matched={c:dict(v) for c,v in by.items() if len(v)>=2}
 payload={'version':1,'source':RAW,'model':json.loads(MODEL.read_text()),'entries_scanned':scanned,'kept_forms':kept,'matched_concepts':len(matched),'languages':sorted(TARGETS),'concepts':matched}
 PREP.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(PREP,'wt',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False)
 print(json.dumps({'entries_scanned':scanned,'kept_forms':kept,'matched_concepts':len(matched),'languages':len(TARGETS)}))

def best(A,B,key,fold=False):
 z=0.0
 for a in A:
  aa=tuple(a[key]);aa=aa[::-1] if fold else aa
  for b in B:z=max(z,edit_sim(aa,tuple(b[key])))
 return z

def initstat():
 return {'n':0,'direct_sum':0.0,'fold_sum':0.0,'null_fold_sum':0.0,'orth_direct_sum':0.0,'orth_fold_sum':0.0,'fold_wins_direct':0,'direct_wins_fold':0,'ties':0,'fold_beats_null':0,'delta_sum':0.0,'delta_sq_sum':0.0}

def shard(i):
 with gzip.open(PREP,'rt',encoding='utf-8') as f:x=json.load(f)
 concepts=x['concepts'];names=sorted(concepts);stats=defaultdict(initstat)
 for pos,c in enumerate(names):
  if pos%N!=i:continue
  langs=sorted(concepts[c])
  for ai in range(len(langs)):
   for bi in range(ai+1,len(langs)):
    a,b=langs[ai],langs[bi];A=concepts[c][a];B=concepts[c][b];key=f'{a}|{b}'
    d=best(A,B,'ipa',False);m=best(A,B,'ipa',True);od=best(A,B,'orth',False);om=best(A,B,'orth',True)
    # Same source meaning against five deterministic wrong meanings in target language.
    null=[]
    for k in range(5):
     for step in range(1,len(names)+1):
      wc=names[(pos+97*(k+1)+31*i+step)%len(names)]
      if wc!=c and b in concepts[wc]:
       null.append(best(A,concepts[wc][b],'ipa',True));break
    nf=statistics.mean(null) if null else 0.0
    s=stats[key];s['n']+=1;s['direct_sum']+=d;s['fold_sum']+=m;s['null_fold_sum']+=nf;s['orth_direct_sum']+=od;s['orth_fold_sum']+=om
    delta=m-d;s['delta_sum']+=delta;s['delta_sq_sum']+=delta*delta
    if delta>1e-12:s['fold_wins_direct']+=1
    elif delta<-1e-12:s['direct_wins_fold']+=1
    else:s['ties']+=1
    if m>nf+1e-12:s['fold_beats_null']+=1
 OUTDIR.mkdir(parents=True,exist_ok=True);p=OUTDIR/f'shard-{i:02d}.json';p.write_text(json.dumps({'shard':i,'pairs':stats},ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'shard':i,'pairs':len(stats),'comparisons':sum(v['n'] for v in stats.values())}))

def merge():
 total=defaultdict(initstat)
 for i in range(N):
  x=json.loads((OUTDIR/f'shard-{i:02d}.json').read_text())
  for key,v in x['pairs'].items():
   t=total[key]
   for k,val in v.items():t[k]+=val
 rows=[]
 for key,s in total.items():
  n=s['n'];
  if n<20:continue
  a,b=key.split('|');dm=s['direct_sum']/n;fm=s['fold_sum']/n;nm=s['null_fold_sum']/n;od=s['orth_direct_sum']/n;om=s['orth_fold_sum']/n;delta=s['delta_sum']/n
  var=max(0.0,(s['delta_sq_sum']/n)-delta*delta);se=math.sqrt(var/n) if n>1 else 0.0;ci=[delta-1.96*se,delta+1.96*se]
  rows.append({'a':a,'b':b,'n':n,'direct_ipa':dm,'literal_fold_ipa':fm,'wrong_meaning_fold_ipa':nm,'fold_minus_direct':delta,'fold_minus_direct_approx95':ci,'fold_wins_direct':s['fold_wins_direct'],'direct_wins_fold':s['direct_wins_fold'],'ties':s['ties'],'fold_beats_wrong_meaning':s['fold_beats_null'],'orth_direct':od,'orth_literal_fold':om,'supports_literal_image_fold':bool(fm>dm and fm>nm and s['fold_wins_direct']>s['direct_wins_fold'] and ci[0]>0)})
 rows.sort(key=lambda r:(r['fold_minus_direct'],r['n']),reverse=True)
 oi=next((r for r in rows if {r['a'],r['b']}=={'occitan','indonesian'}),None)
 positive=[r for r in rows if r['supports_literal_image_fold']]
 hub=defaultdict(list)
 for r in rows:
  hub[r['a']].append(r['literal_fold_ipa']);hub[r['b']].append(r['literal_fold_ipa'])
 hubs=sorted(({'language':k,'mean_fold_compatibility':statistics.mean(v),'pair_count':len(v)} for k,v in hub.items()),key=lambda z:z['mean_fold_compatibility'],reverse=True)
 result={'version':1,'test':'Image-native Man-grid literal bilateral fold — raw IPA, 20 shards','shards':N,'model':json.loads(MODEL.read_text()),'design':{'primary_transform':'Only the visible bilateral fold is used: raw IPA token order is mirrored/reversed.','prohibited':'No 4x4, no 16-state bridge, no 16x16 gates, no row/column/transpose operators, no place/manner/voice transforms, no reconstructed-root forms.','matching':'Exact normalized English meanings from one raw Wiktextract pass.','control':'For each same-meaning pair, folded source is also compared with deterministic wrong meanings in the target language.','score':'Normalized Levenshtein similarity on raw normalized IPA symbols; orthographic reversal is secondary only.','success':'Folded same-meaning IPA must beat direct and wrong-meaning folded IPA, win more concepts than it loses, and have approximate paired 95% interval for fold-minus-direct entirely above zero.'},'occitan_indonesian':oi,'positive_pairs':positive,'pair_results':rows,'language_fold_hubs':hubs,'boundary':'This tests the literal bilateral fold visible in the supplied Man-grid image. It does not assume or import phonetic values for unlabeled manuscript cells.'}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'tested_pairs':len(rows),'positive_pairs':len(positive),'occitan_indonesian':oi,'top_pairs':rows[:10]},ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
 if a.cmd=='prepare':prepare()
 elif a.cmd=='shard':shard(a.id)
 else:merge()
if __name__=='__main__':main()
