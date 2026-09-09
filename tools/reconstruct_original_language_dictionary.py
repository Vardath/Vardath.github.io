#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import re
import statistics
import unicodedata
import urllib.request
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
OUTJ=ROOT/'data/phonetic-original-language-dictionary.json'
OUTM=ROOT/'data/phonetic-original-language-dictionary.md'
ROOTJSON=ROOT/'data/phonetic-proto-reconstruction.json'

FAMILIES=['Proto-Indo-European','Proto-Semitic','Proto-Austronesian','Proto-Uralic','Proto-Dravidian']
URLS={x:f"https://kaikki.org/dictionary/{quote(x)}/kaikki.org-dictionary-{x.replace('-','').replace(' ','')}.jsonl" for x in FAMILIES}

# Basic-vocabulary meanings.  Synonyms are deliberately conservative: a concept is kept
# only when at least three independent proto-family dictionaries provide a matching gloss.
CONCEPTS={
'I':['I','first person pronoun'], 'you':['you','second person pronoun'], 'we':['we','first person plural'],
'who':['who'], 'what':['what'], 'this':['this'], 'that':['that'], 'not':['not'], 'all':['all'], 'many':['many'],
'one':['one'], 'two':['two'], 'three':['three'], 'four':['four'], 'five':['five'],
'big':['big','large'], 'long':['long'], 'small':['small','little'],
'woman':['woman','female person'], 'man':['man','male person'], 'person':['person','human being'], 'child':['child'],
'mother':['mother'], 'father':['father'], 'brother':['brother'], 'sister':['sister'],
'fish':['fish'], 'bird':['bird'], 'dog':['dog'], 'louse':['louse','lice'], 'snake':['snake','serpent'],
'tree':['tree'], 'seed':['seed'], 'leaf':['leaf'], 'root':['root'], 'bark':['tree bark','bark of a tree'],
'skin':['skin'], 'flesh':['flesh'], 'blood':['blood'], 'bone':['bone'], 'fat':['fat','grease'], 'egg':['egg'],
'horn':['horn'], 'tail':['tail'], 'feather':['feather'], 'hair':['hair'], 'head':['head'], 'ear':['ear'], 'eye':['eye'],
'nose':['nose'], 'mouth':['mouth'], 'tooth':['tooth'], 'tongue':['tongue'], 'foot':['foot'], 'knee':['knee'], 'hand':['hand'],
'belly':['belly','abdomen'], 'neck':['neck'], 'breast':['breast'], 'heart':['heart'], 'liver':['liver'],
'drink':['drink'], 'eat':['eat'], 'bite':['bite'], 'see':['see'], 'hear':['hear'], 'know':['know'], 'sleep':['sleep'],
'die':['die'], 'kill':['kill'], 'swim':['swim'], 'fly':['fly'], 'walk':['walk'], 'come':['come'], 'sit':['sit'],
'stand':['stand'], 'give':['give'], 'say':['say','speak'],
'sun':['sun'], 'moon':['moon'], 'star':['star'], 'water':['water'], 'rain':['rain'], 'stone':['stone','rock'],
'sand':['sand'], 'earth':['earth','soil'], 'cloud':['cloud'], 'smoke':['smoke'], 'fire':['fire'], 'ash':['ash'],
'burn':['burn'], 'path':['path','road'], 'mountain':['mountain'],
'red':['red'], 'green':['green'], 'yellow':['yellow'], 'white':['white'], 'black':['black'], 'night':['night'],
'hot':['hot'], 'cold':['cold'], 'full':['full'], 'new':['new'], 'good':['good'], 'round':['round'], 'dry':['dry'], 'name':['name']
}

PHONE={'A1':'i','A2':'a','A3':'u','A4':'ɑ','B1':'m','B2':'n','B3':'ŋ','B4':'r','C1':'f','C2':'s','C3':'x','C4':'h','D1':'p','D2':'t','D3':'k','D4':'ʔ'}
BASE=[('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]
CLASSES=[x[0] for x in BASE]+['metathesis','acrophonic','clipblend','resegmentation']
COST={'identity':0.0,'metathesis':.008,'resegmentation':.012,'clipblend':.025,'acrophonic':.035,
      'reverse':.02,'place':.02,'manner':.02,'reverse+place':.03,'reverse+manner':.03,'place+manner':.03,'reverse+place+manner':.04}

BAD_GLOSS=('alternative form','inflection of','form of','comparative of','superlative of','misspelling','obsolete spelling')

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).lower()
    return ''.join(ch for ch in s if not unicodedata.combining(ch))

def glosses(obj):
    out=[]
    for s in obj.get('senses') or []:
        out += [str(x) for x in (s.get('glosses') or [])]
        out += [str(x) for x in (s.get('raw_glosses') or [])]
    if obj.get('gloss'): out.append(str(obj['gloss']))
    return out

def concept_score(gs, synonyms):
    best=0.0; bestg=''
    for g in gs:
        ng=norm(g)
        if any(b in ng for b in BAD_GLOSS): continue
        for syn in synonyms:
            ns=norm(syn)
            if ng==ns: sc=10
            elif re.search(r'(^|[;,:()]\s*)'+re.escape(ns)+r'($|[;,.():]\s*)',ng): sc=7
            elif re.search(r'\b'+re.escape(ns)+r'\b',ng): sc=5
            else: continue
            # Short, simple glosses are less likely to be accidental secondary senses.
            sc -= min(len(ng)/250.0,1.5)
            if sc>best: best,bestg=sc,g
    return best,bestg

def load_family(fam):
    url=URLS[fam]
    print('download',fam,url,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'Vardath-phonetic-research/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:
        raw=r.read().decode('utf-8','replace')
    rows=[]
    for line in raw.splitlines():
        try:o=json.loads(line)
        except Exception:continue
        w=str(o.get('word') or '').strip()
        if not w or len(w)>50:continue
        gs=glosses(o)
        if gs: rows.append((w,gs,o.get('pos','')))
    print('loaded',fam,len(rows),flush=True)
    return rows

def best_forms(rows):
    found={}
    for c,syns in CONCEPTS.items():
        best=None
        for w,gs,pos in rows:
            sc,g=concept_score(gs,syns)
            if sc<=0:continue
            # Prefer lexical words/roots and reasonably short forms.
            clean=w.strip('*- ')
            if not clean or ' ' in clean: sc-=1.2
            sc-=max(0,len(clean)-14)*.08
            cand=(sc,w,g,pos)
            if best is None or cand[0]>best[0]:best=cand
        if best and best[0]>=3.5:
            found[c]={'form':best[1],'gloss':best[2],'pos':best[3],'match_score':round(best[0],3)}
    return found

def path_for(form):
    s=norm(form.strip('*- '))
    # Remove reconstruction notation that is not a segment in our broad 4x4 classifier.
    s=re.sub(r'[0-9₀-₉\.·ː:\-_=()\[\]{}+?]', '', s)
    out=[]
    for ch in s:
        if ch in 'ieɪɨyɯəeɛæ': out.append('A1' if ch in 'ieɪɨyeɛ' else 'A2')
        elif ch in 'aäɐ': out.append('A2')
        elif ch in 'uoʊɯ': out.append('A3')
        elif ch in 'ɑɔɒ': out.append('A4')
        elif ch in 'mw': out.append('B1')
        elif ch in 'nrlɾɹ': out.append('B2')
        elif ch in 'ŋjɲ': out.append('B3')
        elif ch in 'fvwɸβ': out.append('C1')
        elif ch in 'sšszʃʒθðcç': out.append('C2')
        elif ch in 'xɣχʁ': out.append('C3')
        elif ch in 'hħʕ': out.append('C4')
        elif ch in 'pb': out.append('D1')
        elif ch in 'tdṭḍʈɖ': out.append('D2')
        elif ch in 'kgqḱǵ': out.append('D3')
        elif ch in 'ʔ': out.append('D4')
    # Collapse only exact immediate repeats introduced by orthographic length/gemination.
    q=[]
    for c in out:
        if not q or q[-1]!=c:q.append(c)
    return q

def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
@lru_cache(maxsize=None)
def sim(a,b):
    a=list(a);b=list(b);n=len(a);m=len(b)
    dp=[[0.0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):dp[i][0]=i
    for j in range(m+1):dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            ra,ca=feat(a[i-1]);rb,cb=feat(b[j-1])
            sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
            dp[i][j]=min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+sub)
    return max(0,1-dp[n][m]/max(n,m,1))

def uniq(xs):
    seen=set();out=[]
    for x in xs:
        t=tuple(x)
        if t and t not in seen:seen.add(t);out.append(x)
    return out

def base_transform(p,pl,ma,rv):
    cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
    q=['ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p]
    return q[::-1] if rv else q

def variants(cls,p):
    for nm,pl,ma,rv in BASE:
        if cls==nm:return [base_transform(p,pl,ma,rv)]
    n=len(p);out=[]
    if cls=='metathesis':
        for i in range(n):
            for j in range(i+1,min(n,i+3)):
                q=p[:];q[i],q[j]=q[j],q[i];out.append(q)
    elif cls=='acrophonic':
        for k in range(2,min(4,n)+1):
            for cuts in itertools.combinations(range(1,n),k-1):out.append([p[i] for i in (0,)+cuts])
    elif cls=='clipblend':
        for left in range(1,n):
            for right in range(1,n-left+1):
                q=p[:left]+p[n-right:]
                if 2<=len(q)<n:out.append(q)
        for k in range(2,n):out.extend([p[:k],p[n-k:]])
    elif cls=='resegmentation':
        for k in range(1,n):out.append(p[k:]+p[:k])
    return uniq(out or [p])

def candidate_pool(paths):
    pool=[]
    for p in paths:
        pool.append(p)
        for cls in ('metathesis','resegmentation','clipblend','acrophonic'):
            pool.extend(variants(cls,p))
    return uniq(pool)

def reconstruct(paths):
    med=statistics.median(len(x) for x in paths)
    best=None
    for cand in candidate_pool(paths):
        famscores=[];ops=[]
        for target in paths:
            opbest=(-1,None)
            for cls in CLASSES:
                s=max(sim(tuple(v),tuple(target)) for v in variants(cls,cand))-COST[cls]
                if s>opbest[0]:opbest=(s,cls)
            famscores.append(opbest[0]);ops.append(opbest[1])
        raw=statistics.mean(famscores)
        score=raw-.018*abs(len(cand)-med)
        key=(score,raw,-abs(len(cand)-med),-len(cand),tuple(cand))
        if best is None or key>best[0]:best=(key,cand,raw,ops,famscores)
    return best[1],best[2],best[3],best[4]

def loo_stability(paths,full):
    if len(paths)<4:return None
    vals=[]
    for i in range(len(paths)):
        cand,*_=reconstruct(paths[:i]+paths[i+1:])
        vals.append(sim(tuple(cand),tuple(full)))
    return statistics.mean(vals)

def load_root_gates():
    try:
        d=json.loads(ROOTJSON.read_text(encoding='utf-8'))
        gs=d.get('refined_roots',{}).get('family_balanced',{}).get('top_gates') or d.get('latent_root',{}).get('top_gates') or []
        return {g['gate'] for g in gs[:64]}
    except Exception:return set()

def main():
    famrows={};famfound={}
    for fam in FAMILIES:
        try:
            famrows[fam]=load_family(fam);famfound[fam]=best_forms(famrows[fam])
        except Exception as e:
            print('FAILED',fam,repr(e),flush=True);famfound[fam]={}
    rootg=load_root_gates();entries=[]
    for concept in CONCEPTS:
        ev=[]
        for fam in FAMILIES:
            x=famfound.get(fam,{}).get(concept)
            if not x:continue
            p=path_for(x['form'])
            if len(p)<2:continue
            ev.append({'family':fam,**x,'path':p})
        if len(ev)<3:continue
        paths=[x['path'] for x in ev]
        cand,fit,ops,fs=reconstruct(paths)
        stab=loo_stability(paths,cand)
        gates=[cand[i]+'→'+cand[i+1] for i in range(len(cand)-1)]
        hits=[g for g in gates if g in rootg]
        for x,op,sc in zip(ev,ops,fs):x['best_from_candidate_operator']=op;x['candidate_fit']=round(sc,4)
        # Confidence combines independent-family coverage, model fit and leave-one-family-out stability.
        coverage=len(ev)/len(FAMILIES); stability=stab if stab is not None else fit
        conf=.35*coverage+.4*fit+.25*stability
        entries.append({'meaning':concept,'form':''.join(PHONE[c] for c in cand),'ipa':'/'+''.join(PHONE[c] for c in cand)+'/',
                        'path':cand,'families':len(ev),'fit':round(fit,4),'loo_stability':round(stability,4),
                        'confidence':round(conf,4),'root_gate_overlap':round(len(hits)/max(1,len(gates)),4),
                        'root_gate_hits':hits,'evidence':ev})
    entries.sort(key=lambda x:(-x['confidence'],-x['families'],x['meaning']))
    res={'version':2,'title':'Candidate original-language dictionary','method':{
        'concept_inventory':len(CONCEPTS),'minimum_independent_proto_families':3,'families':FAMILIES,
        'source':'Kaikki/Wiktionary machine-readable proto-family dictionaries',
        'reconstruction':'semantic gloss match -> broad 4x4 phonetic path -> cross-family latent candidate optimized under validated lexical operator bank',
        'research_boundary':'Candidate latent reconstructions under the experiment. They are not historically established Proto-World forms.'},
        'summary':{'entries':len(entries),'five_family_entries':sum(x['families']==5 for x in entries),'four_or_more':sum(x['families']>=4 for x in entries),
                   'mean_confidence':round(statistics.mean([x['confidence'] for x in entries]),4) if entries else 0},
        'entries':entries}
    OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Candidate original-language dictionary','',f"Entries: **{len(entries)}** from {len(CONCEPTS)} tested basic meanings.",'',
           'These are model reconstructions, not historically established Proto-World words.','', '| Meaning | Candidate | Families | Fit | Stability | Confidence |','|---|---|---:|---:|---:|---:|']
    for x in entries:lines.append(f"| {x['meaning']} | {x['ipa']} | {x['families']} | {x['fit']:.3f} | {x['loo_stability']:.3f} | {x['confidence']:.3f} |")
    OUTM.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(res['summary'],indent=2),flush=True)

if __name__=='__main__':main()
