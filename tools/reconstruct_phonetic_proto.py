#!/usr/bin/env python3
"""Recursive phonetic proto-language reconstruction experiment.

Uses the existing frozen 348-language WikiPron/PHOIBLE benchmark profiles.
The goal is deliberately narrower than reconstructing a historical vocabulary:
we ask whether a small, explicit operator vocabulary can align descendant
256-gate phonetic fingerprints into a compact latent ancestor and whether that
operator-aware geometry recovers known genealogical structure better than the
identity-only bridge.

Outputs:
  data/phonetic-proto-reconstruction.json
  data/phonetic-proto-reconstruction.md
"""
from __future__ import annotations

import json, math, random
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/phonetic-benchmark-summary.json"
OUTJ = ROOT / "data/phonetic-proto-reconstruction.json"
OUTM = ROOT / "data/phonetic-proto-reconstruction.md"
RNG = random.Random(137)

CELLS = ["A1","A2","A3","A4","B1","B2","B3","B4","C1","C2","C3","C4","D1","D2","D3","D4"]
EPS = 1e-15


def q(x, n=6):
    return None if x is None else round(float(x), n)


def state_map(place=False, manner=False):
    # Existing bridge columns: 1 labial, 2 coronal, 3 dorsal, 4 other.
    # Exploratory place reflection swaps labial <-> dorsal; coronal/other stay fixed.
    cm = [2, 1, 0, 3] if place else [0, 1, 2, 3]
    # Existing bridge rows: A vowels, B sonorants, C continuants, D stops/obstruents.
    # Exploratory manner reflection swaps B <-> D; A/C remain fixed.
    rm = [0, 3, 2, 1] if manner else [0, 1, 2, 3]
    return [rm[i // 4] * 4 + cm[i % 4] for i in range(16)]


def gate_index_map(place=False, manner=False, reverse=False):
    sm = state_map(place, manner)
    out = np.empty(256, dtype=np.int64)
    for a in range(16):
        for b in range(16):
            aa, bb = sm[a], sm[b]
            if reverse:
                aa, bb = bb, aa
            out[a * 16 + b] = aa * 16 + bb
    return out


def make_operators():
    specs = [
        ("identity", False, False, False, "No transformation"),
        ("reverse", False, False, True, "Reverse gate direction / temporal trajectory"),
        ("place", True, False, False, "Reflect bridge place: labial ↔ dorsal"),
        ("reverse+place", True, False, True, "Reverse trajectory plus place reflection"),
        ("manner", False, True, False, "Reflect broad manner: sonorant ↔ stop/obstruent"),
        ("reverse+manner", False, True, True, "Reverse trajectory plus manner reflection"),
        ("place+manner", True, True, False, "Reflect place and manner"),
        ("reverse+place+manner", True, True, True, "Reverse trajectory plus place and manner reflection"),
    ]
    return [{"id":a,"place":b,"manner":c,"reverse":d,"description":e,"index_map":gate_index_map(b,c,d)} for a,b,c,d,e in specs]


def transform_profiles(P, idx_map):
    # idx_map says where each original gate moves. Scatter into transformed frame.
    T = np.zeros_like(P)
    T[:, idx_map] = P
    return T


def unit_rows(A):
    n = np.linalg.norm(A, axis=1, keepdims=True)
    return A / np.where(n > 0, n, 1.0)


def entropy(v):
    x = v[v > 0]
    return float(-(x * np.log2(x)).sum()) if len(x) else 0.0


def family_nn_accuracy(sim, families):
    fam_counts = Counter(families)
    eligible = [i for i,f in enumerate(families) if f and f != "Unclassified" and fam_counts[f] >= 2]
    hit = 0
    for i in eligible:
        row = sim[i].copy(); row[i] = -1
        j = int(np.argmax(row))
        hit += families[i] == families[j]
    return hit / len(eligible) if eligible else 0.0, len(eligible)


def pair_mask(families):
    n = len(families); same=[]; cross=[]
    for i in range(n):
        for j in range(i+1,n):
            a,b=families[i],families[j]
            if not a or not b or a=="Unclassified" or b=="Unclassified": continue
            (same if a==b else cross).append((i,j))
    return same,cross


def mean_pairs(M, pairs):
    return float(np.mean([M[i,j] for i,j in pairs])) if pairs else 0.0


def random_state_operator():
    sm=list(range(16)); RNG.shuffle(sm)
    idx=np.empty(256,dtype=np.int64)
    for a in range(16):
        for b in range(16): idx[a*16+b]=sm[a]*16+sm[b]
    return idx


def recursive_split(indices, dist, names, families, depth=0, max_depth=4, min_size=5, node_id="R"):
    inds=list(indices); fam=Counter(families[i] for i in inds if families[i] and families[i]!="Unclassified")
    node={"id":node_id,"depth":depth,"size":len(inds),"dominant_family":fam.most_common(1)[0][0] if fam else "Unclassified",
          "family_purity":(fam.most_common(1)[0][1]/len(inds)) if fam else 0.0,
          "families":fam.most_common(8),"examples":[names[i] for i in inds[:8]]}
    if depth>=max_depth or len(inds)<2*min_size:
        node["members"]=[names[i] for i in inds]
        return node
    sub=dist[np.ix_(inds,inds)]
    ai,bi=np.unravel_index(int(np.argmax(sub)),sub.shape); sa,sb=inds[ai],inds[bi]
    left=[];right=[]
    for i in inds:
        (left if dist[i,sa] <= dist[i,sb] else right).append(i)
    if len(left)<min_size or len(right)<min_size:
        node["members"]=[names[i] for i in inds]
        return node
    cross=float(np.mean(dist[np.ix_(left,right)])); within=[]
    if len(left)>1: within.append(float(np.mean(dist[np.ix_(left,left)][np.triu_indices(len(left),1)])))
    if len(right)>1: within.append(float(np.mean(dist[np.ix_(right,right)][np.triu_indices(len(right),1)])))
    node["split"]={"seed_left":names[sa],"seed_right":names[sb],"between_distance":q(cross),"mean_within_distance":q(np.mean(within) if within else 0),"separation":q(cross-(np.mean(within) if within else 0))}
    node["children"]=[recursive_split(left,dist,names,families,depth+1,max_depth,min_size,node_id+"0"),recursive_split(right,dist,names,families,depth+1,max_depth,min_size,node_id+"1")]
    return node


def historical_pairs(names):
    candidates=[
        ("Ancient Greek (to 1453)","Modern Greek (1453-)"),
        ("Old English (ca. 450-1100)","Middle English (1100-1500)"),
        ("Middle English (1100-1500)","English"),
        ("Old Spanish","Spanish"),
        ("Old High German (ca. 750-1050)","German"),
        ("Middle Dutch (ca. 1050-1350)","Dutch"),
        ("Old Russian","Russian"),
        ("Old French (842-ca. 1400)","French"),
        ("Old Irish (to 900)","Middle Irish (900-1200)"),
        ("Middle Irish (900-1200)","Irish"),
    ]
    ix={n:i for i,n in enumerate(names)}
    return [(a,b,ix[a],ix[b]) for a,b in candidates if a in ix and b in ix]


def main():
    data=json.loads(SRC.read_text(encoding="utf-8"))
    langs=data["languages"]
    names=[r["name"] for r in langs]; isos=[r["iso"] for r in langs]; families=[r.get("family","Unclassified") for r in langs]
    counts=np.array([r["sample_counts"] for r in langs],dtype=np.float64)
    row_sums=counts.sum(axis=1,keepdims=True)
    P=counts/np.where(row_sums>0,row_sums,1)
    U=unit_rows(P)
    ops=make_operators(); transformed=[]; sims=[]
    for op in ops:
        T=transform_profiles(P,op["index_map"]); transformed.append(T)
        sims.append(U @ unit_rows(T).T)
    S=np.stack(sims,axis=0)
    identity=S[0]
    best=S.max(axis=0)
    best_op=S.argmax(axis=0)
    np.fill_diagonal(best,1.0)

    same,cross=pair_mask(families)
    improvement=best-identity
    raw_acc,n_eval=family_nn_accuracy(identity,families)
    op_acc,_=family_nn_accuracy(best,families)

    # Structured operators vs matched random state-permutation controls.
    structured_same_gain=mean_pairs(improvement,same); structured_cross_gain=mean_pairs(improvement,cross)
    random_same_gains=[]; random_nn=[]
    for _ in range(12):
        best_r=identity.copy()
        for __ in range(7):
            idx=random_state_operator(); T=transform_profiles(P,idx)
            best_r=np.maximum(best_r,U @ unit_rows(T).T)
        gain=best_r-identity
        random_same_gains.append(mean_pairs(gain,same))
        random_nn.append(family_nn_accuracy(best_r,families)[0])

    # EM-like latent root: align each language to a shared profile under the finite operator vocabulary.
    root=P.mean(axis=0); root/=root.sum() or 1
    chosen=np.zeros(len(langs),dtype=int)
    for _ in range(20):
        ru=root/(np.linalg.norm(root) or 1)
        aligned=[]; new_choice=[]
        for i in range(len(langs)):
            vals=[]
            for oi,T in enumerate(transformed):
                v=T[i]; vals.append(float(np.dot(ru,v/(np.linalg.norm(v) or 1))))
            oi=int(np.argmax(vals)); new_choice.append(oi); aligned.append(transformed[oi][i])
        new=np.mean(np.array(aligned),axis=0); new/=new.sum() or 1
        delta=float(np.linalg.norm(new-root)); root=new; chosen=np.array(new_choice,dtype=int)
        if delta<1e-10: break

    root_u=root/(np.linalg.norm(root) or 1)
    root_identity=[];root_best=[];root_choice=[]
    for i in range(len(langs)):
        vi=P[i]/(np.linalg.norm(P[i]) or 1); root_identity.append(float(np.dot(root_u,vi)))
        vals=[]
        for oi,T in enumerate(transformed):
            v=T[i]; vals.append(float(np.dot(root_u,v/(np.linalg.norm(v) or 1))))
        oi=int(np.argmax(vals)); root_choice.append(oi);root_best.append(vals[oi])
    closest=sorted(range(len(langs)),key=lambda i:-root_best[i])[:25]

    top_idx=np.argsort(root)[::-1][:32]
    top_gates=[]
    for gi in top_idx:
        a,b=divmod(int(gi),16)
        top_gates.append({"index":int(gi),"gate":f"{CELLS[a]}→{CELLS[b]}","mass":q(root[gi]),"source":CELLS[a],"target":CELLS[b]})

    outgoing=root.reshape(16,16).sum(axis=1); incoming=root.reshape(16,16).sum(axis=0)
    state_profile=[{"cell":CELLS[i],"outgoing":q(outgoing[i]),"incoming":q(incoming[i]),"balance":q(incoming[i]-outgoing[i])} for i in range(16)]

    op_counts=Counter(ops[i]["id"] for i in root_choice)
    # Recursive map uses operator-aware distance, but records that this is a descriptive split, not a historical tree.
    dist=np.clip(1-best,0,2)
    tree=recursive_split(range(len(langs)),dist,names,families)

    hist=[]
    for a,b,i,j in historical_pairs(names):
        oi=int(best_op[i,j]); hist.append({"older":a,"newer":b,"identity_similarity":q(identity[i,j]),"best_similarity":q(best[i,j]),"gain":q(best[i,j]-identity[i,j]),"best_operator":ops[oi]["id"]})

    result={
      "version":1,
      "source":{"benchmark":str(SRC.relative_to(ROOT)),"languages":len(langs),"profile":"normalized 256 directed-gate frequency vector","pins":data.get("pins",{})},
      "research_boundary":"This reconstructs a latent phonetic/gate-state prototype, not a recoverable original vocabulary, grammar, script, or proof of deliberate ancient engineering.",
      "operators":[{k:v for k,v in o.items() if k!="index_map"} for o in ops],
      "genealogy_test":{
        "eligible_languages":n_eval,"identity_nearest_neighbor_family_accuracy":q(raw_acc),"operator_aware_nearest_neighbor_family_accuracy":q(op_acc),"change":q(op_acc-raw_acc),
        "same_family_mean_operator_gain":q(structured_same_gain),"cross_family_mean_operator_gain":q(structured_cross_gain),
        "structured_gain_advantage_same_minus_cross":q(structured_same_gain-structured_cross_gain),
        "random_control_same_family_gain_mean":q(np.mean(random_same_gains)),"random_control_same_family_gain_sd":q(np.std(random_same_gains)),
        "random_control_nn_accuracy_mean":q(np.mean(random_nn)),"random_control_nn_accuracy_sd":q(np.std(random_nn))
      },
      "latent_root":{
        "entropy_bits":q(entropy(root)),"effective_gates":q(2**entropy(root)),"mean_identity_similarity":q(np.mean(root_identity)),"mean_operator_aligned_similarity":q(np.mean(root_best)),"alignment_gain":q(np.mean(root_best)-np.mean(root_identity)),
        "operator_usage":dict(op_counts),"top_gates":top_gates,"state_profile":state_profile,
        "closest_language_proxies":[{"iso":isos[i],"name":names[i],"family":families[i],"aligned_similarity":q(root_best[i]),"identity_similarity":q(root_identity[i]),"operator":ops[root_choice[i]]["id"]} for i in closest]
      },
      "diachronic_checks":hist,
      "recursive_operator_map":tree
    }
    OUTJ.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")

    g=result["genealogy_test"]; r=result["latent_root"]
    lines=[
      "# Recursive phonetic proto-language reconstruction", "",
      "This experiment uses the frozen 348-language WikiPron/PHOIBLE 256-gate profiles already published by the phonetic bridge.", "",
      "## What is being reconstructed", "",
      "The result is a **latent phonetic/gate-state prototype**: a probability distribution over the 256 directed bridge gates after allowing a small fixed vocabulary of reflections. It is **not** a reconstructed historical word list, grammar, script, or proof that an ancient device deliberately created languages.", "",
      "## Does the finite operator vocabulary help recover genealogy?", "",
      f"- Identity-only nearest-neighbour family accuracy: **{g['identity_nearest_neighbor_family_accuracy']:.3f}**", f"- Operator-aware accuracy: **{g['operator_aware_nearest_neighbor_family_accuracy']:.3f}** (Δ {g['change']:+.3f})",
      f"- Mean operator gain, same-family pairs: **{g['same_family_mean_operator_gain']:.4f}**", f"- Mean operator gain, cross-family pairs: **{g['cross_family_mean_operator_gain']:.4f}**",
      f"- Random-permutation control mean same-family gain: **{g['random_control_same_family_gain_mean']:.4f} ± {g['random_control_same_family_gain_sd']:.4f}**", "",
      "## Latent root fingerprint", "",
      f"- Entropy: **{r['entropy_bits']:.3f} bits**", f"- Effective gate count: **{r['effective_gates']:.1f}**", f"- Mean similarity to root without operators: **{r['mean_identity_similarity']:.3f}**", f"- Mean similarity after operator alignment: **{r['mean_operator_aligned_similarity']:.3f}** (gain {r['alignment_gain']:+.3f})", "",
      "Top inferred root gates:", ""
    ]
    lines += [f"- {x['gate']}: {x['mass']:.5f}" for x in top_gates[:20]]
    lines += ["", "Closest language profiles to the latent root (after allowed alignment):", ""]
    lines += [f"- {x['name']} [{x['family']}]: {x['aligned_similarity']:.3f} via {x['operator']}" for x in r["closest_language_proxies"][:15]]
    lines += ["", "## Diachronic checks", ""]
    lines += [f"- {x['older']} → {x['newer']}: identity {x['identity_similarity']:.3f}, best {x['best_similarity']:.3f}, Δ {x['gain']:+.3f}, operator **{x['best_operator']}**" for x in hist]
    lines += ["", "## Interpretation", "", "A useful result requires the structured operators to outperform arbitrary state permutations and ideally improve recovery of known family relationships. If they do not, the finite-operator idea is not supported by this test. The recursive map in the JSON is descriptive and should not be mistaken for an accepted linguistic family tree."]
    OUTM.write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"genealogy_test":g,"latent_root_summary":{k:r[k] for k in ("entropy_bits","effective_gates","mean_identity_similarity","mean_operator_aligned_similarity","alignment_gain")},"diachronic_checks":hist},indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
