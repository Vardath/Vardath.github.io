#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,io,json,math,os,re,statistics,unicodedata,urllib.request
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW_URL=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
LEX=ROOT/'data/occitan-indonesian-matched-lexicon.json'
OUTDIR=ROOT/'data/occitan-indonesian-mirror-word-shards'
OUT=ROOT/'data/occitan-indonesian-mirror-words.json'
N=20
CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
OPS=['identity','reverse','place','reverse+place','manner','reverse+manner','place+manner','reverse+place+manner']

def textnorm(s):
 s=unicodedata.normalize('NFKD',str(s)).lower()
 return ''.join(c for c in s if not unicodedata.combining(c))

def concept_key(g):
 x=textnorm(g).strip();x=re.sub(r'\([^)]*\)',' ',x);x=re.sub(r'\[[^]]*\]',' ',x);x=re.sub(r'^(to|a|an|the)\s+','',x);x=x.split(';')[0].strip();x=re.sub(r'\s+',' ',x)
 if len(x)<2 or len(x)>90:return ''
 if any(x.startswith(z) for z in ('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')):return ''
 return x

def token_cell(tok):
 x=textnorm(tok).replace('ˈ','').replace('ˌ','').replace('ː','').replace(':','')
 if not x:return None
 if any(c in x for c in 'ieyɪɨɘeɛæ'):return 'A1'
 if any(c in x for c in 'aäɐ'):return 'A2'
 if any(c in x for c in 'uoʊɯʉ'):return 'A3'
 if any(c in x for c in 'ɑɔɒ'):return 'A4'
 if any(c in x for c in 'mwɱ'):return 'B1'
 if any(c in x for c in 'nrlɾɹɬ'):return 'B2'
 if any(c in x for c in 'ŋɲjɰ'):return 'B3'
 if any(c in x for c in 'fvwɸβ'):return 'C1'
 if any(c in x for c in 'sšzʃʒθðcçɕʑ'):return 'C2'
 if any(c in x for c in 'xɣχʁ'):return 'C3'
 if any(c in x for c in 'hħʕ'):return 'C4'
 if any(c in x for c in 'pbɓ'):return 'D1'
 if any(c in x for c in 'tdṭḍʈɖ'):return 'D2'
 if any(c in x for c in 'kgqɢɟ'):return 'D3'
 if 'ʔ' in x:return 'D4'
 return None

def ipa_path(ipa):
 out=[]
 for ch in str(ipa).strip('/[] '):
  c=token_cell(ch)
  if c and (not out or out[-1]!=c):out.append(c)
 return tuple(out)

def sounds(o):
 vals=[]
 for s in o.get('sounds') or []:
  x=s.get('ipa')
  if isinstance(x,str):vals.append(x)
  elif isinstance(x,list):vals.extend(str(y) for y in x if y)
 return vals

def glosses(o):
 vals=[]
 for s in o.get('senses') or []:
  vals.extend(str(x) for x in (s.get('glosses') or []) if x);vals.extend(str(x) for x in (s.get('raw_glosses') or []) if x)
 return vals

def prepare():
 # One streaming pass over Kaikki; keep only Occitan and Indonesian pronunciations/glosses.
 req=urllib.request.Request(RAW_URL,headers={'User-Agent':'Vardath-phonetic-research/4.0'})
 by=defaultdict(lambda:{'oci':[],'ind':[]});scanned=kept=0
 with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
  for line in f:
   scanned+=1
   try:o=json.loads(line)
   except Exception:continue
   lc=str(o.get('lang_code') or '').lower();ln=str(o.get('lang') or '').lower()
   side='oci' if lc in {'oc','oci'} or ln=='occitan' else ('ind' if lc in {'id','ind'} or ln=='indonesian' else '')
   if not side:continue
   word=str(o.get('word') or '').strip()
   if not word:continue
   ps=[]
   for ipa in sounds(o):
    p=ipa_path(ipa)
    if len(p)>=2 and p not in ps:ps.append(p)
   if not ps:continue
   cs=[]
   for g in glosses(o)[:8]:
    c=concept_key(g)
    if c and c not in cs:cs.append(c)
   for c in cs[:5]:
    for p in ps[:3]:
     item={'word':word,'path':list(p)}
     if item not in by[c][side] and len(by[c][side])<12:by[c][side].append(item);kept+=1
 matched={c:v for c,v in by.items() if v['oci'] and v['ind']}
 payload={'version':1,'source':RAW_URL,'entries_scanned':scanned,'kept_forms':kept,'matched_concepts':len(matched),'concepts':matched}
 LEX.parent.mkdir(parents=True,exist_ok=True);LEX.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'entries_scanned':scanned,'kept_forms':kept,'matched_concepts':len(matched)}))

def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
@lru_cache(maxsize=1000000)
def psim(a,b):
 a=tuple(a);b=tuple(b);n=len(a);m=len(b)
 if not n or not m:return 0.0
 dp=list(range(m+1))
 for i in range(1,n+1):
  nd=[i]+[0]*m;ra,ca=feat(a[i-1])
  for j in range(1,m+1):
   rb,cb=feat(b[j-1]);sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
   nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+sub)
  dp=nd
 return max(0,1-dp[m]/max(n,m))

def op(p,name):
 pl='place' in name;ma='manner' in name;rv='reverse' in name
 cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
 q=tuple('ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p)
 return q[::-1] if rv else q

def snorm(w):return ''.join(c for c in textnorm(w) if c.isalpha())
@lru_cache(maxsize=1000000)
def ssim(a,b):
 if not a or not b:return 0.0
 n,m=len(a),len(b);dp=list(range(m+1))
 for i in range(1,n+1):
  nd=[i]+[0]*m
  for j in range(1,m+1):nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+(a[i-1]!=b[j-1]))
  dp=nd
 return 1-dp[m]/max(n,m)

def pairmetrics(A,B):
 direct=max((psim(tuple(a['path']),tuple(b['path'])) for a in A for b in B),default=0)
 per={o:max((psim(op(tuple(a['path']),o),tuple(b['path'])) for a in A for b in B),default=0) for o in OPS}
 bo=max(per,key=per.get);best=per[bo];rev=per['reverse']
 od=max((ssim(snorm(a['word']),snorm(b['word'])) for a in A for b in B),default=0)
 orv=max((ssim(snorm(a['word'])[::-1],snorm(b['word'])) for a in A for b in B),default=0)
 exactrev=any(snorm(a['word'])[::-1]==snorm(b['word']) and snorm(a['word']) for a in A for b in B)
 return {'direct':direct,'reverse':rev,'best':best,'best_operator':bo,'orth_direct':od,'orth_reverse':orv,'exact_orth_reverse':bool(exactrev)}

def shard(i):
 x=json.loads(LEX.read_text(encoding='utf-8'));C=x['concepts'];names=sorted(C);chosen=[c for j,c in enumerate(names) if j%N==i];rows=[]
 for c in chosen:
  real=pairmetrics(C[c]['oci'],C[c]['ind'])
  # Ten deterministic wrong-meaning controls. This tests whether transformations exploit meaning-matched structure rather than generic phonotactics.
  controls=[];pos=names.index(c)
  for k in range(10):
   wrong=names[(pos+137*(k+1)+17*i)%len(names)]
   if wrong==c:wrong=names[(pos+1)%len(names)]
   controls.append(pairmetrics(C[c]['oci'],C[wrong]['ind']))
  real['null_direct']=statistics.mean(z['direct'] for z in controls);real['null_reverse']=statistics.mean(z['reverse'] for z in controls);real['null_best']=statistics.mean(z['best'] for z in controls);real['null_orth_reverse']=statistics.mean(z['orth_reverse'] for z in controls)
  rows.append({'concept':c,**real})
 OUTDIR.mkdir(parents=True,exist_ok=True);(OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'n':len(rows),'rows':rows},ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'shard':i,'matched_concepts':len(rows),'reverse_mean':statistics.mean(r['reverse'] for r in rows) if rows else 0,'direct_mean':statistics.mean(r['direct'] for r in rows) if rows else 0}))

def merge():
 shards=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)];rows=[r for x in shards for r in x['rows']];n=len(rows)
 means={k:statistics.mean(r[k] for r in rows) for k in ['direct','reverse','best','orth_direct','orth_reverse','null_direct','null_reverse','null_best','null_orth_reverse']} if rows else {}
 counts={'reverse_beats_direct':sum(r['reverse']>r['direct']+1e-12 for r in rows),'reverse_ties_direct':sum(abs(r['reverse']-r['direct'])<=1e-12 for r in rows),'reverse_beats_wrong_meaning_reverse':sum(r['reverse']>r['null_reverse'] for r in rows),'mirror_best_beats_direct':sum(r['best']>r['direct']+1e-12 for r in rows),'orth_reverse_beats_direct':sum(r['orth_reverse']>r['orth_direct']+1e-12 for r in rows),'exact_reversed_spellings':sum(r['exact_orth_reverse'] for r in rows)}
 ops={o:sum(r['best_operator']==o for r in rows) for o in OPS}
 # A conservative compatibility signal requires semantic-matched reversal to improve on both direct alignment and mismatched-meaning reversal.
 reverse_signal=bool(rows and means['reverse']>means['direct'] and means['reverse']>means['null_reverse'] and counts['reverse_beats_direct']/n>.5)
 mirror_signal=bool(rows and means['best']>means['null_best'] and counts['mirror_best_beats_direct']/n>.5)
 verdict={'matched_meanings':n,'means':means,'counts':counts,'best_operator_counts':ops,'supports_literal_backwards_phonetic_compatibility':reverse_signal,'supports_systematic_mirror_compatibility':mirror_signal}
 result={'version':1,'test':'Occitan <-> Indonesian matched-meaning Mirror-Man and backwards-word compatibility','shards':N,'design':{'lexicon':'One full Kaikki/Wiktextract streaming pass extracts only Occitan and Indonesian entries with usable IPA and English glosses.','matching':'Only exact normalized English gloss/concept matches are compared, preventing arbitrary look-alike word fishing.','phonetic_tests':'Direct gate-path similarity, literal path reversal, and all eight preregistered identity/reverse/place/manner Mirror-Man transforms.','orthographic_tests':'Direct spelling similarity, reversed-Occitan spelling similarity, and exact backwards spelling matches.','null':'For every matched meaning, ten deterministic mismatched Indonesian meanings provide a chance/phonotactic control.','falsification':'Literal backwards compatibility requires reversal to beat direct alignment and wrong-meaning reversal overall, and to improve a majority of matched concepts.'},'verdict':verdict,'boundary':'A positive result would establish a reproducible structural correspondence in this representation, not by itself genealogical descent or geographic origin.'}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(verdict,ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
 if a.cmd=='prepare':prepare()
 elif a.cmd=='shard':shard(a.id)
 else:merge()
if __name__=='__main__':main()
