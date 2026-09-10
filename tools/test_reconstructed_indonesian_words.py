#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,io,json,math,os,random,re,statistics,unicodedata,urllib.request
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
PREP=ROOT/'data/reconstructed-indonesian-prepared.json'
OUTDIR=ROOT/'data/reconstructed-indonesian-shards'
OUT=ROOT/'data/reconstructed-indonesian-results.json'
RAW_URL=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
N=20
CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']

def normtxt(s):
 s=unicodedata.normalize('NFKD',str(s)).lower();s=''.join(c for c in s if not unicodedata.combining(c));s=re.sub(r'\([^)]*\)|\[[^]]*\]',' ',s);s=re.sub(r'^(to|a|an|the)\s+','',s);s=s.split(';')[0];return re.sub(r'\s+',' ',s).strip()
def token_cell(ch):
 x=unicodedata.normalize('NFKD',ch).lower().replace('ˈ','').replace('ˌ','').replace('ː','')
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
def ipa_path(ipa):
 out=[]
 for ch in str(ipa).strip('/[] '):
  c=token_cell(ch)
  if c and (not out or out[-1]!=c):out.append(c)
 return tuple(out)
def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
def sim(a,b):
 if not a or not b:return 0.0
 n,m=len(a),len(b);dp=list(range(m+1))
 for i in range(1,n+1):
  nd=[i]+[0]*m;ra,ca=feat(a[i-1])
  for j in range(1,m+1):
   rb,cb=feat(b[j-1]);sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
   nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+sub)
  dp=nd
 return max(0.0,1-dp[m]/max(n,m))
def xform(p,op):
 q=[]
 for c in p:
  r='ABCD'.index(c[0]);k=int(c[1])-1
  if 'row' in op:r=3-r
  if 'col' in op:k=3-k
  q.append('ABCD'[r]+str(k+1))
 if 'reverse' in op:q=q[::-1]
 return tuple(q)
OPS=['identity','reverse','row','col','row_col','reverse_row','reverse_col','reverse_row_col']
def apply(p,op):
 if op=='identity':return tuple(p)
 return xform(p,op)
def prepare():
 gloss=defaultdict(list);req=urllib.request.Request(RAW_URL,headers={'User-Agent':'Vardath-phonetic-research/4.0'})
 with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
  for line in f:
   try:o=json.loads(line)
   except:continue
   if str(o.get('lang_code') or '')!='ind':continue
   word=str(o.get('word') or '').strip();paths=[]
   for s in o.get('sounds') or []:
    ipa=s.get('ipa');vals=[ipa] if isinstance(ipa,str) else (ipa if isinstance(ipa,list) else [])
    for z in vals:
     p=ipa_path(z)
     if len(p)>=2 and p not in paths:paths.append(p)
   if not word or not paths:continue
   gs=[]
   for s in o.get('senses') or []:gs+=(s.get('glosses') or [])+(s.get('raw_glosses') or [])
   for g in gs[:8]:
    k=normtxt(g)
    if 1<len(k)<=90:
     for p in paths[:3]:gloss[k].append({'word':word,'path':list(p)})
 PREP.write_text(json.dumps({'concepts':gloss},ensure_ascii=False),encoding='utf-8');print(len(gloss))
def shard(i):
 roots=json.loads(DICT.read_text(encoding='utf-8'))['entries'];ind=json.loads(PREP.read_text(encoding='utf-8'))['concepts'];rng=random.Random(137+i);allkeys=list(ind);rows=[];controls=[]
 chosen=[e for j,e in enumerate(roots) if j%N==i]
 for e in chosen:
  k=normtxt(e.get('meaning',''));targets=ind.get(k)
  if not targets:continue
  rp=tuple(e['path']);best={op:max(sim(apply(rp,op),tuple(t['path'])) for t in targets) for op in OPS};winner=max(best,key=best.get)
  rows.append({'meaning':k,'root_form':e.get('form',''),'best_indonesian_word':max(targets,key=lambda t:sim(apply(rp,winner),tuple(t['path'])))['word'],'scores':best,'best_operator':winner,'best_score':best[winner]})
  wrong=[]
  for wk in rng.sample(allkeys,min(10,len(allkeys))):
   if wk==k:continue
   wrong.extend(ind[wk][:1])
  if wrong:controls.append(max(sim(apply(rp,winner),tuple(t['path'])) for t in wrong))
 OUTDIR.mkdir(parents=True,exist_ok=True);out={'shard':i,'root_entries':len(chosen),'matched_meanings':len(rows),'mean_by_operator':{op:statistics.mean(r['scores'][op] for r in rows) if rows else 0 for op in OPS},'best_operator_counts':{op:sum(r['best_operator']==op for r in rows) for op in OPS},'mean_best':statistics.mean(r['best_score'] for r in rows) if rows else 0,'mean_wrong_control':statistics.mean(controls) if controls else 0,'examples':sorted(rows,key=lambda r:r['best_score'],reverse=True)[:30]}
 (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:out[k] for k in ('shard','matched_meanings','mean_best','mean_wrong_control')}))
def merge():
 xs=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)];total=sum(x['matched_meanings'] for x in xs)
 w=lambda key:sum(x[key]*x['matched_meanings'] for x in xs)/total if total else 0
 opmeans={op:sum(x['mean_by_operator'][op]*x['matched_meanings'] for x in xs)/total if total else 0 for op in OPS};counts={op:sum(x['best_operator_counts'][op] for x in xs) for op in OPS};bestop=max(opmeans,key=opmeans.get)
 res={'version':1,'test':'reconstructed original-language vs Indonesian meaning-matched word test','shards':N,'matched_meanings':total,'mean_by_operator':opmeans,'best_global_operator':bestop,'best_operator_counts':counts,'mean_best_per_word':w('mean_best'),'mean_wrong_meaning_control':w('mean_wrong_control'),'signal_over_control':w('mean_best')-w('mean_wrong_control'),'interpretation_boundary':'Meaning-matched phonetic/grid compatibility is structural evidence only; it does not by itself establish ancestry or geography.','top_examples':sorted(sum((x['examples'] for x in xs),[]),key=lambda r:r['best_score'],reverse=True)[:100]}
 OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res,ensure_ascii=False,indent=2))
def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();{'prepare':prepare,'merge':merge}.get(a.cmd,lambda:shard(a.id))()
if __name__=='__main__':main()
