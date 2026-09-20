#!/usr/bin/env python3
# Discovery/holdout mirror-meaning word search across NorthEuraLex.
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path

import man_grid_exact_data as D
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/mirror-meaning-word-search-v1.json'
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'
CORE=120
MIN_FORMS=700
MIN_DISC=40
MIN_HOLD=40
NEG=4
K=10
PERMS=2000
OPS=['reverse','reflect_x','reflect_y','rotate180','reverse_reflect_x','reverse_reflect_y','reverse_rotate180']

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-MirrorMeaning/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8-sig')

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def snorm(s):
    s=unicodedata.normalize('NFKD',str(s)).lower()
    return ''.join(c for c in s if c.isalpha() and not unicodedata.combining(c))

def signp(k,n):
    if not n:return 1.0
    return sum(math.comb(n,i) for i in range(k,n+1))/(2**n)

def levsim(a,b):
    if not a or not b:return 0.0
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]+[0]*len(b)
        for j,y in enumerate(b,1):
            cur[j]=min(prev[j]+1,cur[j-1]+1,prev[j-1]+(x!=y))
        prev=cur
    return 1-prev[-1]/max(len(a),len(b))

def resample(points,k=K):
    if not points:return ()
    if len(points)==1:return tuple(points[0] for _ in range(k))
    out=[]
    for j in range(k):
        u=j*(len(points)-1)/(k-1)
        i=min(len(points)-2,int(u));f=u-i
        a,b=points[i],points[i+1]
        out.append((a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f))
    return tuple(out)

def transform(path,op):
    q=path
    if op.startswith('reverse'):
        q=tuple(reversed(q))
    if 'reflect_x' in op:
        q=tuple((1-x,y) for x,y in q)
    elif 'reflect_y' in op:
        q=tuple((x,1-y) for x,y in q)
    elif 'rotate180' in op:
        q=tuple((1-x,1-y) for x,y in q)
    return q

def dist(a,b):
    return sum(math.hypot(x[0]-y[0],x[1]-y[1]) for x,y in zip(a,b))/len(a)

def load():
    _,params,_,_,cov=D.load_phoible();P=FB.fit(params)
    coords=[];alias={}
    for pid in sorted(params):
        p=params[pid];idx=len(coords);coords.append(FB.project(p['features'],P));alias.setdefault(canon(p['name']),idx)

    langs={r['ID']:{'id':r['ID'],'name':r['Name'],'family':r.get('Family') or 'Unknown','subfamily':r.get('Subfamily') or ''}
           for r in csv.DictReader(io.StringIO(fetch('languages.csv')))}
    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('Name') or r['ID'])
            for r in csv.DictReader(io.StringIO(fetch('parameters.csv')))}
    best={}
    for r in csv.DictReader(io.StringIO(fetch('forms.csv'))):
        lid=(r.get('Language_ID') or '').strip();con=(r.get('Parameter_ID') or '').strip()
        if lid not in langs or not con:continue
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if not toks or len(toks)>18:continue
        seq=[];ok=True
        for t in toks:
            j=alias.get(canon(t))
            if j is None:ok=False;break
            seq.append(j)
        if not ok:continue
        form=(r.get('Form') or r.get('Value') or '').strip()
        cand=(len(seq),r.get('ID') or '',seq,form,(r.get('Segments') or '').strip())
        k=(lid,con)
        if k not in best or cand[:2]<best[k][:2]:best[k]=cand
    forms=defaultdict(dict)
    for (lid,con),v in best.items():forms[lid][con]={'seq':v[2],'form':v[3],'segments':v[4]}
    eligible={lid:langs[lid] for lid in sorted(langs) if len(forms.get(lid,{}))>=MIN_FORMS and langs[lid]['family'] not in ('Unknown','Unclassified','')}
    coverage=defaultdict(int)
    for lid in eligible:
        for c in forms[lid]:coverage[c]+=1
    core=sorted(coverage,key=lambda c:(-coverage[c],D.h64('mirror-core',c),c))[:CORE]
    discovery=[c for c in core if D.h64('mirror-split',c)%2==0]
    holdout=[c for c in core if D.h64('mirror-split',c)%2==1]
    # force both halves reasonably balanced by deterministic fallback
    if min(len(discovery),len(holdout))<50:
        order=sorted(core,key=lambda c:(D.h64('mirror-balance',c),c))
        discovery=order[::2];holdout=order[1::2]

    tr={};spell={}
    for lid in eligible:
        tr[lid]={};spell[lid]={}
        for c in core:
            if c not in forms[lid]:continue
            pts=[coords[j] for j in forms[lid][c]['seq']]
            base=resample(pts)
            tr[lid][c]={'identity':base,**{op:transform(base,op) for op in OPS}}
            spell[lid][c]=snorm(forms[lid][c]['form'])
    return eligible,forms,tr,spell,labels,core,discovery,holdout,cov

def wrongs(pool,c,lid_a,lid_b,split):
    xs=[z for z in pool if z!=c]
    xs.sort(key=lambda z:(D.h64('mirror-neg',split,lid_a,lid_b,c,z),z))
    return xs[:NEG]

def eval_pair_op(a,b,op,concepts,tr):
    shared=[c for c in concepts if c in tr[a] and c in tr[b]]
    rows=[]
    for c in shared:
        ws=wrongs(shared,c,a,b,'d' if concepts is DISC else 'h')
        if len(ws)<NEG:continue
        true=dist(tr[a][c][op],tr[b][c]['identity'])
        nd=[dist(tr[a][c][op],tr[b][w]['identity']) for w in ws]
        null=statistics.mean(nd)
        rows.append((c,true,null,null-true))
    if not rows:return None
    return {'n':len(rows),'mean_true':statistics.mean(x[1] for x in rows),'mean_wrong':statistics.mean(x[2] for x in rows),
            'advantage':statistics.mean(x[3] for x in rows),'wins':sum(x[3]>0 for x in rows),'rows':rows}

DISC=[]

def main():
    global DISC
    eligible,forms,tr,spell,labels,core,disc,hold,cov=load();DISC=disc
    lids=sorted(eligible)
    candidates=[]
    for i,a in enumerate(lids):
        for b in lids[i+1:]:
            if eligible[a]['family']==eligible[b]['family']:continue
            sd=sum(c in tr[a] and c in tr[b] for c in disc)
            sh=sum(c in tr[a] and c in tr[b] for c in hold)
            if sd<MIN_DISC or sh<MIN_HOLD:continue
            ident=eval_pair_op(a,b,'identity',disc,tr)
            for op in OPS:
                q=eval_pair_op(a,b,op,disc,tr)
                if not q:continue
                candidates.append({'a':a,'b':b,'op':op,'discovery_shared':q['n'],'holdout_shared':sh,
                                   'discovery_advantage':q['advantage'],'discovery_identity_advantage':ident['advantage'] if ident else None,
                                   'discovery_mirror_gain':q['advantage']-(ident['advantage'] if ident else 0)})
    if not candidates:raise RuntimeError('No cross-family mirror candidates')
    # Choose by mirror-specific discovery gain; semantic advantage is a secondary tie-breaker.
    candidates.sort(key=lambda x:(x['discovery_mirror_gain'],x['discovery_advantage']),reverse=True)
    sel=candidates[0];a,b,op=sel['a'],sel['b'],sel['op']
    H=eval_pair_op(a,b,op,hold,tr);I=eval_pair_op(a,b,'identity',hold,tr)
    if not H or not I:raise RuntimeError('Selected pair lacks holdout')

    # Frozen holdout permutation: shuffle target meaning labels only.
    shared=[c for c in hold if c in tr[a] and c in tr[b]]
    obs_true=statistics.mean(dist(tr[a][c][op],tr[b][c]['identity']) for c in shared)
    perm_means=[]
    for p in range(PERMS):
        perm=sorted(shared,key=lambda c:(D.h64('mirror-hold-perm',p,c),c))
        perm_means.append(statistics.mean(dist(tr[a][c][op],tr[b][perm[i]]['identity']) for i,c in enumerate(shared)))
    pperm=(1+sum(x<=obs_true for x in perm_means))/(PERMS+1)

    # Paired mirror-vs-identity gain on holdout.
    hmap={c:(t,n,adv) for c,t,n,adv in H['rows']}
    imap={c:(t,n,adv) for c,t,n,adv in I['rows']}
    both=sorted(set(hmap)&set(imap))
    gains=[hmap[c][2]-imap[c][2] for c in both]
    gw=sum(x>0 for x in gains);gp=signp(gw,len(gains));gmean=statistics.mean(gains)

    # Individual mirror-word candidates are taken ONLY from untouched holdout concepts.
    ex=[]
    for c,t,n,adv in sorted(H['rows'],key=lambda x:x[3],reverse=True)[:50]:
        sa,sb=spell[a].get(c,''),spell[b].get(c,'')
        ex.append({'concept_id':c,'concept':labels.get(c,c),'mirror_advantage':adv,'mirror_true_distance':t,'wrong_meaning_distance':n,
                   'language_a':eligible[a]['name'],'form_a':forms[a][c]['form'],'segments_a':forms[a][c]['segments'],
                   'language_b':eligible[b]['name'],'form_b':forms[b][c]['form'],'segments_b':forms[b][c]['segments'],
                   'orthographic_direct_similarity':levsim(sa,sb),'orthographic_reversed_a_similarity':levsim(sa[::-1],sb)})

    supported=bool(H['advantage']>0 and pperm<.05 and gmean>0 and gp<.05)
    out={
      'version':1,'status':'complete','test':'Cross-family mirror-meaning word search with discovery/holdout concepts',
      'source':{'NorthEuraLex_commit':NE_SHA,'PHOIBLE_commit':D.PH},
      'question':'Are there language pairs in which same-meaning words systematically match under a fixed phonetic mirror/reversal operation better than ordinary alignment and wrong-meaning controls?',
      'design':{
        'language_pool':f'NorthEuraLex languages with at least {MIN_FORMS} fully PHOIBLE-mapped forms; only cross-family pairs are searched.',
        'concept_pool':f'{CORE} most widely attested NorthEuraLex concepts, chosen by coverage only, never by phonetic resemblance.',
        'split':'Concepts are deterministically divided before scoring into discovery and untouched holdout halves.',
        'operators':OPS,
        'search':'Discovery meanings choose exactly one language pair and one non-identity mirror operator by improvement over identity.',
        'holdout':'The selected pair/operator is frozen before any holdout score is examined.',
        'semantic_control':f'Each same-meaning comparison is contrasted with {NEG} deterministic wrong meanings from the same target language.',
        'permutation':f'{PERMS} holdout target-label permutations test whether same-meaning distance is unusually small.',
        'mirror_specific_control':'On holdout meanings, the selected mirror operation must also improve the same semantic advantage relative to identity alignment.',
        'support_rule':'Support requires positive holdout same-meaning advantage with permutation p<0.05 AND positive mirror-over-identity gain with one-sided sign p<0.05.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'eligible_languages':len(eligible),'cross_family_pair_operator_candidates':len(candidates),
                  'core_concepts':len(core),'discovery_concepts':len(disc),'holdout_concepts':len(hold),'permutations':PERMS},
      'selected':{
        'language_a':{'id':a,**eligible[a]},'language_b':{'id':b,**eligible[b]},'operator':op,
        'discovery':{k:v for k,v in sel.items() if k.startswith('discovery')},
        'holdout':{'shared_concepts':H['n'],'same_meaning_distance':H['mean_true'],'wrong_meaning_distance':H['mean_wrong'],
                   'semantic_advantage':H['advantage'],'semantic_wins':H['wins'],'semantic_sign_p':signp(H['wins'],H['n']),
                   'permutation_p':pperm,'identity_semantic_advantage':I['advantage'],
                   'mirror_over_identity_mean_gain':gmean,'mirror_over_identity_wins':gw,'mirror_over_identity_sign_p':gp,
                   'supported':supported},
        'top_holdout_examples':ex
      },
      'top_discovery_candidates':[
        {'language_a':eligible[x['a']]['name'],'language_b':eligible[x['b']]['name'],'operator':x['op'],
         'discovery_shared':x['discovery_shared'],'discovery_advantage':x['discovery_advantage'],
         'discovery_identity_advantage':x['discovery_identity_advantage'],'discovery_mirror_gain':x['discovery_mirror_gain']}
        for x in candidates[:25]],
      'interpretation':{
        'positive':'A pass would show a reproducible cross-family mirror/reversal correspondence for independently defined meanings in this phonetic representation. It would not establish common ancestry by itself.',
        'negative':'A fail means the strongest discovery-stage mirror pattern did not reproduce on untouched meanings and should not be treated as a systematic language relationship.',
        'examples':'Individual holdout examples are descriptive only unless the aggregate holdout test passes.'
      }}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out['coverage'],ensure_ascii=False,indent=2))
    print(json.dumps(out['selected'],ensure_ascii=False,indent=2))

if __name__=='__main__':main()
