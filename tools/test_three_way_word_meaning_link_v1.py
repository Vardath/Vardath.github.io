#!/usr/bin/env python3
# workflow-trigger: v1
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from pathlib import Path

import man_grid_exact_data as D
import test_man_grid_alphabet_traversal_v1 as T
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
LINKED=ROOT/'data/three-way-linked-language-test-v1.json'
OUT=ROOT/'data/three-way-word-meaning-link-v1.json'
PERMS=400
K=16
MIN_SHARED=150
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-ThreeWayWordMeaning/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:
        return r.read().decode('utf-8-sig')

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def normname(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode('ascii').lower()
    return ''.join(c for c in s if c.isalnum())

def orient(pt,d):
    x,y=pt
    if d=='LR': return (x,y)
    if d=='RL': return (1-x,y)
    if d=='TB': return (1-y,x)
    if d=='BT': return (y,x)
    raise ValueError(d)

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

def pdist(a,b):
    return sum(math.hypot(x[0]-y[0],x[1]-y[1]) for x,y in zip(a,b))/len(a)

def tri_dist(a,b,c):
    return (pdist(a,b)+pdist(a,c)+pdist(b,c))/3

def mean(xs):
    return statistics.mean(xs) if xs else None

def resolve_language(lang_rows,iso,name):
    ni=iso.lower();nn=normname(name)
    exact=[]
    for r in lang_rows:
        vals=[str(v).strip().lower() for v in r.values() if v is not None]
        if ni in vals: exact.append(r)
    if exact:return sorted(exact,key=lambda r:r.get('ID',''))[0]
    named=[r for r in lang_rows if normname(r.get('Name',''))==nn]
    if named:return sorted(named,key=lambda r:r.get('ID',''))[0]
    aliases={
      'nob':['norwegianbokmal','norwegianbokmål'],
      'nno':['norwegiannynorsk'],
      'nor':['norwegian'],
      'cym':['welsh'],
      'dan':['danish'],'fin':['finnish'],'isl':['icelandic'],'swe':['swedish'],
      'yor':['yoruba'],'heb':['hebrew'],'kor':['korean']
    }
    targets=set(normname(x) for x in aliases.get(iso,[]))
    named=[r for r in lang_rows if normname(r.get('Name','')) in targets]
    return sorted(named,key=lambda r:r.get('ID',''))[0] if named else None

def load_data():
    _,params,_,_,cov=D.load_phoible()
    P=FB.fit(params)
    alias={};coords=[]
    for pid in sorted(params):
        p=params[pid];idx=len(coords)
        coords.append(FB.project(p['features'],P))
        alias.setdefault(canon(p['name']),idx)

    linked=json.loads(LINKED.read_text(encoding='utf8'))
    elig=linked['coverage']['eligible_members']
    targets=[]
    for d in ('LR','RL','TB'):
        for q in elig[d]:
            if q['iso']=='okm':continue
            targets.append({'iso':q['iso'],'name':q['name'],'direction':d})

    lrows=list(csv.DictReader(io.StringIO(fetch('languages.csv'))))
    resolved={}
    for q in targets:
        r=resolve_language(lrows,q['iso'],q['name'])
        if r:
            resolved[q['iso']]={'iso':q['iso'],'wanted_name':q['name'],'direction':q['direction'],
                                'id':r['ID'],'name':r.get('Name') or q['name'],
                                'family':r.get('Family') or 'Unknown','subfamily':r.get('Subfamily') or ''}
    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('Name') or r['ID'])
            for r in csv.DictReader(io.StringIO(fetch('parameters.csv')))}

    wanted_ids={x['id']:iso for iso,x in resolved.items()}
    forms={iso:{} for iso in resolved}
    rows=list(csv.DictReader(io.StringIO(fetch('forms.csv'))))
    mapped=0
    for r in rows:
        lid=(r.get('Language_ID') or '').strip()
        if lid not in wanted_ids:continue
        con=(r.get('Parameter_ID') or '').strip()
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if not con or not toks or len(toks)>20:continue
        seq=[];ok=True
        for tok in toks:
            j=alias.get(canon(tok))
            if j is None:ok=False;break
            seq.append(j)
        if not ok:continue
        iso=wanted_ids[lid];mapped+=1
        form=(r.get('Form') or r.get('Value') or '').strip()
        cand=(len(seq),r.get('ID') or '',seq,form,(r.get('Segments') or '').strip())
        if con not in forms[iso] or cand[:2]<forms[iso][con][:2]:
            forms[iso][con]=cand
    clean={}
    for iso,fd in forms.items():
        clean[iso]={c:{'seq':v[2],'form':v[3],'segments':v[4]} for c,v in fd.items()}
    return resolved,clean,coords,labels,cov

def traj(form,coords,d):
    return resample([orient(coords[j],d) for j in form['seq']])

def candidate_score(liso,hiso,kiso,resolved,forms,coords):
    dirs={liso:'LR',hiso:'RL',kiso:'TB'}
    cons=sorted(set(forms[liso])&set(forms[hiso])&set(forms[kiso]))
    if len(cons)<MIN_SHARED:return None
    tr={}
    for iso in (liso,hiso,kiso):
        tr[iso]={c:traj(forms[iso][c],coords,dirs[iso]) for c in cons}
    obs_by={c:tri_dist(tr[liso][c],tr[hiso][c],tr[kiso][c]) for c in cons}
    obs=mean(obs_by.values())

    null=[]
    pairnull={'LR_RL':[],'LR_TB':[],'RL_TB':[]}
    for p in range(PERMS):
        hp=T.shuffled(cons,T.h64('meaning-h',p,liso,hiso,kiso))
        kp=T.shuffled(cons,T.h64('meaning-k',p,liso,hiso,kiso))
        vals=[];lh=[];lk=[];hk=[]
        for i,c in enumerate(cons):
            h=hp[i];k=kp[i]
            A,B,C=tr[liso][c],tr[hiso][h],tr[kiso][k]
            dab=pdist(A,B);dac=pdist(A,C);dbc=pdist(B,C)
            vals.append((dab+dac+dbc)/3);lh.append(dab);lk.append(dac);hk.append(dbc)
        null.append(mean(vals));pairnull['LR_RL'].append(mean(lh));pairnull['LR_TB'].append(mean(lk));pairnull['RL_TB'].append(mean(hk))
    null_mean=mean(null)
    adv=null_mean-obs

    obs_pairs={
      'LR_RL':mean(pdist(tr[liso][c],tr[hiso][c]) for c in cons),
      'LR_TB':mean(pdist(tr[liso][c],tr[kiso][c]) for c in cons),
      'RL_TB':mean(pdist(tr[hiso][c],tr[kiso][c]) for c in cons)
    }
    pair_stats={}
    for key,ov in obs_pairs.items():
        nm=mean(pairnull[key])
        pair_stats[key]={
          'same_meaning_distance':ov,'mismatched_meaning_null':nm,
          'advantage':nm-ov,
          'permutation_p':(1+sum(x<=ov for x in pairnull[key]))/(PERMS+1)
        }

    # Direction-specific control: evaluate all expected/opposite choices on the same concepts.
    opts={liso:['LR','RL'],hiso:['RL','LR'],kiso:['TB','BT']}
    orientation=[]
    for dl in opts[liso]:
      for dh in opts[hiso]:
       for dk in opts[kiso]:
        vals=[]
        for c in cons:
            A=traj(forms[liso][c],coords,dl);B=traj(forms[hiso][c],coords,dh);C=traj(forms[kiso][c],coords,dk)
            vals.append(tri_dist(A,B,C))
        orientation.append({'LR_member':dl,'RL_member':dh,'TB_member':dk,'distance':mean(vals),
                            'is_expected':dl=='LR' and dh=='RL' and dk=='TB'})
    orientation.sort(key=lambda x:x['distance'])
    expected_rank=1+next(i for i,x in enumerate(orientation) if x['is_expected'])

    top=sorted(cons,key=lambda c:obs_by[c])[:40]
    examples=[]
    for c in top:
        examples.append({
          'concept_id':c,
          'concept':c,
          'distance':obs_by[c],
          resolved[liso]['name']:{'form':forms[liso][c]['form'],'segments':forms[liso][c]['segments']},
          resolved[hiso]['name']:{'form':forms[hiso][c]['form'],'segments':forms[hiso][c]['segments']},
          resolved[kiso]['name']:{'form':forms[kiso][c]['form'],'segments':forms[kiso][c]['segments']}
        })
    return {'LR':liso,'RL':hiso,'TB':kiso,'shared_concepts':len(cons),
            'same_meaning_distance':obs,'null_mean_distance':null_mean,'semantic_advantage':adv,
            '_null':null,'pairwise':pair_stats,'orientation_rank':expected_rank,'orientation_table':orientation,
            '_examples':examples,'_obs_by':obs_by}

def main():
    resolved,forms,coords,labels,cov=load_data()
    lr=[iso for iso,x in resolved.items() if x['direction']=='LR']
    rl=[iso for iso,x in resolved.items() if x['direction']=='RL']
    tb=[iso for iso,x in resolved.items() if x['direction']=='TB']
    candidates=[]
    for a in lr:
      for b in rl:
       for c in tb:
        q=candidate_score(a,b,c,resolved,forms,coords)
        if q:candidates.append(q)
    if not candidates:
        raise RuntimeError('No candidate trio has enough shared NorthEuraLex concepts')

    # Candidate-specific null mean adjusts for different language phonotactics.
    for q in candidates:
        q['fixed_trio_permutation_p']=(1+sum((mean(q['_null'])-x)>=q['semantic_advantage'] for x in q['_null']))/(PERMS+1)
    candidates.sort(key=lambda q:q['semantic_advantage'],reverse=True)
    best=candidates[0]

    # Search-corrected statistic: in every shuffled universe, select the best apparent trio.
    null_best=[]
    for p in range(PERMS):
        null_best.append(max(mean(q['_null'])-q['_null'][p] for q in candidates))
    search_p=(1+sum(x>=best['semantic_advantage'] for x in null_best))/(PERMS+1)

    # Attach human labels only after scoring.
    for q in candidates:
        q['languages']={d:resolved[q[d]]['name'] for d in ('LR','RL','TB')}
        for ex in q['_examples']:
            ex['concept']=labels.get(ex['concept_id'],ex['concept_id'])
        q['top_same_meaning_examples']=q.pop('_examples')
        q.pop('_null');q.pop('_obs_by')

    selected=candidates[0]
    selected['search_corrected_permutation_p']=search_p
    pair_all_positive=all(v['advantage']>0 and v['permutation_p']<.05 for v in selected['pairwise'].values())
    selected['all_three_pairwise_links_significant']=pair_all_positive
    selected['expected_orientation_is_best']=selected['orientation_rank']==1
    selected['linked_three_way_supported']=bool(search_p<.05 and pair_all_positive and selected['expected_orientation_is_best'])

    out={
      'version':1,'status':'complete',
      'test':'Independent same-meaning word trajectories for directional language trios',
      'source':{'NorthEuraLex_commit':NE_SHA,'PHOIBLE_commit':D.PH},
      'question':'Do independently defined same-meaning words reveal one linked LR/RL/TB phonetic geometry, and which eligible trio fits it best?',
      'design':{
        'language_selection':'Only languages that already passed the previous alphabet-direction stability gate are eligible. This word test does not choose languages from spelling look-alikes.',
        'concepts':'NorthEuraLex concept IDs define meaning before phonetic comparison. Only concepts attested in all three languages of a candidate trio are used.',
        'phonetics':'NorthEuraLex segmented pronunciations are projected into the frozen PHOIBLE continuous phonetic plane.',
        'sequence_rule':'Speech order is never reversed. The fixed alphabet-direction transform acts only on phonetic coordinates: LR identity, RTL horizontal reflection, TB quarter-turn into the common frame.',
        'primary_score':'For every shared concept, each word trajectory is resampled to 16 positions and the mean of the three pairwise Euclidean trajectory distances is computed. Lower same-meaning distance than mismatched concepts is the semantic linkage signal.',
        'null':f'{PERMS} deterministic concept-label shuffles independently mismatch the RTL and TB meanings while preserving each language vocabulary and phonotactics.',
        'search_correction':'Every shuffled universe repeats the candidate-trio search. The final p-value compares the observed best trio with the best accidental trio in each null universe.',
        'pairwise_requirement':'LR-RL, LR-TB and RL-TB pairs must each independently beat their mismatched-meaning null.',
        'orientation_requirement':'All 8 expected/opposite orientation combinations are checked. A directional three-way link requires the documented LR/RL/TB combination to be the best.'
      },
      'coverage':{
        'phoible_segments':cov['research_segments'],
        'resolved_eligible_languages':[{'iso':iso,**{k:v for k,v in x.items() if k not in ('id','iso')}} for iso,x in sorted(resolved.items())],
        'resolved_counts':{'LR':len(lr),'RL':len(rl),'TB':len(tb)},
        'candidate_triples':len(candidates),'minimum_shared_concepts':MIN_SHARED,'permutations':PERMS
      },
      'selected_trio':selected,
      'ranking':candidates,
      'interpretation_rule':{
        'support':'Search-corrected p<0.05, all three pairwise same-meaning links p<0.05 with positive advantage, and expected orientation ranked first of 8.',
        'meaning':'Passing would show a reproducible meaning-matched phonetic trajectory correspondence under the pre-existing directional transforms. It would not by itself prove common ancestry or that meaning is intrinsically encoded by sound.',
        'failure':'Failure means the proposed directional three-way word system is not supported by this independently defined concept test.'
      }
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out['coverage'],ensure_ascii=False,indent=2))
    print(json.dumps(out['selected_trio'],ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
