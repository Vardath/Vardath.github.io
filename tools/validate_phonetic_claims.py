#!/usr/bin/env python3
"""Controlled validation tests for the remaining orange claims on phonetic-bridge.html.

Tests:
1. 16-cell model selection: use the completed 3/4/5 PHOIBLE cross-language codec benchmark
   and ask whether 4x4 dominates its neighbouring resolutions. It must dominate, not merely
   occupy a trade-off, before the strong 'globally optimal' claim can be promoted.
2. Lexical -> connected speech: compare WikiPron US-English word-internal gate frequencies
   with phone-aligned LibriSpeech test-clean read speech (within-word and full utterance).
   This is a real speech validation, but only one language/register, so it cannot establish
   universal connected-speech equivalence on its own.
3. Duerer/powers-of-3: (a) compare the Duerer 1..16 cell path cost against 100,000 random
   orderings using PHOIBLE feature centroids; (b) test whether gate prevalence is associated
   with absolute powers-of-3 exponent distance more strongly than random magic assignments.

No test is allowed to turn a claim green merely because code executed successfully.
"""
from __future__ import annotations
import csv, io, json, math, os, random, re, statistics, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/phonetic-validation-results.json'
PH='5c477f1934f57b3c1a16168fadc08e83dbc03362'
WP='d282e848a211ea31cfd730f0ced8bc8cdab9e83d'
PHBASE=f'https://raw.githubusercontent.com/cldf-datasets/phoible/{PH}/cldf/'
WPBASE=f'https://raw.githubusercontent.com/CUNY-CL/wikipron/{WP}/data/scrape/tsv/'
MAGIC=[16,2,3,13,5,11,10,8,9,7,6,12,4,14,15,1]
CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
FEATURES=['syllabic','consonantal','sonorant','continuant','delayedRelease','approximant','nasal','lateral','labial','round','labiodental','coronal','anterior','distributed','strident','dorsal','high','low','front','back','spreadGlottis','constrictedGlottis']
PRIMARY={'syllabic','consonantal','sonorant','continuant','labial','coronal','dorsal','high','low','front','back'}


def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Vardath-Validation/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read().decode('utf-8-sig')

def fnum(v):
    if v in (None,'','0','N'): return 0.0
    s=c=0
    for x in str(v).split(','):
        if x=='+':s+=1;c+=1
        elif x=='-':s-=1;c+=1
    return s/c if c else 0.0

def plus(v): return fnum(v)>.25

def classify(p):
    if not p:return None
    sc=(p.get('SegmentClass') or '').lower()
    if sc=='tone' or plus(p.get('tone')):return None
    if sc=='vowel' or (plus(p.get('syllabic')) and not plus(p.get('consonantal'))):
        vert=fnum(p.get('high'))-fnum(p.get('low')); horiz=fnum(p.get('front'))-fnum(p.get('back'))
        if vert>=0:return 'A1' if horiz>=0 else 'A3'
        return 'A2' if horiz>=0 else 'A4'
    row='B' if plus(p.get('sonorant')) else ('C' if plus(p.get('continuant')) else 'D')
    places=[('1',fnum(p.get('labial'))),('2',fnum(p.get('coronal'))),('3',fnum(p.get('dorsal')))]
    places.sort(key=lambda x:x[1],reverse=True)
    return row+(places[0][0] if places[0][1]>.25 else '4')

def vec(p):
    out=[]
    for f in FEATURES:
        w=2 if f in PRIMARY else 1
        out += [fnum(p.get(f))]*w
    return out

def euclid(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/max(1,len(a)))

def meanvec(vs):return [sum(x[i] for x in vs)/len(vs) for i in range(len(vs[0]))]

def pearson(a,b):
    if len(a)<2:return 0.0
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b)); da=sum((x-ma)**2 for x in a); db=sum((y-mb)**2 for y in b)
    return num/math.sqrt(da*db) if da and db else 0.0

def ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and xs[order[j]]==xs[order[i]]:j+=1
        avg=(i+j-1)/2+1
        for k in range(i,j):r[order[k]]=avg
        i=j
    return r

def spearman(a,b):return pearson(ranks(a),ranks(b))

def jsd(p,q):
    sp=sum(p);sq=sum(q)
    if not sp or not sq:return 1.0
    p=[x/sp for x in p];q=[x/sq for x in q];m=[(x+y)/2 for x,y in zip(p,q)]
    def kl(x,y):return sum(a*math.log2(a/b) for a,b in zip(x,y) if a>0 and b>0)
    return .5*kl(p,m)+.5*kl(q,m)

def cosine(a,b):
    num=sum(x*y for x,y in zip(a,b));da=math.sqrt(sum(x*x for x in a));db=math.sqrt(sum(y*y for y in b))
    return num/(da*db) if da and db else 0.0

# ---------- 1. 16-cell model selection ----------
def test_model_selection():
    d=json.loads((ROOT/'data/pyramid-benchmark-summary.json').read_text(encoding='utf-8'))
    s=d['strategies']; rows={k:{'cells':int(k)**2,'coverage':s[k]['coverage_rate'],'forward_loss':s[k]['mean_forward_loss'],'roundtrip_loss':s[k]['mean_roundtrip_loss'],'roundtrip_exact':s[k]['roundtrip_exact_rate']} for k in ('3','4','5')}
    # Strong promotion criterion: 4x4 must be no worse than BOTH neighbours on all principal
    # predictive/reconstruction metrics, and strictly better on at least one versus each.
    def dominates(a,b):
        return a['coverage']>=b['coverage'] and a['forward_loss']<=b['forward_loss'] and a['roundtrip_loss']<=b['roundtrip_loss'] and a['roundtrip_exact']>=b['roundtrip_exact'] and (a!=b)
    green=dominates(rows['4'],rows['3']) and dominates(rows['4'],rows['5'])
    # Pareto membership: not dominated by a neighbour.
    dominated_by=[]
    for k in ('3','5'):
        if dominates(rows[k],rows['4']):dominated_by.append(k)
    return {'status':'green' if green else 'orange','claim':'The 16-cell compression is globally optimal.','criterion':'4x4 must dominate both adjacent 3x3 and 5x5 resolutions on coverage, forward loss, round-trip loss, and exact recovery.','results':rows,'dominated_by':dominated_by,'conclusion':('Supported under this model-selection criterion.' if green else 'Not established: 4x4 is a trade-off. 3x3 has higher coverage; 5x5 has lower feature/round-trip loss. Global optimality therefore remains unproven.')}

# ---------- shared PHOIBLE maps ----------
def phoible():
    params={}
    for p in csv.DictReader(io.StringIO(fetch(PHBASE+'parameters.csv'))):
        name=(p.get('Name') or '').strip()
        if name:params[name]=p
    buckets=defaultdict(list)
    for p in params.values():
        c=classify(p)
        if c:buckets[c].append(vec(p))
    cent={c:meanvec(vs) for c,vs in buckets.items() if vs}
    return params,cent,{c:len(vs) for c,vs in buckets.items()}

def phone_class_ipa(ph,params):
    x=ph.strip().strip('/').replace('ˈ','').replace('ˌ','').replace('.','').replace('‿','').replace('#','')
    p=params.get(x)
    return classify(p) if p else None

# ---------- 2. speech validation ----------
ARPA={
 'IY':'A1','IH':'A1','EY':'A1','EH':'A1','AE':'A2',
 'UW':'A3','UH':'A3','OW':'A3','AO':'A4','AA':'A4','AH':'A4','ER':'A4','AY':'A2','AW':'A4','OY':'A3',
 'M':'B1','W':'B1','N':'B2','L':'B2','R':'B2','Y':'B3','NG':'B3',
 'F':'C1','V':'C1','TH':'C2','DH':'C2','S':'C2','Z':'C2','SH':'C2','ZH':'C2','HH':'C4',
 'P':'D1','B':'D1','T':'D2','D':'D2','CH':'D2','JH':'D2','K':'D3','G':'D3'
}
def arpa_cell(ph):return ARPA.get(re.sub(r'\d+$','',ph.upper()))
def gate_counts(seq,break_token=None):
    z=[0]*256;prev=None
    for x in seq:
        if x is None or (break_token is not None and x==break_token):prev=None;continue
        c=x if x in CELLS else None
        if c is None:prev=None;continue
        cur=CELLS.index(c)
        if prev is not None:z[prev*16+cur]+=1
        prev=cur
    return z

def parse_textgrid(path):
    text=path.read_text(encoding='utf-8',errors='ignore')
    # Pull phone tier only.
    m=re.search(r'name = "phones"(.*)$',text,re.S)
    if not m:return []
    return re.findall(r'text = "([^"]*)"',m.group(1))

def wikipron_english_counts(params):
    # US General American broad is the closest WikiPron comparator to LibriSpeech read English.
    text=fetch(WPBASE+'eng_latn_us_broad.tsv')
    counts=[0]*256; mapped=unknown=words=0
    for line in text.splitlines():
        if '\t' not in line:continue
        words+=1;prev=None
        for ph in line.split('\t',1)[1].split():
            c=phone_class_ipa(ph,params)
            if c is None:unknown+=1;prev=None;continue
            mapped+=1;cur=CELLS.index(c)
            if prev is not None:counts[prev*16+cur]+=1
            prev=cur
    return counts,{'words':words,'mapped':mapped,'unknown':unknown,'mapping_coverage':mapped/(mapped+unknown) if mapped+unknown else 0}

def test_speech(params):
    corpus=Path(os.environ.get('ALIGNED_LIBRISPEECH','/tmp/aligned-librispeech/librispeech_aligned'))
    files=sorted(corpus.rglob('*.TextGrid')) if corpus.exists() else []
    # deterministic cap keeps CI bounded while spanning many speakers/books
    cap=int(os.environ.get('SPEECH_TEXTGRID_CAP','2500'))
    if len(files)>cap:
        step=len(files)/cap; files=[files[int(i*step)] for i in range(cap)]
    full=[0]*256;utterances=phones=0
    for f in files:
        seq=parse_textgrid(f)
        if not seq:continue
        utterances+=1;cells=[]
        for ph in seq:
            if ph.lower() in {'sil','sp','spn','<eps>',''}:cells.append(None);continue
            c=arpa_cell(ph);cells.append(c); phones+=int(c is not None)
        z=gate_counts(cells)
        full=[a+b for a,b in zip(full,z)]
    wp,meta=wikipron_english_counts(params)
    corr=pearson(wp,full);cs=cosine(wp,full);j=jsd(wp,full)
    # Promotion threshold is intentionally demanding, but even passing it is only English read-speech support.
    passes=corr>=.90 and cs>=.95 and j<=.10 and utterances>=500
    return {'status':'amber' if passes else 'orange','claim':'WikiPron lexical transitions equal continuous connected-speech articulation.','corpus':'MontrealCorpusTools/aligned-librispeech test-clean, MFA phone alignments','speech_textgrids_used':utterances,'mapped_speech_phones':phones,'wikipron':meta,'metrics':{'pearson_gate_frequency':corr,'cosine_gate_frequency':cs,'jensen_shannon_divergence':j},'criterion':'Pearson >= 0.90, cosine >= 0.95, JSD <= 0.10, >=500 aligned utterances. Passing supports only English read speech, not universal equivalence.','conclusion':('Strong English read-speech agreement; partial validation only. A multilingual conversational/acoustic replication is still required for green.' if passes else 'The lexical gate distribution does not meet the predeclared speech-agreement threshold; the claim remains orange.')}

# ---------- 3. magic / powers-of-3 ----------
def path_cost(order,cent):
    return sum(euclid(cent[CELLS[order[i]]],cent[CELLS[order[i+1]]]) for i in range(15))
def test_magic(cent):
    # order of cell indexes visited by magic values 1..16
    pos=[MAGIC.index(v) for v in range(1,17)]
    observed=path_cost(pos,cent)
    rng=random.Random(137);N=100000;better=0;vals=[]
    base=list(range(16))
    for _ in range(N):
        q=base[:];rng.shuffle(q);c=path_cost(q,cent);better+=c<=observed
        if len(vals)<10000:vals.append(c)
    p_path=(better+1)/(N+1)
    # Independent gate-prevalence test against random assignments of 1..16 to cells.
    bench=json.loads((ROOT/'data/phonetic-benchmark-summary.json').read_text(encoding='utf-8'))
    prev=[g['prevalence'] for g in bench['gate_prevalence']]
    absdelta=[abs(MAGIC[j]-MAGIC[i]) for i in range(16) for j in range(16)]
    rho=spearman(absdelta,prev)
    M=20000;as_or_more=0
    for _ in range(M):
        mm=list(range(1,17));rng.shuffle(mm)
        d=[abs(mm[j]-mm[i]) for i in range(16) for j in range(16)]
        rr=spearman(d,prev)
        if rr<=rho:as_or_more+=1  # hypothesized direction: smaller exponent distance => higher prevalence => negative rho
    p_gate=(as_or_more+1)/(M+1)
    green=p_path<.01 and rho<0 and p_gate<.01
    return {'status':'green' if green else 'orange','claim':'The magic-square / powers-of-3 ordering has a phonetic relationship beyond chance.','centroid_path':{'observed_cost':observed,'random_permutations':N,'random_mean':statistics.mean(vals),'random_sd':statistics.pstdev(vals),'one_sided_p':p_path,'percentile_better':p_path},'gate_prevalence':{'spearman_abs_exponent_distance_vs_prevalence':rho,'random_magic_assignments':M,'one_sided_p':p_gate},'criterion':'Both independent tests p < 0.01 in the predicted direction: unusually short PHOIBLE centroid path and negative gate-prevalence association with |power exponent delta|.','conclusion':('Replicated across two independent metrics under the preregistered-style criterion.' if green else 'The Duerer/powers-of-3 ordering does not pass both controlled chance tests; it remains an exploratory overlay.')}

def main():
    params,cent,occupancy=phoible()
    missing=[c for c in CELLS if c not in cent]
    if missing:raise RuntimeError('Missing PHOIBLE centroids: '+','.join(missing))
    result={'validation_version':1,'pins':{'phoible':PH,'wikipron':WP,'aligned_librispeech':'MontrealCorpusTools/aligned-librispeech main (workflow checkout)'},'principle':'Claims are promoted only when their predeclared validation criterion is met. An executed test is not itself evidence of success.','tests':{'sixteen_cell_optimality':test_model_selection(),'lexical_vs_speech':test_speech(params),'magic_powers3':test_magic(cent)},'phoible_cell_occupancy':occupancy}
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result['tests'],indent=2,ensure_ascii=False))
if __name__=='__main__':main()
