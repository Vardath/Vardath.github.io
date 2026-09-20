#!/usr/bin/env python3
from __future__ import annotations
import csv, json, statistics, unicodedata
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

def tau_seq(seq):
    # Kendall-style pairwise order concordance with tied grid cells excluded.
    if len(seq)<2:return 0.0
    vals=sorted(set(seq));rank={v:i+1 for i,v in enumerate(vals)}
    bit=[0]*(len(vals)+2)
    def add(i):
        while i<len(bit):
            bit[i]+=1;i+=i&-i
    def qry(i):
        s=0
        while i>0:
            s+=bit[i];i-=i&-i
        return s
    con=dis=seen=0
    for v in seq:
        r=rank[v];less=qry(r-1);le=qry(r)
        con+=less;dis+=seen-le
        add(r);seen+=1
    den=con+dis
    return (con-dis)/den if den else 0.0

def traversal_arrays(stable_order,C,n):
    R=Cn=n
    out={k:[] for k in (
      'row_lr_top','row_lr_bottom','row_rl_top','row_rl_bottom',
      'col_tb_left','col_tb_right','col_bt_left','col_bt_right')}
    for g in stable_order:
        x=max(0,min(.999999,C[g][0]));y=max(0,min(.999999,C[g][1]))
        c=min(n-1,int(x*n));r=min(n-1,int((1-y)*n))
        vals={
          'row_lr_top':r*Cn+c,
          'row_lr_bottom':(R-1-r)*Cn+c,
          'row_rl_top':r*Cn+(Cn-1-c),
          'row_rl_bottom':(R-1-r)*Cn+(Cn-1-c),
          'col_tb_left':c*R+r,
          'col_tb_right':(Cn-1-c)*R+r,
          'col_bt_left':c*R+(R-1-r),
          'col_bt_right':(Cn-1-c)*R+(R-1-r)
        }
        for k,v in vals.items():out[k].append(v)
    return out

def class_scores(arrays,perm=None):
    if perm is None:
        def s(k):return tau_seq(arrays[k])
    else:
        def s(k):
            a=arrays[k]
            return tau_seq([a[i] for i in perm])
    return {
      'LR':max(s('row_lr_top'),s('row_lr_bottom')),
      'RL':max(s('row_rl_top'),s('row_rl_bottom')),
      'TB':max(s('col_tb_left'),s('col_tb_right')),
      'BT':max(s('col_bt_left'),s('col_bt_right'))
    }

def directional_delta(arrays,exp,perm):
    if exp=='LR':
        e=max(tau_seq([arrays['row_lr_top'][i] for i in perm]),
              tau_seq([arrays['row_lr_bottom'][i] for i in perm]))
        o=max(tau_seq([arrays['row_rl_top'][i] for i in perm]),
              tau_seq([arrays['row_rl_bottom'][i] for i in perm]))
    elif exp=='RL':
        e=max(tau_seq([arrays['row_rl_top'][i] for i in perm]),
              tau_seq([arrays['row_rl_bottom'][i] for i in perm]))
        o=max(tau_seq([arrays['row_lr_top'][i] for i in perm]),
              tau_seq([arrays['row_lr_bottom'][i] for i in perm]))
    elif exp=='TB':
        e=max(tau_seq([arrays['col_tb_left'][i] for i in perm]),
              tau_seq([arrays['col_tb_right'][i] for i in perm]))
        o=max(tau_seq([arrays['col_bt_left'][i] for i in perm]),
              tau_seq([arrays['col_bt_right'][i] for i in perm]))
    else:
        e=max(tau_seq([arrays['col_bt_left'][i] for i in perm]),
              tau_seq([arrays['col_bt_right'][i] for i in perm]))
        o=max(tau_seq([arrays['col_tb_left'][i] for i in perm]),
              tau_seq([arrays['col_tb_right'][i] for i in perm]))
    return e-o

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
    rows=[];failures=[]
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
            stable_order=[g for g in alphabet if g in stable]
            frac=len(stable_order)/len(alphabet) if alphabet else 0
            if frac<T.MIN_SYMBOL_COVERAGE:
                raise RuntimeError(f'low stable-symbol coverage {frac:.3f}')
            arrays={n:traversal_arrays(stable_order,stable,n) for n in RESOLUTIONS}
            rows.append({
              'iso':iso,'name':meta['name'],'script':meta['script'],'family':meta['family'],
              'direction':T.expected_class(iso),'alphabet_source':presets[iso]['source'],
              'alphabet_size':len(alphabet),'stable_symbols':len(stable_order),'symbol_fraction':frac,
              'train_words':len(train),'test_alignment':T.test_alignment(test,stable),
              'train_mean_coordinate_error':trainerr,'_stable_order':stable_order,'_arrays':arrays
            })
        except Exception as e:
            failures.append({'iso':iso,'name':meta['name'],'error':str(e)})
    return rows,failures,cov

def observed(rows):
    res=[]
    for n in RESOLUTIONS:
        langs=[]
        for x in rows:
            cls=class_scores(x['_arrays'][n])
            exp=x['direction'];opp=T.opposite(exp)
            langs.append({
              'iso':x['iso'],'name':x['name'],'direction':exp,
              'classes':cls,'best_class':max(cls,key=cls.get),
              'delta_vs_opposite':cls[exp]-cls[opp]
            })
        groups={}
        for g in ('LR','RL','TB'):
            xs=[x for x in langs if x['direction']==g]
            groups[g]={
              'languages':len(xs),
              'mean_delta_vs_opposite':statistics.mean(x['delta_vs_opposite'] for x in xs),
              'positive_languages':sum(x['delta_vs_opposite']>0 for x in xs),
              'expected_class_best_languages':sum(x['best_class']==g for x in xs)
            }
        res.append({'n':n,'groups':groups,'languages':langs})
    return res

def permutation_nulls(rows):
    groups=('LR','RL','TB')
    null={g:{n:[] for n in RESOLUTIONS} for g in groups}
    by_group={g:[x for x in rows if x['direction']==g] for g in groups}
    for k in range(PERMS):
        # One independently shuffled alphabet order per language is reused across
        # every resolution. This preserves the dependence of the 3->23 ladder.
        perms={x['iso']:T.shuffled(range(len(x['_stable_order'])),T.h64('sq23-shared',k,x['iso']))
               for x in rows}
        for g in groups:
            xs=by_group[g]
            for n in RESOLUTIONS:
                ds=[directional_delta(x['_arrays'][n],g,perms[x['iso']]) for x in xs]
                null[g][n].append(statistics.mean(ds))
        if (k+1)%100==0:print(f'permutations {k+1}/{PERMS}',flush=True)
    return null

def attach_significance(resolutions,null):
    for g in ('LR','RL','TB'):
        tmp=[]
        for z in resolutions:
            n=z['n'];obs=z['groups'][g]['mean_delta_vs_opposite'];ns=null[g][n]
            p=(1+sum(v>=obs for v in ns))/(PERMS+1)
            z['groups'][g]['permutation_p']=p
            z['groups'][g]['null_mean']=statistics.mean(ns)
            tmp.append({'n':n,'p':p})
        bh(tmp)
        qs={x['n']:x['q'] for x in tmp}
        for z in resolutions:z['groups'][g]['bh_q_across_21_resolutions']=qs[z['n']]

def global_group_tests(rows,resolutions,null):
    out={}
    for g in ('LR','RL','TB'):
        obs_by=[z['groups'][g]['mean_delta_vs_opposite'] for z in resolutions]
        obs=statistics.mean(obs_by)
        global_null=[statistics.mean(null[g][n][k] for n in RESOLUTIONS) for k in range(PERMS)]
        out[g]={
          'languages':sum(x['direction']==g for x in rows),
          'resolutions':len(RESOLUTIONS),
          'mean_delta_across_resolutions':obs,
          'positive_resolutions':sum(v>0 for v in obs_by),
          'permutation_p':(1+sum(v>=obs for v in global_null))/(PERMS+1),
          'null_mean':statistics.mean(global_null),
          'significant_raw_p_lt_0_05':sum(z['groups'][g]['permutation_p']<.05 for z in resolutions),
          'significant_bh_q_lt_0_05':sum(z['groups'][g]['bh_q_across_21_resolutions']<.05 for z in resolutions)
        }
    return out

def progression(resolutions,group):
    ys=[z['groups'][group]['mean_delta_vs_opposite'] for z in resolutions]
    mx=statistics.mean(RESOLUTIONS);my=statistics.mean(ys)
    den=sum((x-mx)**2 for x in RESOLUTIONS)
    slope=sum((x-mx)*(y-my) for x,y in zip(RESOLUTIONS,ys))/den if den else 0
    return {
      'slope_per_grid_step':slope,'first_3x3':ys[0],'last_23x23':ys[-1],
      'max_delta':max(ys),'max_at_n':RESOLUTIONS[ys.index(max(ys))],
      'min_delta':min(ys),'min_at_n':RESOLUTIONS[ys.index(min(ys))]
    }

def main():
    rows,failures,cov=prepare_languages()
    resolutions=observed(rows)
    null=permutation_nulls(rows)
    attach_significance(resolutions,null)
    global_groups=global_group_tests(rows,resolutions,null)
    trends={g:progression(resolutions,g) for g in ('LR','RL','TB')}

    korean={}
    for iso in ('kor','okm'):
        seq=[]
        for z in resolutions:
            x=next((q for q in z['languages'] if q['iso']==iso),None)
            if x:
                seq.append({'n':z['n'],'classes':x['classes'],'best_class':x['best_class'],
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
        'controls':f'{PERMS} deterministic shuffled alphabet orders. Each shuffled alphabet is reused across all 21 resolutions to preserve ladder dependence; Benjamini-Hochberg correction is applied across resolutions, plus a global full-ladder permutation test.',
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
    print('GLOBAL',json.dumps(global_groups,indent=2))
    print('TRENDS',json.dumps(trends,indent=2))
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
          'q':round(z['groups'][g]['bh_q_across_21_resolutions'],5),
          'best':z['groups'][g]['expected_class_best_languages']
        } for g in ('LR','RL','TB')}))

if __name__=='__main__':
    main()
