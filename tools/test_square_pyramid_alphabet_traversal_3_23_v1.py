#!/usr/bin/env python3
from __future__ import annotations
import csv, json, statistics, unicodedata
from collections import defaultdict
from pathlib import Path

import man_grid_exact_data as D
import test_man_grid_alphabet_traversal_v1 as T

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/square-pyramid-alphabet-traversal-3-23-v1.json'
RESOLUTIONS=list(range(3,24))
PERMS=400

def bh(rows,pkey='p',qkey='q'):
    if not rows:return
    order=sorted(range(len(rows)),key=lambda i:rows[i][pkey])
    prev=1.0;m=len(rows)
    for rank in range(m,0,-1):
        i=order[rank-1]
        q=min(prev,rows[i][pkey]*m/rank)
        rows[i][qkey]=q;prev=q

def square_spec(n):
    return {'upper':[{'id':f'{n}x{n}','rows':n,'columns':n}],'lower':[]}

def prepare_languages():
    _,params,_,_,cov=D.load_phoible()
    name_to_pt={}
    for q in params.values():
        nm=unicodedata.normalize('NFC',q['name'])
        name_to_pt[nm]=(q['grid']['x'],q['grid']['y'])

    metas={r['iso']:r for r in csv.DictReader(T.BENCH.read_text(encoding='utf8').splitlines())
           if str(r.get('canonical','')).lower()=='true'}
    presets=json.loads(T.ORDERS.read_text(encoding='utf8'))['orders']
    presets={**presets,
      'kor':{'source':'Unicode modern Hangul Jamo order (compatibility forms)','symbols':T.K_ORDER},
      'okm':{'source':'Unicode modern Hangul Jamo order used as a restricted historical-Hangul probe','symbols':T.K_ORDER}
    }
    rows=[]
    failures=[]
    for iso in sorted(x for x in presets if x in metas):
        meta=metas[iso]
        alphabet=[T.normalizer(iso,x) if iso not in T.VERTICAL else x for x in presets[iso]['symbols']]
        try:
            lines=T.sample_lines(T.fetch(T.WP_BASE+meta['file']),T.MAX_WORDS,meta['file'])
            parsed=T.parse_words(lines,alphabet,iso,name_to_pt)
            train=[x for x in parsed if T.h64('split',iso,x[0])%5!=0]
            test=[x for x in parsed if T.h64('split',iso,x[0])%5==0]
            if len(train)<40:raise RuntimeError('too few mapped training words')
            C,support,trainerr=T.learn_centroids(train,alphabet)
            stable={g:C[g] for g in alphabet if g in C and support.get(g,0)>=T.MIN_SYMBOL_SUPPORT}
            frac=len(stable)/len(alphabet) if alphabet else 0
            if frac<T.MIN_SYMBOL_COVERAGE:
                raise RuntimeError(f'low stable-symbol coverage {frac:.3f}')
            rows.append({
              'iso':iso,'name':meta['name'],'script':meta['script'],'family':meta['family'],
              'direction':T.expected_class(iso),'alphabet_source':presets[iso]['source'],
              'alphabet_size':len(alphabet),'stable_symbols':len(stable),'symbol_fraction':frac,
              'train_words':len(train),'test_alignment':T.test_alignment(test,stable),
              'train_mean_coordinate_error':trainerr,'_alphabet':alphabet,'_centroids':stable
            })
        except Exception as e:
            failures.append({'iso':iso,'name':meta['name'],'error':str(e)})
    return rows,failures,cov

def group_stat(rows,group,n,perm_index=None):
    spec=square_spec(n);vals=[]
    for x in rows:
        if x['direction']!=group:continue
        alphabet=x['_alphabet']
        if perm_index is not None:
            alphabet=T.shuffled(alphabet,T.h64('sq23',group,n,perm_index,x['iso']))
        s=T.score_order(alphabet,x['_centroids'],spec)
        vals.append({
          'iso':x['iso'],'name':x['name'],'classes':s['classes'],
          'best_class':s['best_class'],
          'delta':s['classes'][group]-s['classes'][T.opposite(group)]
        })
    if not vals:return None,[]
    return statistics.mean(v['delta'] for v in vals),vals

def resolution_results(rows):
    allres=[]
    for n in RESOLUTIONS:
        groups={}
        langs={}
        for g in ('LR','RL','TB'):
            obs,detail=group_stat(rows,g,n)
            if obs is None:
                groups[g]={'languages':0};continue
            null=[]
            for k in range(PERMS):
                z,_=group_stat(rows,g,n,k);null.append(z)
            p=(1+sum(v>=obs for v in null))/(PERMS+1)
            groups[g]={
              'languages':len(detail),
              'mean_delta_vs_opposite':obs,
              'positive_languages':sum(v['delta']>0 for v in detail),
              'expected_class_best_languages':sum(v['best_class']==g for v in detail),
              'permutation_p':p,
              'null_mean':statistics.mean(null)
            }
            for v in detail:
                langs.setdefault(v['iso'],{
                  'iso':v['iso'],'name':v['name'],'direction':g
                }).update({
                  'classes':v['classes'],'best_class':v['best_class'],
                  'delta_vs_opposite':v['delta']
                })
        allres.append({'n':n,'groups':groups,'languages':list(langs.values())})

    for g in ('LR','RL','TB'):
        tmp=[{'n':z['n'],'p':z['groups'][g]['permutation_p']} for z in allres if z['groups'][g].get('languages',0)]
        bh(tmp)
        q={x['n']:x['q'] for x in tmp}
        for z in allres:
            if z['n'] in q:z['groups'][g]['bh_q_across_21_resolutions']=q[z['n']]
    return allres

def global_group_test(rows,group,resolutions):
    xs=[x for x in rows if x['direction']==group]
    if not xs:return {'languages':0}
    obs_by_n=[z['groups'][group]['mean_delta_vs_opposite'] for z in resolutions]
    obs=statistics.mean(obs_by_n)
    null=[]
    for k in range(PERMS):
        per=[]
        for n in RESOLUTIONS:
            vals=[]
            spec=square_spec(n)
            for x in xs:
                a=T.shuffled(x['_alphabet'],T.h64('sq23-global',group,k,x['iso']))
                s=T.score_order(a,x['_centroids'],spec)
                vals.append(s['classes'][group]-s['classes'][T.opposite(group)])
            per.append(statistics.mean(vals))
        null.append(statistics.mean(per))
    return {
      'languages':len(xs),
      'resolutions':len(RESOLUTIONS),
      'mean_delta_across_resolutions':obs,
      'positive_resolutions':sum(v>0 for v in obs_by_n),
      'permutation_p':(1+sum(v>=obs for v in null))/(PERMS+1),
      'null_mean':statistics.mean(null),
      'significant_raw_p_lt_0_05':sum(z['groups'][group]['permutation_p']<.05 for z in resolutions),
      'significant_bh_q_lt_0_05':sum(z['groups'][group].get('bh_q_across_21_resolutions',1)<.05 for z in resolutions)
    }

def progression(resolutions,group):
    ys=[z['groups'][group]['mean_delta_vs_opposite'] for z in resolutions]
    ns=RESOLUTIONS
    mx=statistics.mean(ns);my=statistics.mean(ys)
    den=sum((x-mx)**2 for x in ns)
    slope=sum((x-mx)*(y-my) for x,y in zip(ns,ys))/den if den else 0
    return {'slope_per_grid_step':slope,'first_3x3':ys[0],'last_23x23':ys[-1],
            'max_delta':max(ys),'max_at_n':ns[ys.index(max(ys))],
            'min_delta':min(ys),'min_at_n':ns[ys.index(min(ys))]}

def main():
    rows,failures,cov=prepare_languages()
    resolutions=resolution_results(rows)
    global_groups={g:global_group_test(rows,g,resolutions) for g in ('LR','RL','TB')}
    trends={g:progression(resolutions,g) for g in ('LR','RL','TB')}

    # Korean detail is surfaced because TB is the hypothesis of greatest interest.
    korean={}
    for iso in ('kor','okm'):
        seq=[]
        for z in resolutions:
            x=next((q for q in z['languages'] if q['iso']==iso),None)
            if x:seq.append({'n':z['n'],'classes':x['classes'],'best_class':x['best_class'],
                             'delta_vs_BT':x['delta_vs_opposite']})
        if seq:
            korean[iso]={
              'name':next(x['name'] for x in rows if x['iso']==iso),
              'best_is_TB_count':sum(x['best_class']=='TB' for x in seq),
              'positive_TB_vs_BT_count':sum(x['delta_vs_BT']>0 for x in seq),
              'sequence':seq
            }

    clean=[{k:v for k,v in x.items() if not k.startswith('_')} for x in rows]
    out={
      'version':1,'status':'complete',
      'test':'Frozen phonetic alphabet traversal across square resolutions 3x3 through 23x23',
      'source':{
        'phoible_commit':D.PH,'wikipron_commit':T.WP_COMMIT,
        'alphabet_orders':'data/phonetic-alphabet-orders.json + Unicode modern Hangul Jamo order for Korean probes'
      },
      'question':'Does the same pronunciation-derived alphabet placement reveal LTR, RTL, or top-to-bottom alphabet order when quantized through successive square grids from 3x3 to 23x23?',
      'design':{
        'continuous_coordinates':'Exactly the same frozen pronunciation-derived grapheme centroids as the exact-Man-Grid traversal test.',
        'resolution_sweep':'Every n x n square for n=3..23. No grapheme is re-fitted or moved between resolutions; only coordinate quantization changes.',
        'directions':{
          'LR':'row-major left-to-right, best of top-first/bottom-first',
          'RL':'row-major right-to-left, best of top-first/bottom-first',
          'TB':'column-major top-to-bottom, best of left-first/right-first',
          'BT':'column-major bottom-to-top, best of left-first/right-first'
        },
        'primary_statistic':'Pairwise alphabet-order concordance; expected direction minus its opposite.',
        'controls':f'{PERMS} deterministic shuffled alphabet orders at each resolution; Benjamini-Hochberg correction across the 21 resolutions; a second global permutation test averages all 21 resolutions while preserving their dependence.',
        'heldout':'20% deterministic word holdout is retained from the previous test for grapheme-to-pronunciation alignment validation.',
        'boundary':'Han characters remain excluded as an alphabet. Korean probes use ordered Hangul jamo.'
      },
      'coverage':{
        'phoible_segments':cov['research_segments'],
        'scored_systems':len(rows),'failures':len(failures),
        'resolutions':len(RESOLUTIONS),'range':[3,23]
      },
      'global_groups':global_groups,
      'resolution_trends':trends,
      'korean':korean,
      'resolutions':resolutions,
      'languages':clean,
      'failures':failures
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out['coverage'],indent=2))
    print('GLOBAL')
    print(json.dumps(global_groups,indent=2))
    print('TRENDS')
    print(json.dumps(trends,indent=2))
    print('KOREAN')
    for iso,x in korean.items():
        print(iso,x['best_is_TB_count'],x['positive_TB_vs_BT_count'])
        for q in x['sequence']:
            print(q['n'],round(q['delta_vs_BT'],5),q['best_class'])
    print('BY RESOLUTION')
    for z in resolutions:
        print(z['n'],json.dumps({g:{
          'delta':round(z['groups'][g]['mean_delta_vs_opposite'],5),
          'p':round(z['groups'][g]['permutation_p'],5),
          'q':round(z['groups'][g].get('bh_q_across_21_resolutions',1),5),
          'best':z['groups'][g]['expected_class_best_languages']
        } for g in ('LR','RL','TB')}))

if __name__=='__main__':
    main()
