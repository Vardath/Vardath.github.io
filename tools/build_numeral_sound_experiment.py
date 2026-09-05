#!/usr/bin/env python3
"""Build the compact numeral-sound experiment dataset.

Numeral meanings are used as stable semantic anchors. UniNum lexical forms are
NOT treated as universal IPA. Character/form similarity is therefore labelled
as an orthographic/transcription proxy. True phonetic claims remain reserved
for attested historical forms or pronunciation-backed bridge data.
"""
from __future__ import annotations
import csv, io, json, random, unicodedata, urllib.request
from collections import defaultdict
from pathlib import Path

PIN="b9ece9f6048915cf2846bdfa0d5fd4c338620d69"
BASE=f"https://raw.githubusercontent.com/numeralbank/googleuninum/{PIN}/cldf"
OUT=Path("data/phonetic-numeral-sounds.json")
KEEP={str(i) for i in range(0,21)}

def get(name):
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=60) as r:
        return r.read().decode("utf-8")

def rows(name):
    return list(csv.DictReader(io.StringIO(get(name))))

def norm(s):
    s=unicodedata.normalize("NFKD", s or "")
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    return "".join(c for c in s if c.isalpha())

def latinish(s):
    x=norm(s)
    return bool(x) and sum("a" <= c <= "z" for c in x)/len(x) >= .8

def lev(a,b):
    a,b=norm(a),norm(b)
    if not a or not b: return None
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def sim(a,b):
    a,b=norm(a),norm(b)
    if not a or not b: return None
    return 1-lev(a,b)/max(len(a),len(b))

def mean(xs):
    xs=[x for x in xs if x is not None]
    return sum(xs)/len(xs) if xs else None

langs={r["ID"]:r for r in rows("languages.csv")}
forms=[]
for r in rows("forms.csv"):
    p=r.get("Parameter_ID","")
    if p not in KEEP: continue
    l=langs.get(r.get("Language_ID",""))
    if not l: continue
    form=(r.get("Form") or r.get("Value") or "").strip()
    if not form: continue
    forms.append({
        "number":int(p),"form":form,"segments":(r.get("Segments") or "").split(),
        "language_id":l["ID"],"language":l["Name"],"iso":l.get("ISO639P3code","") or "",
        "family":l.get("Family","") or "Unclassified","macroarea":l.get("Macroarea","") or "",
        "script":l.get("Script","") or "","glottocode":l.get("Glottocode","") or "",
        "latin_proxy":latinish(form)
    })

by_num=defaultdict(list)
for x in forms: by_num[x["number"]].append(x)

same_family=[]; cross_family=[]; per_num={}
for n,arr in sorted(by_num.items()):
    sf=[]; cf=[]
    usable=[x for x in arr if x["latin_proxy"] and len(norm(x["form"]))>=2]
    for i,a in enumerate(usable):
        for b in usable[i+1:]:
            s=sim(a["form"],b["form"])
            if a["family"]==b["family"] and a["family"]!="Unclassified":
                sf.append(s); same_family.append(s)
            elif a["family"]!=b["family"]:
                cf.append(s); cross_family.append(s)
    per_num[str(n)]={"forms":len(arr),"latin_proxy_forms":len(usable),"same_family_mean":mean(sf),"cross_family_mean":mean(cf),"same_family_pairs":len(sf),"cross_family_pairs":len(cf)}

rng=random.Random(137)
latin=[x for x in forms if x["latin_proxy"] and len(norm(x["form"]))>=2]
null=[]
for _ in range(50000):
    a,b=rng.sample(latin,2)
    if a["number"]==b["number"] or a["family"]==b["family"]: continue
    null.append(sim(a["form"],b["form"]))

out=[]
for n,arr in sorted(by_num.items()):
    usable=[x for x in arr if x["latin_proxy"] and len(norm(x["form"]))>=2]
    cand=[]
    for i,a in enumerate(usable):
        for b in usable[i+1:]:
            if a["family"]==b["family"]: continue
            s=sim(a["form"],b["form"])
            if s is not None: cand.append((s,a,b))
    for s,a,b in sorted(cand,key=lambda z:z[0],reverse=True)[:5]:
        out.append({"number":n,"similarity":s,"a":{k:a[k] for k in ("form","language","family","iso")},"b":{k:b[k] for k in ("form","language","family","iso")}})

eight_controls=[
 {"from":"*oḱtṓw","to":"oktṓ","status":"green","note":"established Indo-European numeral lineage"},
 {"from":"oktṓ","to":"ógdoos","status":"green","note":"Greek ordinal development; source of ogdo-/ogdoad"},
 {"from":"*oḱtṓw","to":"*ahtō","status":"green","note":"established Germanic branch"},
 {"from":"*ahtō","to":"eahta","status":"green","note":"Germanic to Old English lineage"},
 {"from":"eahta","to":"eight","status":"green","note":"Old English to Modern English lineage"}
]

sfm=mean(same_family); cfm=mean(cross_family); nm=mean(null)
result={
 "generated_from":{"dataset":"UniNum / Google number names CLDF","repo":"numeralbank/googleuninum","commit":PIN,"license":"CC-BY-4.0","forms_total_documented":19877,"languages_total_documented":182,"scope":"integer number names 0-20"},
 "method":{"warning":"UniNum Form/Segments are lexical/transcription data and are not assumed to be universal IPA. Form similarity is a Latin-script proxy only.","normalization":"Unicode NFKD, remove combining marks/nonletters; normalized Levenshtein similarity","null":"different-number, different-family Latin-script form pairs, deterministic seed 137"},
 "summary":{"forms_in_scope":len(forms),"languages_in_scope":len({x['language_id'] for x in forms}),"families_in_scope":len({x['family'] for x in forms}),"same_family_same_number_mean":sfm,"cross_family_same_number_mean":cfm,"cross_family_different_number_null_mean":nm,"same_number_minus_null":None if cfm is None or nm is None else cfm-nm,"same_family_minus_cross_family":None if sfm is None or cfm is None else sfm-cfm,"same_family_pairs":len(same_family),"cross_family_same_number_pairs":len(cross_family),"null_pairs":len(null)},
 "per_number":per_num,"forms":forms,
 "cross_family_lookalikes":sorted(out,key=lambda x:x['similarity'],reverse=True)[:50],
 "eight_controls":eight_controls
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print(json.dumps(result["summary"],indent=2))
