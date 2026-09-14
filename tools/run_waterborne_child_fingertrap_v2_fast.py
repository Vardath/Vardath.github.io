#!/usr/bin/env python3
"""Execution-only accelerator for the frozen waterborne-child fingertrap v2 protocol.

Scientific constants, classification rules, thresholds, statistics, and audit remain in
`test_waterborne_child_fingertrap_v2.py`. This wrapper changes only merge acquisition:
it fetches the same per-title English extracts concurrently instead of serially.
"""
import argparse, csv, json
from concurrent.futures import ThreadPoolExecutor, as_completed

import test_waterborne_child_fingertrap_v2 as core


def fast_merge(workers=6):
    paths=sorted(core.WORK.glob("shard-*.json"))
    if len(paths)!=20: raise SystemExit(f"need 20 shard files, found {len(paths)}")
    payloads=[json.loads(p.read_text(encoding="utf-8")) for p in paths]
    bykey={}
    for sh in payloads:
        for r in sh["rows"]:
            title=r.get("en_title")
            if not title: continue
            key=("q",r.get("qid")) if r.get("qid") else ("t",core.norm(title))
            out=bykey.setdefault(key,{"en_title":title,"qid":r.get("qid"),"source_langs":set(),"source_titles":set(),"discovery_groups":set()})
            out["source_langs"].add(sh["lang"]); out["source_titles"].add(r.get("title") or ""); out["discovery_groups"].update(r.get("discovery_groups") or [])
    print(json.dumps({"unique_english_candidates":len(bykey),"merge_transport":"concurrent_single_title","workers":workers}),flush=True)

    items=list(bykey.items())
    fetched=[None]*len(items)
    def get_one(i):
        key,r=items[i]
        return i, core.fetch_extract(r["en_title"])
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs=[ex.submit(get_one,i) for i in range(len(items))]
        done=0
        for fut in as_completed(futs):
            i,e=fut.result(); fetched[i]=e; done+=1
            if done%50==0: print(json.dumps({"extract_progress":done,"total":len(items)}),flush=True)

    records=[]
    for idx,(key,r) in enumerate(items):
        e=fetched[idx]
        if not e: continue
        row={"title":e["title"],"qid":e.get("qid") or r.get("qid"),"extract":e["extract"],"source_langs":";".join(sorted(r["source_langs"])),"source_titles":" | ".join(sorted(r["source_titles"])),"discovery_groups":";".join(sorted(r["discovery_groups"]))}
        row.update(core.classify(row)); records.append(row)

    tests={"T1_package2":core.stat(records,"package2"),"T2_strict_geometry":core.stat(records,"f1_strict_geometry"),"T3_boundary":core.stat(records,"f2_boundary"),"T4_identity":core.stat(records,"f3_identity"),"T5_package3":core.stat(records,"package3"),"T6_negative":core.stat(records,"negative"),"descriptive_any_enclosure":core.stat(records,"f1_enclosure")}
    core.bh(tests,["T2_strict_geometry","T3_boundary","T4_identity","T5_package3"])
    t1=tests["T1_package2"]; t1["underpowered"]=t1["target_n"]<25 or t1["control_n"]<25
    t1["pass"]=bool(not t1["underpowered"] and core.rr_at_least(t1["risk_ratio"],1.5) and t1["p"] is not None and t1["p"]<0.05)
    for n in ["T2_strict_geometry","T3_boundary","T4_identity","T5_package3"]:
        s=tests[n]; s["pass"]=bool(core.rr_at_least(s["risk_ratio"],1.5) and s.get("q") is not None and s["q"]<0.05)
    n=tests["T6_negative"]; n["confound_flag"]=bool(core.rr_at_least(n["risk_ratio"],1.5) and n["p"] is not None and n["p"]<0.05)
    titles={core.norm(r["title"]):r["title"] for r in records}
    audit={x:any(core.norm(x)==k or core.norm(x) in k or k in core.norm(x) for k in titles) for x in core.CANONICAL_AUDIT}
    summary={"protocol":"waterborne_child_fingertrap_v2","merge_transport":"concurrent_single_title","workers":workers,"shards":20,"raw_discoveries":sum(p["discovered"] for p in payloads),"english_mapped_occurrences":sum(p["english_mapped"] for p in payloads),"unique_english_candidates":len(bykey),"unique_english_records":len(records),"eligible_records":sum(r["eligible"] for r in records),"waterborne_targets":sum(r["group"]=="waterborne" for r in records),"nonwater_controls":sum(r["group"]=="control" for r in records),"ambiguous_water_records":sum(r["group"]=="ambiguous" for r in records),"target_discovery_languages":sorted({lg for r in records if r["group"]=="waterborne" for lg in r["source_langs"].split(";") if lg}),"canonical_retrieval_audit":audit,"tests":tests,"top_targets":[{k:r[k] for k in ("title","qid","source_langs","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3")} for r in records if r["group"]=="waterborne"][:40],"top_controls":[{k:r[k] for k in ("title","qid","source_langs","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3")} for r in records if r["group"]=="control"][:40]}
    core.RESULTS.mkdir(parents=True,exist_ok=True)
    (core.RESULTS/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    fields=["title","qid","source_langs","source_titles","discovery_groups","eligible","group","f1_enclosure","f1_strict_geometry","f2_boundary","f3_identity","package2","package3","negative","length"]
    with (core.RESULTS/"records.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in records: w.writerow({k:r.get(k) for k in fields})
    report=["# Waterborne-child travelling-fingertrap v2 result","",f"- Raw multilingual discoveries: {summary['raw_discoveries']}",f"- English-mapped occurrences: {summary['english_mapped_occurrences']}",f"- Unique English candidates: {summary['unique_english_candidates']}",f"- Eligible mythic/exposed-child records: {summary['eligible_records']}",f"- Waterborne targets: {summary['waterborne_targets']}",f"- Non-water controls: {summary['nonwater_controls']}",f"- Ambiguous-water exclusions: {summary['ambiguous_water_records']}","","## Canonical retrieval audit",""]
    report += [f"- {k}: {'FOUND' if v else 'not found'}" for k,v in audit.items()]
    report += ["","## Confirmatory tests",""]
    for k,v in tests.items(): report.append(f"- **{k}**: `{json.dumps(v,ensure_ascii=False,default=str)}`")
    (core.RESULTS/"report.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str),flush=True)


def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("validate"); sh=sp.add_parser("shard"); sh.add_argument("--id",type=int,required=True); mg=sp.add_parser("merge"); mg.add_argument("--workers",type=int,default=6)
    a=ap.parse_args()
    if a.cmd=="validate": core.validate(); print(json.dumps({"v2_fast_transport":"ok","scientific_protocol":"unchanged"}))
    elif a.cmd=="shard": core.run_shard(a.id)
    else: fast_merge(a.workers)

if __name__=="__main__": main()
