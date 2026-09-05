#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,random,statistics,unicodedata
from collections import defaultdict
from pathlib import Path
import benchmark_phonetic_bridge as bp
import benchmark_pyramid_codec as pc

try:
    import icu
    import pycountry
except Exception as e:
    raise SystemExit('PyICU and pycountry are required: '+str(e))

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'data/phonetic-benchmark-languages.csv'
TOPO=ROOT/'data/phonetic-group-comparison.json'
OUT=ROOT/'data/magic-language-groups.json'
PERMS=int(__import__('os').environ.get('MAGIC_345_PERMS','300'))
SAMPLE_WORDS=int(__import__('os').environ.get('MAGIC_345_WORDS','8000'))
MAGIC=bp.MAGIC_EXP


def iso_to_locale(iso3):
    try:
        x=pycountry.languages.get(alpha_3=iso3)
        code=getattr(x,'alpha_2',None) or iso3
    except Exception:
        code=iso3
    return code

def is_letter(ch): return unicodedata.category(ch).startswith('L')
def chars(word): return [c.casefold() for c in unicodedata.normalize('NFC',word) if is_letter(c)]

def ordered_alphabet(words,iso3):
    seen=set()
    for w in words: seen.update(chars(w))
    if len(seen)<3:return None,None
    loc=iso_to_locale(iso3)
    try:
        coll=icu.Collator.createInstance(icu.Locale(loc))
        ordered=sorted(seen,key=coll.getSortKey)
        # ICU root fallback is still deterministic, but we only call a locale tailored
        # when ICU reports at least the requested language code.
        src=f'ICU collation locale {loc}'
    except Exception:
        coll=icu.Collator.createInstance(icu.Locale.getRoot())
        ordered=sorted(seen,key=coll.getSortKey);src='ICU root collation fallback'
    return ordered,src

def rank_to_cell(rank,total,n):
    if total<=1:return 0
    x=rank/(total-1)
    return min(n-1,int(x*n))

def cosine(a,b):
    sa=sum(x*x for x in a);sb=sum(x*x for x in b)
    if not sa or not sb:return 0.0
    return sum(x*y for x,y in zip(a,b))/math.sqrt(sa*sb)

def power_delta_mean(counts):
    total=sum(counts)
    if not total:return 1.0
    s=0.0
    for i,n in enumerate(counts):
        if n:
            a,b=divmod(i,16);s+=n*abs(MAGIC[b]-MAGIC[a])/15
    return s/total

def make_orth_counts(pair_counts,rankmap,n,perm=None):
    out=[0]*(n*n)
    total=len(rankmap)
    for (a,b),cnt in pair_counts.items():
        ra,rb=rankmap[a],rankmap[b]
        ca,cb=rank_to_cell(ra,total,n),rank_to_cell(rb,total,n)
        if n==4 and perm is not None: ca,cb=perm[ca],perm[cb]
        out[ca*n+cb]+=cnt
    return out

def phone_counts(lines,params,n):
    out=[0]*(n*n);mapped=unknown=0
    for line in lines:
        tab=line.find('\t')
        if tab<0:continue
        prev=None
        for ph in line[tab+1:].strip().split():
            key=bp.normalize_phone(ph);p=params.get(key)
            if p is None:
                base=key.replace('ˈ','').replace('ˌ','').replace('.','').replace('‿','').replace('#','');p=params.get(base)
            if not p or bp.classify(p) is None:
                unknown+=1;prev=None;continue
            mapped+=1;cur=pc.cell(p,n)
            if prev is not None:out[prev*n+cur]+=1
            prev=cur
    return out,mapped,unknown

def analyze_language(row,params):
    text=bp.fetch_text(bp.WPBASE+'tsv/'+row['file'])
    all_lines=[x for x in text.splitlines() if '\t' in x]
    lines=bp.deterministic_reservoir(all_lines,min(SAMPLE_WORDS,len(all_lines)),row['file']+':ordered345:'+str(SAMPLE_WORDS))
    words=[x.split('\t',1)[0] for x in lines]
    alphabet,order_source=ordered_alphabet(words,row['iso'])
    if not alphabet:return None
    rank={c:i for i,c in enumerate(alphabet)}
    pairs=defaultdict(int)
    for w in words:
        cs=[c for c in chars(w) if c in rank]
        for a,b in zip(cs,cs[1:]):pairs[(a,b)]+=1
    if not pairs:return None
    p3,m3,u3=phone_counts(lines,params,3);p4,m4,u4=phone_counts(lines,params,4);p5,m5,u5=phone_counts(lines,params,5)
    if not sum(p4):return None
    o3=make_orth_counts(pairs,rank,3);o4=make_orth_counts(pairs,rank,4);o5=make_orth_counts(pairs,rank,5)
    sim3,sim4,sim5=cosine(o3,p3),cosine(o4,p4),cosine(o5,p5)
    # The middle layer should bridge broad and fine rather than being an isolated match.
    bridge_residual=abs(sim4-(sim3+sim5)/2)
    magic_cost=power_delta_mean(o4)
    observed=(1-sim3)+(1-sim4)+(1-sim5)+bridge_residual+0.25*magic_cost

    rng=random.Random('alphabet345:'+row['iso']);vals=[];bridge_vals=[];magic_vals=[]
    ids=list(range(len(alphabet)))
    for _ in range(PERMS):
        shuffled=ids[:];rng.shuffle(shuffled)
        rr={c:shuffled[i] for i,c in enumerate(alphabet)}
        q3=make_orth_counts(pairs,rr,3);q4=make_orth_counts(pairs,rr,4);q5=make_orth_counts(pairs,rr,5)
        s3,s4,s5=cosine(q3,p3),cosine(q4,p4),cosine(q5,p5)
        br=abs(s4-(s3+s5)/2);mg=power_delta_mean(q4)
        vals.append((1-s3)+(1-s4)+(1-s5)+br+0.25*mg);bridge_vals.append(br);magic_vals.append(mg)
    mu=statistics.mean(vals);sd=statistics.pstdev(vals) or 1e-12;z=(observed-mu)/sd
    p=(1+sum(v<=observed for v in vals))/(PERMS+1)
    bz=(bridge_residual-statistics.mean(bridge_vals))/(statistics.pstdev(bridge_vals) or 1e-12)
    mz=(magic_cost-statistics.mean(magic_vals))/(statistics.pstdev(magic_vals) or 1e-12)
    return {'iso':row['iso'],'name':row['name'],'family':row.get('family') or 'Unclassified','macroarea':row.get('macroarea') or '',
      'file':row['file'],'alphabet_order':' '.join(alphabet),'alphabet_size':len(alphabet),'order_source':order_source,'word_sample':len(lines),
      'sim_3x3':sim3,'sim_4x4':sim4,'sim_5x5':sim5,'bridge_residual':bridge_residual,'bridge_z':bz,'magic_cost':magic_cost,'magic_z':mz,
      'composite_cost':observed,'random_mean':mu,'random_sd':sd,'z':z,'p_low_cost':p,'better_than_random_percentile':sum(v>=observed for v in vals)/PERMS,
      'mapping_coverage':m4/(m4+u4) if m4+u4 else 0,
      'fit_band':'strong ordered-alphabet 3-4-5 fit' if p<.01 and z<0 else 'suggestive ordered-alphabet 3-4-5 fit' if p<.05 and z<0 else 'weak ordered-alphabet lean' if z<0 else 'none / anti-fit'}

def normal_cdf(z):return 0.5*(1+math.erf(z/math.sqrt(2)))
def bh(rows,key='p_low_fit'):
    if not rows:return
    order=sorted(range(len(rows)),key=lambda i:rows[i][key]);m=len(rows);q=[1.0]*m;prev=1.0
    for rank in range(m,0,-1):
        i=order[rank-1];v=min(prev,rows[i][key]*m/rank);q[i]=v;prev=v
    for i,v in enumerate(q):rows[i]['q']=v

def group_rows(mapping,langs,typ):
    byiso={x['iso']:x for x in langs};out=[]
    for name,members in mapping.items():
        xs=[byiso[i] for i in members if i in byiso]
        if len(xs)<3:continue
        z=sum(x['z'] for x in xs)/math.sqrt(len(xs));p=normal_cdf(z)
        out.append({'group':name,'type':typ,'languages':len(xs),'mean_z':statistics.mean(x['z'] for x in xs),'median_z':statistics.median(x['z'] for x in xs),'stouffer_z':z,'p_low_fit':p,'mean_bridge_z':statistics.mean(x['bridge_z'] for x in xs),'mean_magic_z':statistics.mean(x['magic_z'] for x in xs),'mean_3x3':statistics.mean(x['sim_3x3'] for x in xs),'mean_4x4':statistics.mean(x['sim_4x4'] for x in xs),'mean_5x5':statistics.mean(x['sim_5x5'] for x in xs),'members':sorted(x['name'] for x in xs),'strong_members':sum(x['fit_band'].startswith('strong') for x in xs),'suggestive_members':sum(('fit' in x['fit_band']) and not x['fit_band'].startswith('none') for x in xs)})
    bh(out)
    for g in out:g['strength']='strong' if g['q']<.01 and g['stouffer_z']<0 else 'moderate' if g['q']<.05 and g['stouffer_z']<0 else 'weak' if g['stouffer_z']<0 else 'none/anti-fit'
    return sorted(out,key=lambda g:g['stouffer_z'])

def main():
    params,_=bp.build_phoible_maps();rows=[r for r in csv.DictReader(CANON.open(encoding='utf-8')) if r.get('canonical','').lower()=='true']
    langs=[]
    for i,r in enumerate(rows,1):
        try:
            x=analyze_language(r,params)
            if x:langs.append(x)
            print(i,len(rows),r['iso'],x['z'] if x else 'NA',flush=True)
        except Exception as e:print('FAIL',r.get('iso'),e,flush=True)
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
    out={'version':4,'system':'ordered alphabet numbers → 3×3 → 4×4 phonetic bridge → 5×5, with Dürer/powers-of-3 on 4×4','method':{
      'alphabet_order':'Observed alphabetic characters are sorted with ICU locale collation for the language and assigned ordinal numbers 1..N. This preserves language-specific ordering among observed letters; multi-character letters/digraphs are a stated limitation.',
      'projection':'Ordinal alphabet positions are normalized and projected into 3, 4 and 5 ordered bins. Word letter-to-letter transitions generate an ordered-alphabet transition graph at each resolution.',
      'phonetic_comparison':'WikiPron pronunciations are independently projected through the existing PHOIBLE-derived 3×3, 4×4 and 5×5 phonetic layers. Cosine similarity compares ordered-alphabet and phonetic transition distributions at each resolution.',
      'bridge_score':'Absolute difference between 4×4 similarity and the midpoint of 3×3 and 5×5 similarities. Lower means the 4×4 layer behaves as an interpolating bridge.',
      'magic_score':'Mean Dürer powers-of-3 exponent distance for ordered-alphabet 4×4 transitions; lower is more locally aligned to the magic ordering.',
      'composite':'(1-sim3)+(1-sim4)+(1-sim5)+bridge_residual+0.25×magic_cost.',
      'randomization':'Shuffle the alphabet ordinal assignments while leaving words and pronunciations fixed. This directly tests whether intended alphabet order carries more 3–4–5 phonetic structure than arbitrary letter numbering.',
      'per_language_random_assignments':PERMS,'sample_words_cap':SAMPLE_WORDS,'group_test':'Stouffer combination of per-language composite z scores with Benjamini-Hochberg correction. Negative z is better than shuffled alphabet orders.'},
      'counts':{'languages_tested':len(langs),'families_tested':len(families),'topology_groups_tested':len(topology)},'fit_bands':{k:sorted(v) for k,v in bands.items()},'groups':families,'topology_groups':topology,'languages':sorted(langs,key=lambda x:x['z'])}
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'languages':len(langs),'families':len(families),'topology_groups':len(topology),'top_topology':[(g['group'],round(g['stouffer_z'],3),round(g['q'],4),g['strength']) for g in topology[:10]]},indent=2))
if __name__=='__main__':main()
