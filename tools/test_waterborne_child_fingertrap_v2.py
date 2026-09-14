#!/usr/bin/env python3
import argparse, csv, json, math, re, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path("research/waterborne_child_fingertrap_v2")
WORK = Path("research/waterborne_child_fingertrap_v2_work")
RESULTS = Path("research/waterborne_child_fingertrap_v2_results")
UA = "Vardath-Cosmology-Research/2.0 (GitHub Actions; multilingual comparative mythology)"
MAX_CHARS = 5000

LANGS = [
("en","English",["baby river myth","infant river legend","child water mythology","child set adrift legend","baby river religious story"],["exposed child myth","abandoned child legend","foundling mythology","abandoned infant folklore","exposed child religious story"]),
("fr","French",["bébé rivière mythe","nourrisson rivière légende","enfant eau mythologie","enfant à la dérive légende","bébé rivière récit religieux"],["enfant exposé mythe","enfant abandonné légende","enfant trouvé mythologie","nourrisson abandonné folklore","enfant exposé récit religieux"]),
("de","German",["Baby Fluss Mythos","Säugling Fluss Legende","Kind Wasser Mythologie","Kind ausgesetzt Fluss Legende","Baby Fluss religiöse Erzählung"],["ausgesetztes Kind Mythos","verlassenes Kind Legende","Findelkind Mythologie","ausgesetzter Säugling Folklore","ausgesetztes Kind religiöse Erzählung"]),
("es","Spanish",["bebé río mito","infante río leyenda","niño agua mitología","niño a la deriva leyenda","bebé río relato religioso"],["niño expuesto mito","niño abandonado leyenda","expósito mitología","bebé abandonado folclore","niño expuesto relato religioso"]),
("it","Italian",["bambino fiume mito","neonato fiume leggenda","bambino acqua mitologia","bambino alla deriva leggenda","neonato fiume racconto religioso"],["bambino esposto mito","bambino abbandonato leggenda","trovatello mitologia","neonato abbandonato folklore","bambino esposto racconto religioso"]),
("pt","Portuguese",["bebê rio mito","recém-nascido rio lenda","criança água mitologia","criança à deriva lenda","bebê rio história religiosa"],["criança exposta mito","criança abandonada lenda","enjeitado mitologia","bebê abandonado folclore","criança exposta história religiosa"]),
("nl","Dutch",["baby rivier mythe","zuigeling rivier legende","kind water mythologie","kind op drift legende","baby rivier religieus verhaal"],["te vondeling gelegd kind mythe","verlaten kind legende","vondeling mythologie","verlaten baby folklore","te vondeling gelegd kind religieus verhaal"]),
("pl","Polish",["niemowlę rzeka mit","dziecko rzeka legenda","dziecko woda mitologia","dziecko puszczone z nurtem legenda","niemowlę rzeka opowieść religijna"],["porzucone dziecko mit","porzucone dziecko legenda","znajda mitologia","porzucone niemowlę folklor","porzucone dziecko opowieść religijna"]),
("cs","Czech",["dítě řeka mýtus","nemluvně řeka legenda","dítě voda mytologie","dítě unášené proudem legenda","nemluvně řeka náboženský příběh"],["odložené dítě mýtus","opuštěné dítě legenda","nalezenec mytologie","opuštěné nemluvně folklor","odložené dítě náboženský příběh"]),
("ru","Russian",["младенец река миф","ребенок река легенда","ребенок вода мифология","младенец плывет по реке легенда","младенец река религиозный рассказ"],["брошенный ребенок миф","подкидыш легенда","оставленный младенец мифология","брошенный младенец фольклор","брошенный ребенок религиозный рассказ"]),
("uk","Ukrainian",["немовля річка міф","дитина річка легенда","дитина вода міфологія","немовля пливе річкою легенда","немовля річка релігійна оповідь"],["покинута дитина міф","покинута дитина легенда","підкинуте немовля міфологія","покинуте немовля фольклор","покинута дитина релігійна оповідь"]),
("el","Greek",["βρέφος ποτάμι μύθος","μωρό ποτάμι θρύλος","παιδί νερό μυθολογία","παιδί παρασυρμένο ποτάμι θρύλος","βρέφος ποτάμι θρησκευτική ιστορία"],["έκθετο παιδί μύθος","εγκαταλελειμμένο παιδί θρύλος","έκθετο βρέφος μυθολογία","εγκαταλελειμμένο βρέφος λαογραφία","έκθετο παιδί θρησκευτική ιστορία"]),
("tr","Turkish",["bebek nehir mit","bebek nehir efsane","çocuk su mitoloji","çocuk nehirde sürüklenme efsane","bebek nehir dini hikâye"],["terk edilmiş çocuk mit","terk edilmiş çocuk efsane","buluntu çocuk mitoloji","terk edilmiş bebek folklor","terk edilmiş çocuk dini hikâye"]),
("ar","Arabic",["رضيع نهر أسطورة","طفل نهر أسطورة","طفل ماء ميثولوجيا","رضيع يجرفه النهر أسطورة","رضيع نهر قصة دينية"],["طفل مهجور أسطورة","رضيع متروك أسطورة","لقيط ميثولوجيا","طفل مهجور فولكلور","طفل مهجور قصة دينية"]),
("he","Hebrew",["תינוק נהר מיתוס","תינוק נהר אגדה","ילד מים מיתולוגיה","תינוק נסחף בנהר אגדה","תינוק נהר סיפור דתי"],["ילד נטוש מיתוס","תינוק נטוש אגדה","אסופי מיתולוגיה","תינוק נטוש פולקלור","ילד נטוש סיפור דתי"]),
("fa","Persian",["نوزاد رودخانه اسطوره","کودک رودخانه افسانه","کودک آب اسطوره شناسی","نوزاد شناور رودخانه افسانه","نوزاد رودخانه داستان دینی"],["کودک رها شده اسطوره","نوزاد رها شده افسانه","کودک سرراهی اسطوره شناسی","نوزاد رها شده فولکلور","کودک رها شده داستان دینی"]),
("hi","Hindi",["शिशु नदी मिथक","बच्चा नदी कथा","बच्चा पानी पौराणिक कथा","शिशु नदी में बहता कथा","शिशु नदी धार्मिक कथा"],["परित्यक्त बच्चा मिथक","त्यागा हुआ शिशु कथा","लावारिस बच्चा पौराणिक कथा","त्यागा शिशु लोककथा","परित्यक्त बच्चा धार्मिक कथा"]),
("bn","Bengali",["শিশু নদী মিথ","শিশু নদী কিংবদন্তি","শিশু জল পুরাণ","শিশু নদীতে ভাসমান কিংবদন্তি","শিশু নদী ধর্মীয় কাহিনি"],["পরিত্যক্ত শিশু মিথ","ত্যাগ করা শিশু কিংবদন্তি","কুড়িয়ে পাওয়া শিশু পুরাণ","পরিত্যক্ত শিশু লোককথা","পরিত্যক্ত শিশু ধর্মীয় কাহিনি"]),
("ja","Japanese",["赤子 川 神話","赤ん坊 川 伝説","子供 水 神話","赤子 川 流される 伝説","赤子 川 宗教 物語"],["捨て子 神話","捨てられた赤子 伝説","拾い子 神話","捨て子 民話","捨て子 宗教 物語"]),
("zh","Chinese",["婴儿 河 神话","婴儿 河 传说","孩子 水 神话","婴儿 随河漂流 传说","婴儿 河 宗教 故事"],["弃婴 神话","被遗弃的婴儿 传说","弃儿 神话","弃婴 民间故事","弃婴 宗教 故事"]),
]

CHILD = ["baby","infant","newborn","child","boy","girl","son","daughter","babe","foundling","twins","twin"]
EXPOSURE = ["abandon","abandoned","exposed","exposure","cast out","cast away","cast into","thrown","throw into","set adrift","adrift","left to die","deserted","foundling","unwanted","placed in","put in","laid in","sent down","floated","floating","drifted","drifting"]
MYTHIC = ["myth","mythology","legend","legendary","folklore","folktale","folk tale","fairy tale","epic","saga","scripture","biblical","bible","quran","qur'an","torah","vedas","vedic","purana","puranic","mahabharata","ramayana","jataka","buddhist","hindu","religious tradition","religion","deity","god ","goddess","hero","saint","ancient greek","roman mythology","tradition says","traditional story","oral tradition","creation myth"]
WATER = ["river","stream","nile","euphrates","tiber","yamuna","yamunā","ganges","ganga","sea","ocean","water","flood","current","canal","lake","waters","downstream","upstream","shore","bank"]
TRANSPORT = ["set adrift","adrift","cast into","thrown into","put into","placed in","laid in","floated","floating","drifted","drifting","carried by","carried down","sent down","swept away","washed away"]
F1_GEOM = ["basket","wicker","reed basket","woven","weave","reeds","rush basket","papyrus basket","bamboo","tube","tubular","hollow","sealed","enclosed","wrapped","flexible","reopen","ark","chest","box","casket","coffer","cradle","barrel","drum","bag","sack","jar","pot","vessel","trough","coracle"]
F1_STRICT = ["basket","wicker","reed basket","woven","weave","rush basket","papyrus basket","bamboo","tube","tubular","hollow","sealed","enclosed","wrapped","flexible","reopen","coracle"]
F2 = ["shore","bank","reeds","weir","net","ashore","landing","was found","were found","is found","discovered","caught","rescued","retrieved","recovered","fisherman","fisher","washerwoman","water-drawer","water drawer","temple","palace","household","washed ashore","drifted ashore","picked up","found by","rescued by","received by"]
F3 = ["adopt","adopted","adoption","foster","raised by","brought up by","named","renamed","orphan","new family","new household","parentage","reborn","rebirth","second birth","reared by","brought up","adoptive","fostered","became known as","given the name","nursed by","suckled by"]
NEG = ["horse","equestrian","sword","spear","weapon","musical instrument","lyre","harp","chair","furniture","garment","clothing","robe"]
CANONICAL_AUDIT = ["Moses","Sargon of Akkad","Karna","Romulus and Remus","Danaë","Perseus"]

def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"\s+", " ", s)

def positions(text, terms):
    out=[]; t=norm(text)
    for term in terms:
        q=norm(term)
        if re.fullmatch(r"[a-z0-9'-]+", q) and len(q)<=4:
            pat=re.compile(r"(?<![a-z0-9])"+re.escape(q)+r"(?![a-z0-9])")
            out.extend(m.start() for m in pat.finditer(t))
        else:
            start=0
            while True:
                i=t.find(q,start)
                if i<0: break
                out.append(i); start=i+max(1,len(q))
    return sorted(set(out))

def near(pa,pb,dist):
    if not pa or not pb: return False
    i=j=0
    while i<len(pa) and j<len(pb):
        d=abs(pa[i]-pb[j])
        if d<=dist: return True
        if pa[i]<pb[j]: i+=1
        else: j+=1
    return False

def api_get(base, params, retries=10):
    params=dict(params); params["format"]="json"; params["utf8"]=1
    url=base+"?"+urllib.parse.urlencode(params,doseq=True)
    delay=8.0
    for attempt in range(retries):
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if attempt==retries-1: raise
            wait=delay
            if e.code==429 and e.headers:
                try: wait=max(delay,float(e.headers.get("Retry-After") or delay))
                except Exception: pass
            print(f"HTTP {getattr(e,'code','?')} retry in {wait:.1f}s",flush=True)
            time.sleep(wait); delay=min(delay*2,120)
        except Exception:
            if attempt==retries-1: raise
            time.sleep(delay); delay=min(delay*2,120)

def wiki_get(lang, params): return api_get(f"https://{lang}.wikipedia.org/w/api.php",params)
def wd_get(params): return api_get("https://www.wikidata.org/w/api.php",params)
def batches(xs,n):
    for i in range(0,len(xs),n): yield xs[i:i+n]

def search_pages(lang, queries, source_group):
    found={}
    for q in queries:
        data=wiki_get(lang,{"action":"query","list":"search","srsearch":q,"srlimit":40,"srnamespace":0})
        for r in data.get("query",{}).get("search",[]):
            pid=r["pageid"]
            rec=found.setdefault(pid,{"pageid":pid,"title":r["title"],"query_hits":[],"discovery_groups":[]})
            if q not in rec["query_hits"]: rec["query_hits"].append(q)
            if source_group not in rec["discovery_groups"]: rec["discovery_groups"].append(source_group)
        time.sleep(0.35)
    return found

def resolve_pages(lang, pages):
    byid={pid:dict(rec) for pid,rec in pages.items()}
    for batch in batches(list(byid),50):
        data=wiki_get(lang,{"action":"query","prop":"pageprops","pageids":"|".join(map(str,batch)),"ppprop":"wikibase_item"})
        for p in data.get("query",{}).get("pages",{}).values():
            pid=p.get("pageid")
            if pid in byid:
                byid[pid]["qid"]=p.get("pageprops",{}).get("wikibase_item")
                if lang=="en": byid[pid]["en_title"]=p.get("title") or byid[pid]["title"]
        time.sleep(0.35)
    if lang!="en":
        qids=sorted({r.get("qid") for r in byid.values() if r.get("qid")})
        en_by_qid={}
        for batch in batches(qids,50):
            data=wd_get({"action":"wbgetentities","ids":"|".join(batch),"props":"sitelinks","sitefilter":"enwiki"})
            for qid,e in data.get("entities",{}).items():
                title=e.get("sitelinks",{}).get("enwiki",{}).get("title")
                if title: en_by_qid[qid]=title
            time.sleep(0.45)
        for r in byid.values():
            if r.get("qid") in en_by_qid: r["en_title"]=en_by_qid[r["qid"]]
    return list(byid.values())

def run_shard(i):
    lang,name,tq,cq=LANGS[i]
    found=search_pages(lang,tq,"water_search")
    controls=search_pages(lang,cq,"control_search")
    for pid,rec in controls.items():
        if pid not in found: found[pid]=rec
        else:
            for q in rec["query_hits"]:
                if q not in found[pid]["query_hits"]: found[pid]["query_hits"].append(q)
            for g in rec["discovery_groups"]:
                if g not in found[pid]["discovery_groups"]: found[pid]["discovery_groups"].append(g)
    rows=resolve_pages(lang,found)
    WORK.mkdir(parents=True,exist_ok=True)
    payload={"shard":i,"lang":lang,"language":name,"target_queries":tq,"control_queries":cq,"discovered":len(rows),"english_mapped":sum(bool(r.get("en_title")) for r in rows),"rows":rows}
    (WORK/f"shard-{i:02d}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ("shard","lang","language","discovered","english_mapped")},ensure_ascii=False),flush=True)

def fetch_extract(title):
    data=wiki_get("en",{"action":"query","prop":"extracts|pageprops","explaintext":1,"exlimit":1,"redirects":1,"titles":title,"ppprop":"wikibase_item"})
    for p in data.get("query",{}).get("pages",{}).values():
        if "missing" in p: continue
        text=(p.get("extract") or "")[:MAX_CHARS]
        if not text: continue
        return {"title":p.get("title",title),"extract":text,"qid":p.get("pageprops",{}).get("wikibase_item")}
    return None

def classify(rec):
    t=norm(rec.get("extract") or "")
    child=positions(t,CHILD); exp=positions(t,EXPOSURE); myth=positions(t,MYTHIC); water=positions(t,WATER); trans=positions(t,TRANSPORT)
    eligible=len(t)>=250 and bool(child) and bool(myth) and near(child,exp,1000)
    anchors=sorted(set(child+exp)); water_near=near(anchors,water,1000)
    transport_near=near(sorted(set(child+water)),trans,1400) or near(exp,water,1200)
    if not eligible: group="ineligible"
    elif water_near and transport_near: group="waterborne"
    elif not water: group="control"
    else: group="ambiguous"
    f1=near(sorted(set(child+exp+water)),positions(t,F1_GEOM),1400)
    f1s=near(sorted(set(child+exp+water)),positions(t,F1_STRICT),1400)
    f2=near(sorted(set(child+water)),positions(t,F2),1700)
    f3=near(child,positions(t,F3),1900)
    neg=bool(positions(t,NEG))
    return {"eligible":eligible,"group":group,"f1_enclosure":f1,"f1_strict_geometry":f1s,"f2_boundary":f2,"f3_identity":f3,"package2":sum([f1s,f2,f3])>=2,"package3":f1s and f2 and f3,"negative":neg,"length":len(t)}

def fisher_two_sided(a,b,c,d):
    n1=a+b; n2=c+d; m1=a+c; n=n1+n2
    lo=max(0,m1-n2); hi=min(n1,m1)
    def prob(x): return math.comb(n1,x)*math.comb(n2,m1-x)/math.comb(n,m1)
    p0=prob(a)
    return min(1.0,sum(prob(x) for x in range(lo,hi+1) if prob(x)<=p0+1e-15))

def stat(rows,field):
    t=[r for r in rows if r["group"]=="waterborne"]; c=[r for r in rows if r["group"]=="control"]
    a=sum(bool(r[field]) for r in t); b=len(t)-a; cc=sum(bool(r[field]) for r in c); d=len(c)-cc
    rt=a/len(t) if t else None; rc=cc/len(c) if c else None
    if not t or not c: rr=None
    elif rc==0: rr="Infinity" if rt and rt>0 else None
    else: rr=rt/rc
    p=fisher_two_sided(a,b,cc,d) if t and c else None
    return {"target_n":len(t),"control_n":len(c),"target_hits":a,"control_hits":cc,"target_rate":rt,"control_rate":rc,"risk_ratio":rr,"p":p}

def rr_at_least(rr, threshold): return rr=="Infinity" or (isinstance(rr,(int,float)) and rr>=threshold)

def bh(stats,names):
    vals=sorted([(stats[n]["p"],n) for n in names if stats[n]["p"] is not None]); m=len(vals); raw={}
    for rank,(p,n) in enumerate(vals,1): raw[n]=p*m/rank
    running=1.0
    for p,n in reversed(vals): running=min(running,raw[n]); raw[n]=running
    for n in names: stats[n]["q"]=raw.get(n)

def merge():
    paths=sorted(WORK.glob("shard-*.json"))
    if len(paths)!=20: raise SystemExit(f"need 20 shard files, found {len(paths)}")
    payloads=[json.loads(p.read_text(encoding="utf-8")) for p in paths]
    bykey={}
    for sh in payloads:
        for r in sh["rows"]:
            title=r.get("en_title")
            if not title: continue
            key=("q",r.get("qid")) if r.get("qid") else ("t",norm(title))
            out=bykey.setdefault(key,{"en_title":title,"qid":r.get("qid"),"source_langs":set(),"source_titles":set(),"discovery_groups":set()})
            out["source_langs"].add(sh["lang"]); out["source_titles"].add(r.get("title") or ""); out["discovery_groups"].update(r.get("discovery_groups") or [])
    print(json.dumps({"unique_english_candidates":len(bykey)}),flush=True)
    records=[]
    for idx,(key,r) in enumerate(bykey.items(),1):
        e=fetch_extract(r["en_title"])
        if not e: continue
        row={"title":e["title"],"qid":e.get("qid") or r.get("qid"),"extract":e["extract"],"source_langs":";".join(sorted(r["source_langs"])),"source_titles":" | ".join(sorted(r["source_titles"])),"discovery_groups":";".join(sorted(r["discovery_groups"]))}
        row.update(classify(row)); records.append(row)
        if idx%25==0: print(json.dumps({"extract_progress":idx,"records":len(records)}),flush=True)
        time.sleep(0.35)
    tests={"T1_package2":stat(records,"package2"),"T2_strict_geometry":stat(records,"f1_strict_geometry"),"T3_boundary":stat(records,"f2_boundary"),"T4_identity":stat(records,"f3_identity"),"T5_package3":stat(records,"package3"),"T6_negative":stat(records,"negative"),"descriptive_any_enclosure":stat(records,"f1_enclosure")}
    bh(tests,["T2_strict_geometry","T3_boundary","T4_identity","T5_package3"])
    t1=tests["T1_package2"]; t1["underpowered"]=t1["target_n"]<25 or t1["control_n"]<25
    t1["pass"]=bool(not t1["underpowered"] and rr_at_least(t1["risk_ratio"],1.5) and t1["p"] is not None and t1["p"]<0.05)
    for n in ["T2_strict_geometry","T3_boundary","T4_identity","T5_package3"]:
        s=tests[n]; s["pass"]=bool(rr_at_least(s["risk_ratio"],1.5) and s.get("q") is not None and s["q"]<0.05)
    n=tests["T6_negative"]; n["confound_flag"]=bool(rr_at_least(n["risk_ratio"],1.5) and n["p"] is not None and n["p"]<0.05)
    titles={norm(r["title"]):r["title"] for r in records}
    audit={x:any(norm(x)==k or norm(x) in k or k in norm(x) for k in titles) for x in CANONICAL_AUDIT}
    summary={"protocol":"waterborne_child_fingertrap_v2","shards":20,"raw_discoveries":sum(p["discovered"] for p in payloads),"english_mapped_occurrences":sum(p["english_mapped"] for p in payloads),"unique_english_candidates":len(bykey),"unique_english_records":len(records),"eligible_records":sum(r["eligible"] for r in records),"waterborne_targets":sum(r["group"]=="waterborne" for r in records),"nonwater_controls":sum(r["group"]=="control" for r in records),"ambiguous_water_records":sum(r["group"]=="ambiguous" for r in records),"target_discovery_languages":sorted({lg for r in records if r["group"]=="waterborne" for lg in r["source_langs"].split(";") if lg}),"canonical_retrieval_audit":audit,"tests":tests,"top_targets":[{k:r[k] for k in ("title","qid","source_langs","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3")} for r in records if r["group"]=="waterborne"][:40],"top_controls":[{k:r[k] for k in ("title","qid","source_langs","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3")} for r in records if r["group"]=="control"][:40]}
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    fields=["title","qid","source_langs","source_titles","discovery_groups","eligible","group","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3","negative","length"]
    with (RESULTS/"records.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in records: w.writerow({k:r.get(k) for k in fields})
    report=["# Waterborne-child travelling-fingertrap v2 result","",f"- Raw multilingual discoveries: {summary['raw_discoveries']}",f"- English-mapped occurrences: {summary['english_mapped_occurrences']}",f"- Unique English candidates: {summary['unique_english_candidates']}",f"- Eligible mythic/exposed-child records: {summary['eligible_records']}",f"- Waterborne targets: {summary['waterborne_targets']}",f"- Non-water controls: {summary['nonwater_controls']}",f"- Ambiguous-water exclusions: {summary['ambiguous_water_records']}","","## Canonical retrieval audit",""]
    report += [f"- {k}: {'FOUND' if v else 'not found'}" for k,v in audit.items()]
    report += ["","## Confirmatory tests",""]
    for k,v in tests.items(): report.append(f"- **{k}**: `{json.dumps(v,ensure_ascii=False,default=str)}`")
    (RESULTS/"report.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str),flush=True)

def validate():
    assert len(LANGS)==20
    assert all(len(lang[2])==5 and len(lang[3])==5 for lang in LANGS)
    forbidden=[norm(x) for x in F1_GEOM+F2+F3]
    for code,name,tq,cq in LANGS:
        if code=="en":
            for q in tq+cq:
                nq=norm(q); assert not any(f in nq for f in forbidden if len(f)>4)
    assert positions("dark ark mark",["ark"])==[5]
    print(json.dumps({"status":"ok","languages":20,"target_queries_per_language":5,"control_queries_per_language":5,"primary_prediction":"strict enclosure geometry + boundary/receiver + identity/second-birth","sample_floor_each_group":25}))

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
