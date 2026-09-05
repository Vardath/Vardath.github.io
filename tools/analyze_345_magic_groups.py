#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,random,statistics
from collections import defaultdict
from pathlib import Path
import benchmark_phonetic_bridge as bp
import benchmark_pyramid_codec as pc

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'data/phonetic-benchmark-languages.csv'
TOPO=ROOT/'data/phonetic-group-comparison.json'
OUT=ROOT/'data/magic-language-groups.json'
PERMS=int(__import__('os').environ.get('MAGIC_345_PERMS','500'))
SAMPLE_WORDS=int(__import__('os').environ.get('MAGIC_345_WORDS','12000'))
MAGIC=bp.MAGIC_EXP


def norm_manhattan(idx1,idx2,n):
    r1,c1=divmod(idx1,n);r2,c2=divmod(idx2,n)
    return (abs(r1-r2)+abs(c1-c2))/(2*(n-1))

def analyze_language(row,params):
    text=bp.fetch_text(bp.WPBASE+'tsv/'+row['file'])
    lines=[x for x in text.splitlines() if x]
    sample=bp.deterministic_reservoir(lines,min(SAMPLE_WORDS,len(lines)),row['file']+':345:'+str(SAMPLE_WORDS))
    combos=defaultdict(int); transitions=0; mapped=unknown=0
    for line in sample:
        tab=line.find('\t')
        if tab<0: continue
        prev=None
        for ph in line[tab+1:].strip().split():
            p=params.get(bp.normalize_phone(ph))
            if p is None:
                base=bp.normalize_phone(ph).replace('ˈ','').replace('ˌ','').replace('.','').replace('‿','').replace('#','')
                p=params.get(base)
            if not p or bp.classify(p) is None:
                unknown+=1; prev=None; continue
            mapped+=1
            c3=pc.cell(p,3); c4=pc.cell(p,4); c5=pc.cell(p,5)
            cur=(c3,c4,c5)
            if prev is not None:
                a3,a4,a5=prev; b3,b4,b5=cur
                combos[(a3,b3,a4,b4,a5,b5)]+=1; transitions+=1
            prev=cur
    if not transitions:return None

    def score_for_perm(perm):
        bridge=magic=0.0
        for (a3,b3,a4,b4,a5,b5),n in combos.items():
            pa4,pb4=perm[a4],perm[b4]
            d3=norm_manhattan(a3,b3,3); d4=norm_manhattan(pa4,pb4,4); d5=norm_manhattan(a5,b5,5)
            bridge += n*abs(d4-(d3+d5)/2)
            magic += n*(abs(MAGIC[pb4]-MAGIC[pa4])/15)
        bridge/=transitions; magic/=transitions
        return bridge,magic,bridge+0.25*magic

    ident=list(range(16)); ob,om,oc=score_for_perm(ident)
    rng=random.Random('345magic:'+row['iso'])
    vals=[]; bvals=[]; mvals=[]
    for _ in range(PERMS):
        p=ident[:]; rng.shuffle(p)
        b,m,c=score_for_perm(p); vals.append(c); bvals.append(b); mvals.append(m)
    mu=statistics.mean(vals); sd=statistics.pstdev(vals) or 1e-12
    z=(oc-mu)/sd
    p=(1+sum(v<=oc for v in vals))/(PERMS+1)
    bmu=statistics.mean(bvals); bsd=statistics.pstdev(bvals) or 1e-12
    mmu=statistics.mean(mvals); msd=statistics.pstdev(mvals) or 1e-12
    bz=(ob-bmu)/bsd; mz=(om-mmu)/msd
    return {
      'iso':row['iso'],'name':row['name'],'family':row.get('family') or 'Unclassified','macroarea':row.get('macroarea') or '',
      'file':row['file'],'transitions':transitions,'mapping_coverage':mapped/(mapped+unknown) if mapped+unknown else 0,
      'bridge_residual':ob,'bridge_z':bz,'magic_cost':om,'magic_z':mz,'composite_cost':oc,'random_mean':mu,'random_sd':sd,
      'z':z,'p_low_cost':p,'better_than_random_percentile':sum(v>=oc for v in vals)/PERMS,
      'fit_band':'strong 3-4-5 magic fit' if p<.01 and z<0 else 'suggestive 3-4-5 magic fit' if p<.05 and z<0 else 'weak 3-4-5 lean' if z<0 else 'none / anti-fit'
    }

def normal_cdf(z):return 0.5*(1+math.erf(z/math.sqrt(2)))
def bh(rows,key='p_low_fit'):
    if not rows:return
    ordered=sorted(range(len(rows)),key=lambda i:rows[i][key]);m=len(rows);prev=1.0;q=[1.0]*m
    for rank in range(m,0,-1):
        i=ordered[rank-1];val=min(prev,rows[i][key]*m/rank);q[i]=val;prev=val
    for i,v in enumerate(q):rows[i]['q']=v

def group_rows(name_to_members,langs,typ):
    byiso={x['iso']:x for x in langs};out=[]
    for name,members in name_to_members.items():
        xs=[byiso[i] for i in members if i in byiso]
        if len(xs)<3:continue
        z=sum(x['z'] for x in xs)/math.sqrt(len(xs)); p=normal_cdf(z)
        out.append({'group':name,'type':typ,'languages':len(xs),'mean_z':statistics.mean(x['z'] for x in xs),'median_z':statistics.median(x['z'] for x in xs),'stouffer_z':z,'p_low_fit':p,'mean_bridge_z':statistics.mean(x['bridge_z'] for x in xs),'mean_magic_z':statistics.mean(x['magic_z'] for x in xs),'members':sorted(x['name'] for x in xs),'strong_members':sum(x['fit_band'].startswith('strong') for x in xs),'suggestive_members':sum('fit' in x['fit_band'] and not x['fit_band'].startswith('none') for x in xs)})
    bh(out)
    for g in out:
        g['strength']='strong' if g['q']<.01 and g['stouffer_z']<0 else 'moderate' if g['q']<.05 and g['stouffer_z']<0 else 'weak' if g['stouffer_z']<0 else 'none/anti-fit'
    return sorted(out,key=lambda g:g['stouffer_z'])

def main():
    params,_=bp.build_phoible_maps()
    rows=[r for r in csv.DictReader(CANON.open(encoding='utf-8')) if r.get('canonical','').lower()=='true']
    langs=[]
    for i,r in enumerate(rows,1):
        try:
            x=analyze_language(r,params)
            if x: langs.append(x)
            print(i,len(rows),r['iso'],x['z'] if x else 'NA',flush=True)
        except Exception as e: print('FAIL',r.get('iso'),e,flush=True)
    fam=defaultdict(list)
    for x in langs:fam[x['family']].append(x['iso'])
    families=group_rows(fam,langs,'Glottolog family')
    topo={}
    if TOPO.exists():
        d=json.loads(TOPO.read_text(encoding='utf-8'))
        for g in d.get('groups',[]):topo[f"Topology group {g['group']}"]=[m['iso'] for m in g.get('members',[])]
    topology=group_rows(topo,langs,'Phonetic topology group')
    bands=defaultdict(list)
    for x in langs:bands[x['fit_band']].append(x['name'])
    out={'version':3,'system':'3×3 → 4×4 → 5×5 phonetic bridge with Dürer/powers-of-3 overlay','method':{
      'bridge_score':'For each observed phone transition, compare normalized 4×4 spatial distance with the midpoint of its 3×3 and 5×5 distances; lower residual means the 4×4 layer behaves more like an interpolating bridge.',
      'magic_score':'Mean |Dürer power exponent delta|/15 on the observed 4×4 transitions; lower means frequent transitions stay closer in the magic ordering.',
      'composite':'bridge_residual + 0.25 × magic_cost','randomization':'Shuffle the mapping of the sixteen 4×4 phonetic cells to sixteen grid positions. This simultaneously breaks 3-4-5 geometry and the Dürer-number overlay while preserving the language data.','per_language_random_assignments':PERMS,'sample_words_cap':SAMPLE_WORDS,'group_test':'Stouffer combination of per-language composite z scores; Benjamini-Hochberg correction within each grouping system. Negative z means better 3-4-5 magic fit than randomized 4×4 bridges.'},
      'counts':{'languages_tested':len(langs),'families_tested':len(families),'topology_groups_tested':len(topology)},'fit_bands':{k:sorted(v) for k,v in bands.items()},'groups':families,'topology_groups':topology,'languages':sorted(langs,key=lambda x:x['z'])}
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'languages':len(langs),'families':len(families),'topology_groups':len(topology),'top_topology':[(g['group'],round(g['stouffer_z'],3),round(g['q'],4),g['strength']) for g in topology[:10]]},indent=2))
if __name__=='__main__':main()
