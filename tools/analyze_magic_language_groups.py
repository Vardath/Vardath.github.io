#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,random,statistics
from collections import defaultdict
from pathlib import Path
import benchmark_phonetic_bridge as bp

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'data/phonetic-benchmark-languages.csv'
TOPO=ROOT/'data/phonetic-group-comparison.json'
OUT=ROOT/'data/magic-language-groups.json'
PERMS=1000


def cost(counts, exps):
    total=sum(counts)
    if not total:return None
    s=0.0
    for i,n in enumerate(counts):
        if not n:continue
        a,b=divmod(i,16)
        s+=n*abs(exps[b]-exps[a])
    return s/total

def normal_cdf(z):return 0.5*(1+math.erf(z/math.sqrt(2)))

def bh(rows,key='p_low_fit'):
    if not rows:return
    m=len(rows);order=sorted(range(m),key=lambda i:rows[i][key]);q=[1.0]*m;prev=1.0
    for rank in range(m,0,-1):
        i=order[rank-1];val=min(prev,rows[i][key]*m/rank);q[i]=val;prev=val
    for i,v in enumerate(q):rows[i]['q']=v

def fit_one(row,params):
    text=bp.fetch_text(bp.WPBASE+'tsv/'+row['file']);lines=[x for x in text.splitlines() if x]
    sample=bp.deterministic_reservoir(lines,min(bp.SAMPLE_WORDS,len(lines)),row['file']+str(bp.SAMPLE_WORDS))
    a=bp.analyze_lines(sample,params);counts=a['counts'];obs=cost(counts,bp.MAGIC_EXP)
    if obs is None:return None
    rng=random.Random('magicfit:'+row['iso']);base=list(range(16));vals=[]
    for _ in range(PERMS):
        ex=base[:];rng.shuffle(ex);vals.append(cost(counts,ex))
    mu=statistics.mean(vals);sd=statistics.pstdev(vals) or 1e-12;z=(obs-mu)/sd
    p=(1+sum(v<=obs for v in vals))/(PERMS+1);pct=sum(v>=obs for v in vals)/PERMS
    return {'iso':row['iso'],'name':row['name'],'family':row.get('family') or 'Unclassified','macroarea':row.get('macroarea') or '',
      'file':row['file'],'transitions':a['transitions'],'observed_cost':obs,'random_mean':mu,'random_sd':sd,'z':z,
      'p_low_cost':p,'better_than_random_percentile':pct,
      'fit_band':'strong fit' if p<.01 and z<0 else 'suggestive fit' if p<.05 and z<0 else 'anti-fit' if z>1 else 'neutral'}

def aggregate(label,kind,xs):
    zs=[x['z'] for x in xs];st=sum(zs)/math.sqrt(len(zs));p=normal_cdf(st)
    return {'group':label,'type':kind,'languages':len(xs),'mean_z':statistics.mean(zs),'median_z':statistics.median(zs),
      'stouffer_z':st,'p_low_fit':p,'members':sorted(x['name'] for x in xs),
      'strong_members':sum(x['fit_band']=='strong fit' for x in xs),
      'suggestive_members':sum(x['fit_band'] in ('strong fit','suggestive fit') for x in xs)}

def finish(groups):
    bh(groups)
    for g in groups:
        g['strength']='strong' if g['q']<.01 and g['stouffer_z']<0 else 'moderate' if g['q']<.05 and g['stouffer_z']<0 else 'weak' if g['stouffer_z']<0 else 'none/anti-fit'
    groups.sort(key=lambda g:g['stouffer_z'])
    return groups

def main():
    params,_=bp.build_phoible_maps();rows=[r for r in csv.DictReader(CANON.open(encoding='utf-8')) if r.get('canonical','').lower()=='true']
    langs=[]
    for i,r in enumerate(rows,1):
        try:
            x=fit_one(r,params)
            if x:langs.append(x)
            print(i,len(rows),r['iso'],x['z'] if x else 'NA',flush=True)
        except Exception as e:print('FAIL',r.get('iso'),e,flush=True)
    byiso={x['iso']:x for x in langs}
    fams=defaultdict(list)
    for x in langs:fams[x['family']].append(x)
    family_groups=finish([aggregate(f,'Glottolog family',xs) for f,xs in fams.items() if len(xs)>=3])
    topo=json.loads(TOPO.read_text(encoding='utf-8'));topology_groups=[]
    for g in topo.get('groups',[]):
        xs=[byiso[m['iso']] for m in g.get('members',[]) if m.get('iso') in byiso]
        if len(xs)>=3:topology_groups.append(aggregate(f"Topology group {g['group']}",'Phonetic topology group',xs))
    topology_groups=finish(topology_groups)
    bands=defaultdict(list)
    for x in langs:bands[x['fit_band']].append(x['name'])
    result={'version':2,'method':{'score':'transition-frequency-weighted mean absolute Durer power-exponent difference; lower is better','per_language_random_magic_assignments':PERMS,'group_test':'Stouffer combination of per-language z scores with Benjamini-Hochberg correction within each grouping system','warning':'A subgroup is called strong/moderate only after multiple-comparison correction. Negative z means closer alignment to the Durer ordering than random.'},
      'counts':{'languages_tested':len(langs),'families_tested':len(family_groups),'topology_groups_tested':len(topology_groups)},
      'fit_bands':{k:sorted(v) for k,v in bands.items()},'groups':family_groups,'topology_groups':topology_groups,'languages':sorted(langs,key=lambda x:x['z'])}
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'languages':len(langs),'families':[(g['group'],round(g['stouffer_z'],2),round(g['q'],4)) for g in family_groups[:8]],'topology':[(g['group'],round(g['stouffer_z'],2),round(g['q'],4)) for g in topology_groups[:12]]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
