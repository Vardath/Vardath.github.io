#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Local defaults are overridable by args/env in GitHub workflow via cwd/repo layout.
REPO = ROOT
WORK = REPO / 'data' / 'man-grid-test14-exact-v4-work'
T13 = REPO / 'data' / 'man-grid-test-13-exact-v4.json'
MODEL = REPO / 'data' / 'man-grid-exact-v4-work' / 'model.json.gz'
OUT = REPO / 'data' / 'man-grid-test-14-exact-v4.json'
N = 20
GAP = 0.70
MIN_RULE_SUPPORT = 3
CELL_RE = re.compile(r'-R(\d+)-C(\d+)$')
DELETE = '__DELETE__'


def set_repo(root: Path):
    global REPO, WORK, T13, MODEL, OUT
    REPO = root
    WORK = REPO / 'data' / 'man-grid-test14-exact-v4-work'
    T13 = REPO / 'data' / 'man-grid-test-13-exact-v4.json'
    MODEL = REPO / 'data' / 'man-grid-exact-v4-work' / 'model.json.gz'
    OUT = REPO / 'data' / 'man-grid-test-14-exact-v4.json'


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def read_gz(p):
    with gzip.open(p, 'rt', encoding='utf-8') as f:
        return json.load(f)


def write_gz(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def cell_rc(cell):
    m = CELL_RE.search(cell)
    if not m:
        raise RuntimeError(f'cannot parse Man Grid cell {cell!r}')
    return tuple(map(int, m.groups()))


def layer_specs(model):
    return [*model['grid']['upper'], *model['grid']['lower']]


def mirror_grid_distance(a, b, model):
    ga = model['params'][a]['grid']; gb = model['params'][b]['grid']
    layers = layer_specs(model)
    vals = []
    for sa, sb in [('all_left','all_right'), ('all_right','all_left')]:
        one = []
        for ca, cb, layer in zip(ga[sa], gb[sb], layers):
            ra, xa = cell_rc(ca); rb, xb = cell_rc(cb)
            rd = abs(ra-rb) / max(1, int(layer['rows'])-1)
            cd = abs(xa-xb) / max(1, int(layer['columns'])-1)
            one.append((rd+cd)/2.0)
        vals.append(statistics.mean(one))
    return statistics.mean(vals)


def one_way_grid_distance(a, b, model, from_side, to_side):
    ga=model['params'][a]['grid']; gb=model['params'][b]['grid']; layers=layer_specs(model)
    pa=ga['all_left'] if from_side=='L' else ga['all_right']
    pb=gb['all_right'] if to_side=='R' else gb['all_left']
    vals=[]
    for ca,cb,layer in zip(pa,pb,layers):
        ra,xa=cell_rc(ca); rb,xb=cell_rc(cb)
        vals.append((abs(ra-rb)/max(1,int(layer['rows'])-1)+abs(xa-xb)/max(1,int(layer['columns'])-1))/2.0)
    return statistics.mean(vals)


def signed_grid_move(a, b, model):
    ga=model['params'][a]['grid']; gb=model['params'][b]['grid']; layers=layer_specs(model); out=[]
    for i,layer in enumerate(layers):
        al=cell_rc(ga['all_left'][i]); ar=cell_rc(ga['all_right'][i])
        bl=cell_rc(gb['all_left'][i]); br=cell_rc(gb['all_right'][i])
        rd=max(1,int(layer['rows'])-1); cd=max(1,int(layer['columns'])-1)
        dr=(((br[0]-al[0])/rd)+((bl[0]-ar[0])/rd))/2.0
        dc=(((br[1]-al[1])/cd)+((bl[1]-ar[1])/cd))/2.0
        out.extend([round(dr,8),round(dc,8)])
    return out


def costs_for(model):
    roots = list(model['root_ids'])
    return {a:{b:mirror_grid_distance(a,b,model) for b in roots} for a in roots}


def seqdist(a, b, costs):
    a=tuple(a); b=tuple(b)
    if not a and not b: return 0.0
    if not a or not b: return 1.0
    dp=[j*GAP for j in range(len(b)+1)]
    for i,x in enumerate(a,1):
        nd=[i*GAP]+[0.0]*len(b)
        for j,y in enumerate(b,1):
            nd[j]=min(dp[j]+GAP, nd[j-1]+GAP, dp[j-1]+costs[x][y])
        dp=nd
    return min(1.0, dp[-1]/max(len(a),len(b)))


def fold_of(key):
    h=hashlib.sha256((key[0]+'|'+key[1]).encode('utf-8')).hexdigest()
    return int(h[:12],16)%N


def pos_class(i,n):
    if n == 1: return 'single'
    if i == 0: return 'initial'
    if i == n-1: return 'final'
    return 'medial'


def gap_class(i,n):
    if i == 0: return 'initial_gap'
    if i == n: return 'final_gap'
    return 'medial_gap'


def weighted_medoid(counter, roots, costs):
    den=sum(counter.values())
    if den <= 0: return None
    return min(roots, key=lambda q:(sum((costs[q][t]**2)*w for t,w in counter.items())/den, q))


def event_loss(source, prediction, target, costs):
    # target/prediction None means deletion/no token.
    if prediction is None:
        return 0.0 if target is None else GAP
    if target is None:
        return GAP
    return costs[prediction][target]


def choose_token_rule(source, stat, roots, costs):
    n=stat['n']
    if n < MIN_RULE_SUPPORT:
        return None
    target_counts=stat['targets']
    candidates=[source, None]
    med=weighted_medoid(target_counts, roots, costs)
    if med is not None: candidates.append(med)
    uniq=[]
    for x in candidates:
        if x not in uniq: uniq.append(x)
    def total_loss(pred):
        return stat['deletions']*event_loss(source,pred,None,costs) + sum(w*event_loss(source,pred,t,costs) for t,w in target_counts.items())
    scored=sorted((total_loss(q), 0 if q==source else 1, '' if q is None else str(q), q) for q in uniq)
    best=scored[0][3]
    base=total_loss(source)
    gain=base-scored[0][0]
    if best == source or gain <= 1e-12:
        return None
    return {'prediction':best, 'support':n, 'train_gain':gain/n, 'base_loss':base/n, 'rule_loss':scored[0][0]/n}


def choose_insertion_rule(stat, roots, costs):
    # Each opportunity has zero or more actual inserted roots. Predict either none or one root.
    n=stat['opportunities']
    if n < MIN_RULE_SUPPORT:
        return None
    targets=stat['targets']
    med=weighted_medoid(targets, roots, costs)
    if med is None: return None
    # Baseline predicts no insertion. Every actual inserted token costs GAP.
    base=sum(len(x)*w*GAP for x,w in stat['actual_sequences'].items())
    rule=0.0
    for actual,w in stat['actual_sequences'].items():
        if not actual:
            rule += w*GAP
        else:
            rule += w*(costs[med][actual[0]] + max(0,len(actual)-1)*GAP)
    if rule + 1e-12 >= base:
        return None
    return {'prediction':med, 'support':n, 'train_gain':(base-rule)/n, 'base_loss':base/n, 'rule_loss':rule/n}


def build_lineage_model(train_entries, roots, costs):
    base_stats=defaultdict(lambda:{'n':0,'deletions':0,'targets':Counter()})
    pos_stats=defaultdict(lambda:{'n':0,'deletions':0,'targets':Counter()})
    gap_stats=defaultdict(lambda:{'opportunities':0,'targets':Counter(),'actual_sequences':Counter()})
    for e in train_entries:
        anc=e['ancestor_seq']; n=len(anc)
        inserted=defaultdict(list)
        for ev in e['alignment']:
            a=ev['a']; b=ev['b']
            if a is None:
                gi=int(ev['ia'])
                if b is not None: inserted[gi].append(b)
                continue
            i=int(ev['ia']); pc=pos_class(i,n)
            for key,stats in [(a,base_stats), ((a,pc),pos_stats)]:
                st=stats[key]; st['n']+=1
                if b is None: st['deletions']+=1
                else: st['targets'][b]+=1
        for gi in range(n+1):
            left=anc[gi-1] if gi>0 else '^'
            right=anc[gi] if gi<n else '$'
            key=(left,right,gap_class(gi,n))
            st=gap_stats[key]; st['opportunities']+=1
            actual=tuple(inserted.get(gi,[]))
            st['actual_sequences'][actual]+=1
            st['targets'].update(actual)
    base_rules={}
    for a,st in base_stats.items():
        r=choose_token_rule(a,st,roots,costs)
        if r: base_rules[a]=r
    pos_rules={}
    for (a,pc),st in pos_stats.items():
        r=choose_token_rule(a,st,roots,costs)
        if r: pos_rules[(a,pc)]=r
    ins_rules={}
    for key,st in gap_stats.items():
        r=choose_insertion_rule(st,roots,costs)
        if r: ins_rules[key]=r
    return {'base':base_rules,'pos':pos_rules,'ins':ins_rules}


def transform(seq, lm, contextual=True, allow_insertions=True):
    seq=list(seq); n=len(seq); out=[]
    def maybe_insert(gi):
        if not contextual or not allow_insertions: return
        left=seq[gi-1] if gi>0 else '^'; right=seq[gi] if gi<n else '$'
        r=lm['ins'].get((left,right,gap_class(gi,n)))
        if r and r['prediction'] is not None: out.append(r['prediction'])
    maybe_insert(0)
    for i,a in enumerate(seq):
        r=None
        if contextual: r=lm['pos'].get((a,pos_class(i,n)))
        if r is None: r=lm['base'].get(a)
        pred=a if r is None else r['prediction']
        if pred is not None: out.append(pred)
        maybe_insert(i+1)
    return out


def rule_key_token(source, pos, pred):
    return ('token',source,pos,DELETE if pred is None else pred)


def rule_key_insert(left,right,gc,pred):
    return ('insert',left,right,gc,pred)


def heldout_rule_events(e, lm, costs):
    anc=e['ancestor_seq']; n=len(anc); rows=[]
    inserted=defaultdict(list)
    for ev in e['alignment']:
        a=ev['a']; b=ev['b']
        if a is None:
            if b is not None: inserted[int(ev['ia'])].append(b)
            continue
        i=int(ev['ia']); pc=pos_class(i,n)
        r=lm['pos'].get((a,pc))
        if r is not None:
            pred=r['prediction']
            rows.append((rule_key_token(a,pc,pred), event_loss(a,a,b,costs), event_loss(a,pred,b,costs)))
    for gi in range(n+1):
        left=anc[gi-1] if gi>0 else '^'; right=anc[gi] if gi<n else '$'; gc=gap_class(gi,n)
        r=lm['ins'].get((left,right,gc))
        if r is None: continue
        actual=tuple(inserted.get(gi,[])); pred=r['prediction']
        base=len(actual)*GAP
        if not actual: rl=GAP
        else: rl=costs[pred][actual[0]] + max(0,len(actual)-1)*GAP
        rows.append((rule_key_insert(left,right,gc,pred),base,rl))
    return rows


def paired_dz(real, ctrl):
    ds=[c-r for r,c in zip(real,ctrl)]
    if len(ds)<2: return None
    sd=statistics.stdev(ds)
    return statistics.mean(ds)/sd if sd else None


def diff_moments(real, ctrl):
    ds=[c-r for r,c in zip(real,ctrl)]
    return {'n':len(ds),'sum':sum(ds),'sumsq':sum(x*x for x in ds)}


def dz_from_moments(ms):
    n=sum(m['n'] for m in ms); sm=sum(m['sum'] for m in ms); ss=sum(m['sumsq'] for m in ms)
    if n < 2: return None
    mean=sm/n
    var=(ss-(sm*sm/n))/(n-1)
    sd=math.sqrt(max(0.0,var))
    return mean/sd if sd else None


def exact_two_sided_sign_p(wins, losses):
    n=wins+losses
    if n <= 0: return 1.0
    k=min(wins,losses)
    tail=sum(math.comb(n,i) for i in range(k+1))/(2**n)
    return min(1.0,2.0*tail)


def bh_qvalues(ps):
    m=len(ps); out=[1.0]*m; prev=1.0
    ranked=sorted((p,i) for i,p in enumerate(ps))
    for rank in range(m,0,-1):
        p,i=ranked[rank-1]
        q=min(prev,p*m/rank)
        out[i]=q; prev=q
    return out


def validate_sources(t13, model):
    if t13.get('test_id') != 13 or t13.get('status') != 'complete' or t13.get('shards') != 20:
        raise RuntimeError('Test 13 source is not the completed corrected 20-shard result')
    c=t13.get('calculation',{})
    if c.get('feature_distance_used_for_test13_scoring') is not False or c.get('old_grid_rules_imported') is not False:
        raise RuntimeError('Test 13 source violates corrected-grid contract')
    if c.get('central_circle_operator_used') is not False:
        raise RuntimeError('Test 13 unexpectedly used a circle operator')
    if int(model.get('grid',{}).get('counts',{}).get('total_cells',0)) != 1074:
        raise RuntimeError('model is not the exact 1,074-cell Man Grid')
    if len(model.get('root_ids',[])) != 36:
        raise RuntimeError('model does not contain the corrected 36-root inventory')
    if model.get('calculation',{}).get('feature_distance_used_for_test5_reconstruction') is not False:
        raise RuntimeError('model is not corrected mirror-grid model')
    if model.get('calculation',{}).get('transformative_circle_operator') is not None:
        raise RuntimeError('model unexpectedly contains a circle operator')


def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    t13=read_json(T13); model=read_gz(MODEL); validate_sources(t13,model)
    write_gz(WORK/'test13.json.gz',t13); write_gz(WORK/'model.json.gz',model)
    lineages=defaultdict(lambda:{'train':0,'heldout':0})
    for e in t13['entries']:
        k=(e['parent_code'],e['child_code'])
        lineages[k][e['role']]+=1
    evals=[k for k,v in lineages.items() if v['heldout']>0 and v['train']>0]
    fold_sizes=[0]*N; fold_records=[0]*N
    for k in evals:
        f=fold_of(k); fold_sizes[f]+=1; fold_records[f]+=lineages[k]['heldout']
    manifest={
      'version':4,'test_id':14,'test':'Cross-validated historical transformation-rule discovery on the corrected mirrored Man Grid',
      'shards':N,'dependency':{'test13':'completed corrected exact-v4 Test 13 historical records','test1':'36-root inventory embedded in corrected mirror-grid model'},
      'grid':{'cells':1074,'all_rectangles_mirrored':True,'layers_per_side':10,'transformative_circle_operator':None},
      'calculation':{
        'metric':'exact_mirror_man_grid_10_layer_bilateral',
        'rule_unit':'lineage-specific source-root + word-position class, with source-root backoff; insertion rules use exact ancestor gap context',
        'rule_target_selection':'target root minimizing weighted squared exact mirrored-Man-Grid distance; deletion/no-insertion compete directly under the same alignment cost; rule retained only if training loss strictly improves on identity/no-insertion',
        'minimum_repeated_training_support':MIN_RULE_SUPPORT,
        'heldout_validation':'uses only Test 13 records preassigned heldout; Test 13 train records alone discover rules',
        'controls':['identity/no-rule ancestor','source-root-only rule model','deterministically shuffled foreign-lineage rule model'],
        'portable_rule_validation':'at least 8 heldout applications across at least 3 independent documented lineages, positive mean exact-grid gain, more heldout wins than losses, and Benjamini-Hochberg FDR q<=0.05 across discovered contextual rule types',
        'mirror_effect_test':'bilateral L->R and R->L geometry is scored explicitly; because the source representation supplies both mirror addresses but no observed side label, a side-specific historical mirror effect is not identifiable and is not invented',
        'circle_behavior_test':'Test 13 supplies no learned transformative-circle operator or circle-labelled transition evidence; no circle behavior is inferred',
        'feature_distance_used_for_test14_scoring':False,
        'test5_lexicon_used_for_test14':False,
        'old_test14_result_used':False,
        'old_grid_rules_imported':False,
        'central_circle_operator_used':False,
      },
      'coverage':{'historical_records':len(t13['entries']),'documented_lineages':len(lineages),'evaluation_lineages':len(evals),'heldout_records':sum(lineages[k]['heldout'] for k in evals)},
      'lineage_fold_sizes':fold_sizes,'heldout_record_fold_sizes':fold_records,
      'execution':{'partition':'20 deterministic disjoint heldout-lineage folds; all records for a lineage remain in one fold','merge_requires_all_20':True,'workflow_custom_timeout_minutes':None}
    }
    write_json(WORK/'prepared-manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


def run_shard(shard):
    t13=read_gz(WORK/'test13.json.gz'); model=read_gz(WORK/'model.json.gz'); validate_sources(t13,model)
    roots=list(model['root_ids']); costs=costs_for(model)
    bylin=defaultdict(list)
    names={}
    for e in t13['entries']:
        k=(e['parent_code'],e['child_code']); bylin[k].append(e); names[k]=(e['parent_language'],e['child_language'])
    models={}
    for k,es in bylin.items():
        tr=[e for e in es if e['role']=='train']
        if tr: models[k]=build_lineage_model(tr,roots,costs)
    allkeys=sorted(models)
    evalkeys=[k for k in allkeys if fold_of(k)==shard and any(e['role']=='heldout' for e in bylin[k])]
    contextual=[]; sourceonly=[]; identity=[]; shuffled=[]; lineages=[]
    ruleval=defaultdict(lambda:{'applications':0,'lineages':set(),'base_loss':0.0,'rule_loss':0.0,'wins':0,'ties':0,'losses':0})
    for k in evalkeys:
        lm=models[k]
        idx=allkeys.index(k)
        offset=1+(int(hashlib.sha256((k[0]+'>'+k[1]+'|shuffle').encode()).hexdigest()[:8],16)%(len(allkeys)-1))
        sk=allkeys[(idx+offset)%len(allkeys)]
        if sk==k: sk=allkeys[(idx+1)%len(allkeys)]
        sm=models[sk]
        lr=[]; li=[]; ls=[]; lsh=[]
        for e in bylin[k]:
            if e['role']!='heldout': continue
            actual=e['descendant_seq']; anc=e['ancestor_seq']
            rp=seqdist(transform(anc,lm,True,True),actual,costs)
            sp=seqdist(transform(anc,lm,False,False),actual,costs)
            ip=seqdist(anc,actual,costs)
            hp=seqdist(transform(anc,sm,True,True),actual,costs)
            contextual.append(rp); sourceonly.append(sp); identity.append(ip); shuffled.append(hp)
            lr.append(rp); li.append(ip); ls.append(sp); lsh.append(hp)
            for rk,bl,rl in heldout_rule_events(e,lm,costs):
                st=ruleval[rk]; st['applications']+=1; st['lineages'].add(k); st['base_loss']+=bl; st['rule_loss']+=rl
                if rl < bl-1e-12: st['wins']+=1
                elif abs(rl-bl)<=1e-12: st['ties']+=1
                else: st['losses']+=1
        if lr:
            lineages.append({'parent_code':k[0],'child_code':k[1],'parent_language':names[k][0],'child_language':names[k][1],
              'heldout_records':len(lr),'contextual_mean':statistics.mean(lr),'source_only_mean':statistics.mean(ls),'identity_mean':statistics.mean(li),'shuffled_lineage_mean':statistics.mean(lsh),
              'contextual_beats_identity':statistics.mean(lr)<statistics.mean(li),'contextual_beats_shuffled':statistics.mean(lr)<statistics.mean(lsh),
              'contextual_rules':len(lm['pos']),'base_rules':len(lm['base']),'insertion_rules':len(lm['ins'])})
    rv=[]
    for rk,st in ruleval.items():
        typ=rk[0]
        rec={'type':typ,'applications':st['applications'],'lineages':len(st['lineages']),'mean_base_loss':st['base_loss']/st['applications'],'mean_rule_loss':st['rule_loss']/st['applications'],'mean_gain':(st['base_loss']-st['rule_loss'])/st['applications'],'wins':st['wins'],'ties':st['ties'],'losses':st['losses']}
        if typ=='token': rec.update({'source':rk[1],'position':rk[2],'prediction':None if rk[3]==DELETE else rk[3]})
        else: rec.update({'left':rk[1],'right':rk[2],'gap_class':rk[3],'prediction':rk[4]})
        rv.append(rec)
    rv.sort(key=lambda x:(-x['mean_gain'],-x['applications'],-x['lineages']))
    result={'shard':shard,'lineages':lineages,'rule_validation':rv,
      'summary':{
        'lineages_evaluated':len(lineages),'heldout_records':len(contextual),
        'mean_contextual_rule_distance':statistics.mean(contextual) if contextual else None,
        'mean_source_only_rule_distance':statistics.mean(sourceonly) if sourceonly else None,
        'mean_identity_distance':statistics.mean(identity) if identity else None,
        'mean_shuffled_lineage_rule_distance':statistics.mean(shuffled) if shuffled else None,
        'contextual_beats_identity_records':sum(r<i for r,i in zip(contextual,identity)),
        'contextual_beats_source_only_records':sum(r<s for r,s in zip(contextual,sourceonly)),
        'contextual_beats_shuffled_records':sum(r<s for r,s in zip(contextual,shuffled)),
        'effect_dz_contextual_vs_identity':paired_dz(contextual,identity),
        'effect_dz_contextual_vs_source_only':paired_dz(contextual,sourceonly),
        'effect_dz_contextual_vs_shuffled':paired_dz(contextual,shuffled),
        'diff_moments_contextual_vs_identity':diff_moments(contextual,identity),
        'diff_moments_contextual_vs_source_only':diff_moments(contextual,sourceonly),
        'diff_moments_contextual_vs_shuffled':diff_moments(contextual,shuffled),
      }}
    write_gz(WORK/f't14-result-{shard}.json.gz',result)
    print(json.dumps(result['summary'],ensure_ascii=False,indent=2))


def merge():
    manifest=read_json(WORK/'prepared-manifest.json'); model=read_gz(WORK/'model.json.gz')
    shards=[]
    for i in range(N):
        p=WORK/f't14-result-{i}.json.gz'
        if not p.exists(): raise RuntimeError(f'missing Test 14 shard {i}')
        shards.append(read_gz(p))
    lineages=[x for s in shards for x in s['lineages']]
    def wmean(field):
        vals=[(s['summary'][field],s['summary']['heldout_records']) for s in shards if s['summary']['heldout_records'] and s['summary'][field] is not None]
        return sum(v*n for v,n in vals)/sum(n for v,n in vals)
    total=sum(s['summary']['heldout_records'] for s in shards)
    wins_id=sum(s['summary']['contextual_beats_identity_records'] for s in shards)
    wins_src=sum(s['summary']['contextual_beats_source_only_records'] for s in shards)
    wins_sh=sum(s['summary']['contextual_beats_shuffled_records'] for s in shards)
    agg={}
    for s in shards:
        for r in s['rule_validation']:
            key=(r['type'],r.get('source'),r.get('position'),r.get('left'),r.get('right'),r.get('gap_class'),r.get('prediction'))
            a=agg.setdefault(key,{'applications':0,'lineages':0,'base_sum':0.0,'rule_sum':0.0,'wins':0,'ties':0,'losses':0,'proto':r})
            n=r['applications']; a['applications']+=n; a['lineages']+=r['lineages']; a['base_sum']+=r['mean_base_loss']*n; a['rule_sum']+=r['mean_rule_loss']*n; a['wins']+=r['wins']; a['ties']+=r['ties']; a['losses']+=r['losses']
    rules=[]
    for a in agg.values():
        n=a['applications']; p=a['proto']; rr={k:v for k,v in p.items() if k not in ('applications','lineages','mean_base_loss','mean_rule_loss','mean_gain','wins','ties','losses')}
        rr.update({'applications':n,'lineages':a['lineages'],'mean_base_loss':a['base_sum']/n,'mean_rule_loss':a['rule_sum']/n,'mean_gain':(a['base_sum']-a['rule_sum'])/n,'wins':a['wins'],'ties':a['ties'],'losses':a['losses']})
        rr['sign_test_p']=exact_two_sided_sign_p(a['wins'],a['losses'])
        if rr.get('source'):
            rr['source_ipa']=model['params'][rr['source']]['name']; rr['prediction_ipa']=None if rr.get('prediction') is None else model['params'][rr['prediction']]['name']
            if rr.get('prediction') is not None:
                rr['grid_distance_source_to_prediction']=round(mirror_grid_distance(rr['source'],rr['prediction'],model),8)
                rr['grid_movement_vector']=signed_grid_move(rr['source'],rr['prediction'],model)
                lr=one_way_grid_distance(rr['source'],rr['prediction'],model,'L','R'); rl=one_way_grid_distance(rr['source'],rr['prediction'],model,'R','L')
                rr['mirror_lr_distance']=round(lr,8); rr['mirror_rl_distance']=round(rl,8); rr['mirror_distance_asymmetry']=round(abs(lr-rl),8)
        elif rr.get('prediction'):
            rr['prediction_ipa']=model['params'][rr['prediction']]['name']
        rules.append(rr)
    qs=bh_qvalues([r['sign_test_p'] for r in rules])
    for r,q in zip(rules,qs):
        r['fdr_q']=q
        r['validated_portable']=bool(r['applications']>=8 and r['lineages']>=3 and r['mean_gain']>0 and r['wins']>r['losses'] and q<=0.05)
    rules.sort(key=lambda x:(not x['validated_portable'],x['fdr_q'],-x['mean_gain'],-x['applications'],-x['lineages']))
    portable=[r for r in rules if r['validated_portable']]
    shard_id=sum(1 for s in shards if s['summary']['mean_contextual_rule_distance'] < s['summary']['mean_identity_distance'])
    shard_src=sum(1 for s in shards if s['summary']['mean_contextual_rule_distance'] < s['summary']['mean_source_only_rule_distance'])
    shard_sh=sum(1 for s in shards if s['summary']['mean_contextual_rule_distance'] < s['summary']['mean_shuffled_lineage_rule_distance'])
    summary={
      'shards_completed':N,'lineages_evaluated':len(lineages),'heldout_records_evaluated':total,
      'mean_contextual_rule_distance':round(wmean('mean_contextual_rule_distance'),8),
      'mean_source_only_rule_distance':round(wmean('mean_source_only_rule_distance'),8),
      'mean_identity_distance':round(wmean('mean_identity_distance'),8),
      'mean_shuffled_lineage_rule_distance':round(wmean('mean_shuffled_lineage_rule_distance'),8),
      'contextual_beats_identity_records':wins_id,'fraction_contextual_beats_identity_records':round(wins_id/total,8),
      'contextual_beats_source_only_records':wins_src,'fraction_contextual_beats_source_only_records':round(wins_src/total,8),
      'contextual_beats_shuffled_records':wins_sh,'fraction_contextual_beats_shuffled_records':round(wins_sh/total,8),
      'lineages_contextual_mean_beats_identity':sum(x['contextual_beats_identity'] for x in lineages),
      'lineages_contextual_mean_beats_shuffled':sum(x['contextual_beats_shuffled'] for x in lineages),
      'effect_dz_contextual_vs_identity':round(dz_from_moments([s['summary']['diff_moments_contextual_vs_identity'] for s in shards]),8),
      'effect_dz_contextual_vs_source_only':round(dz_from_moments([s['summary']['diff_moments_contextual_vs_source_only'] for s in shards]),8),
      'effect_dz_contextual_vs_shuffled':round(dz_from_moments([s['summary']['diff_moments_contextual_vs_shuffled'] for s in shards]),8),
      'shards_contextual_mean_beats_identity':shard_id,'shards_contextual_mean_beats_source_only':shard_src,'shards_contextual_mean_beats_shuffled':shard_sh,
      'candidate_rule_types_observed':len(rules),'validated_portable_rule_types':len(portable),
      'validated_portable_substitution_rules':sum(1 for r in portable if r['type']=='token' and r.get('prediction') is not None),
      'validated_portable_deletion_rules':sum(1 for r in portable if r['type']=='token' and r.get('prediction') is None),
      'validated_portable_insertion_rules':sum(1 for r in portable if r['type']=='insert'),
    }
    out={'version':4,'test_id':14,'test':'Cross-validated historical transformation-rule discovery on the corrected mirrored Man Grid','status':'complete','shards':N,
      'dependency':manifest['dependency'],'grid':manifest['grid'],'calculation':manifest['calculation'],'coverage':manifest['coverage'],'summary':summary,
      'shard_summaries':[s['summary'] for s in shards], 'lineage_results':lineages,
      'validated_portable_rules':portable[:500], 'all_rule_validation_ranked':rules[:2000],
      'execution':manifest['execution'],
      'evidence_boundary':'Discovers and cross-validates transformation rules within documented historical lineages. Portable-rule labels additionally pass heldout repetition and FDR control, but do not imply universality or chronology outside documented lineages. Mirror-specific side effects are not identifiable from bilateral addresses without observed side labels, and no transformative-circle operator is inferred because no circle-labelled historical evidence exists.'}
    write_json(OUT,out)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['prepare','run','merge']); ap.add_argument('--shard',type=int); ap.add_argument('--repo',default=None)
    a=ap.parse_args()
    if a.repo: set_repo(Path(a.repo).resolve())
    if a.mode=='prepare': prepare()
    elif a.mode=='run':
        if a.shard is None or not 0<=a.shard<N: raise SystemExit('--shard 0..19 required')
        run_shard(a.shard)
    else: merge()

if __name__=='__main__': main()
