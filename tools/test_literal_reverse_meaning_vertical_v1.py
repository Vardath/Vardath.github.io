#!/usr/bin/env python3
# Literal reversed-pronunciation same-meaning search, then vertical-language follow-up.
from __future__ import annotations
import csv, io, json, math, statistics, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path

import man_grid_exact_data as D
import test_phonetic_feature_birth_v1 as FB

ROOT=Path(__file__).resolve().parents[1]
LINKED=ROOT/'data/three-way-linked-language-test-v1.json'
OUT=ROOT/'data/literal-reverse-meaning-vertical-v1.json'
NE_SHA='e9a8119f25cf6078299132d8c4e7db338d46ff23'
NE_BASE=f'https://raw.githubusercontent.com/lexibank/northeuralex/{NE_SHA}/cldf/'
NEG=20
MIN_SHARED=250
TOP_FRACTION=0.10
PERMS=2000

def fetch(name):
    req=urllib.request.Request(NE_BASE+name,headers={'User-Agent':'Vardath-LiteralReverseVertical/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8-sig')

def canon(s):
    s=unicodedata.normalize('NFD',str(s).strip()).replace('\u0361','').replace('\u035c','').replace('ɡ','g')
    return unicodedata.normalize('NFC',s)

def mean(xs): return statistics.mean(xs) if xs else None

def signp(k,n):
    return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def edit(seq1,seq2,coords):
    if not seq1 or not seq2:return 1.0
    prev=[float(j) for j in range(len(seq2)+1)]
    for i,a in enumerate(seq1,1):
        cur=[float(i)]+[0.0]*len(seq2)
        ax,ay=coords[a]
        for j,b in enumerate(seq2,1):
            bx,by=coords[b]
            sub=min(1.0,math.hypot(ax-bx,ay-by)/math.sqrt(2))
            cur[j]=min(prev[j]+1.0,cur[j-1]+1.0,prev[j-1]+sub)
        prev=cur
    return prev[-1]/max(len(seq1),len(seq2))

def rotate_tb_seq(seq,coords):
    # Preserve spoken phone order; rotate each phone coordinate using the same fixed
    # TB -> canonical transform used in the earlier directional test.
    out=[]
    for j in seq:
        x,y=coords[j]
        out.append((1-y,x))
    return out

def edit_points_to_seq(points,seq,coords):
    if not points or not seq:return 1.0
    prev=[float(j) for j in range(len(seq)+1)]
    for i,(ax,ay) in enumerate(points,1):
        cur=[float(i)]+[0.0]*len(seq)
        for j,b in enumerate(seq,1):
            bx,by=coords[b]
            sub=min(1.0,math.hypot(ax-bx,ay-by)/math.sqrt(2))
            cur[j]=min(prev[j]+1.0,cur[j-1]+1.0,prev[j-1]+sub)
        prev=cur
    return prev[-1]/max(len(points),len(seq))

def midpoint_points(a,b,coords):
    # Align reversed-LTR to RTL using a simple normalized rank resampling so a vertical
    # third word can be compared against the horizontal consensus without learning parameters.
    def rs(seq,k):
        pts=[coords[j] for j in seq]
        if len(pts)==1:return [pts[0]]*k
        out=[]
        for q in range(k):
            u=q*(len(pts)-1)/(k-1);i=min(len(pts)-2,int(u));f=u-i
            x1,y1=pts[i];x2,y2=pts[i+1]
            out.append((x1*(1-f)+x2*f,y1*(1-f)+y2*f))
        return out
    k=max(len(a),len(b),4)
    A=rs(a,k);B=rs(b,k)
    return [((x1+x2)/2,(y1+y2)/2) for (x1,y1),(x2,y2) in zip(A,B)]

def main():
    _,params,_,_,cov=D.load_phoible();P=FB.fit(params)
    coords=[];alias={}
    for pid in sorted(params):
        p=params[pid];idx=len(coords);coords.append(FB.project(p['features'],P));alias.setdefault(canon(p['name']),idx)

    linked=json.loads(LINKED.read_text(encoding='utf8'))
    eligible=linked['coverage']['eligible_members']
    wanted={}
    for d in ('LR','RL','TB'):
        for x in eligible[d]:
            if x['iso']=='okm':continue
            wanted[x['iso']]={'iso':x['iso'],'name':x['name'],'direction':d}

    lang_rows=list(csv.DictReader(io.StringIO(fetch('languages.csv'))))
    def normname(s):
        return ''.join(c for c in unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode('ascii').lower() if c.isalnum())
    aliases={'cym':['welsh'],'dan':['danish'],'fin':['finnish'],'heb':['hebrew'],'isl':['icelandic'],
             'kor':['korean'],'nob':['norwegianbokmal'],'nor':['norwegian'],'swe':['swedish']}
    resolved={}
    for iso,w in wanted.items():
        rr=None
        for r in lang_rows:
            vals=[str(v).strip().lower() for v in r.values() if v is not None]
            if iso.lower() in vals:rr=r;break
        if rr is None:
            targets={normname(w['name']),*(normname(z) for z in aliases.get(iso,[]))}
            rr=next((r for r in lang_rows if normname(r.get('Name','')) in targets),None)
        if rr:
            resolved[iso]={**w,'id':rr['ID'],'dataset_name':rr.get('Name') or w['name'],
                           'family':rr.get('Family') or 'Unknown','subfamily':rr.get('Subfamily') or ''}

    ids={x['id']:iso for iso,x in resolved.items()}
    forms={iso:{} for iso in resolved}
    labels={r['ID']:(r.get('Concepticon_Gloss') or r.get('Name') or r['ID'])
            for r in csv.DictReader(io.StringIO(fetch('parameters.csv')))}
    for r in csv.DictReader(io.StringIO(fetch('forms.csv'))):
        lid=(r.get('Language_ID') or '').strip()
        if lid not in ids:continue
        con=(r.get('Parameter_ID') or '').strip()
        toks=[x for x in (r.get('Segments') or '').split() if x]
        if not con or not toks or len(toks)>18:continue
        seq=[];ok=True
        for t in toks:
            j=alias.get(canon(t))
            if j is None:ok=False;break
            seq.append(j)
        if not ok:continue
        iso=ids[lid]
        cand=(len(seq),r.get('ID') or '',seq,(r.get('Form') or r.get('Value') or '').strip(),(r.get('Segments') or '').strip())
        if con not in forms[iso] or cand[:2]<forms[iso][con][:2]:
            forms[iso][con]=cand
    clean={iso:{c:{'seq':v[2],'form':v[3],'segments':v[4]} for c,v in fd.items()} for iso,fd in forms.items()}

    lr=[iso for iso,x in resolved.items() if x['direction']=='LR']
    rtl=[iso for iso,x in resolved.items() if x['direction']=='RL']
    tb=[iso for iso,x in resolved.items() if x['direction']=='TB']
    if not rtl or not tb:raise RuntimeError('Need RTL and TB languages')

    horizontal=[]
    for a in lr:
        for b in rtl:
            shared=sorted(set(clean[a])&set(clean[b]))
            if len(shared)<MIN_SHARED:continue
            rows=[]
            for c in shared:
                A=clean[a][c]['seq'];B=clean[b][c]['seq']
                rev=edit(list(reversed(A)),B,coords)
                direct=edit(A,B,coords)
                wrongs=[z for z in shared if z!=c]
                wrongs=sorted(wrongs,key=lambda z:(D.h64('litrev-neg',a,b,c,z),z))[:NEG]
                nd=[edit(list(reversed(A)),clean[b][z]['seq'],coords) for z in wrongs]
                null=mean(nd)
                rows.append({'concept_id':c,'concept':labels.get(c,c),'reverse_distance':rev,'direct_distance':direct,
                             'wrong_meaning_reverse_distance':null,'semantic_advantage':null-rev,
                             'reverse_gain_vs_direct':direct-rev,
                             'a_form':clean[a][c]['form'],'a_segments':clean[a][c]['segments'],
                             'b_form':clean[b][c]['form'],'b_segments':clean[b][c]['segments']})
            adv=mean([r['semantic_advantage'] for r in rows]);gain=mean([r['reverse_gain_vs_direct'] for r in rows])
            wins=sum(r['semantic_advantage']>0 for r in rows);gwins=sum(r['reverse_gain_vs_direct']>0 for r in rows)
            horizontal.append({'LR':a,'RL':b,'languages':[resolved[a]['dataset_name'],resolved[b]['dataset_name']],
                               'shared_concepts':len(rows),'mean_semantic_advantage':adv,'mean_reverse_gain_vs_direct':gain,
                               'semantic_wins':wins,'semantic_sign_p':signp(wins,len(rows)),
                               'reverse_gain_wins':gwins,'reverse_gain_sign_p':signp(gwins,len(rows)),
                               '_rows':rows})
    if not horizontal:raise RuntimeError('No horizontal pairs')
    horizontal.sort(key=lambda x:(x['mean_semantic_advantage'],x['mean_reverse_gain_vs_direct']),reverse=True)
    best=horizontal[0]

    # Pair-search-corrected permutation: for each universe, mismatch RTL meanings and keep the best LR candidate.
    pair_null=[]
    for p in range(PERMS):
        vals=[]
        for q in horizontal:
            a,b=q['LR'],q['RL']
            shared=sorted(set(clean[a])&set(clean[b]))
            perm=sorted(shared,key=lambda c:(D.h64('litrev-perm',p,a,b,c),c))
            vals.append(mean([edit(list(reversed(clean[a][c]['seq'])),clean[b][perm[i]]['seq'],coords)
                              for i,c in enumerate(shared)]))
        pair_null.append(min(vals))
    obs_pair_mean=mean([r['reverse_distance'] for r in best['_rows']])
    pair_search_p=(1+sum(x<=obs_pair_mean for x in pair_null))/(PERMS+1)

    # Freeze strongest literal-reversal concepts BEFORE vertical test: top 10% by a score that
    # requires same-meaning advantage and reversal improvement over direct alignment.
    scored=[r for r in best['_rows'] if r['semantic_advantage']>0 and r['reverse_gain_vs_direct']>0]
    scored.sort(key=lambda r:(min(r['semantic_advantage'],r['reverse_gain_vs_direct']),r['semantic_advantage']),reverse=True)
    nkeep=max(10,round(len(best['_rows'])*TOP_FRACTION))
    hits=scored[:nkeep]
    hit_ids=[r['concept_id'] for r in hits]

    vertical_results=[]
    for ciso in tb:
        usable=[c for c in hit_ids if c in clean[ciso]]
        if len(usable)<8:continue
        rows=[]
        for c in usable:
            A=list(reversed(clean[best['LR']][c]['seq']))
            B=clean[best['RL']][c]['seq']
            consensus=midpoint_points(A,B,coords)
            Cpts=rotate_tb_seq(clean[ciso][c]['seq'],coords)
            # Compare vertical rotated path to horizontal consensus via edit distance with point costs.
            # Convert consensus and Cpts symmetrically using rank resampling.
            def rspts(P,k):
                if len(P)==1:return [P[0]]*k
                out=[]
                for q in range(k):
                    u=q*(len(P)-1)/(k-1);i=min(len(P)-2,int(u));f=u-i
                    x1,y1=P[i];x2,y2=P[i+1]
                    out.append((x1*(1-f)+x2*f,y1*(1-f)+y2*f))
                return out
            k=max(len(consensus),len(Cpts),4);X=rspts(consensus,k);Y=rspts(Cpts,k)
            true=mean([math.hypot(x1-x2,y1-y2) for (x1,y1),(x2,y2) in zip(X,Y)])
            pool=[z for z in clean[ciso] if z!=c]
            pool=sorted(pool,key=lambda z:(D.h64('vert-neg',ciso,c,z),z))[:NEG]
            nulls=[]
            for z in pool:
                Z=rotate_tb_seq(clean[ciso][z]['seq'],coords);Z=rspts(Z,k)
                nulls.append(mean([math.hypot(x1-x2,y1-y2) for (x1,y1),(x2,y2) in zip(X,Z)]))
            null=mean(nulls)
            rows.append({'concept_id':c,'concept':labels.get(c,c),'vertical_distance':true,
                         'wrong_meaning_vertical_distance':null,'vertical_advantage':null-true,
                         'vertical_form':clean[ciso][c]['form'],'vertical_segments':clean[ciso][c]['segments']})
        wins=sum(r['vertical_advantage']>0 for r in rows)
        vertical_results.append({'TB':ciso,'language':resolved[ciso]['dataset_name'],'tested_horizontal_hits':len(rows),
                                 'mean_vertical_advantage':mean([r['vertical_advantage'] for r in rows]),
                                 'wins':wins,'sign_p':signp(wins,len(rows)),'rows':rows})

    # Permutation p for vertical follow-up on the frozen hit list.
    for q in vertical_results:
        ciso=q['TB'];usable=[r['concept_id'] for r in q['rows']]
        obs=mean([r['vertical_distance'] for r in q['rows']])
        pn=[]
        for p in range(PERMS):
            perm=sorted(usable,key=lambda c:(D.h64('vert-perm',p,ciso,c),c))
            vals=[]
            for i,c in enumerate(usable):
                A=list(reversed(clean[best['LR']][c]['seq']));B=clean[best['RL']][c]['seq']
                consensus=midpoint_points(A,B,coords)
                z=perm[i];Cpts=rotate_tb_seq(clean[ciso][z]['seq'],coords)
                k=max(len(consensus),len(Cpts),4)
                def rspts(P,k):
                    if len(P)==1:return [P[0]]*k
                    out=[]
                    for qq in range(k):
                        u=qq*(len(P)-1)/(k-1);ii=min(len(P)-2,int(u));f=u-ii
                        x1,y1=P[ii];x2,y2=P[ii+1]
                        out.append((x1*(1-f)+x2*f,y1*(1-f)+y2*f))
                    return out
                X=rspts(consensus,k);Y=rspts(Cpts,k)
                vals.append(mean([math.hypot(x1-x2,y1-y2) for (x1,y1),(x2,y2) in zip(X,Y)]))
            pn.append(mean(vals))
        q['permutation_p']=(1+sum(x<=obs for x in pn))/(PERMS+1)

    # Public rows
    for q in horizontal:
        q['top_reverse_same_meaning_examples']=sorted(q.pop('_rows'),key=lambda r:(r['semantic_advantage']+r['reverse_gain_vs_direct']),reverse=True)[:40]
    selected=horizontal[0]
    selected['pair_search_corrected_permutation_p']=pair_search_p
    selected['frozen_reverse_hit_count']=len(hits)
    selected['frozen_reverse_hits']=[{k:v for k,v in r.items()} for r in hits[:50]]

    out={
      'version':1,'status':'complete',
      'test':'Literal reversed-pronunciation same-meaning search with vertical-language follow-up',
      'question':'Do any directionally eligible LTR/RTL languages contain same-meaning words whose phone order literally reverses across languages, and do those concepts then align in the top-to-bottom language?',
      'source':{'NorthEuraLex_commit':NE_SHA,'PHOIBLE_commit':D.PH},
      'design':{
        'horizontal':'For each same-meaning LTR/RTL word pair, reverse the LTR phone sequence itself, then compute phonetic-feature edit distance to the RTL word. No geometric reflection or arbitrary transform is allowed.',
        'controls':f'Each real meaning is compared with {NEG} wrong meanings in the RTL language. Reverse-vs-direct improvement is also required for the strongest hits.',
        'pair_search':f'All eligible LTR languages are tested against the eligible RTL language; {PERMS} label permutations correct for choosing the best horizontal pair.',
        'hit_freeze':f'The strongest {TOP_FRACTION:.0%} of concepts that both beat wrong meanings and improve under literal reversal are frozen before looking at the vertical language.',
        'vertical':'For the frozen horizontal reversal hits only, the Korean/TB word is rotated by the fixed TB coordinate transform from the earlier alphabet test and compared with the midpoint phonetic path of the reversed-LTR and RTL words.',
        'vertical_control':f'Each true vertical meaning is compared with {NEG} wrong vertical meanings and {PERMS} label permutations.',
        'support':'A linked three-way signal would require a horizontal reverse effect that survives pair-search correction and a positive vertical follow-up with p<0.05 on the frozen horizontal hits.'
      },
      'coverage':{'phoible_segments':cov['research_segments'],'resolved_languages':resolved,'horizontal_pairs':len(horizontal),
                  'permutations':PERMS,'wrong_meanings_per_case':NEG},
      'horizontal_ranking':horizontal,
      'selected_horizontal_pair':selected,
      'vertical_followup':vertical_results
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'selected_horizontal_pair':selected,'vertical_followup':vertical_results},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
