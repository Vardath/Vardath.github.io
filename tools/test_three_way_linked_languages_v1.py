#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, statistics, unicodedata
from pathlib import Path

import man_grid_exact_data as D
import test_man_grid_alphabet_traversal_v1 as T

ROOT=Path(__file__).resolve().parents[1]
SWEEP=ROOT/'data/square-pyramid-alphabet-traversal-3-23-v1.json'
OUT=ROOT/'data/three-way-linked-language-test-v1.json'
PERMS=1000
K=64
MIN_POSITIVE_RESOLUTIONS=15

def prepare_languages():
    _,params,_,_,cov=D.load_phoible()
    name_to_pt={}
    for q in params.values():
        nm=unicodedata.normalize('NFC',q['name'])
        name_to_pt[nm]=(q['grid']['x'],q['grid']['y'])
    metas={r['iso']:r for r in csv.DictReader(T.BENCH.read_text(encoding='utf8').splitlines())
           if str(r.get('canonical','')).lower()=='true'}
    presets=json.loads(T.ORDERS.read_text(encoding='utf8'))['orders']
    presets={**presets,'kor':{'source':'Unicode modern Hangul Jamo order (compatibility forms)','symbols':T.K_ORDER}}
    targets=[x for x in presets if x in metas and x!='okm']  # modern systems only for the independent-trio search
    rows={}
    for iso in sorted(targets):
        meta=metas[iso]
        alphabet=[T.normalizer(iso,x) if iso not in T.VERTICAL else x for x in presets[iso]['symbols']]
        try:
            lines=T.sample_lines(T.fetch(T.WP_BASE+meta['file']),T.MAX_WORDS,meta['file'])
            parsed=T.parse_words(lines,alphabet,iso,name_to_pt)
            train=[x for x in parsed if T.h64('split',iso,x[0])%5!=0]
            test=[x for x in parsed if T.h64('split',iso,x[0])%5==0]
            if len(train)<40:continue
            C,support,trainerr=T.learn_centroids(train,alphabet)
            stable_order=[g for g in alphabet if g in C and support.get(g,0)>=T.MIN_SYMBOL_SUPPORT]
            stable={g:C[g] for g in stable_order}
            frac=len(stable_order)/len(alphabet) if alphabet else 0
            if frac<T.MIN_SYMBOL_COVERAGE:continue
            rows[iso]={
              'iso':iso,'name':meta['name'],'script':meta['script'],'family':meta['family'],
              'direction':T.expected_class(iso),'alphabet_size':len(alphabet),
              'stable_symbols':len(stable_order),'symbol_fraction':frac,
              'test_alignment':T.test_alignment(test,stable),
              '_order':stable_order,'_C':stable
            }
        except Exception:
            pass
    return rows,cov

def orient(pt,dir):
    x,y=pt
    if dir=='LR': return (x,y)
    if dir=='RL': return (1-x,y)
    if dir=='TB': return (1-y,x)
    if dir=='BT': return (y,x)
    raise ValueError(dir)

def resample(points,k=K):
    if not points:return []
    if len(points)==1:return [points[0]]*k
    out=[]
    for j in range(k):
        u=j*(len(points)-1)/(k-1)
        i=min(len(points)-2,int(math.floor(u)))
        f=u-i
        a,b=points[i],points[i+1]
        out.append((a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f))
    return out

def trajectory(row,order_override=None):
    order=order_override if order_override is not None else row['_order']
    pts=[orient(row['_C'][g],row['direction']) for g in order]
    return resample(pts)

def pairdist(a,b):
    return statistics.mean(math.dist(x,y) for x,y in zip(a,b))

def trio_distance(A,B,C):
    return statistics.mean((pairdist(A,B),pairdist(A,C),pairdist(B,C)))

def pearson(a,b):
    ma=statistics.mean(a);mb=statistics.mean(b)
    da=[x-ma for x in a];db=[y-mb for y in b]
    den=math.sqrt(sum(x*x for x in da)*sum(y*y for y in db))
    return sum(x*y for x,y in zip(da,db))/den if den else 0.0

def avg_profile_corr(a,b,c):
    return statistics.mean((pearson(a,b),pearson(a,c),pearson(b,c)))

def rotate(v,k):
    k%=len(v)
    return v[k:]+v[:k]

def main():
    rows,cov=prepare_languages()
    sweep=json.loads(SWEEP.read_text(encoding='utf8'))
    byiso={}
    for z in sweep['resolutions']:
        for x in z['languages']:
            if x['iso']=='okm':continue
            q=byiso.setdefault(x['iso'],{'dir':x['direction'],'delta':[],'best':[]})
            q['delta'].append(x['delta_vs_opposite']);q['best'].append(x['best_class']==x['direction'])
    stability={}
    for iso,q in byiso.items():
        stability[iso]={
          'direction':q['dir'],'positive_resolutions':sum(x>0 for x in q['delta']),
          'mean_delta':statistics.mean(q['delta']),
          'best_direction_resolutions':sum(q['best']),
          'profile':q['delta']
        }

    eligible={'LR':[],'RL':[],'TB':[]}
    for iso,row in rows.items():
        st=stability.get(iso)
        if not st:continue
        if st['mean_delta']>0 and st['positive_resolutions']>=MIN_POSITIVE_RESOLUTIONS:
            eligible[row['direction']].append(iso)

    # Only independent modern systems are admitted. The current dataset has one
    # qualifying TB system (Korean) and, as the results show, one qualifying RTL
    # system (Hebrew), leaving the LTR member to be selected by the linked test.
    triples=[]
    traj={iso:trajectory(rows[iso]) for g in eligible.values() for iso in g}
    for a in eligible['LR']:
        for b in eligible['RL']:
            for c in eligible['TB']:
                dist=trio_distance(traj[a],traj[b],traj[c])
                corr=avg_profile_corr(stability[a]['profile'],stability[b]['profile'],stability[c]['profile'])
                triples.append({
                  'LR':a,'RL':b,'TB':c,'trajectory_distance':dist,
                  'trajectory_similarity':1-dist/math.sqrt(2),
                  'resolution_profile_correlation':corr,
                  'mean_directional_delta':statistics.mean((
                     stability[a]['mean_delta'],stability[b]['mean_delta'],stability[c]['mean_delta']))
                })
    triples.sort(key=lambda x:(x['trajectory_distance'],-x['resolution_profile_correlation']))
    if not triples:raise RuntimeError('no eligible three-way triples')
    best=triples[0]

    # Search-corrected null: shuffle alphabet order within every eligible language,
    # then re-run the entire eligible-triple search and retain the best accidental trio.
    null_best=[];fixed_null=[]
    for k in range(PERMS):
        ptraj={}
        for g in eligible.values():
            for iso in g:
                o=T.shuffled(rows[iso]['_order'],T.h64('linked-trio',k,iso))
                ptraj[iso]=trajectory(rows[iso],o)
        ds=[]
        for tr in triples:
            d=trio_distance(ptraj[tr['LR']],ptraj[tr['RL']],ptraj[tr['TB']])
            ds.append(d)
            if tr is best:fixed_null.append(d)
        null_best.append(min(ds))
    best_p=(1+sum(x<=best['trajectory_distance'] for x in null_best))/(PERMS+1)
    fixed_p=(1+sum(x<=best['trajectory_distance'] for x in fixed_null))/(PERMS+1)

    # Secondary linkage check: do the three directional-strength profiles rise and
    # fall together at the same grid sizes? Circular shifts preserve each profile's
    # smoothness while breaking shared resolution phase.
    A=stability[best['LR']]['profile'];B=stability[best['RL']]['profile'];C=stability[best['TB']]['profile']
    obs_corr=avg_profile_corr(A,B,C)
    corr_null=[]
    n=len(A)
    for k in range(PERMS):
        sb=1+(T.h64('corr-b',k)% (n-1))
        sc=1+(T.h64('corr-c',k)% (n-1))
        corr_null.append(avg_profile_corr(A,rotate(B,sb),rotate(C,sc)))
    corr_p=(1+sum(x>=obs_corr for x in corr_null))/(PERMS+1)

    # Wrong-orientation control for the selected trio.
    opposite={'LR':'RL','RL':'LR','TB':'BT'}
    wrong=[]
    for iso in (best['LR'],best['RL'],best['TB']):
        row=rows[iso]
        pts=[orient(row['_C'][g],opposite[row['direction']]) for g in row['_order']]
        wrong.append(resample(pts))
    wrong_dist=trio_distance(*wrong)

    clean_triples=[]
    for tr in triples:
        x=dict(tr)
        x['languages']={
          'LR':rows[tr['LR']]['name'],'RL':rows[tr['RL']]['name'],'TB':rows[tr['TB']]['name']
        }
        clean_triples.append(x)

    selected={
      **best,
      'languages':{'LR':rows[best['LR']]['name'],'RL':rows[best['RL']]['name'],'TB':rows[best['TB']]['name']},
      'search_corrected_permutation_p':best_p,
      'fixed_trio_permutation_p':fixed_p,
      'resolution_profile_correlation_p':corr_p,
      'wrong_orientation_distance':wrong_dist,
      'wrong_orientation_worse':wrong_dist>best['trajectory_distance'],
      'members':{}
    }
    for g,iso in (('LR',best['LR']),('RL',best['RL']),('TB',best['TB'])):
        selected['members'][g]={
          'iso':iso,'name':rows[iso]['name'],'family':rows[iso]['family'],'script':rows[iso]['script'],
          'positive_resolutions':stability[iso]['positive_resolutions'],
          'best_direction_resolutions':stability[iso]['best_direction_resolutions'],
          'mean_delta':stability[iso]['mean_delta'],
          'stable_symbols':rows[iso]['stable_symbols'],
          'symbol_fraction':rows[iso]['symbol_fraction']
        }

    out={
      'version':1,'status':'complete',
      'test':'Linked three-way language traversal search',
      'question':'Which LTR, RTL and top-to-bottom languages form the strongest linked trio on one frozen phonetic field, rather than merely fitting their directions separately?',
      'design':{
        'eligibility':f'A language must beat its opposite direction at >= {MIN_POSITIVE_RESOLUTIONS}/21 resolutions and have positive mean directional advantage. Middle Korean is excluded so the vertical member is a modern independent system.',
        'no_refitting':'All grapheme positions are learned from pronunciation evidence exactly as in the previous frozen-grid test. No language is translated, rotated freely, rescaled, shifted or re-placed to improve trio fit.',
        'direction_normalization':'LTR is unchanged; RTL is reflected horizontally; TB is rotated into the same canonical left-to-right frame. These are fixed transforms determined only by documented reading direction.',
        'primary_linkage':'The full ordered grapheme trajectory of each language is resampled to 64 rank positions. Linkage is mean pairwise Euclidean distance between the three canonical trajectories. Lower is better.',
        'search_control':f'{PERMS} within-language alphabet-order shuffles repeat the entire eligible-triple search. The reported search-corrected p-value asks whether the best observed trio is closer than the best accidental trio produced by each shuffled universe.',
        'secondary_linkage':'The 21-resolution directional-strength profiles must also rise and fall together. Circular-shift nulls preserve each profile but break common resolution phase.',
        'wrong_orientation_control':'The selected trio is also scored after applying the opposite direction to each member.'
      },
      'coverage':{
        'phoible_segments':cov['research_segments'],
        'eligible':{g:len(v) for g,v in eligible.items()},
        'eligible_members':{g:[{'iso':i,'name':rows[i]['name']} for i in v] for g,v in eligible.items()},
        'candidate_triples':len(triples),
        'permutations':PERMS
      },
      'selected_trio':selected,
      'ranking':clean_triples,
      'interpretation_rule':{
        'linked_support':'Strong evidence would require a search-corrected trajectory p<0.05, positive direction stability for all three members, a positive resolution-profile correlation with its own p<0.05, and the correct-orientation trio to beat the wrong-orientation control.',
        'partial_support':'If only the primary trajectory test passes, the trio is geometrically linked but the shared multiresolution pattern is not independently established.',
        'not_supported':'If the search-corrected primary test fails, the apparent trio can be explained by selecting the best-looking combination from the available languages.'
      }
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out['coverage'],indent=2))
    print(json.dumps(out['selected_trio'],indent=2))
    print('TOP RANKING')
    for x in clean_triples[:10]:print(json.dumps(x))

if __name__=='__main__':
    main()
