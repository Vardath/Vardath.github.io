#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, math, hashlib, statistics, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path
import man_grid_exact_data as D
import man_grid_exact_engine as E

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/man-grid-alphabet-traversal-v1.json'
BENCH=ROOT/'data/phonetic-benchmark-languages.csv'
ORDERS=ROOT/'data/phonetic-alphabet-orders.json'
WP_COMMIT='d282e848a211ea31cfd730f0ced8bc8cdab9e83d'
WP_BASE=f'https://raw.githubusercontent.com/CUNY-CL/wikipron/{WP_COMMIT}/data/scrape/tsv/'
MAX_WORDS=3000
ALIGN_ITERS=5
PERMS=400
MIN_SYMBOL_SUPPORT=8
MIN_SYMBOL_COVERAGE=.55
GAP=.18

# The primary directional hypothesis. Secondary-axis starting side is deliberately
# not fixed: LR/RL allow either top- or bottom-first rows; TB/BT allow either
# left- or right-first columns.
RTL={'heb','ara','fas'}
VERTICAL={'kor','okm'}

K_CONS=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
K_VOW=['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']
K_ORDER=K_CONS+K_VOW
K_FINAL=['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
K_SPLIT={'ㄳ':['ㄱ','ㅅ'],'ㄵ':['ㄴ','ㅈ'],'ㄶ':['ㄴ','ㅎ'],'ㄺ':['ㄹ','ㄱ'],'ㄻ':['ㄹ','ㅁ'],'ㄼ':['ㄹ','ㅂ'],'ㄽ':['ㄹ','ㅅ'],'ㄾ':['ㄹ','ㅌ'],'ㄿ':['ㄹ','ㅍ'],'ㅀ':['ㄹ','ㅎ'],'ㅄ':['ㅂ','ㅅ']}

def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf8')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big')

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Vardath-ManGrid-AlphabetTraversal/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read().decode('utf-8-sig')

def sample_lines(text,n,seed):
    rows=[x for x in text.splitlines() if '\t' in x]
    if len(rows)<=n:return rows
    # deterministic hash sample; no random module dependency
    return sorted(rows,key=lambda x:h64(seed,x))[:n]

def decompose_hangul(s):
    out=[]
    for ch in unicodedata.normalize('NFC',s):
        cp=ord(ch)
        if 0xAC00<=cp<=0xD7A3:
            k=cp-0xAC00; li=k//588; vi=(k%588)//28; ti=k%28
            out.extend([K_CONS[li],K_VOW[vi]])
            if ti:
                f=K_FINAL[ti];out.extend(K_SPLIT.get(f,[f]))
        elif ch in K_ORDER:
            out.append(ch)
    return out

def normalizer(iso,s):
    s=unicodedata.normalize('NFC',s).lower()
    if iso=='heb':
        s=s.translate(str.maketrans({'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'}))
    elif iso in {'ara','fas'}:
        s=s.translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ئ':'ي','ؤ':'و','ة':'ه','ك':'ک' if iso=='fas' else 'ك','ي':'ی' if iso=='fas' else 'ي'}))
    return s

def tokenize(word,alphabet,iso):
    if iso in VERTICAL:return decompose_hangul(word)
    text=normalizer(iso,word)
    toks=sorted(alphabet,key=len,reverse=True);out=[];i=0
    while i<len(text):
        hit=None
        for t in toks:
            if text.startswith(t,i):hit=t;break
        if hit is not None:
            out.append(hit);i+=len(hit);continue
        i+=1
    return out

def phone_key(s):
    return unicodedata.normalize('NFC',s.strip().strip('/'))

def phone_lookup(name_to_pt,s):
    z=phone_key(s)
    for q in (z,z.replace('ˈ','').replace('ˌ','').replace('.','').replace('‿','').replace('#','')):
        if q in name_to_pt:return name_to_pt[q]
    return None

def parse_words(lines,alphabet,iso,name_to_pt):
    out=[]
    for line in lines:
        a,b=line.split('\t',1)
        gs=tokenize(a,alphabet,iso)
        ps=[phone_lookup(name_to_pt,x) for x in b.strip().split()]
        ps=[p for p in ps if p is not None]
        if 1<=len(gs)<=24 and 1<=len(ps)<=24:out.append((a,gs,ps))
    return out

def centroid(rows):
    if not rows:return None
    return (sum(x for x,y in rows)/len(rows),sum(y for x,y in rows)/len(rows))

def sq(a,b):
    return (a[0]-b[0])**2+(a[1]-b[1])**2

def align(gs,ps,C):
    m,n=len(gs),len(ps);inf=1e99
    dp=[[inf]*(n+1) for _ in range(m+1)];bt=[[None]*(n+1) for _ in range(m+1)]
    dp[0][0]=0.0
    for i in range(1,m+1):dp[i][0]=dp[i-1][0]+GAP;bt[i][0]='g'
    for j in range(1,n+1):dp[0][j]=dp[0][j-1]+GAP;bt[0][j]='p'
    for i in range(1,m+1):
        c=C.get(gs[i-1])
        for j in range(1,n+1):
            mc=(sq(c,ps[j-1]) if c is not None else .20)
            opts=[(dp[i-1][j-1]+mc,'m'),(dp[i-1][j]+GAP,'g'),(dp[i][j-1]+GAP,'p')]
            dp[i][j],bt[i][j]=min(opts,key=lambda z:(z[0],{'m':0,'g':1,'p':2}[z[1]]))
    i,j=m,n;matches=[]
    while i or j:
        op=bt[i][j]
        if op=='m':matches.append((i-1,j-1));i-=1;j-=1
        elif op=='g':i-=1
        else:j-=1
    matches.reverse();return matches,dp[m][n]

def learn_centroids(rows,alphabet):
    bag=defaultdict(list)
    for _,gs,ps in rows:
        m,n=len(gs),len(ps)
        for i,g in enumerate(gs):
            j=min(n-1,max(0,int((i+.5)*n/m)))
            bag[g].append(ps[j])
    C={g:centroid(v) for g,v in bag.items() if v}
    for _ in range(ALIGN_ITERS):
        bag=defaultdict(list)
        for _,gs,ps in rows:
            M,_=align(gs,ps,C)
            for i,j in M:bag[gs[i]].append(ps[j])
        C2={g:centroid(v) for g,v in bag.items() if v}
        for g in alphabet:
            if g not in C2 and g in C:C2[g]=C[g]
        C=C2
    support=defaultdict(int);err=[]
    for _,gs,ps in rows:
        M,_=align(gs,ps,C)
        for i,j in M:
            support[gs[i]]+=1
            if gs[i] in C:err.append(math.sqrt(sq(C[gs[i]],ps[j])))
    return C,dict(support),(statistics.mean(err) if err else None)

def test_alignment(rows,C):
    tok=mat=0;err=[]
    for _,gs,ps in rows:
        tok+=len(gs);M,_=align(gs,ps,C);mat+=len(M)
        for i,j in M:
            if gs[i] in C:err.append(math.sqrt(sq(C[gs[i]],ps[j])))
    return {'words':len(rows),'grapheme_tokens':tok,'matched_tokens':mat,
            'match_rate':mat/tok if tok else 0,
            'mean_coordinate_error':statistics.mean(err) if err else None}

def layer_cell(pt,layer):
    x=max(0,min(.999999,pt[0]));y=max(0,min(.999999,pt[1]))
    c=min(layer['columns']-1,int(x*layer['columns']))
    r=min(layer['rows']-1,int((1-y)*layer['rows']))
    return r,c

def trav_indices(r,c,R,C):
    return {
      'row_lr_top': r*C+c,
      'row_lr_bottom': (R-1-r)*C+c,
      'row_rl_top': r*C+(C-1-c),
      'row_rl_bottom': (R-1-r)*C+(C-1-c),
      'col_tb_left': c*R+r,
      'col_tb_right': (C-1-c)*R+r,
      'col_bt_left': c*R+(R-1-r),
      'col_bt_right': (C-1-c)*R+(R-1-r),
      'row_snake_lr': r*C+(c if r%2==0 else C-1-c),
      'row_snake_rl': r*C+((C-1-c) if r%2==0 else c),
      'col_snake_tb': c*R+(r if c%2==0 else R-1-r),
      'col_snake_bt': c*R+((R-1-r) if c%2==0 else r)
    }

def tau(order,values):
    con=dis=tied=0
    for i in range(len(order)):
        for j in range(i+1,len(order)):
            a,b=values[order[i]],values[order[j]]
            if a==b:tied+=1
            elif a<b:con+=1
            else:dis+=1
    den=con+dis
    return {'tau':(con-dis)/den if den else 0.0,'resolved_pairs':den,'ties':tied,
            'pair_coverage':den/(den+tied) if den+tied else 0.0}

def score_order(alphabet,C,spec):
    usable=[g for g in alphabet if g in C]
    layers=[*spec['upper'],*spec['lower']]
    per={};agg=defaultdict(list)
    for L in layers:
        vals=defaultdict(dict)
        for g in usable:
            r,c=layer_cell(C[g],L)
            for k,v in trav_indices(r,c,L['rows'],L['columns']).items():vals[k][g]=v
        z={}
        for k,d in vals.items():
            q=tau(usable,d);z[k]=q
            if q['pair_coverage']>=.30:agg[k].append(q['tau'])
        per[L['id']]={'rows':L['rows'],'columns':L['columns'],'scores':z}
    mean={k:(statistics.mean(v) if v else 0.0) for k,v in agg.items()}
    cls={
      'LR':max(mean.get('row_lr_top',0),mean.get('row_lr_bottom',0)),
      'RL':max(mean.get('row_rl_top',0),mean.get('row_rl_bottom',0)),
      'TB':max(mean.get('col_tb_left',0),mean.get('col_tb_right',0)),
      'BT':max(mean.get('col_bt_left',0),mean.get('col_bt_right',0))
    }
    return {'usable_symbols':len(usable),'symbol_fraction':len(usable)/len(alphabet) if alphabet else 0,
            'classes':cls,'best_class':max(cls,key=cls.get),'layers':per}

def expected_class(iso):
    return 'TB' if iso in VERTICAL else ('RL' if iso in RTL else 'LR')

def opposite(c):return {'LR':'RL','RL':'LR','TB':'BT','BT':'TB'}[c]

def shuffled(a,seed):
    z=list(a);state=seed or 1
    for i in range(len(z)-1,0,-1):
        state=(6364136223846793005*state+1442695040888963407)&((1<<64)-1)
        j=state%(i+1);z[i],z[j]=z[j],z[i]
    return z

def empirical_language(alphabet,C,spec,exp,obs,seed):
    null=[]
    for k in range(PERMS):
        q=score_order(shuffled(alphabet,h64(seed,k)),C,spec)['classes']
        null.append(q[exp]-q[opposite(exp)])
    return (1+sum(x>=obs for x in null))/(len(null)+1),statistics.mean(null)

def group_empirical(rows,group,spec,seed):
    xs=[x for x in rows if x['direction']==group]
    if not xs:return {'languages':0}
    obs=statistics.mean(x['delta_vs_opposite'] for x in xs)
    null=[]
    for k in range(PERMS):
        ds=[]
        for x in xs:
            q=score_order(shuffled(x['_alphabet'],h64(seed,k,x['iso'])),x['_centroids'],spec)['classes']
            ds.append(q[group]-q[opposite(group)])
        null.append(statistics.mean(ds))
    p=(1+sum(v>=obs for v in null))/(len(null)+1)
    return {'languages':len(xs),'mean_delta_vs_opposite':obs,'positive_languages':sum(x['delta_vs_opposite']>0 for x in xs),
            'expected_class_best_languages':sum(x['best_class']==group for x in xs),
            'permutation_p':p,'null_mean':statistics.mean(null)}

def main():
    spec,params,_,_,cov=D.load_phoible()
    name_to_pt={}
    for q in params.values():
        nm=unicodedata.normalize('NFC',q['name'])
        name_to_pt[nm]=(q['grid']['x'],q['grid']['y'])

    metas={r['iso']:r for r in csv.DictReader(BENCH.read_text(encoding='utf8').splitlines()) if str(r.get('canonical','')).lower()=='true'}
    presets=json.loads(ORDERS.read_text(encoding='utf8'))['orders']
    # Korean vertical-capable ordered jamo are added only for this test. The
    # order is Unicode's modern leading-consonant then medial-vowel order.
    presets={**presets,'kor':{'source':'Unicode modern Hangul Jamo order (compatibility forms)','symbols':K_ORDER},
             'okm':{'source':'Unicode modern Hangul Jamo order used as a restricted historical-Hangul probe','symbols':K_ORDER}}

    targets=[iso for iso in presets if iso in metas]
    results=[]
    for iso in sorted(targets):
        meta=metas[iso];alphabet=[normalizer(iso,x) if iso not in VERTICAL else x for x in presets[iso]['symbols']]
        try:
            lines=sample_lines(fetch(WP_BASE+meta['file']),MAX_WORDS,meta['file'])
            parsed=parse_words(lines,alphabet,iso,name_to_pt)
            train=[x for x in parsed if h64('split',iso,x[0])%5!=0]
            test=[x for x in parsed if h64('split',iso,x[0])%5==0]
            if len(train)<40:raise RuntimeError('too few mapped training words')
            C,support,trainerr=learn_centroids(train,alphabet)
            stable={g:C[g] for g in alphabet if g in C and support.get(g,0)>=MIN_SYMBOL_SUPPORT}
            s=score_order(alphabet,stable,spec);exp=expected_class(iso);opp=opposite(exp);delta=s['classes'][exp]-s['classes'][opp]
            p,nullmean=empirical_language(alphabet,stable,spec,exp,delta,iso)
            row={'iso':iso,'name':meta['name'],'script':meta['script'],'family':meta['family'],'direction':exp,
                 'alphabet_source':presets[iso]['source'],'alphabet_size':len(alphabet),'stable_symbols':s['usable_symbols'],
                 'symbol_fraction':s['symbol_fraction'],'train_words':len(train),'test_alignment':test_alignment(test,stable),
                 'train_mean_coordinate_error':trainerr,'classes':s['classes'],'best_class':s['best_class'],
                 'delta_vs_opposite':delta,'permutation_p':p,'null_mean_delta':nullmean,
                 '_alphabet':alphabet,'_centroids':stable}
            if s['symbol_fraction']>=MIN_SYMBOL_COVERAGE:results.append(row)
        except Exception as e:
            results.append({'iso':iso,'name':meta['name'],'script':meta['script'],'family':meta['family'],
                            'direction':expected_class(iso),'status':'failed','error':str(e)})

    ok=[x for x in results if x.get('status')!='failed' and x.get('symbol_fraction',0)>=MIN_SYMBOL_COVERAGE]
    groups={g:group_empirical(ok,g,spec,'group-'+g) for g in ('LR','RL','TB')}
    overall=[x for x in ok if x['direction'] in groups]
    mean_delta=statistics.mean(x['delta_vs_opposite'] for x in overall) if overall else 0
    best=sum(x['best_class']==x['direction'] for x in overall)
    pos=sum(x['delta_vs_opposite']>0 for x in overall)

    # Layer-specific group means expose whether any effect is concentrated in
    # one rectangle rather than the Man Grid as a whole.
    layer_groups={}
    for L in [*spec['upper'],*spec['lower']]:
        layer_groups[L['id']]={}
        for g in ('LR','RL','TB'):
            vals=[]
            for x in ok:
                if x['direction']!=g:continue
                # recompute per-layer from frozen centroids.
                z=score_order(x['_alphabet'],x['_centroids'],{'upper':[L],'lower':[]})['classes']
                vals.append(z[g]-z[opposite(g)])
            layer_groups[L['id']][g]={'n':len(vals),'mean_delta':statistics.mean(vals) if vals else None,
                                      'positive':sum(v>0 for v in vals)}

    clean=[]
    for x in results:
        y={k:v for k,v in x.items() if not k.startswith('_')}
        clean.append(y)

    out={
      'version':1,'status':'complete','test':'Fixed Man Grid multi-direction alphabet traversal',
      'source':{'phoible_commit':D.PH,'wikipron_commit':WP_COMMIT,
                'alphabet_orders':'data/phonetic-alphabet-orders.json + Unicode modern Hangul Jamo order for Korean probes'},
      'question':'When alphabet symbols are placed on one frozen PHOIBLE-derived Man Grid solely from pronunciation evidence, do known LTR, RTL and vertical-capable ordered systems preferentially emerge under the matching grid traversal direction?',
      'design':{
        'frozen_grid':'Exact 1,074-cell mirrored Man Grid. Phone coordinates are fixed by the existing PHOIBLE projection; no direction label or alphabet rank is used to place phones.',
        'symbol_placement':'Grapheme-to-phone centroids are learned from WikiPron word/pronunciation pairs by iterative monotonic alignment. Alphabet rank is not used during alignment.',
        'heldout':'20% deterministic held-out words assess alignment stability; traversal scores use only stable symbols learned from the remaining words.',
        'directions':{'LR':'row-major left-to-right, allowing top-first or bottom-first rows',
                      'RL':'row-major right-to-left, allowing top-first or bottom-first rows',
                      'TB':'column-major top-to-bottom, allowing left-first or right-first columns',
                      'BT':'column-major bottom-to-top, allowing left-first or right-first columns'},
        'primary_statistic':'Mean pairwise order-concordance across all 10 exact Man Grid rectangles. Expected direction is compared with its opposite.',
        'controls':f'{PERMS} deterministic within-alphabet order permutations per language and per direction group.',
        'eligibility':f'>={MIN_SYMBOL_SUPPORT} aligned training tokens per symbol and >={MIN_SYMBOL_COVERAGE:.0%} of alphabet symbols stably placed.',
        'boundary':'This tests ordered alphabet/jamo traversal through the phonetic grid. It does not treat Han characters as an alphabet and therefore does not directly test Chinese character order.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'candidate_systems':len(targets),'scored_systems':len(ok),
                  'failed_or_low_coverage':len(results)-len(ok)},
      'summary':{'scored_systems':len(overall),'positive_vs_opposite':pos,
                 'expected_class_best':best,'mean_delta_vs_opposite':mean_delta,'groups':groups},
      'layer_groups':layer_groups,'languages':clean
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(out['coverage'],indent=2))
    print(json.dumps(out['summary'],indent=2))
    print('LANGUAGES')
    for x in clean:
        if x.get('status')=='failed':print(x['iso'],'FAIL',x['error'])
        else:print(x['iso'],x['direction'],x['best_class'],round(x['delta_vs_opposite'],4),round(x['permutation_p'],4),round(x['symbol_fraction'],3))
    print('LAYERS')
    print(json.dumps(layer_groups,indent=2))

if __name__=='__main__':main()
