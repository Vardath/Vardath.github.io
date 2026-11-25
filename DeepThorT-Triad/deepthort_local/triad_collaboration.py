"""Fixed in-memory three-role collaboration challenge; never execute model text."""
import hashlib
import json
from .triad_acceptance import resident_roles
from .triad_errors import error_record

SPEC=("Synthetic ship manifest, not an X4 game file. Original: ship id demo_pe, "
      "base speed 120, multiply speed by 4, owner player, cargo 80, crew 6. "
      "Amendment: speed multiplier is now 3 instead of 4; all other requirements remain. "
      "The final manifest has exactly these keys: id, speed, owner, cargo, crew. "
      "Speed, cargo and crew are integers. No extra keys.")
BAD={"id":"demo_pe","speed":480,"owner":"npc","cargo":80,"crew":6}
EXPECTED={"id":"demo_pe","speed":360,"owner":"player","cargo":80,"crew":6}

def decode(raw):
    if not isinstance(raw,str) or len(raw)>3000:raise ValueError("Invalid response")
    s=raw.strip()
    if s.startswith("```json\n") and s.endswith("\n```"):s=s[8:-4].strip()
    elif s.startswith("```\n") and s.endswith("\n```"):s=s[4:-4].strip()
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError("Duplicate JSON key")
            result[k]=v
        return result
    result=json.loads(s,object_pairs_hook=pairs)
    if not isinstance(result,dict):raise ValueError("Expected JSON object")
    return result

def correct_manifest(obj):
    return (set(obj)==set(EXPECTED) and
            all(type(obj[k]) is type(v) and obj[k]==v for k,v in EXPECTED.items()))

def review_ok(obj,verdict,fields):
    return (set(obj)=={"verdict","fields"} and obj["verdict"]==verdict
            and isinstance(obj["fields"],list) and all(isinstance(x,str) for x in obj["fields"])
            and len(obj["fields"])==len(fields) and set(obj["fields"])==set(fields))

def collaboration(health,ask,pid,cancelled,notify=None):
    stages={}
    def finish(status,detail,artifact=None):
        evidence={"collaboration_stages":stages.copy()}
        if artifact is not None:
            evidence["artifact_sha256"]=hashlib.sha256(json.dumps(artifact,sort_keys=True).encode()).hexdigest()
        return {"status":status,"detail":detail,"evidence":evidence}
    try:
        initial=health();models=resident_roles(initial,pid)
        if initial.get("serial_memory_mode") is not False or any(m.get("busy") for m in models.values()):
            return finish("inconclusive","Parallel workers must be idle before collaboration")
    except Exception:
        return finish("blocked","Resident models unavailable")
    def call(stage,role,prompt,tokens,validator):
        if cancelled.is_set():return "cancelled",None
        if notify:notify(stage)
        try:
            current=health();resident_roles(current,pid)
            if current.get("serial_memory_mode") is not False:return "blocked",None
            obj=decode(ask(role,prompt,tokens))
            if cancelled.is_set():return "cancelled",None
            stages[stage]={"role":role,"status":"passed" if validator(obj) else "failed"}
            return stages[stage]["status"],obj
        except (ValueError,TypeError,KeyError):
            stages[stage]={"role":role,"status":"failed","reason":"invalid structured reply"}
            return "failed",None
        except Exception as e:
            stages[stage]={"role":role,"status":"blocked","error":error_record(e)}
            return "blocked",None
    status,plan=call("plan","janus",SPEC+" Return JSON only: an object of the five required final field values. Calculate the amended speed.",160,correct_manifest)
    if status!="passed":return finish(status,"JANUS plan did not satisfy amended specification")
    review_instruction=' Return JSON only with verdict "reject" or "accept", and fields: an array of every incorrect field name, empty if correct.'
    status,review=call("reject_defect","sentinel",SPEC+" Review this candidate independently: "+json.dumps(BAD)+review_instruction,128,lambda x:review_ok(x,"reject",{"speed","owner"}))
    if status!="passed":return finish(status,"Sentinel did not independently reject both seeded defects")
    status,artifact=call("repair","implementation",SPEC+" Defective candidate: "+json.dumps(BAD)+" JANUS plan: "+json.dumps(plan)+" Sentinel review: "+json.dumps(review)+" Repair it. Return the final five-key JSON object only.",160,correct_manifest)
    if status!="passed":return finish(status,"Implementation repair failed independent manifest validation")
    status,_=call("verify_repair","sentinel",SPEC+" Review this repaired candidate independently: "+json.dumps(artifact)+review_instruction,128,lambda x:review_ok(x,"accept",set()))
    if status!="passed":return finish(status,"Sentinel did not verify the independently valid repair",artifact)
    try:
        final=health();end_models=resident_roles(final,pid)
        if (final.get("serial_memory_mode") is not False or final.get("memory_retries",0)!=initial.get("memory_retries",0)
                or any(end_models[r]["pid"]!=models[r]["pid"] for r in models)):
            return finish("inconclusive","Workers changed or memory recovery occurred during collaboration",artifact)
    except Exception:
        return finish("blocked","Workers unavailable after collaboration",artifact)
    return finish("passed","JANUS planned amendment, Sentinel rejected both defects, implementation repaired, independent validator and Sentinel accepted; same three workers retained.",artifact)
