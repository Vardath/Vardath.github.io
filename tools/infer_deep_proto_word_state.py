#!/usr/bin/env python3
from __future__ import annotations
import json, random, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phonetic-cross-family-proto-meaning.json'
OUTJ=ROOT/'data/phonetic-deep-proto-word-state.json'
OUTM=ROOT/'data/phonetic-deep-proto-word-state.md'
RNG=random.Random(137)
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
OPS=[('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]

def feat(c): return ('ABCD'.index(c[0]),int(c[1])-1)
def sim(a,b):
 n,m=len(a),len(b);dp=[[0.0]*(m+1) for _ in range(n+1)]
 for i in range(n+1):dp[i][0]=i
 for j in range(m+1):dp[0][j]=j
 for i in range(1,n+1):
  for j in range(1,m+1):
   ra,ca=feat(a[i-1]);rb,cb=feat(b[j-1]);sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
   dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+sub)
 return max(0.0,1-dp[n][m]/max(n,m,1))
def transform(p,pl=False,ma=False,rv=False):
 cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
 q=['ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p]
 return q[::-1] if rv else q
def best(a,b): return max((sim(transform(a,pl,ma,rv),b),name) for name,pl,ma,rv in OPS)
def objective(p,forms): return statistics.mean(best(p,f['path'])[0] for f in forms)

def infer(forms):
 # Beam search across lengths 2..6. Start from all 1-state seeds then expand; retain top 160 unique paths per layer.
 beam=[([c],objective([c],forms)) for c in CELLS]
 candidates=[]
 for L in range(1,7):
  beam=sorted(beam,key=lambda x:x[1],reverse=True)[:160]
  if L>=2:candidates.extend(beam[:80])
  if L==6:break
  nxt=[]
  for p,_ in beam:
   for c in CELLS:
    q=p+[c];nxt.append((q,objective(q,forms)))
  beam=nxt
 # small parsimony tie-break discourages longer paths unless they help measurably
 bestp=max(candidates,key=lambda x:x[1]-0.004*max(0,len(x[0])-4))[0]
 score=objective(bestp,forms)
 align=[]
 for f in forms:
  s,op=best(bestp,f['path']);align.append({'family':f['family'],'form':f['form'],'score':round(s,6),'operator':op,'path':f['path']})
 return bestp,score,align

data=json.loads(SRC.read_text(encoding='utf-8'))
results={}
obs=[]
for meaning,x in data['meanings'].items():
 p,s,a=infer(x['forms']);obs.append(s);results[meaning]={'hidden_path':p,'mean_fit':round(s,6),'alignments':a}
obs_mean=statistics.mean(obs)
# Control: shuffle meaning labels independently within each family slot, then infer four pseudo-meanings.
meanings=list(data['meanings'])
slots=['Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian']
def slotform(m,slot):
 for f in data['meanings'][m]['forms']:
  if f['family']==slot or (slot=='Proto-Uralic' and f['family'].startswith('Proto-Uralic')):return f
 raise KeyError((m,slot))
perm=[]
for _ in range(300):
 maps={}
 for slot in slots:
  z=meanings[:];RNG.shuffle(z);maps[slot]=dict(zip(meanings,z))
 vals=[]
 for pseudo in meanings:
  forms=[slotform(maps[slot][pseudo],slot) for slot in slots]
  _,s,_=infer(forms);vals.append(s)
 perm.append(statistics.mean(vals))
p=(sum(v>=obs_mean for v in perm)+1)/(len(perm)+1)
res={'version':1,'research_boundary':'Hidden paths are mathematical bridge-state ancestors that best fit the supplied family-level proto-forms under the fixed operator vocabulary. They are not recovered historical words and do not establish Proto-World or deliberate language engineering.','method':{'beam_width':160,'path_lengths':'2..6','operators':[x[0] for x in OPS],'permutation_controls':300,'shuffle':'meaning labels independently within each family'},'summary':{'observed_mean_hidden_fit':round(obs_mean,6),'permutation_mean':round(statistics.mean(perm),6),'permutation_sd':round(statistics.stdev(perm),6),'p_ge_observed':round(p,6),'delta_vs_permutation':round(obs_mean-statistics.mean(perm),6)},'meanings':results}
OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Hidden ancestral proto-word bridge states','',res['research_boundary'],'',f"Observed mean optimized fit: **{obs_mean:.3f}**",f"Shuffled-meaning optimized fit: **{statistics.mean(perm):.3f} ± {statistics.stdev(perm):.3f}**",f"Δ **{obs_mean-statistics.mean(perm):+.3f}**, permutation p **{p:.4f}**",'']
for m,x in results.items():
 lines += [f"## {m.title()}",f"Hidden bridge path: **{' → '.join(x['hidden_path'])}**",f"Mean fit: **{x['mean_fit']:.3f}**"]
 for a in x['alignments']:lines.append(f"- {a['family']} {a['form']}: {a['score']:.3f} via {a['operator']}")
 lines.append('')
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(res['summary'],indent=2))