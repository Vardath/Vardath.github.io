#!/usr/bin/env python3
"""Cross-family proto-word/meaning test.

Compares independently reconstructed proto-forms for the SAME basic meanings
across five established language families, after mapping broad sound proxies
into the existing 4x4 bridge. The test asks whether same-meaning proto-forms
are unusually similar, with and without the fixed bridge operators, relative
to shuffled meaning labels.

This is deliberately a falsification test: no positive result is assumed.
"""
from __future__ import annotations
import itertools, json, random, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTJ=ROOT/'data/phonetic-cross-family-proto-meaning.json'
OUTM=ROOT/'data/phonetic-cross-family-proto-meaning.md'
RNG=random.Random(137)

PHONE={
'i':'A1','e':'A1','y':'A1','ɪ':'A1','ɛ':'A2','æ':'A2','a':'A2','ə':'A2','ä':'A2',
'u':'A3','o':'A3','ɔ':'A4','ɑ':'A4',
'm':'B1','w':'B1','v':'C1','f':'C1','p':'D1','b':'D1',
'n':'B2','l':'B2','r':'B2','ɾ':'B2','s':'C2','z':'C2','θ':'C2','ð':'C2','ʃ':'C2','ʒ':'C2','t':'D2','d':'D2',
'ŋ':'B3','ɲ':'B3','j':'B3','x':'C3','ɣ':'C3','χ':'C3','k':'D3','g':'D3','q':'D3',
'h':'C4','ʔ':'D4'
}
# Conventional reconstructions are kept for display; broad segment proxies are
# only for placement in the coarse bridge. Proto-Uralic *täštä is specifically
# Finno-Volgaic in the cited reconstruction and is marked as such below.
DATA={
'water':[
 {'family':'Proto-Indo-European','form':'*wódr̥','seg':['w','o','d','r'],'source':'standard PIE reconstruction used in the calibrated daughter test'},
 {'family':'Proto-Semitic','form':'*māy-','seg':['m','a','j'],'source':'Kogan/Fronzaroli tradition; broad y→j proxy'},
 {'family':'Proto-Austronesian','form':'*daNum','seg':['d','a','n','u','m'],'source':'Austronesian Comparative Dictionary; conventional N collapsed to broad nasal proxy'},
 {'family':'Proto-Uralic','form':'*wete','seg':['w','e','t','e'],'source':'Uralic etymological reconstruction'},
 {'family':'Proto-Dravidian','form':'*nīr','seg':['n','i','r'],'source':'Krishnamurti / Dravidian Etymological Dictionary'}],
'mother':[
 {'family':'Proto-Indo-European','form':'*méh₂tēr','seg':['m','e','t','e','r'],'source':'standard PIE reconstruction; laryngeal omitted in broad proxy'},
 {'family':'Proto-Semitic','form':'*ʔimm-','seg':['ʔ','i','m'],'source':'Proto-Semitic reconstruction'},
 {'family':'Proto-Austronesian','form':'*ina','seg':['i','n','a'],'source':'Austronesian Comparative Dictionary'},
 {'family':'Proto-Uralic','form':'*emä','seg':['e','m','a'],'source':'Uralic reconstruction; irregular initial-vowel correspondence noted in source'},
 {'family':'Proto-Dravidian','form':'*taḷḷay','seg':['t','a','l','l','a','j'],'source':'Krishnamurti; retroflex lateral collapsed to broad lateral proxy'}],
'fire':[
 {'family':'Proto-Indo-European','form':'*péh₂wr̥','seg':['p','e','χ','w','r'],'source':'standard PIE reconstruction; h₂→χ proxy'},
 {'family':'Proto-Semitic','form':'*ʔiš-','seg':['ʔ','i','ʃ'],'source':'Proto-Semitic reconstruction'},
 {'family':'Proto-Austronesian','form':'*Sapuy','seg':['s','a','p','u','j'],'source':'Austronesian Comparative Dictionary; conventional S→broad s proxy'},
 {'family':'Proto-Uralic','form':'*tule','seg':['t','u','l','e'],'source':'Uralic etymological reconstruction'},
 {'family':'Proto-Dravidian','form':'*tiyam','seg':['t','i','j','a','m'],'source':'Proto-Dravidian reconstruction'}],
'star':[
 {'family':'Proto-Indo-European','form':'*h₂stḗr','seg':['χ','s','t','e','r'],'source':'standard PIE reconstruction; h₂→χ proxy'},
 {'family':'Proto-Semitic','form':'*kabkab-','seg':['k','a','b','k','a','b'],'source':'Proto-Semitic reconstruction'},
 {'family':'Proto-Austronesian','form':'*bituqən','seg':['b','i','t','u','q','ə','n'],'source':'Austronesian Comparative Dictionary; IPA /bituqən/'},
 {'family':'Proto-Uralic (Finno-Volgaic)','form':'*täštä','seg':['t','a','ʃ','t','a'],'source':'Finno-Volgaic reconstruction; NOT claimed for all Proto-Uralic'},
 {'family':'Proto-Dravidian','form':'*miHn','seg':['m','i','n'],'source':'Krishnamurti / DEDR; H omitted as uncertain broad proxy'}]
}

OPS=[
 ('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),
 ('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]

def path(seg):return [PHONE.get(x,'B4') for x in seg]
def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
def similarity(a,b):
    n,m=len(a),len(b);dp=[[0.0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):dp[i][0]=i
    for j in range(m+1):dp[0][j]=j
    for i in range(1,n+1):
      for j in range(1,m+1):
        ra,ca=feat(a[i-1]);rb,cb=feat(b[j-1])
        sub=0.0 if a[i-1]==b[j-1] else (abs(ra-rb)/3+abs(ca-cb)/3)/2
        dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+sub)
    return max(0.0,1-dp[n][m]/max(n,m,1))
def transform(p,place=False,manner=False,reverse=False):
    cm=[2,1,0,3] if place else [0,1,2,3];rm=[0,3,2,1] if manner else [0,1,2,3]
    out=[]
    for c in p:
      r='ABCD'.index(c[0]);k=int(c[1])-1;out.append('ABCD'[rm[r]]+str(cm[k]+1))
    if reverse:out.reverse()
    return out
def best_similarity(a,b):
    vals=[(similarity(transform(a,pl,ma,rv),b),name) for name,pl,ma,rv in OPS]
    return max(vals,key=lambda x:x[0])

# Add bridge paths.
for forms in DATA.values():
  for x in forms:x['path']=path(x['seg'])

same_identity=[];same_best=[];per_mean={}
for meaning,forms in DATA.items():
  rows=[]
  for a,b in itertools.combinations(forms,2):
    ident=similarity(a['path'],b['path']);best,op=best_similarity(a['path'],b['path'])
    same_identity.append(ident);same_best.append(best)
    rows.append({'a':a['family'],'b':b['family'],'identity':round(ident,6),'best':round(best,6),'operator':op})
  # Medoid = attested family proto-form with greatest mean operator-aware similarity to the others.
  med=[]
  for a in forms:
    vals=[best_similarity(a['path'],b['path'])[0] for b in forms if b is not a]
    med.append((statistics.mean(vals),a))
  med_score,medoid=max(med,key=lambda z:z[0])
  per_mean[meaning]={'pairs':rows,'identity_mean':round(statistics.mean(x['identity'] for x in rows),6),
                     'operator_mean':round(statistics.mean(x['best'] for x in rows),6),
                     'medoid_family':medoid['family'],'medoid_form':medoid['form'],'medoid_path':medoid['path'],'medoid_mean_similarity':round(med_score,6)}

# Wrong-meaning control, cross-family only.
wrong_identity=[];wrong_best=[]
flat=[(m,x) for m,forms in DATA.items() for x in forms]
for (ma,a),(mb,b) in itertools.combinations(flat,2):
  if ma==mb or a['family']==b['family']:continue
  wrong_identity.append(similarity(a['path'],b['path']))
  wrong_best.append(best_similarity(a['path'],b['path'])[0])

obs_id=statistics.mean(same_identity);obs_best=statistics.mean(same_best)
# Shuffle meaning labels independently within each family; preserves each family's phonotactics/forms.
families=[]
for forms in DATA.values():
  for x in forms:
    if x['family'] not in families:families.append(x['family'])
# Finno-Volgaic star variant needs to belong to Uralic slot for permutation indexing.
slots=['Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian']
def get_slot_form(meaning,slot):
  for x in DATA[meaning]:
    if x['family']==slot or (slot=='Proto-Uralic' and x['family'].startswith('Proto-Uralic')):return x
  raise KeyError((meaning,slot))
meanings=list(DATA)
perm_id=[];perm_best=[]
for _ in range(10000):
  assignment={}
  for slot in slots:
    sh=meanings[:];RNG.shuffle(sh);assignment[slot]={m:sh[i] for i,m in enumerate(meanings)}
  vi=[];vb=[]
  for m in meanings:
    for sa,sb in itertools.combinations(slots,2):
      a=get_slot_form(assignment[sa][m],sa);b=get_slot_form(assignment[sb][m],sb)
      vi.append(similarity(a['path'],b['path']));vb.append(best_similarity(a['path'],b['path'])[0])
  perm_id.append(statistics.mean(vi));perm_best.append(statistics.mean(vb))
p_id=(sum(x>=obs_id for x in perm_id)+1)/(len(perm_id)+1)
p_best=(sum(x>=obs_best for x in perm_best)+1)/(len(perm_best)+1)

result={
 'version':1,
 'scope':'cross-family proto-form meaning test',
 'research_boundary':'These are independently reconstructed family-level forms mapped through coarse bridge proxies. Similarity cannot establish a Proto-World word, deliberate language engineering, or intrinsic sound meaning. A null result is evidence against a simple universal lexical-form hypothesis at this resolution.',
 'method':{'meanings':meanings,'family_slots':slots,'proto_forms':sum(len(x) for x in DATA.values()),'same_mean_cross_family_pairs':len(same_identity),'wrong_mean_cross_family_pairs':len(wrong_identity),'permutations':10000,'operators':[x[0] for x in OPS]},
 'summary':{
   'same_mean_identity':round(obs_id,6),'wrong_mean_identity':round(statistics.mean(wrong_identity),6),'identity_uplift':round(obs_id-statistics.mean(wrong_identity),6),
   'identity_permutation_mean':round(statistics.mean(perm_id),6),'identity_permutation_sd':round(statistics.stdev(perm_id),6),'identity_p_ge_observed':round(p_id,6),
   'same_mean_operator_best':round(obs_best,6),'wrong_mean_operator_best':round(statistics.mean(wrong_best),6),'operator_uplift':round(obs_best-statistics.mean(wrong_best),6),
   'operator_permutation_mean':round(statistics.mean(perm_best),6),'operator_permutation_sd':round(statistics.stdev(perm_best),6),'operator_p_ge_observed':round(p_best,6)},
 'meanings':{m:{'forms':DATA[m],**per_mean[m]} for m in meanings}
}
OUTJ.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
s=result['summary'];lines=['# Cross-family proto-word meaning test','',result['research_boundary'],'',
 f"Same-meaning identity similarity: **{s['same_mean_identity']:.3f}** vs wrong-meaning **{s['wrong_mean_identity']:.3f}** (Δ {s['identity_uplift']:+.3f}; permutation p={s['identity_p_ge_observed']:.4f})",
 f"Same-meaning best-operator similarity: **{s['same_mean_operator_best']:.3f}** vs wrong-meaning **{s['wrong_mean_operator_best']:.3f}** (Δ {s['operator_uplift']:+.3f}; permutation p={s['operator_p_ge_observed']:.4f})",'']
for m,x in result['meanings'].items():
  lines += [f"## {m.title()}",f"Identity mean {x['identity_mean']:.3f}; operator mean {x['operator_mean']:.3f}; medoid {x['medoid_family']} {x['medoid_form']} ({x['medoid_mean_similarity']:.3f})"]
  for f in x['forms']:lines.append(f"- {f['family']}: {f['form']} · {' → '.join(f['path'])}")
  lines.append('')
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(result['summary'],indent=2))
