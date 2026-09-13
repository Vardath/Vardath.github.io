#!/usr/bin/env python3
import argparse, json, math, random, statistics
from pathlib import Path
import numpy as np

TAU = 2.0 * math.pi
PHI = 1.618033988749895
SEED0 = 73013
CASES_PER_SHARD = 80
PHASE_GRID = 24
NALPHA = 180
PITCH_MULTS = [0.70, 0.85, 1.00, 1.15, 1.30]
PITCH_PENALTY = 0.08
WORK = Path('research/three_shell_attraction_v1_work')
RESULTS = Path('research/three_shell_attraction_v1_results')


def med(xs):
    xs = [float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return statistics.median(xs) if xs else None


def mean(xs):
    xs = [float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return statistics.fmean(xs) if xs else None


def cv(xs):
    xs = [float(x) for x in xs]
    if len(xs) < 2 or statistics.fmean(xs) == 0:
        return None
    return statistics.pstdev(xs) / statistics.fmean(xs)


def profile(a1, b1, c1, a2, b2, c2, phi2, turns, sigma):
    alpha = np.linspace(0.0, TAU, NALPHA, endpoint=False)
    k = np.arange(turns, dtype=float)
    base1 = np.mod(alpha, TAU) if c1 == 1 else np.mod(-alpha, TAU)
    base2 = np.mod(alpha - phi2, TAU) if c2 == 1 else np.mod(phi2 - alpha, TAU)
    lr1 = math.log(a1) + b1 * (base1[:, None] + TAU * k[None, :])
    lr2 = math.log(a2) + b2 * (base2[:, None] + TAU * k[None, :])
    diff = np.abs(lr1[:, :, None] - lr2[:, None, :])
    flat = diff.reshape(NALPHA, turns * turns)
    arg = np.argmin(flat, axis=1)
    sep = flat[np.arange(NALPHA), arg]
    i1 = arg // turns
    i2 = arg % turns
    mid = 0.5 * (lr1[np.arange(NALPHA), i1] + lr2[np.arange(NALPHA), i2])
    prox = np.exp(-sep / sigma)
    return sep, mid, prox


def scan_phase(a1, b1, c1, a2, b2, c2, turns, sigma):
    scores = []
    profs = []
    for j in range(PHASE_GRID):
        phi = TAU * j / PHASE_GRID
        p = profile(a1, b1, c1, a2, b2, c2, phi, turns, sigma)
        scores.append(float(np.mean(p[2])))
        profs.append(p)
    imax = int(np.argmax(scores)); imin = int(np.argmin(scores))
    return {
        'attraction': scores[imax], 'repulsion': scores[imin],
        'phi_attraction': TAU * imax / PHASE_GRID,
        'phi_repulsion': TAU * imin / PHASE_GRID,
        'profile_attraction': profs[imax], 'profile_repulsion': profs[imin],
    }


def gate_info(p, sigma):
    sep, mid, prox = p
    idx = []
    for i in range(NALPHA):
        if sep[i] < sep[(i-1) % NALPHA] and sep[i] <= sep[(i+1) % NALPHA]:
            idx.append(i)
    spacing_cv = None
    if len(idx) >= 3:
        ds = [idx[i+1] - idx[i] for i in range(len(idx)-1)] + [NALPHA - idx[-1] + idx[0]]
        spacing_cv = cv(ds)
    radii = sorted(float(math.exp(mid[i])) for i in idx)
    unique = []
    for r in radii:
        if not unique or abs(math.log(r / unique[-1])) > math.log(1.01):
            unique.append(r)
    concentration = float(np.percentile(prox, 95) / max(float(np.mean(prox)), 1e-15))
    strong_fraction = float(np.mean(sep < sigma))
    return {
        'count': len(idx), 'spacing_cv': spacing_cv, 'radii': unique,
        'concentration': concentration, 'strong_fraction': strong_fraction,
    }


def timing_phi_metrics(radii, rng):
    out = {'timing_error': None, 'timing_null': None, 'phi_error': None,
           'phi_null': None, 'median_ratio': None}
    if len(radii) < 2:
        return out
    ratios = [radii[i+1] / radii[i] for i in range(len(radii)-1) if radii[i] > 0]
    if ratios:
        out['phi_error'] = med([abs(math.log(x / PHI)) for x in ratios])
        out['median_ratio'] = med(ratios)
    lo, hi = min(radii), max(radii)
    if hi > lo and lo > 0:
        null = sorted(math.exp(rng.uniform(math.log(lo), math.log(hi))) for _ in range(len(radii)))
        nr = [null[i+1] / null[i] for i in range(len(null)-1)]
        out['phi_null'] = med([abs(math.log(x / PHI)) for x in nr]) if nr else None
    if len(radii) >= 3:
        target = [1.0, 395.0/138.0, 792.0/138.0]
        errs = []
        for i in range(len(radii)-2):
            obs = [1.0, radii[i+1]/radii[i], radii[i+2]/radii[i]]
            errs.append(math.sqrt(sum(((obs[j]-target[j])/target[j])**2 for j in range(3))/3.0))
        out['timing_error'] = med(errs)
        if hi > lo and lo > 0:
            null = sorted(math.exp(rng.uniform(math.log(lo), math.log(hi))) for _ in range(len(radii)))
            ne = []
            for i in range(len(null)-2):
                obs = [1.0, null[i+1]/null[i], null[i+2]/null[i]]
                ne.append(math.sqrt(sum(((obs[j]-target[j])/target[j])**2 for j in range(3))/3.0))
            out['timing_null'] = med(ne)
    return out


def torque_gradient(a1,b1,c1,a2,b2,c2,phi,turns,sigma):
    h = 0.001
    pp = profile(a1,b1,c1,a2,b2,c2,phi+h,turns,sigma)
    pm = profile(a1,b1,c1,a2,b2,c2,phi-h,turns,sigma)
    sp = float(np.mean(pp[2])); sm = float(np.mean(pm[2]))
    return (sp-sm)/(2*h)


def pitch_choices(a1,b1,c1,a2,b2,c2,turns,sigma):
    rows=[]
    for m in PITCH_MULTS:
        sc=scan_phase(a1,b1,c1,a2,b2*m,c2,turns,sigma)
        penalty=PITCH_PENALTY*(m-1.0)**2
        rows.append((m, sc['attraction']-penalty, -sc['repulsion']-penalty))
    attr=max(rows,key=lambda x:x[1])[0]
    rep=max(rows,key=lambda x:x[2])[0]
    return attr,rep


def run_case(rng):
    turns=rng.randint(4,8)
    b1=rng.uniform(0.018,0.075)
    b2=b1*rng.uniform(0.88,1.12)
    b3=b1*rng.uniform(0.88,1.12)
    q1=rng.uniform(1.15,2.10); q2=rng.uniform(1.15,2.10)
    a1=1.0; a2=q1; a3=q1*q2
    sigma=rng.uniform(0.045,0.12)

    p12_pp=scan_phase(a1,b1,1,a2,b2,1,turns,sigma)
    p12_pm=scan_phase(a1,b1,1,a2,b2,-1,turns,sigma)
    p12_mp=scan_phase(a1,b1,-1,a2,b2,1,turns,sigma)
    p23_pp=scan_phase(a2,b2,1,a3,b3,1,turns,sigma)
    p23_pm=scan_phase(a2,b2,1,a3,b3,-1,turns,sigma)
    p23_mp=scan_phase(a2,b2,-1,a3,b3,1,turns,sigma)

    same_attr=mean([p12_pp['attraction'],p23_pp['attraction']])
    opp_attr=mean([p12_pm['attraction'],p12_mp['attraction'],p23_pm['attraction'],p23_mp['attraction']])
    same_rep=mean([p12_pp['repulsion'],p23_pp['repulsion']])
    opp_rep=mean([p12_pm['repulsion'],p12_mp['repulsion'],p23_pm['repulsion'],p23_mp['repulsion']])

    attr_scores={
      '+++':p12_pp['attraction']+p23_pp['attraction'],
      '+-+':p12_pm['attraction']+p23_mp['attraction'],
      '++-':p12_pp['attraction']+p23_pm['attraction'],
      '-++':p12_mp['attraction']+p23_pp['attraction'],
    }
    rep_scores={
      '+++':p12_pp['repulsion']+p23_pp['repulsion'],
      '+-+':p12_pm['repulsion']+p23_mp['repulsion'],
      '++-':p12_pp['repulsion']+p23_pm['repulsion'],
      '-++':p12_mp['repulsion']+p23_pp['repulsion'],
    }
    attr_winner=max(attr_scores,key=attr_scores.get)
    rep_winner=min(rep_scores,key=rep_scores.get)  # lowest proximity is repulsion-preferred
    edge_best=max(attr_scores['++-'],attr_scores['-++'])

    random_phi=rng.random()*TAU
    grad=torque_gradient(a1,b1,1,a2,b2,-1,random_phi,turns,sigma)

    gs=gate_info(p12_pp['profile_attraction'],sigma)
    go=gate_info(p12_pm['profile_attraction'],sigma)
    bridge=timing_phi_metrics(go['radii'],rng)
    pitch_attr,pitch_rep=pitch_choices(a1,b1,1,a2,b2,-1,turns,sigma)

    flip_same=scan_phase(a1,b1,-1,a2,b2,-1,turns,sigma)
    flip_opp=scan_phase(a1,b1,-1,a2,b2,1,turns,sigma)
    inv_err=max(abs(p12_pp['attraction']-flip_same['attraction']),
                abs(p12_pm['attraction']-flip_opp['attraction']),
                abs(p12_pp['repulsion']-flip_same['repulsion']),
                abs(p12_pm['repulsion']-flip_opp['repulsion']))

    return {
      'turns':turns,'b1':b1,'b2':b2,'b3':b3,'q1':q1,'q2':q2,'sigma':sigma,
      'torque_abs':abs(grad),'torque_nonzero':abs(grad)>1e-12,'opposite_force_directions':abs(grad)>1e-12,
      'same_attr':same_attr,'opp_attr':opp_attr,'opp_same_attr_ratio':opp_attr/max(same_attr,1e-15),'opp_attr_wins':opp_attr>same_attr,
      'same_rep':same_rep,'opp_rep':opp_rep,
      'attr_winner':attr_winner,'rep_winner':rep_winner,'attr_mid_edge_ratio':attr_scores['+-+']/max(edge_best,1e-15),
      'gate_same_count':gs['count'],'gate_opp_count':go['count'],'gate_same_cv':gs['spacing_cv'],'gate_opp_cv':go['spacing_cv'],
      'bundle_same_concentration':gs['concentration'],'bundle_opp_concentration':go['concentration'],'bundle_opp_fraction':go['strong_fraction'],
      'pitch_attr':pitch_attr,'pitch_rep':pitch_rep,
      'timing_error':bridge['timing_error'],'timing_null':bridge['timing_null'],
      'phi_error':bridge['phi_error'],'phi_null':bridge['phi_null'],'gate_median_ratio':bridge['median_ratio'],
      'invariance_error':inv_err,
    }


def run_shard(i):
    rng=random.Random(SEED0+i*100003)
    rows=[run_case(rng) for _ in range(CASES_PER_SHARD)]
    WORK.mkdir(parents=True,exist_ok=True)
    p=WORK/f'shard-{i:02d}.json'
    p.write_text(json.dumps({'shard':i,'seed':SEED0+i*100003,'cases':rows},indent=2),encoding='utf8')
    print(json.dumps({'shard':i,'cases':len(rows),'median_opp_same':med([r['opp_same_attr_ratio'] for r in rows]),'mid_wins':sum(r['attr_winner']=='+-+' for r in rows)},indent=2))


def aggregate(rows):
    n=len(rows)
    t1_grad=med([r['torque_abs'] for r in rows]); t1_dir=mean([1.0 if r['opposite_force_directions'] else 0.0 for r in rows])
    t2_ratio=med([r['opp_same_attr_ratio'] for r in rows]); t2_win=mean([1.0 if r['opp_attr_wins'] else 0.0 for r in rows])
    t3_win=mean([1.0 if r['attr_winner']=='+-+' else 0.0 for r in rows]); t3_ratio=med([r['attr_mid_edge_ratio'] for r in rows])
    t4_repwin=mean([1.0 if r['rep_winner']=='+-+' else 0.0 for r in rows]); t4_delta=t3_win-t4_repwin
    gsame=med([r['gate_same_count'] for r in rows]); gopp=med([r['gate_opp_count'] for r in rows]);
    cvsame=med([r['gate_same_cv'] for r in rows]); cvopp=med([r['gate_opp_cv'] for r in rows])
    c_same=med([r['bundle_same_concentration'] for r in rows]); c_opp=med([r['bundle_opp_concentration'] for r in rows]); frac=med([r['bundle_opp_fraction'] for r in rows])
    pa=mean([1.0 if abs(r['pitch_attr']-1)>1e-9 else 0.0 for r in rows]); pr=mean([1.0 if abs(r['pitch_rep']-1)>1e-9 else 0.0 for r in rows]); pdelta=pa-pr
    terr=med([r['timing_error'] for r in rows]); tnull=med([r['timing_null'] for r in rows]);
    perr=med([r['phi_error'] for r in rows]); pnull=med([r['phi_null'] for r in rows]); grat=med([r['gate_median_ratio'] for r in rows]); inv=max(r['invariance_error'] for r in rows)
    tests={
      'T1_attraction_torque':{'median_abs_gradient':t1_grad,'opposite_direction_rate':t1_dir,'pass':bool(t1_grad is not None and t1_grad>0.01 and t1_dir>0.80)},
      'T2_opposite_chirality_attraction':{'median_ratio':t2_ratio,'opposite_win_rate':t2_win,'pass':bool(t2_ratio is not None and t2_ratio>1.20 and t2_win>0.65)},
      'T3_middle_reversed':{'middle_reversed_win_rate':t3_win,'median_middle_vs_best_edge_ratio':t3_ratio,'pass':bool(t3_win>0.60 and t3_ratio is not None and t3_ratio>1.10)},
      'T4_attraction_specificity':{'attraction_middle_win_rate':t3_win,'repulsion_middle_win_rate':t4_repwin,'difference':t4_delta,'pass':bool(t4_delta>0.25)},
      'T5_recurring_gates':{'median_same_gate_count':gsame,'median_opposite_gate_count':gopp,'median_same_spacing_cv':cvsame,'median_opposite_spacing_cv':cvopp,'pass':bool(gopp is not None and gsame is not None and gopp>=2*max(gsame,1e-12) and cvopp is not None and (cvsame is None or cvopp<cvsame))},
      'T6_temporary_bundling':{'median_same_concentration':c_same,'median_opposite_concentration':c_opp,'median_opposite_strong_fraction':frac,'pass':bool(c_opp is not None and c_opp>1.5 and c_same is not None and c_opp>c_same and frac is not None and frac<0.35)},
      'T7_pitch_change':{'attraction_nonunit_rate':pa,'repulsion_nonunit_rate':pr,'difference':pdelta,'pass':bool(pdelta>=0.15)},
      'T8_timing_138_395_792':{'median_error':terr,'median_null_error':tnull,'improvement':None if terr is None or tnull in (None,0) else 1-terr/tnull,'pass':bool(terr is not None and tnull not in (None,0) and terr<0.10 and terr<=0.75*tnull)},
      'T9_phi_bridge':{'median_phi_error':perr,'median_null_error':pnull,'median_gate_radius_ratio':grat,'improvement':None if perr is None or pnull in (None,0) else 1-perr/pnull,'pass':bool(perr is not None and pnull not in (None,0) and perr<=0.75*pnull and grat is not None and abs(grat/PHI-1)<=0.05)},
      'T10_handedness_label_invariance':{'max_metric_difference':inv,'pass':bool(inv<1e-9)},
    }
    return {'protocol':'three-shell-attraction-v1','cases':n,'tests':tests}


def merge():
    files=sorted(WORK.glob('shard-*.json'))
    if len(files)!=20: raise SystemExit(f'need 20 shards, found {len(files)}')
    rows=[]
    for p in files: rows.extend(json.loads(p.read_text())['cases'])
    out=aggregate(rows)
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'summary.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    lines=['# Three-shell attraction / chirality test — results','',f"Cases: **{out['cases']:,}** across 20 shards.",'', '| test | verdict | key result |','|---|---|---|']
    for name,x in out['tests'].items():
        details=', '.join(f'{k}={v:.6g}' if isinstance(v,float) else f'{k}={v}' for k,v in x.items() if k!='pass')
        lines.append(f"| {name} | **{'PASS' if x['pass'] else 'FAIL'}** | {details} |")
    lines += ['','## Interpretation','','PASS means only that the frozen toy geometry met its preregistered rule. It is not evidence that a physical attractive shell force exists. T8/T9 are deliberately independent bridges: failure means the geometry does not derive those numerical sequences under v1.','']
    (RESULTS/'2026-09-14_report.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps(out,indent=2))


def validate():
    assert CASES_PER_SHARD==80 and PHASE_GRID==24 and NALPHA==180
    assert len(PITCH_MULTS)==5
    print('validated three-shell-attraction-v1; 20 shards x 80 cases')


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate'); s=sub.add_parser('shard'); s.add_argument('--id',type=int,required=True); sub.add_parser('merge')
    a=ap.parse_args()
    if a.cmd=='validate': validate()
    elif a.cmd=='shard': run_shard(a.id)
    else: merge()

if __name__=='__main__': main()
