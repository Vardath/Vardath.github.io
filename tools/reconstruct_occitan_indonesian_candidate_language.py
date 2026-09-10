#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,io,json,math,os,re,statistics,unicodedata,urllib.request
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW_URL=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
LEX=ROOT/'data/occitan-indonesian-candidate-prepared.json'
ROOTDICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/occitan-indonesian-candidate-shards'
OUT=ROOT/'data/occitan-indonesian-candidate-results.json'
DICTOUT=ROOT/'data/occitan-indonesian-candidate-language.json'
N=20
CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
OPS=['identity','reverse','place','reverse+place','manner','reverse+manner','place+manner','reverse+place+manner']
REP={'A1':'i','A2':'a','A3':'u','A4':'o','B1':'m','B2':'n','B3':'ŋ','B4':'r','C1':'f','C2':'s','C3':'x','C4':'h','D1':'p','D2':'t','D3':'k','D4':'ʔ'}
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}

def textnorm(s):
 s=unicodedata.normalize('NFKD',str(s)).lower();return ''.join(c for c in s if not unicodedata.combining(c))
def concept_key(g):
 x=textnorm(g).strip();x=re.sub(r'\([^)]*\)|\[[^]]*\]',' ',x);x=re.sub(r'^(to|a|an|the)\s+','',x);x=x.split(';')[0].strip();x=re.sub(r'\s+',' ',x)
 if len(x)<2 or len(x)>90:return ''
 if any(x.startswith(z) for z in ('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')):return ''
 return x

def token_cell(tok):
 x=textnorm(tok).replace('ˈ','').replace('ˌ','').replace('ː','').replace(':','')
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
  x=s.get('ipa');vals += ([x] if isinstance(x,str) else [str(y) for y in x if y] if isinstance(x,list) else [])
 return vals
def glosses(o):
 vals=[]
 for s in o.get('senses') or []: vals += [str(x) for x in (s.get('glosses') or []) if x]+[str(x) for x in (s.get('raw_glosses') or []) if x]
 return vals

def prepare():
 req=urllib.request.Request(RAW_URL,headers={'User-Agent':'Vardath-phonetic-research/5.0'})
 by=defaultdict(lambda:{'oci':[],'ind':[]});scanned=kept=0
 with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
  for line in f:
   scanned+=1
   try:o=json.loads(line)
   except Exception:continue
   lc=str(o.get('lang_code') or '').lower();ln=str(o.get('lang') or '').lower();side='oci' if lc in {'oc','oci'} or ln=='occitan' else ('ind' if lc in {'id','ind'} or ln=='indonesian' else '')
   if not side:continue
   w=str(o.get('word') or '').strip()
   if not w:continue
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
    for p in ps[:2]:
     item={'word':w,'path':list(p)}
     if item not in by[c][side] and len(by[c][side])<4:by[c][side].append(item);kept+=1
 matched={c:v for c,v in by.items() if v['oci'] and v['ind']}
 if len(matched)<100:raise RuntimeError(f'Only {len(matched)} matched concepts extracted')
 LEX.write_text(json.dumps({'version':1,'entries_scanned':scanned,'kept_forms':kept,'matched_concepts':len(matched),'concepts':matched},ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'entries_scanned':scanned,'matched_concepts':len(matched)}))

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
 pl='place' in name;ma='manner' in name;rv='reverse' in name;cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
 q=tuple('ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p);return q[::-1] if rv else q

def align_consensus(a,b):
 a=tuple(a);b=tuple(b);n=len(a);m=len(b);dp=[[0]*(m+1) for _ in range(n+1)];bt=[[None]*(m+1) for _ in range(n+1)]
 for i in range(1,n+1):dp[i][0]=i;bt[i][0]='u'
 for j in range(1,m+1):dp[0][j]=j;bt[0][j]='l'
 for i in range(1,n+1):
  ra,ca=feat(a[i-1])
  for j in range(1,m+1):
   rb,cb=feat(b[j-1]);sub=(abs(ra-rb)+abs(ca-cb))/6;opts=[(dp[i-1][j]+1,'u'),(dp[i][j-1]+1,'l'),(dp[i-1][j-1]+sub,'d')];dp[i][j],bt[i][j]=min(opts,key=lambda x:x[0])
 pairs=[];i=n;j=m
 while i or j:
  z=bt[i][j]
  if z=='d':pairs.append((a[i-1],b[j-1]));i-=1;j-=1
  elif z=='u':pairs.append((a[i-1],None));i-=1
  else:pairs.append((None,b[j-1]));j-=1
 pairs.reverse();out=[]
 for x,y in pairs:
  if x is None:c=y
  elif y is None:c=x
  elif x==y:c=x
  else:
   rx,cx=feat(x);ry,cy=feat(y);r=round((rx+ry)/2);q=round((cx+cy)/2);c='ABCD'[max(0,min(3,r))]+str(max(0,min(3,q))+1)
  if c and (not out or out[-1]!=c):out.append(c)
 return tuple(out)

def infer(A,B):
 best=None
 for a in A:
  pa=tuple(a['path'])
  for b in B:
   pb=tuple(b['path'])
   for oa in OPS:
    aa=op(pa,oa)
    for ob in OPS:
     bb=op(pb,ob);s=psim(aa,bb)
     if best is None or s>best[0]:best=(s,a,b,oa,ob,aa,bb)
 s,a,b,oa,ob,aa,bb=best;latent=align_consensus(aa,bb)
 return {'agreement':s,'occitan_word':a['word'],'indonesian_word':b['word'],'occitan_operator':oa,'indonesian_operator':ob,'path':list(latent),'form':''.join(REP[c] for c in latent),'ipa':'/'+''.join(REP[c] for c in latent)+'/'}

def rootmap():
 d=json.loads(ROOTDICT.read_text(encoding='utf-8'));return {concept_key(x.get('meaning','')):x for x in d['entries'] if concept_key(x.get('meaning',''))}

def shard(i):
 x=json.loads(LEX.read_text(encoding='utf-8'));C=x['concepts'];names=sorted(C);chosen=[c for j,c in enumerate(names) if j%N==i];R=rootmap();rows=[]
 for c in chosen:
  q=infer(C[c]['oci'],C[c]['ind']);root=R.get(c);rp=tuple(root['path']) if root else ()
  if rp:
   q['root_similarity']=psim(tuple(q['path']),rp);q['occitan_root_similarity']=max(psim(tuple(a['path']),rp) for a in C[c]['oci']);q['indonesian_root_similarity']=max(psim(tuple(b['path']),rp) for b in C[c]['ind'])
  else:q['root_similarity']=q['occitan_root_similarity']=q['indonesian_root_similarity']=None
  pos=names.index(c);null=[]
  for k in range(10):
   wrong=names[(pos+131*(k+1)+19*i)%len(names)];wrong=names[(pos+1)%len(names)] if wrong==c else wrong;null.append(infer(C[c]['oci'],C[wrong]['ind'])['agreement'])
  q['null_agreement']=statistics.mean(null);q['agreement_uplift']=q['agreement']-q['null_agreement'];q['meaning']=c;q['confidence']=max(0,min(1,.55*q['agreement']+.25*max(0,q['agreement_uplift'])+.20*(q['root_similarity'] if q['root_similarity'] is not None else q['agreement'])));rows.append(q)
 if not rows:raise RuntimeError(f'Empty shard {i}')
 OUTDIR.mkdir(parents=True,exist_ok=True);(OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'rows':rows},ensure_ascii=False),encoding='utf-8');print(json.dumps({'shard':i,'n':len(rows),'agreement':statistics.mean(r['agreement'] for r in rows)}))

def norm(v):
 s=sum(v);return [z/s for z in v] if s else [0.0]*256
def profile(paths):
 v=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]):
   if a in CELLS and b in CELLS:v[CELLS.index(a)*16+CELLS.index(b)]+=1
 return norm(v)
def cosine(a,b):
 d=sum(x*y for x,y in zip(a,b));aa=sum(x*x for x in a);bb=sum(x*x for x in b);return d/math.sqrt(aa*bb) if aa and bb else 0
def jsd(a,b):
 m=[(x+y)/2 for x,y in zip(a,b)];kl=lambda x,y:sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q);return .5*kl(a,m)+.5*kl(b,m)
def overlap(a,b,k=32):
 A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]);B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k]);return len(A&B)/k
def pscore(a,b):return .55*cosine(a,b)+.30*(1-min(1,jsd(a,b)))+.15*overlap(a,b)
def cellop(c,name):
 r='ABCD'.index(c[0]);q=int(c[1])-1
 if 'manner' in name:r=[0,3,2,1][r]
 if 'place' in name:q=[2,1,0,3][q]
 return 'ABCD'[r]+str(q+1)
def pathop(p,name):
 q=tuple(cellop(c,name) for c in p);return q[::-1] if 'reverse' in name else q
def profbest(src,tgt):return max(pscore(profile([pathop(p,o) for p in src]),tgt) for o in OPS)

def merge():
 xs=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)];rows=[r for x in xs for r in x['rows']]
 if len(rows)<100:raise RuntimeError(f'Only {len(rows)} merged candidates')
 same=[r for r in rows if r['root_similarity'] is not None];opsO=defaultdict(int);opsI=defaultdict(int)
 for r in rows:opsO[r['occitan_operator']]+=1;opsI[r['indonesian_operator']]+=1
 verdict={'candidate_words':len(rows),'mean_occitan_indonesian_parent_agreement':statistics.mean(r['agreement'] for r in rows),'mean_wrong_meaning_parent_agreement':statistics.mean(r['null_agreement'] for r in rows),'mean_agreement_uplift':statistics.mean(r['agreement_uplift'] for r in rows),'root_matched_words':len(same)}
 if same:
  verdict.update({'mean_candidate_to_current_root':statistics.mean(r['root_similarity'] for r in same),'mean_occitan_to_current_root':statistics.mean(r['occitan_root_similarity'] for r in same),'mean_indonesian_to_current_root':statistics.mean(r['indonesian_root_similarity'] for r in same),'candidate_beats_both_children_count':sum(r['root_similarity']>max(r['occitan_root_similarity'],r['indonesian_root_similarity']) for r in same)})
 # Independent language-profile generalization: candidate is inferred only from O+I words; compare to all other canonical profiles.
 bench=json.loads(BENCH.read_text(encoding='utf-8'));langs={r['iso']:{'family':r.get('family') or 'Unclassified','p':norm(list(map(float,r['sample_counts'])))} for r in bench['languages']};rootrows=json.loads(ROOTDICT.read_text(encoding='utf-8'))['entries'];sources={'candidate':[tuple(r['path']) for r in rows],'root':[tuple(r['path']) for r in rootrows]}
 for iso in ('oci','ind','lat'):
  if iso in langs:sources[iso]=None
 scores=defaultdict(list);famwins=defaultdict(int)
 for iso,t in langs.items():
  if iso in {'oci','ind'}:continue
  cur={}
  for k,p in sources.items():
   cur[k]=profbest(p,t['p']) if p is not None else max(pscore(profile([pathop(tuple(),o)]),t['p']) for o in ['identity'])
  # canonical sources use their existing benchmark profile directly under 4x4 profile transforms
  for k in ('oci','ind','lat'):
   if k in langs:
    base=langs[k]['p'];vals=[]
    for o in OPS:
     # transform transition profile by transforming endpoint cells
     z=[0.0]*256
     for a in range(16):
      for b in range(16):
       ca,cb=CELLS[a],CELLS[b];na=CELLS.index(cellop(ca,o));nb=CELLS.index(cellop(cb,o));idx=na*16+nb
       if 'reverse' in o:idx=nb*16+na
       z[idx]+=base[a*16+b]
     vals.append(pscore(z,t['p']))
    cur[k]=max(vals)
  for k,v in cur.items():scores[k].append(v)
  famwins[max(cur,key=cur.get)]+=1
 verdict['heldout_language_profile_scores']={k:statistics.mean(v) for k,v in scores.items()};verdict['best_heldout_profile_predictor']=max(verdict['heldout_language_profile_scores'],key=verdict['heldout_language_profile_scores'].get);verdict['profile_target_wins']=dict(famwins);verdict['occitan_operator_counts']=dict(opsO);verdict['indonesian_operator_counts']=dict(opsI)
 result={'version':1,'test':'20-shard word-by-word Occitan + Indonesian latent candidate language reconstruction','shards':N,'design':{'inference':'For each exact matched English meaning, Occitan and Indonesian IPA paths are independently inverse-transformed through all 8x8 fixed Man-grid operator pairs. The pair with highest mutual agreement is aligned and merged into one latent bridge path. The existing reconstructed dictionary is never used to choose the candidate word.','null':'Each real meaning is compared with ten deterministic wrong Indonesian meanings using the identical 8x8 search.','root_check':'After reconstruction, candidate words are compared with same-meaning entries in the existing 12,000-word reconstruction and against the Occitan/Indonesian child forms.','external_profile_check':'The merged candidate profile is then tested against canonical language profiles excluding Occitan and Indonesian.'},'verdict':verdict,'boundary':'This is an experimental latent phonetic-grid reconstruction, not an attested historical language. Positive generalization is evidence for structure in this representation, not by itself proof of chronology or descent.'}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');rows.sort(key=lambda r:(-r['confidence'],r['meaning']));DICTOUT.write_text(json.dumps({'version':1,'title':'Occitan + Indonesian shared-parent candidate language','summary':verdict,'method':result['design'],'research_boundary':result['boundary'],'entries':rows},ensure_ascii=False),encoding='utf-8');print(json.dumps(verdict,ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();prepare() if a.cmd=='prepare' else shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__':main()
