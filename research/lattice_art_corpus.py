#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MOTIFS = {
    "mesh": [
        r"\binterlac(?:e|ed|ing)?\b", r"\bknot(?:s|ted|work)?\b", r"\bbraid(?:ed|ing|s)?\b",
        r"\bplait(?:ed|ing|s)?\b", r"\bguilloche\b", r"\blattice\b", r"\bmeander\b",
        r"\bentwin(?:e|ed|ing)\b", r"\bintertw(?:ine|ined|ining)\b"
    ],
    "axis": [
        r"\baxis\b", r"\baxial\b", r"\bpillar\b", r"\bcolumn\b", r"\bstaff\b", r"\brod\b",
        r"\bpole\b", r"\bspear\b", r"\bworld tree\b", r"\btree of life\b", r"\bsacred tree\b"
    ],
    "serpent": [
        r"\bserpent(?:s)?\b", r"\bsnake(?:s)?\b", r"\bdragon(?:s)?\b", r"\bcaduceus\b",
        r"\buraeus\b", r"\bnaga(?:s)?\b", r"\bnāga(?:s)?\b", r"\bophidian\b",
        r"\btwin[- ]tailed\b", r"\btwo[- ]tailed\b", r"\bsiren(?:s)?\b"
    ],
    "enclosure": [
        r"\bcircle\b", r"\bcircular\b", r"\bring(?:s)?\b", r"\broundel(?:s)?\b",
        r"\bmedallion(?:s)?\b", r"\bmandorla\b", r"\bhalo(?:s)?\b", r"\boval\b", r"\benclos(?:e|ed|ure)\b"
    ],
    "four_eight": [
        r"\bfourfold\b", r"\bfour[- ]part\b", r"\bquadripartite\b", r"\bquatrefoil\b",
        r"\boctagon(?:al)?\b", r"\beightfold\b", r"\beight[- ]point(?:ed)?\b", r"\beight[- ]lobed\b"
    ],
    "node": [
        r"\beye(?:s)?\b", r"\bstar(?:s)?\b", r"\brosette(?:s)?\b", r"\bjewel(?:s)?\b",
        r"\bboss(?:es)?\b", r"\bsun\b", r"\bsolar disc\b", r"\bsolar disk\b"
    ],
    "water": [
        r"\bwater\b", r"\briver(?:s)?\b", r"\bsea\b", r"\bocean\b", r"\bwave(?:s)?\b",
        r"\bmarine\b", r"\baquatic\b"
    ],
}

CONTROL_MOTIFS = {
    "bird": [r"\bbird(?:s)?\b", r"\beagle(?:s)?\b"],
    "horse": [r"\bhorse(?:s)?\b", r"\bequestrian\b"],
    "lion": [r"\blion(?:s)?\b"],
    "flower": [r"\bflower(?:s)?\b", r"\bfloral\b"],
    "vessel": [r"\bvessel(?:s)?\b", r"\bcup(?:s)?\b", r"\bbowl(?:s)?\b"],
    "portrait": [r"\bportrait(?:s)?\b"],
}

RX = {k: re.compile("|".join(v), re.I) for k, v in MOTIFS.items()}
CONTROL_RX = {k: re.compile("|".join(v), re.I) for k, v in CONTROL_MOTIFS.items()}
COMPANIONS = ["axis", "serpent", "enclosure", "four_eight", "node", "water"]

CULTURE_GROUPS = [
    ("Ancient Egypt / Coptic", r"\begypt|egyptian|coptic"),
    ("Mesopotamia / Ancient Near East / Iran", r"mesopot|sumer|assyri|babylon|akkad|levant|phoenici|hittite|anatolia|persia|persian|iran|sasan|parth"),
    ("Greek / Roman / Etruscan", r"\bgreek|greece|hellen|roman|\brome\b|etrusc"),
    ("Celtic / Insular / Norse", r"celt|irish|ireland|insular|anglo[- ]saxon|viking|norse|scandin|pict|british isles"),
    ("Byzantine / Eastern Christian", r"byzant|constantinop|eastern christian|armenian|georgian|syriac"),
    ("Islamic world", r"islam|mamluk|ottoman|seljuk|timurid|safavid|umayyad|abbasid|fatimid|mughal"),
    ("South Asia / Himalaya", r"\bindia|indian|nepal|tibet|sri lanka|pakistan|gandhar|\bpala\b|chola|himalay"),
    ("China", r"\bchina|chinese|\bming\b|\bqing\b|\bhan\b|\btang\b|\bsong\b|\byuan\b"),
    ("Japan", r"\bjapan|japanese|\bedo\b|heian|kamakura|muromachi"),
    ("Korea", r"\bkorea|korean|goryeo|joseon"),
    ("Southeast Asia", r"khmer|cambod|thailand|\bthai\b|burma|myanmar|vietnam|java|javan|bali|indonesia|sumatra"),
    ("Mesoamerica", r"\bmaya\b|aztec|mexica|olmec|teotihuac|mesoamer|zapotec|mixtec"),
    ("Andes", r"\bandes|andean|\binca\b|moche|nazca|nasca|chimu|\bwari\b|tiwanaku|peru"),
    ("Sub-Saharan Africa", r"yoruba|benin|kongo|akan|dogon|\bmali\b|ghana|nigeria|ethiop|africa"),
    ("Oceania", r"polynes|melanes|micrones|maori|papua|hawai|oceania"),
    ("Indigenous North America", r"native american|american indian|pueblo|navajo|hopi|inuit|eskimo|plains|northwest coast|haida|tlingit"),
    ("Medieval / early modern Europe", r"medieval|\bfrance\b|french|\bengland\b|english|german|\bitaly\b|italian|\bspain\b|spanish|netherlands|flemish|europe"),
]
CULTURE_RX = [(name, re.compile(pat, re.I)) for name, pat in CULTURE_GROUPS]


def clean(v):
    if v is None:
        return ""
    return str(v).replace("\x00", " ").strip()


def normalize_key(k):
    return re.sub(r"[^a-z0-9]+", "", (k or "").lower())


def int_year(v):
    s = clean(v).replace("−", "-").replace("–", "-")
    m = re.search(r"(?<!\d)-?\d{1,4}(?!\d)", s)
    if not m:
        return None
    try:
        y = int(m.group())
    except ValueError:
        return None
    if y < -10000 or y > 3000:
        return None
    return y


def word_bin(n):
    if n < 25: return "00-24"
    if n < 50: return "25-49"
    if n < 100: return "50-99"
    if n < 200: return "100-199"
    return "200+"


def classify_culture(text):
    for name, rx in CULTURE_RX:
        if rx.search(text):
            return name
    return "Other / unclassified"


def motif_flags(text):
    flags = {k: bool(rx.search(text)) for k, rx in RX.items()}
    controls = {k: bool(rx.search(text)) for k, rx in CONTROL_RX.items()}
    return flags, controls


def met_record(row):
    text_fields = ["Title","Object Name","Culture","Period","Dynasty","Reign","Medium","Classification","Tags","Country","Region","Subregion","Locale","Locus"]
    culture_fields = ["Culture","Period","Dynasty","Country","Region","Subregion","Department"]
    text = " | ".join(clean(row.get(k)) for k in text_fields if clean(row.get(k)))
    ctext = " | ".join(clean(row.get(k)) for k in culture_fields if clean(row.get(k)))
    begin = int_year(row.get("Object Begin Date")); end = int_year(row.get("Object End Date"))
    year = end if end is not None else begin
    oid = clean(row.get("Object ID"))
    url = clean(row.get("Link Resource")) or (f"https://www.metmuseum.org/art/collection/search/{oid}" if oid else "")
    return {
        "source":"The Met", "id":oid, "title":clean(row.get("Title")) or clean(row.get("Object Name")),
        "date":clean(row.get("Object Date")), "year":year, "culture_label":clean(row.get("Culture")) or clean(row.get("Period")),
        "culture_text":ctext, "text":text, "url":url, "image_url":""
    }


def cleveland_record(row):
    keys = {normalize_key(k): k for k in row.keys()}
    def val(*names):
        for n in names:
            k = keys.get(normalize_key(n))
            if k is not None and clean(row.get(k)):
                return clean(row.get(k))
        return ""
    useful_names = ["title","title_in_original_language","series","culture","technique","department","collection","type","description","wall_description","did_you_know","fun_fact","digital_description","tombstone"]
    text = " | ".join(val(n) for n in useful_names if val(n))
    ctext = " | ".join(val(n) for n in ["culture","department","collection","creators"] if val(n))
    begin = int_year(val("creation_date_earliest")); end = int_year(val("creation_date_latest")); year = end if end is not None else begin
    oid = val("id"); accession = val("accession_number")
    url = val("url") or (f"https://www.clevelandart.org/art/{accession}" if accession else "")
    images = val("images")
    image_url = ""
    if images:
        try:
            j = json.loads(images)
            if isinstance(j, dict):
                for size in ("web","print","full"):
                    if isinstance(j.get(size), dict) and j[size].get("url"):
                        image_url = j[size]["url"]; break
        except Exception:
            m = re.search(r"https?://[^\s\"']+\.(?:jpg|jpeg|png|webp)", images, re.I)
            if m: image_url = m.group(0)
    return {
        "source":"Cleveland Museum of Art", "id":oid, "title":val("title"), "date":val("creation_date"), "year":year,
        "culture_label":val("culture"), "culture_text":ctext, "text":text, "url":url, "image_url":image_url
    }


def walters_record(row):
    keys = {normalize_key(k): k for k in row.keys()}
    def val(*names):
        for n in names:
            k = keys.get(normalize_key(n))
            if k is not None and clean(row.get(k)):
                return clean(row.get(k))
        return ""
    text_parts=[]; culture_parts=[]
    for k,v in row.items():
        sv=clean(v)
        if not sv: continue
        nk=normalize_key(k)
        if any(x in nk for x in ["title","name","description","keyword","medium","material","style","period","culture","dynasty","classification","collection"]):
            text_parts.append(sv)
        if any(x in nk for x in ["culture","period","style","collection","location","place","geograph","creator"]):
            culture_parts.append(sv)
    text=" | ".join(text_parts); ctext=" | ".join(culture_parts)
    begin=None; end=None
    for candidate in ["datebegin","beginyear","creationdateearliest","earliestdate","yearbegin"]:
        if candidate in keys: begin=int_year(row.get(keys[candidate])); break
    for candidate in ["dateend","endyear","creationdatelatest","latestdate","yearend"]:
        if candidate in keys: end=int_year(row.get(keys[candidate])); break
    if begin is None and end is None:
        for k,v in row.items():
            if "date" in normalize_key(k):
                y=int_year(v)
                if y is not None: begin=y; end=y; break
    year=end if end is not None else begin
    oid=val("objectid","id"); title=val("title","objectname","name"); date=val("date","displaydate","objectdate")
    accession=val("accessionnumber","accession")
    url=val("url","objecturl")
    if not url and oid: url=f"https://art.thewalters.org/detail/{oid}"
    return {"source":"Walters Art Museum","id":oid or accession,"title":title,"date":date,"year":year,
            "culture_label":val("culture","period"),"culture_text":ctext,"text":text,"url":url,"image_url":""}


def iter_csv(path, converter):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            try:
                rec=converter(row)
            except Exception:
                continue
            yield rec


def enrich(rec):
    text=rec["text"].lower()
    flags, controls=motif_flags(text)
    rec["flags"]=flags; rec["controls"]=controls
    rec["word_count"]=len(re.findall(r"\b\w+\b", text)); rec["word_bin"]=word_bin(rec["word_count"])
    rec["culture_group"]=classify_culture((rec["culture_text"] + " | " + rec["culture_label"]).lower())
    rec["companion_score"]=sum(1 for k in COMPANIONS if flags[k])
    rec["control_score"]=sum(1 for k in CONTROL_MOTIFS if controls[k])
    rec["premodern"]=rec["year"] is not None and -5000 <= rec["year"] <= 1800
    return rec


def ratio(a,b):
    return (a/b) if b else None


def odds_ratio(a,b,c,d):
    # Haldane correction prevents infinities.
    return ((a+0.5)*(d+0.5))/((b+0.5)*(c+0.5))


def prop_test(a,n1,b,n2):
    if n1==0 or n2==0: return None
    p1=a/n1; p2=b/n2; p=(a+b)/(n1+n2)
    se=math.sqrt(max(1e-15,p*(1-p)*(1/n1+1/n2)))
    z=(p1-p2)/se
    # two-sided normal approximation
    pval=math.erfc(abs(z)/math.sqrt(2))
    return {"z":z,"p":pval,"p_mesh":p1,"p_control":p2,"risk_ratio":(p1/p2 if p2 else None),"odds_ratio":odds_ratio(a,n1-a,b,n2-b)}


def match_controls(mesh, nonmesh, seed=137):
    rng=random.Random(seed)
    pools=defaultdict(list)
    wider=defaultdict(list)
    sourcepool=defaultdict(list)
    for r in nonmesh:
        pools[(r["source"],r["culture_group"],r["word_bin"])].append(r)
        wider[(r["source"],r["culture_group"])].append(r)
        sourcepool[r["source"]].append(r)
    for p in list(pools.values())+list(wider.values())+list(sourcepool.values()): rng.shuffle(p)
    idx=Counter(); controls=[]; quality=Counter()
    for r in mesh:
        keys=[("exact",(r["source"],r["culture_group"],r["word_bin"]),pools),
              ("culture",(r["source"],r["culture_group"]),wider),
              ("source",r["source"],sourcepool)]
        chosen=None
        for label,key,d in keys:
            pool=d.get(key,[])
            if pool:
                i=idx[(label,key)]%len(pool); idx[(label,key)]+=1; chosen=pool[i]; quality[label]+=1; break
        if chosen: controls.append(chosen)
    return controls, quality


def summarize(records):
    pre=[r for r in records if r["premodern"]]
    mesh=[r for r in pre if r["flags"]["mesh"]]
    nonmesh=[r for r in pre if not r["flags"]["mesh"]]
    controls, match_quality=match_controls(mesh, nonmesh)
    n1=len(mesh); n2=len(controls)
    comp={}
    for k in COMPANIONS:
        a=sum(r["flags"][k] for r in mesh); b=sum(r["flags"][k] for r in controls)
        comp[k]={"mesh_count":a,"control_count":b,"test":prop_test(a,n1,b,n2)}
    threshold={}
    for t in (1,2,3,4):
        a=sum(r["companion_score"]>=t for r in mesh); b=sum(r["companion_score"]>=t for r in controls)
        threshold[str(t)]={"mesh_count":a,"control_count":b,"test":prop_test(a,n1,b,n2)}
    ctrl={}
    for k in CONTROL_MOTIFS:
        a=sum(r["controls"][k] for r in mesh); b=sum(r["controls"][k] for r in controls)
        ctrl[k]={"mesh_count":a,"control_count":b,"test":prop_test(a,n1,b,n2)}
    culture=[]
    groups=sorted(set(r["culture_group"] for r in pre))
    for g in groups:
        rr=[r for r in pre if r["culture_group"]==g]; mm=[r for r in rr if r["flags"]["mesh"]]
        sources=sorted(set(r["source"] for r in mm if r["companion_score"]>=2))
        culture.append({"culture_group":g,"premodern_n":len(rr),"mesh_n":len(mm),"mesh_rate":len(mm)/len(rr) if rr else 0,
                        "mesh_core_n":sum(r["companion_score"]>=2 for r in mm),
                        "mesh_strong_n":sum(r["companion_score"]>=3 for r in mm),"strong_sources":sources})
    source=[]
    for s in sorted(set(r["source"] for r in records)):
        allr=[r for r in records if r["source"]==s]; pp=[r for r in allr if r["premodern"]]; mm=[r for r in pp if r["flags"]["mesh"]]
        source.append({"source":s,"raw_n":len(allr),"premodern_n":len(pp),"mesh_n":len(mm),"core_n":sum(r["companion_score"]>=2 for r in mm)})
    examples=[]
    priority=[g for g,_ in CULTURE_GROUPS]+["Other / unclassified"]
    for g in priority:
        candidates=[r for r in mesh if r["culture_group"]==g and r["companion_score"]>=2]
        candidates.sort(key=lambda r:(r["companion_score"], bool(r["image_url"]), r["word_count"]), reverse=True)
        for r in candidates[:3]:
            examples.append({"culture_group":g,"source":r["source"],"id":r["id"],"title":r["title"],"date":r["date"],
                             "culture_label":r["culture_label"],"url":r["url"],"image_url":r["image_url"],
                             "companion_score":r["companion_score"],"motifs":[k for k,v in r["flags"].items() if v]})
    return {"raw_n":len(records),"premodern_n":len(pre),"mesh_n":n1,"control_n":n2,"match_quality":dict(match_quality),
            "mean_words_mesh":sum(r["word_count"] for r in mesh)/n1 if n1 else 0,
            "mean_words_control":sum(r["word_count"] for r in controls)/n2 if n2 else 0,
            "companion_results":comp,"threshold_results":threshold,"negative_control_results":ctrl,
            "culture_stats":culture,"source_stats":source,"examples":examples}


def fmt_pct(x): return f"{100*x:.2f}%"
def fmt_num(x): return f"{x:,}"

def make_markdown(res):
    lines=[]
    lines += ["# Cross-cultural lattice-art corpus test", "", "## Corpus", "",
              f"Raw museum records scanned: **{fmt_num(res['raw_n'])}**.",
              f"Strict premodern records with usable dates (<= 1800 CE): **{fmt_num(res['premodern_n'])}**.",
              f"Premodern records carrying a pre-registered mesh/interlace marker: **{fmt_num(res['mesh_n'])}**.",
              f"Matched non-mesh controls: **{fmt_num(res['control_n'])}**.", "",
              "The control match uses the same museum source, broad culture group and catalogue-text length bin where possible. The test is metadata-level: it measures museum cataloguing descriptions/tags, not automated pixel recognition of every image.", "",
              "## Primary enrichment test", "",
              "| Companion family | Mesh prevalence | Matched-control prevalence | Risk ratio | Odds ratio |", "|---|---:|---:|---:|---:|"]
    for k in COMPANIONS:
        d=res['companion_results'][k]; t=d['test'] or {}; p1=t.get('p_mesh',0); p2=t.get('p_control',0)
        rr=t.get('risk_ratio'); orr=t.get('odds_ratio')
        lines.append(f"| {k} | {fmt_pct(p1)} | {fmt_pct(p2)} | {rr:.2f} | {orr:.2f} |" if rr is not None else f"| {k} | {fmt_pct(p1)} | {fmt_pct(p2)} | — | {orr:.2f} |")
    lines += ["", "## Package thresholds", "", "| Companion families on same record | Mesh | Controls | Risk ratio |", "|---|---:|---:|---:|"]
    for tkey in ['1','2','3','4']:
        d=res['threshold_results'][tkey]; t=d['test'] or {}; rr=t.get('risk_ratio')
        lines.append(f"| >= {tkey} | {fmt_pct(t.get('p_mesh',0))} | {fmt_pct(t.get('p_control',0))} | {rr:.2f} |" if rr is not None else f"| >= {tkey} | {fmt_pct(t.get('p_mesh',0))} | {fmt_pct(t.get('p_control',0))} | — |")
    lines += ["", "## Culture coverage", "", "| Culture group | Premodern records | Mesh records | >=2 companion package | >=3 strong package | Institutions with >=2 package hits |", "|---|---:|---:|---:|---:|---:|"]
    for d in sorted(res['culture_stats'], key=lambda x:x['mesh_core_n'], reverse=True):
        if d['premodern_n'] < 25 and d['mesh_n']==0: continue
        lines.append(f"| {d['culture_group']} | {fmt_num(d['premodern_n'])} | {fmt_num(d['mesh_n'])} | {fmt_num(d['mesh_core_n'])} | {fmt_num(d['mesh_strong_n'])} | {len(d['strong_sources'])} |")
    lines += ["", "## Negative-control motifs", "", "If every unrelated subject term rises by a similar amount in mesh records, the result may reflect richer catalogue descriptions rather than the Vardath motif package.", "", "| Control term family | Mesh prevalence | Matched-control prevalence | Risk ratio |", "|---|---:|---:|---:|"]
    for k,d in res['negative_control_results'].items():
        t=d['test'] or {}; rr=t.get('risk_ratio')
        lines.append(f"| {k} | {fmt_pct(t.get('p_mesh',0))} | {fmt_pct(t.get('p_control',0))} | {rr:.2f} |" if rr is not None else f"| {k} | {fmt_pct(t.get('p_mesh',0))} | {fmt_pct(t.get('p_control',0))} | — |")
    lines += ["", "## Candidate examples for visual verification", ""]
    for e in res['examples'][:45]:
        lines.append(f"- **{e['culture_group']} — {e['title'] or e['id']}** ({e['source']}; {e['date'] or 'date not displayed'}): {', '.join(e['motifs'])}. {e['url']}")
    return "\n".join(lines)+"\n"


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--met',required=True); ap.add_argument('--cleveland',required=True); ap.add_argument('--walters',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    records=[]
    for path,conv in [(a.met,met_record),(a.cleveland,cleveland_record),(a.walters,walters_record)]:
        for rec in iter_csv(path,conv): records.append(enrich(rec))
    res=summarize(records)
    (out/'results.json').write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding='utf-8')
    (out/'report.md').write_text(make_markdown(res),encoding='utf-8')
    with open(out/'culture_stats.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['culture_group','premodern_n','mesh_n','mesh_rate','mesh_core_n','mesh_strong_n','strong_sources']); w.writeheader()
        for r in res['culture_stats']:
            rr=dict(r); rr['strong_sources']='; '.join(rr['strong_sources']); w.writerow(rr)
    with open(out/'examples.csv','w',newline='',encoding='utf-8') as f:
        fields=['culture_group','source','id','title','date','culture_label','url','image_url','companion_score','motifs']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for e in res['examples']:
            ee=dict(e); ee['motifs']='; '.join(ee['motifs']); w.writerow(ee)
    print(make_markdown(res))

if __name__=='__main__': main()
