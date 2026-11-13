#!/usr/bin/env python3
"""Inspect the pinned Kuertee Workshop catalog for narrow XPath selectors only.
No third-party source bodies are committed. CI writes limited structural metadata.
"""
import json,urllib.request,hashlib,struct
from pathlib import Path
from lxml import etree as E
BASE=Path(__file__).resolve().parents[1]
source=json.loads((BASE/"tools/sources.json").read_text())
item=next(x for x in source if x["path"].endswith("kuertee_emergent_missions_rescue.xml"))
req=urllib.request.Request(item["url"],headers={"User-Agent":"Vardath-X4-source-audit"})
data=urllib.request.urlopen(req,timeout=90).read()
if data[:4]!=b'XRWS':raise ValueError("Unexpected Workshop container")
v,count,nsize,total=struct.unpack_from(">4I",data,4)
sizes=struct.unpack_from(">"+str(count)+"I",data,20)
start=20+4*count
names=data[start:start+nsize].rstrip(b'\0').decode().split("\0")
offset=start+nsize;files={}
for name,size in zip(names,sizes):
  files[name]=data[offset:offset+size];offset+=size
if sum(sizes)!=total:raise ValueError("Archive length mismatch")
res={"workshop_id":item["workshop"],"catalogs":[],"files":{},"callers":[],"targets":[]}
wanted=["Bounties_RegisterPilot","Bounties_RegisterKill","EnemyTargetManager_SetPlayerTarget","kEMissions_Rescue_EnemyTargetManager"]
for name,cat in files.items():
  if not name.endswith(".cat") or name[:-4]+".dat" not in files:continue
  payload=files[name[:-4]+".dat"];offset=0
  for line in cat.decode().splitlines():
    path,size,stamp,checksum=line.rsplit(" ",3);size=int(size)
    body=payload[offset:offset+size];offset+=size
    if not path.lower().endswith(".xml") or not path.startswith("md/"):continue
    if not any(w.lower() in path.lower() for w in ["emergent_missions","patrol_raid"]):continue
    # Mirror workshop_source(): the first matched CAT entry is authoritative.
    if path in res["files"]:continue
    try:r=E.fromstring(body)
    except E.XMLSyntaxError:continue
    norm=body.removeprefix(b'\\xef\\xbb\\xbf').replace(b'\\r\\n',b'\\n')
    res["files"][path]={"sha256_lf":hashlib.sha256(norm).hexdigest(),"catalog_md5":checksum}
    for action in r.xpath("//run_actions[contains(@ref, 'Bounties_RegisterPilot') or contains(@ref, 'Bounties_RegisterKill')]"):
      res["callers"].append({"file":path,"path":r.getroottree().getpath(action),"attrs":dict(action.attrib),
          "params":[{"name":x.get("name"),"value":x.get("value")} for x in action.findall("param")],
          "parent":dict(action.getparent().attrib),"parent_tag":str(action.getparent().tag)})
    for cue in r.xpath("//*[self::cue or self::library]"):
      if cue.get("name") not in wanted:continue
      entry={"file":path,"cue":cue.get("name"),"cue_path":r.getroottree().getpath(cue),"root_tag":r.tag,"root_name":r.get("name"),"items":[]}
      for child in cue.iter():
        if child is cue or not isinstance(child.tag,str):continue
        if len(entry["items"])>=90:break
        attrs={k:v[:500] for k,v in child.attrib.items()}
        entry["items"].append({"path":r.getroottree().getpath(child),"tag":child.tag,"attrs":attrs})
      res["targets"].append(entry)
# Match the exact unpack + newline normalization code used by release CI.
from validate import workshop_source, normalized
for file, meta in res["files"].items():
    native=workshop_source(data,{"catalog_path":file,"catalog_md5":meta["catalog_md5"]})
    meta["validator_sha256_lf"]=hashlib.sha256(normalized(native)).hexdigest()
res["source_sha256"]=hashlib.sha256(data).hexdigest()
(BASE/"tools/kem_source_audit.json").write_text(json.dumps(res,indent=2)+"\n")
print("Found",len(res["targets"]),"target cue definitions")
if not res["targets"]:raise ValueError("Target cues not in source; do not invent selectors")
