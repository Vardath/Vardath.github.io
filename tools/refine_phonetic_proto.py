#!/usr/bin/env python3
"""Refine the proto-gate reconstruction against family imbalance and attestation bias.

Runs after reconstruct_phonetic_proto.py and augments its JSON/Markdown with:
- family-balanced latent root
- older/early-labelled attested subset root
- bootstrap stability from one-language-per-family samples
- family-level recurrent gate core
"""
from __future__ import annotations
import json, random
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phonetic-benchmark-summary.json'
OUTJ=ROOT/'data/phonetic-proto-reconstruction.json'
OUTM=ROOT/'data/phonetic-proto-reconstruction.md'
CELLS=["A1","A2","A3","A4","B1","B2","B3","B4","C1","C2","C3","C4","D1","D2","D3","D4"]
R=random.Random(137)

def q(x,n=6): return round(float(x),n)
def unit(v):
    n=np.linalg.norm(v); return v/(n if n else 1)
def state_map(place=False,manner=False):
    cm=[2,1,0,3] if place else [0,1,2,3]; rm=[0,3,2,1] if manner else [0,1,2,3]
    return [rm[i//4]*4+cm[i%4] for i in range(16)]
def gate_map(place=False,manner=False,reverse=False):
    sm=state_map(place,manner); out=np.empty(256,dtype=int)
    for a in range(16):
        for b in range(16):
            aa,bb=sm[a],sm[b]
            if reverse: aa,bb=bb,aa
            out[a*16+b]=aa*16+bb
    return out
OPS=[('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]
MAPS=[gate_map(*x[1:]) for x in OPS]
def trans(v,mp):
    o=np.zeros_like(v); o[mp]=v; return o

def align_root(vectors,iterations=20):
    root=np.mean(vectors,axis=0); root/=root.sum() or 1
    choices=[]
    for _ in range(iterations):
        ru=unit(root); aligned=[]; choices=[]
        for v in vectors:
            tv=[trans(v,m) for m in MAPS]; sims=[float(np.dot(ru,unit(x))) for x in tv]; k=int(np.argmax(sims));choices.append(k);aligned.append(tv[k])
        nr=np.mean(aligned,axis=0); nr/=nr.sum() or 1
        if np.linalg.norm(nr-root)<1e-10: root=nr;break
        root=nr
    return root,choices

def top_gates(root,n=24):
    out=[]
    for gi in np.argsort(root)[::-1][:n]:
        a,b=divmod(int(gi),16);out.append({'index':int(gi),'gate':f'{CELLS[a]}→{CELLS[b]}','mass':q(root[gi])})
    return out

def closest(root,P,names,families,isos,n=15):
    ru=unit(root);rows=[]
    for i,v in enumerate(P):
        vals=[float(np.dot(ru,unit(trans(v,m)))) for m in MAPS];k=int(np.argmax(vals));rows.append({'iso':isos[i],'name':names[i],'family':families[i],'similarity':q(vals[k]),'operator':OPS[k][0]})
    return sorted(rows,key=lambda x:-x['similarity'])[:n]

def root_summary(label,root,choices,P,names,families,isos):
    ent=-sum(float(x)*np.log2(float(x)) for x in root if x>0)
    return {'label':label,'entropy_bits':q(ent),'effective_gates':q(2**ent),'operator_usage':dict(Counter(OPS[k][0] for k in choices)),'top_gates':top_gates(root),'closest_proxies':closest(root,P,names,families,isos)}

def main():
    d=json.loads(SRC.read_text());res=json.loads(OUTJ.read_text())
    L=d['languages'];names=[x['name'] for x in L];families=[x.get('family','Unclassified') for x in L];isos=[x['iso'] for x in L]
    C=np.array([x['sample_counts'] for x in L],dtype=float);P=C/np.where(C.sum(1,keepdims=True)>0,C.sum(1,keepdims=True),1)
    fam_ix=defaultdict(list)
    for i,f in enumerate(families):
        if f and f!='Unclassified': fam_ix[f].append(i)
    fam_names=sorted(fam_ix)
    fam_centroids=[]
    for f in fam_names:
        v=np.mean(P[fam_ix[f]],axis=0);v/=v.sum() or 1;fam_centroids.append(v)
    fam_centroids=np.array(fam_centroids)
    fb_root,fb_choices=align_root(fam_centroids)
    # Proxies are still searched across all languages, but construction weights each named family once.
    fb=root_summary('Family-balanced root',fb_root,fb_choices,P,names,families,isos);fb['families_weighted_equally']=len(fam_names)

    # Explicitly listed older/early-attested labels; no hidden dating inference.
    early_terms=('Ancient ','Old ','Middle ','Classical ','Official Aramaic','Akkadian','Sanskrit','Latin','Gothic','Egyptian (Ancient)','Kawi','Biblical ')
    early_ix=[i for i,n in enumerate(names) if n.startswith(early_terms) or any(t in n for t in ('Official Aramaic','Egyptian (Ancient)'))]
    early_vec=P[early_ix]
    eroot,echoices=align_root(early_vec)
    early=root_summary('Older/early-labelled attested subset',eroot,echoices,P,names,families,isos)
    early['source_languages']=[names[i] for i in early_ix];early['source_count']=len(early_ix)

    # Recurrent family gate core: gate appears in a family's top-32 by probability.
    recurrence=np.zeros(256,dtype=int)
    for v in fam_centroids:
        recurrence[np.argsort(v)[::-1][:32]]+=1
    recurrent=[]
    for gi in np.argsort(recurrence)[::-1]:
        if recurrence[gi]<2: break
        a,b=divmod(int(gi),16);recurrent.append({'gate':f'{CELLS[a]}→{CELLS[b]}','families_top32':int(recurrence[gi]),'family_fraction':q(recurrence[gi]/len(fam_names))})

    # Bootstrap: sample one language per family, align a root, record top-20 gate survival.
    boots=80;survival=np.zeros(256,dtype=int);roots=[]
    for _ in range(boots):
        ix=[R.choice(fam_ix[f]) for f in fam_names]
        rr,_=align_root(P[ix],iterations=10);roots.append(rr);survival[np.argsort(rr)[::-1][:20]]+=1
    bmean=np.mean(roots,axis=0);bmean/=bmean.sum() or 1
    stable=[]
    for gi in np.argsort(survival)[::-1][:30]:
        a,b=divmod(int(gi),16);stable.append({'gate':f'{CELLS[a]}→{CELLS[b]}','top20_bootstrap_fraction':q(survival[gi]/boots),'mean_mass':q(bmean[gi])})

    # Compare roots to one another.
    v1=np.zeros(256)
    for x in res['latent_root']['top_gates']: v1[x['index']]=x['mass']
    # v1 is sparse because v1 JSON does not store full root; compare robustly using top-gate overlap instead.
    old_top={x['gate'] for x in res['latent_root']['top_gates'][:20]};fb_top={x['gate'] for x in fb['top_gates'][:20]};e_top={x['gate'] for x in early['top_gates'][:20]}
    comparison={'all_vs_family_balanced_top20_overlap':len(old_top&fb_top),'all_vs_early_top20_overlap':len(old_top&e_top),'family_balanced_vs_early_top20_overlap':len(fb_top&e_top)}

    res['version']=2
    res['refined_roots']={'family_balanced':fb,'early_attested_subset':early,'family_recurrent_gate_core':recurrent[:50],'bootstrap_stability':stable,'root_comparison':comparison}
    OUTJ.write_text(json.dumps(res,indent=2,ensure_ascii=False))

    text=OUTM.read_text()
    add=['','## Refinement: can the root survive family imbalance?','',f"The family-balanced reconstruction gives each of **{len(fam_names)} named PHOIBLE families one vote**, rather than allowing large families to dominate the root.",'',f"- Family-balanced entropy: **{fb['entropy_bits']:.3f} bits** ({fb['effective_gates']:.1f} effective gates)",f"- Top-20 overlap with the all-language root: **{comparison['all_vs_family_balanced_top20_overlap']}/20**",'',"Family-balanced top gates:",'']+[f"- {x['gate']}: {x['mass']:.5f}" for x in fb['top_gates'][:15]]
    add += ['','## Refinement: older/early-labelled subset','',f"The benchmark contains **{len(early_ix)}** records explicitly labelled Ancient/Old/Middle/Classical or selected early-attested languages. This is not a chronological phylogeny; it is a bias check using the labels available in WikiPron.",'',f"- Early-subset entropy: **{early['entropy_bits']:.3f} bits**",f"- Top-20 overlap with the all-language root: **{comparison['all_vs_early_top20_overlap']}/20",'',"Early-subset top gates:",'']+[f"- {x['gate']}: {x['mass']:.5f}" for x in early['top_gates'][:15]]
    add += ['','## Bootstrap-stable root gates','',"Each bootstrap chooses one language from every named family, reconstructs a root, and records which gates remain in the top 20. High survival means the inferred root feature is not being carried by one oversized family.",'']+[f"- {x['gate']}: top-20 in {x['top20_bootstrap_fraction']:.1%} of runs; mean mass {x['mean_mass']:.5f}" for x in stable[:15]]
    add += ['','## Recurrent family-level gates','']+[f"- {x['gate']}: top-32 in {x['families_top32']}/{len(fam_names)} families ({x['family_fraction']:.1%})" for x in recurrent[:15]]
    OUTM.write_text(text+'\n'+'\n'.join(add))
    print(json.dumps({'family_balanced_top':fb['top_gates'][:10],'early_top':early['top_gates'][:10],'bootstrap':stable[:10],'comparison':comparison,'early_count':len(early_ix)},indent=2))

if __name__=='__main__': main()
