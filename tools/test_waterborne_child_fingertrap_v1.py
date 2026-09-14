#!/usr/bin/env python3
import argparse, csv, json, math, re, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

WORK = Path("research/waterborne_child_fingertrap_v1_work")
RESULTS = Path("research/waterborne_child_fingertrap_v1_results")
UA = "Vardath-Cosmology-Research/1.0 (GitHub Actions; comparative mythology corpus test)"
MAX_CHARS = 5000
WATER_DISTANCE = 900
F1_DISTANCE = 1200
F2_DISTANCE = 1500
F3_DISTANCE = 1800

LANGS = [
    ("en","English",["abandoned child","exposed infant","foundling child"]),
    ("fr","French",["enfant abandonné","enfant exposé","enfant trouvé"]),
    ("de","German",["ausgesetztes Kind","Findelkind","verlassenes Kind"]),
    ("es","Spanish",["niño abandonado","niño expuesto","niño expósito"]),
    ("it","Italian",["bambino abbandonato","neonato esposto","trovatello"]),
    ("pt","Portuguese",["criança abandonada","bebê exposto","enjeitado"]),
    ("nl","Dutch",["verlaten kind","vondeling","te vondeling gelegd kind"]),
    ("pl","Polish",["porzucone dziecko","podrzucone niemowlę","znajda dziecko"]),
    ("cs","Czech",["opuštěné dítě","odložené dítě","nalezenec"]),
    ("ru","Russian",["брошенный ребенок","подкидыш","оставленный младенец"]),
    ("uk","Ukrainian",["покинута дитина","підкинуте немовля","знайда"]),
    ("el","Greek",["εγκαταλελειμμένο παιδί","έκθετο βρέφος","έκθετο παιδί"]),
    ("tr","Turkish",["terk edilmiş çocuk","terk edilmiş bebek","buluntu çocuk"]),
    ("ar","Arabic",["طفل مهجور","رضيع متروك","لقيط"]),
    ("he","Hebrew",["ילד נטוש","תינוק נטוש","אסופי"]),
    ("fa","Persian",["کودک رها شده","نوزاد رها شده","کودک سرراهی"]),
    ("hi","Hindi",["परित्यक्त बच्चा","त्यागा हुआ शिशु","लावारिस बच्चा"]),
    ("bn","Bengali",["পরিত্যক্ত শিশু","ত্যাগ করা শিশু","কুড়িয়ে পাওয়া শিশু"]),
    ("ja","Japanese",["捨て子","捨てられた赤子","拾い子"]),
    ("zh","Chinese",["弃婴","被遗弃的婴儿","弃儿"]),
]

CHILD = ["baby","infant","newborn","child","boy","girl","son","daughter","babe","foundling"]
EXPOSURE = [
    "abandon","abandoned","exposed","exposure","cast out","cast away","cast into",
    "thrown","throw into","set adrift","adrift","left to die","deserted",
    "foundling","unwanted","placed in","put in","laid in"
]
MYTHIC = [
    "myth","mythology","legend","legendary","folklore","folktale","folk tale","fairy tale",
    "epic","saga","scripture","biblical","bible","quran","qur'an","hindu","buddhist",
    "religious tradition","religion","deity","god ","goddess","hero","saint","ancient greek",
    "roman mythology","tradition says","traditional story","oral tradition"
]
WATER = [
    "river","stream","nile","euphrates","tiber","yamuna","yamunā","ganges","ganga","sea","ocean",
    "water","flood","current","canal","lake","waters","downstream","upstream","shore"
]
F1 = [
    "basket","ark","chest","box","casket","cradle","barrel","drum","bag","sack","bamboo","tube",
    "vessel","trough","boat","raft","container","wicker","reed basket","woven","hollow","sealed",
    "enclosed","wrapped","leather bag","coffer","coracle","jar","pot"
]
F2 = [
    "shore","bank","reeds","weir","net","ashore","landing","was found","were found","is found",
    "discovered","caught","rescued","retrieved","recovered","fisherman","fisher","washerwoman",
    "water-drawer","water drawer","temple","palace","household","washed ashore","drifted ashore","picked up"
]
F3 = [
    "adopt","adopted","adoption","foster","raised by","brought up by","named","renamed",
    "orphan","new family","new household","parentage","reborn","rebirth","second birth","reared by",
    "brought up","adoptive","fostered"
]
NEG = [
    "horse","equestrian","sword","spear","weapon","musical instrument","lyre","harp","chair","furniture",
    "garment","clothing","robe"
]


def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"\s+", " ", s)


def positions(text, terms):
    out=[]
    t=norm(text)
    for term in terms:
        q=norm(term)
        start=0
        while True:
            i=t.find(q,start)
            if i<0: break
            out.append(i)
            start=i+max(1,len(q))
    return sorted(set(out))


def near(pa, pb, dist):
    if not pa or not pb: return False
    i=j=0
    while i<len(pa) and j<len(pb):
        d=abs(pa[i]-pb[j])
        if d<=dist: return True
        if pa[i]<pb[j]: i+=1
        else: j+=1
    return False


def any_term(text, terms):
    t=norm(text)
    return any(norm(x) in t for x in terms)


def api_get(lang, params, retries=5):
    base=f"https://{lang}.wikipedia.org/w/api.php"
    params=dict(params)
    params["format"]="json"
    params["utf8"]=1
    url=base+"?"+urllib.parse.urlencode(params, doseq=True)
    req=urllib.request.Request(url, headers={"User-Agent":UA, "Accept":"application/json"})
    delay=1.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if attempt==retries-1: raise
            time.sleep(delay)
            delay*=2


def batches(xs,n):
    for i in range(0,len(xs),n):
        yield xs[i:i+n]


def search_pages(lang, queries):
    found={}
    for q in queries:
        data=api_get(lang,{"action":"query","list":"search","srsearch":q,"srlimit":50,"srnamespace":0})
        for r in data.get("query",{}).get("search",[]):
            pid=r["pageid"]
            if pid not in found:
                found[pid]={"pageid":pid,"title":r["title"],"query_hits":[q]}
            elif q not in found[pid]["query_hits"]:
                found[pid]["query_hits"].append(q)
        time.sleep(0.12)
    return list(found.values())


def resolve_local(lang, pages):
    byid={p["pageid"]:p for p in pages}
    for batch in batches(list(byid),50):
        data=api_get(lang,{
            "action":"query","prop":"pageprops|langlinks",
            "pageids":"|".join(str(x) for x in batch),
            "ppprop":"wikibase_item","lllang":"en","lllimit":1
        })
        for _,p in data.get("query",{}).get("pages",{}).items():
            pid=p.get("pageid")
            if pid not in byid: continue
            byid[pid]["qid"]=p.get("pageprops",{}).get("wikibase_item")
            if lang=="en":
                byid[pid]["en_title"]=p.get("title")
            else:
                lls=p.get("langlinks",[])
                if lls: byid[pid]["en_title"]=lls[0].get("*")
        time.sleep(0.12)
    return list(byid.values())


def fetch_en_extracts(titles):
    out={}
    for batch in batches(titles,25):
        data=api_get("en",{
            "action":"query","prop":"extracts|pageprops","explaintext":1,
            "redirects":1,"titles":"|".join(batch),"ppprop":"wikibase_item"
        })
        for _,p in data.get("query",{}).get("pages",{}).items():
            if "missing" in p: continue
            title=p.get("title","")
            out[title]={
                "title":title,
                "extract":p.get("extract",""),
                "qid":p.get("pageprops",{}).get("wikibase_item")
            }
        time.sleep(0.12)
    return out


def run_shard(i):
    lang,name,queries=LANGS[i]
    pages=resolve_local(lang,search_pages(lang,queries))
    titles=sorted({p.get("en_title") for p in pages if p.get("en_title")})
    en=fetch_en_extracts(titles)
    rows=[]
    for p in pages:
        et=p.get("en_title")
        if not et:
            rows.append({
                "source_lang":lang,"source_language":name,"source_title":p.get("title"),
                "qid":p.get("qid"),"en_title":None,"extract":None
            })
            continue
        e=en.get(et)
        if not e:
            for v in en.values():
                if norm(v["title"])==norm(et): e=v; break
        rows.append({
            "source_lang":lang,"source_language":name,"source_title":p.get("title"),
            "qid":(e or {}).get("qid") or p.get("qid"),
            "en_title":(e or {}).get("title") or et,
            "extract":(e or {}).get("extract","")
        })
    WORK.mkdir(parents=True,exist_ok=True)
    payload={"shard":i,"lang":lang,"language":name,"queries":queries,"discovered":len(pages),"english_linked":sum(bool(r.get("extract")) for r in rows),"rows":rows}
    (WORK/f"shard-{i:02d}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ("shard","lang","language","discovered","english_linked")},ensure_ascii=False))


def classify(rec):
    text=(rec.get("extract") or "")[:MAX_CHARS]
    ntext=norm(text)
    child=positions(ntext,CHILD)
    exposure=positions(ntext,EXPOSURE)
    myth=positions(ntext,MYTHIC)
    water=positions(ntext,WATER)
    eligible=len(ntext)>=250 and bool(child) and bool(myth) and near(child,exposure,900)
    if not eligible:
        group="ineligible"
    else:
        anchors=sorted(set(child+exposure))
        water_near=near(anchors,water,WATER_DISTANCE)
        if water_near: group="waterborne"
        elif not water: group="control"
        else: group="ambiguous"
    anchors1=sorted(set(child+exposure+water))
    f1=near(anchors1,positions(ntext,F1),F1_DISTANCE)
    f2=near(sorted(set(child+water)),positions(ntext,F2),F2_DISTANCE)
    f3=near(child,positions(ntext,F3),F3_DISTANCE)
    neg=any_term(ntext,NEG)
    return {
        "eligible":eligible,"group":group,"f1_carrier":f1,"f2_boundary":f2,"f3_identity":f3,
        "package2":sum([f1,f2,f3])>=2,"package3":f1 and f2 and f3,"negative":neg,
        "length":len(ntext)
    }


def fisher_two_sided(a,b,c,d):
    n1=a+b; n2=c+d; m1=a+c; n=n1+n2
    lo=max(0,m1-n2); hi=min(n1,m1)
    def prob(x):
        return math.comb(n1,x)*math.comb(n2,m1-x)/math.comb(n,m1)
    p0=prob(a)
    return min(1.0,sum(prob(x) for x in range(lo,hi+1) if prob(x)<=p0+1e-15))


def stat(rows, field):
    t=[r for r in rows if r["group"]=="waterborne"]
    c=[r for r in rows if r["group"]=="control"]
    a=sum(bool(r[field]) for r in t); b=len(t)-a
    cc=sum(bool(r[field]) for r in c); d=len(c)-cc
    rt=a/len(t) if t else None
    rc=cc/len(c) if c else None
    if rc==0:
        rr=math.inf if rt and rt>0 else None
    else:
        rr=rt/rc if rt is not None else None
    p=fisher_two_sided(a,b,cc,d) if t and c else None
    return {"target_n":len(t),"control_n":len(c),"target_hits":a,"control_hits":cc,"target_rate":rt,"control_rate":rc,"risk_ratio":rr,"p":p}


def bh(stats, names):
    vals=sorted([(stats[n]["p"],n) for n in names if stats[n]["p"] is not None])
    m=len(vals); qraw={}
    for rank,(p,n) in enumerate(vals,1):
        qraw[n]=p*m/rank
    running=1.0
    for p,n in reversed(vals):
        running=min(running,qraw[n]); qraw[n]=running
    for n in names: stats[n]["q"]=qraw.get(n)


def mh_or(rows, field):
    bins=[(250,749),(750,1499),(1500,2999),(3000,5000)]
    num=den=0.0; used=0
    for lo,hi in bins:
        rr=[r for r in rows if lo<=r["length"]<=hi and r["group"] in ("waterborne","control")]
        t=[r for r in rr if r["group"]=="waterborne"]; c=[r for r in rr if r["group"]=="control"]
        if not t or not c: continue
        a=sum(r[field] for r in t); b=len(t)-a; cc=sum(r[field] for r in c); d=len(c)-cc
        n=a+b+cc+d
        num += a*d/n; den += b*cc/n; used+=1
    return {"odds_ratio":(num/den if den>0 else None),"strata_used":used}


def merge():
    files=sorted(WORK.glob("shard-*.json"))
    if len(files)!=20: raise SystemExit(f"expected 20 shard files, found {len(files)}")
    shard_payloads=[json.loads(p.read_text(encoding="utf-8")) for p in files]
    merged={}; discovery_no_en=0
    for sp in shard_payloads:
        for r in sp["rows"]:
            if not r.get("extract"):
                discovery_no_en+=1; continue
            key=r.get("qid") or ("TITLE:"+norm(r.get("en_title","")))
            if key not in merged:
                merged[key]={
                    "key":key,"qid":r.get("qid"),"en_title":r.get("en_title"),"extract":r.get("extract"),
                    "source_langs":[r["source_lang"]],"source_titles":[r["source_title"]]
                }
            else:
                if r["source_lang"] not in merged[key]["source_langs"]: merged[key]["source_langs"].append(r["source_lang"])
                merged[key]["source_titles"].append(r["source_title"])
    rows=[]
    for rec in merged.values():
        rec.update(classify(rec))
        rec["source_langs"]=";".join(sorted(rec["source_langs"]))
        rec["source_titles"]=";".join(sorted(set(rec["source_titles"])))
        rows.append(rec)
    rows.sort(key=lambda r:(r["group"],r["en_title"] or ""))
    stats={
        "T1_package2":stat(rows,"package2"),
        "T2_carrier":stat(rows,"f1_carrier"),
        "T3_boundary":stat(rows,"f2_boundary"),
        "T4_identity":stat(rows,"f3_identity"),
        "T5_package3":stat(rows,"package3"),
        "T6_negative":stat(rows,"negative"),
    }
    bh(stats,["T2_carrier","T3_boundary","T4_identity","T5_package3"])
    t1=stats["T1_package2"]
    t1["underpowered"]=t1["target_n"]<25 or t1["control_n"]<25
    t1["pass"]=bool(not t1["underpowered"] and t1["risk_ratio"] is not None and t1["risk_ratio"]>=1.5 and t1["p"] is not None and t1["p"]<0.05)
    for n in ["T2_carrier","T3_boundary","T4_identity","T5_package3"]:
        x=stats[n]; x["pass"]=bool(x["risk_ratio"] is not None and x["risk_ratio"]>=1.5 and x.get("q") is not None and x["q"]<0.05)
    n6=stats["T6_negative"]
    n6["confound_flag"]=bool(n6["risk_ratio"] is not None and n6["risk_ratio"]>=1.5 and n6["p"] is not None and n6["p"]<0.05)
    robust={f:mh_or(rows,f) for f in ["package2","f1_carrier","f2_boundary","f3_identity","package3"]}
    eligible=[r for r in rows if r["eligible"]]
    targets=[r for r in rows if r["group"]=="waterborne"]
    controls=[r for r in rows if r["group"]=="control"]
    amb=[r for r in rows if r["group"]=="ambiguous"]
    langs_target=sorted({x for r in targets for x in r["source_langs"].split(";") if x})
    duplicate_multilang=sum(1 for r in rows if ";" in r["source_langs"])
    def score(r): return int(r["f1_carrier"])+int(r["f2_boundary"])+int(r["f3_identity"])
    top_targets=sorted(targets,key=lambda r:(-score(r),r["en_title"]))[:15]
    top_controls=sorted(controls,key=lambda r:(-score(r),r["en_title"]))[:15]
    summary={
        "protocol":"waterborne_child_fingertrap_v1","shards":20,"languages":[x[0] for x in LANGS],
        "raw_discoveries":sum(sp["discovered"] for sp in shard_payloads),
        "english_linked_discoveries":sum(sp["english_linked"] for sp in shard_payloads),
        "discoveries_without_english_extract":discovery_no_en,"unique_english_records":len(rows),
        "eligible_records":len(eligible),"waterborne_targets":len(targets),"nonwater_controls":len(controls),
        "ambiguous_water_records":len(amb),"target_discovery_languages":langs_target,
        "target_discovery_language_count":len(langs_target),"multilanguage_duplicate_records":duplicate_multilang,
        "tests":stats,"robustness_mh":robust,
        "top_targets":[{"title":r["en_title"],"qid":r["qid"],"langs":r["source_langs"],"f1":r["f1_carrier"],"f2":r["f2_boundary"],"f3":r["f3_identity"]} for r in top_targets],
        "top_controls":[{"title":r["en_title"],"qid":r["qid"],"langs":r["source_langs"],"f1":r["f1_carrier"],"f2":r["f2_boundary"],"f3":r["f3_identity"]} for r in top_controls],
    }
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    fields=["key","qid","en_title","source_langs","source_titles","eligible","group","f1_carrier","f2_boundary","f3_identity","package2","package3","negative","length","extract"]
    with (RESULTS/"records.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in fields})
    def fmt(x):
        if x is None: return "NA"
        if isinstance(x,float):
            if math.isinf(x): return "∞"
            return f"{x:.4g}"
        return str(x)
    report=[
        "# Waterborne-child / travelling-fingertrap v1 — 20-shard result","",
        "This report was generated from the preregistered protocol without retuning the language list, search design, coding windows, lexicons or pass thresholds.","",
        "## Corpus",
        f"- 20 language shards completed.",f"- Raw discoveries: **{summary['raw_discoveries']}**.",
        f"- Discoveries with an English extract: **{summary['english_linked_discoveries']}**.",
        f"- Unique deduplicated English-linked records: **{summary['unique_english_records']}**.",
        f"- Eligible mythic/religious exposed-child records: **{summary['eligible_records']}**.",
        f"- Waterborne targets: **{summary['waterborne_targets']}**.",f"- Non-water controls: **{summary['nonwater_controls']}**.",
        f"- Ambiguous water records excluded from confirmatory comparison: **{summary['ambiguous_water_records']}**.",
        f"- Distinct discovery languages contributing waterborne targets: **{summary['target_discovery_language_count']}**.","",
        "## Confirmatory tests","","| test | target | control | RR | p | q | result |","|---|---:|---:|---:|---:|---:|---|",
    ]
    labels=[("T1_package2","T1 >=2 of 3 families"),("T2_carrier","T2 carrier/enclosure"),("T3_boundary","T3 boundary/receiver"),("T4_identity","T4 household/identity/second-birth"),("T5_package3","T5 all 3 families")]
    for key,label in labels:
        x=stats[key]; res="UNDERPOWERED" if key=="T1_package2" and x.get("underpowered") else ("PASS" if x.get("pass") else "FAIL")
        report.append(f"| {label} | {x['target_hits']}/{x['target_n']} | {x['control_hits']}/{x['control_n']} | {fmt(x['risk_ratio'])} | {fmt(x['p'])} | {fmt(x.get('q'))} | **{res}** |")
    x=stats["T6_negative"]
    report += ["",f"Negative-control family: {x['target_hits']}/{x['target_n']} targets vs {x['control_hits']}/{x['control_n']} controls; RR={fmt(x['risk_ratio'])}, p={fmt(x['p'])}. Confound flag: **{'YES' if x['confound_flag'] else 'NO'}**.","","## Length-stratified robustness"]
    for k,v in robust.items(): report.append(f"- {k}: Mantel-Haenszel OR **{fmt(v['odds_ratio'])}** across {v['strata_used']} usable length strata.")
    report += ["","## Highest-scoring waterborne targets"]
    for r in top_targets[:10]: report.append(f"- **{r['en_title']}** — QID {r['qid'] or 'NA'}; discovered via {r['source_langs']}; F1={r['f1_carrier']} F2={r['f2_boundary']} F3={r['f3_identity']}.")
    report += ["","## Highest-scoring non-water controls"]
    for r in top_controls[:10]: report.append(f"- **{r['en_title']}** — QID {r['qid'] or 'NA'}; discovered via {r['source_langs']}; F1={r['f1_carrier']} F2={r['f2_boundary']} F3={r['f3_identity']}.")
    report += ["","## Frozen interpretation rule","","A positive result is evidence for enrichment of the preregistered narrative grammar in this corpus. A null result counts against the strong textual prediction as formulated. Similar enrichment of the unrelated negative-control family is treated as a confound. This v1 does not alter its criteria after seeing the data."]
    (RESULTS/"2026-09-14_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False))


def validate():
    assert len(LANGS)==20
    assert len({x[0] for x in LANGS})==20
    forbidden = WATER + F1 + ["shore","bank","reeds","weir","net","ashore","landing","rescued","retrieved","recovered","foster","adopt","rebirth","second birth"]
    for _,_,qs in LANGS:
        for q in qs:
            nq=norm(q)
            for term in forbidden:
                nt=norm(term)
                if len(nt)>=4 and re.fullmatch(r"[a-z0-9 \-']+",nt) and nt in nq:
                    raise AssertionError(f"forbidden dependent term {term!r} in query {q!r}")
    print(json.dumps({"status":"ok","languages":20,"max_chars":MAX_CHARS,"water_distance":WATER_DISTANCE}))


def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("validate"); sh=sp.add_parser("shard"); sh.add_argument("--id",type=int,required=True); sp.add_parser("merge")
    a=ap.parse_args()
    if a.cmd=="validate": validate()
    elif a.cmd=="shard":
        if not 0<=a.id<20: raise SystemExit("shard id must be 0..19")
        run_shard(a.id)
    else: merge()

if __name__=="__main__": main()
