#!/usr/bin/env python3
"""Calibration test: do established early Indo-European reconstructions retain
more bridge-path similarity to same-meaning daughter forms than to shuffled meanings?

This is deliberately small and transparent. It is a calibration layer for the
phonetic bridge, not a Proto-World reconstruction.
"""
import json, math, random, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTJ=ROOT/'data/phonetic-proto-word-test.json'
OUTM=ROOT/'data/phonetic-proto-word-test.md'
RNG=random.Random(137)
CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
PHONE={
'i':'A1','e':'A1','y':'A1','ɪ':'A1','ɛ':'A2','æ':'A2','a':'A2','ə':'A2',
'u':'A3','o':'A3','ɔ':'A4','ɑ':'A4',
'm':'B1','w':'B1','v':'C1','f':'C1','p':'D1','b':'D1',
'n':'B2','l':'B2','r':'B2','ɾ':'B2','s':'C2','z':'C2','θ':'C2','ð':'C2','ʃ':'C2','ʒ':'C2','t':'D2','d':'D2',
'ŋ':'B3','j':'B3','x':'C3','ɣ':'C3','χ':'C3','k':'D3','g':'D3',
'h':'C4','ʔ':'D4'
}
# Approximate segment strings used only to place forms in the broad 4x4 bridge.
# Display forms preserve the conventional reconstruction/orthography separately.
DATA={
'water':{'proto_display':'*wódr̥','proto_ipa':['w','o','d','r'],'source_note':'Proto-Indo-European reconstruction; compare Hittite wātar, Sanskrit udán, Greek hýdōr, Old English wæter.',
'desc':[
{'language':'Hittite','form':'wātar','ipa':['w','a','t','a','r']},
{'language':'Sanskrit','form':'udán','ipa':['u','d','a','n']},
{'language':'Ancient Greek','form':'hýdōr','ipa':['h','y','d','ɔ','r']},
{'language':'Old English','form':'wæter','ipa':['w','æ','t','e','r']}]},
'mother':{'proto_display':'*méh₂tēr','proto_ipa':['m','e','t','e','r'],'source_note':'Proto-Indo-European reconstruction; bridge playback omits uncertain laryngeal realization.',
'desc':[
{'language':'Sanskrit','form':'mātṛ','ipa':['m','a','t','r']},
{'language':'Ancient Greek','form':'mḗtēr','ipa':['m','e','t','e','r']},
{'language':'Latin','form':'māter','ipa':['m','a','t','e','r']},
{'language':'Old English','form':'mōdor','ipa':['m','o','d','o','r']}]},
'father':{'proto_display':'*ph₂tḗr','proto_ipa':['p','χ','t','e','r'],'source_note':'Proto-Indo-European reconstruction; h₂ is represented as a dorsal/pharyngeal proxy χ only for the bridge experiment.',
'desc':[
{'language':'Sanskrit','form':'pitṛ','ipa':['p','i','t','r']},
{'language':'Ancient Greek','form':'patḗr','ipa':['p','a','t','e','r']},
{'language':'Latin','form':'pater','ipa':['p','a','t','e','r']},
{'language':'Old English','form':'fæder','ipa':['f','æ','d','e','r']}]},
'night':{'proto_display':'*nókʷts','proto_ipa':['n','o','k','w','t','s'],'source_note':'Proto-Indo-European reconstruction; labialized kʷ is represented as k+w in the coarse bridge.',
'desc':[
{'language':'Sanskrit','form':'náktam','ipa':['n','a','k','t','a','m']},
{'language':'Ancient Greek','form':'nýx','ipa':['n','y','k','s']},
{'language':'Latin','form':'nox','ipa':['n','o','k','s']},
{'language':'Old English','form':'niht','ipa':['n','i','x','t']}]},
'fire':{'proto_display':'*péh₂wr̥','proto_ipa':['p','e','χ','w','r'],'source_note':'Proto-Indo-European reconstruction; h₂ uses χ as a coarse experimental proxy.',
'desc':[
{'language':'Hittite','form':'paḫḫur','ipa':['p','a','χ','χ','u','r']},
{'language':'Ancient Greek','form':'pŷr','ipa':['p','y','r']},
{'language':'Old English','form':'fȳr','ipa':['f','y','r']},
{'language':'Armenian','form':'hur','ipa':['h','u','r']}]},
'heart':{'proto_display':'*ḱḗr','proto_ipa':['k','e','r'],'source_note':'Proto-Indo-European reconstruction; palatovelar ḱ is collapsed to the dorsal stop region in the 4x4 bridge.',
'desc':[
{'language':'Sanskrit','form':'hṛd','ipa':['h','r','d']},
{'language':'Ancient Greek','form':'kardía','ipa':['k','a','r','d','i','a']},
{'language':'Latin','form':'cor','ipa':['k','o','r']},
{'language':'Old English','form':'heorte','ipa':['h','e','o','r','t','e']}]},
'star':{'proto_display':'*h₂stḗr','proto_ipa':['χ','s','t','e','r'],'source_note':'Proto-Indo-European reconstruction; h₂ uses χ as a coarse experimental proxy.',
'desc':[
{'language':'Sanskrit','form':'stṛ','ipa':['s','t','r']},
{'language':'Ancient Greek','form':'astḗr','ipa':['a','s','t','e','r']},
{'language':'Latin','form':'stella','ipa':['s','t','e','l','l','a']},
{'language':'Old English','form':'steorra','ipa':['s','t','e','o','r','r','a']}]}
}

def path(seq):return [PHONE.get(x,'B4') for x in seq]
def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
def sim(a,b):
    n,m=len(a),len(b);dp=[[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):dp[i][0]=i
    for j in range(m+1):dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            ra,ca=feat(a[i-1]);rb,cb=feat(b[j-1])
            sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)/3+abs(ca-cb)/3)/2
            dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+sub)
    return max(0,1-dp[n][m]/max(n,m,1))

rows=[]; same=[]
for meaning,d in DATA.items():
    pp=path(d['proto_ipa']); ds=[]
    for x in d['desc']:
        s=sim(pp,path(x['ipa']));same.append(s);ds.append({**x,'bridge_path':path(x['ipa']),'similarity_to_proto':round(s,6)})
    rows.append({'meaning':meaning,'proto_form':d['proto_display'],'proto_segments':d['proto_ipa'],'proto_bridge_path':pp,'source_note':d['source_note'],'descendants':ds,'mean_same_mean_similarity':round(statistics.mean(x['similarity_to_proto'] for x in ds),6)})
obs=statistics.mean(same)
means=list(DATA)
wrong=[]
for meaning,d in DATA.items():
    for x in d['desc']:
        xp=path(x['ipa'])
        for other in means:
            if other!=meaning:wrong.append(sim(path(DATA[other]['proto_ipa']),xp))
wrong_mean=statistics.mean(wrong)
perm=[]
for _ in range(10000):
    shuffled=means[:];RNG.shuffle(shuffled);scores=[]
    for meaning,pmeaning in zip(means,shuffled):
        pp=path(DATA[pmeaning]['proto_ipa'])
        for x in DATA[meaning]['desc']:scores.append(sim(pp,path(x['ipa'])))
    perm.append(statistics.mean(scores))
p=(sum(v>=obs for v in perm)+1)/(len(perm)+1)
# Meaning-path prototype: consensus cell at each normalized fractional position, only illustrative.
result={'version':1,'scope':'Proto-Indo-European calibration pilot','research_boundary':'This tests whether established reconstructed meanings retain bridge-path similarity to daughter forms. It does not reconstruct Proto-World or prove intrinsic sound-meaning symbolism. IPA values are broad experimental approximations used only for bridge placement.',
'method':{'meanings':len(DATA),'descendant_forms':len(same),'permutations':10000,'similarity':'feature-aware edit similarity on 4x4 bridge paths','control':'one-to-one shuffled assignment of proto meanings to descendant meaning sets'},
'summary':{'same_mean_mean_similarity':round(obs,6),'all_wrong_mean_similarity':round(wrong_mean,6),'uplift':round(obs-wrong_mean,6),'permutation_mean':round(statistics.mean(perm),6),'permutation_sd':round(statistics.stdev(perm),6),'permutation_p_ge_observed':round(p,6)},'meanings':rows}
OUTJ.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Proto-word meaning ↔ phonetic bridge calibration','',result['research_boundary'],'',f"Mean same-meaning proto→daughter similarity: **{obs:.3f}**",f"Mean wrong-meaning similarity: **{wrong_mean:.3f}**",f"Uplift: **{obs-wrong_mean:+.3f}**",f"Permutation control: **{statistics.mean(perm):.3f} ± {statistics.stdev(perm):.3f}**, p≥observed **{p:.4f}**",'']
for r in rows:
    lines += [f"## {r['meaning'].title()} — {r['proto_form']}",f"Proto bridge path: {' → '.join(r['proto_bridge_path'])}",f"Mean same-meaning similarity: {r['mean_same_mean_similarity']:.3f}"]+[f"- {x['language']} {x['form']}: {x['similarity_to_proto']:.3f} · {' → '.join(x['bridge_path'])}" for x in r['descendants']]+['']
OUTM.write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(result['summary'],indent=2))