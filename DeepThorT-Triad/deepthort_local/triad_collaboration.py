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

def review_evidence(obj):
    # Export only known field labels and enumerated verdicts, never model prose.
    verdict=obj.get("verdict")
    fields=obj.get("fields")
    return {"verdict":verdict if verdict in ("accept","reject") else "invalid",
            "reported_fields":sorted({x for x in fields if isinstance(x,str) and x in EXPECTED})
                if isinstance(fields,list) else [],
            "field_count":len(fields) if isinstance(fields,list) else None,
            "valid_review_shape":set(obj)=={"verdict","fields"} and
                isinstance(fields,list) and all(isinstance(x,str) and x in EXPECTED for x in fields)}

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
            raw=ask(role,prompt,tokens)
            if cancelled.is_set():return "cancelled",None
            try:obj=decode(raw)
            except (ValueError,TypeError):
                stages[stage]={"role":role,"status":"failed","reason":"invalid structured reply",
                    "response_chars":len(raw) if isinstance(raw,str) else None}
                return "failed",None
            entry={"role":role,"status":"passed" if validator(obj) else "failed"}
            if stage in ("reject_defect","verify_repair"):
                entry.update(review_evidence(obj))
                if entry["status"]=="failed":entry["reason"]="review did not match independent validator"
            stages[stage]=entry
            return entry["status"],obj
        except (ValueError,TypeError,KeyError):
            stages[stage]={"role":role,"status":"failed","reason":"invalid structured reply"}
            return "failed",None
        except Exception as e:
            stages[stage]={"role":role,"status":"blocked","error":error_record(e)}
            return "blocked",None
    status,plan=call("plan","janus",SPEC+" Return JSON only: an object of the five required final field values. Calculate the amended speed.",160,correct_manifest)
    if status!="passed":return finish(status,"JANUS plan did not satisfy amended specification")
    review_instruction=(
        ' Act as an independent auditor, not a repair author. Apply the later amendment before reviewing. '
        'Calculate the required speed from the base speed and current multiplier. '
        'Compare each candidate field separately against the requirements: id, speed, owner, cargo, crew. '
        'If any field differs, reject; if all match, accept. Report ALL mismatching field names, '
        'not their values, and do not list correct fields. '
        'Return exactly one JSON object, with keys "verdict" (string "reject" or "accept") '
        'and "fields" (array of field-name strings, empty when all match). No explanation or extra keys.')
    def audit(stage,candidate):
        differences={k for k,v in EXPECTED.items() if type(candidate[k]) is not type(v) or candidate[k]!=v}
        verdict="reject" if differences else "accept"
        status,review=call(stage,"sentinel",SPEC+" Review this candidate independently: "+json.dumps(candidate)+review_instruction,192,
                           lambda x:review_ok(x,verdict,differences))
        if status=="passed" or status!="failed":return status,review
        # Preserve the original failed holistic verdict. A separate bounded
        # audit must independently derive every required value and compare it
        # to the observed value; do not supply the expected values or defect list.
        stages[stage]["recovery"]="field_by_field"
        found=[]
        for field in EXPECTED:
            value=candidate[field]
            def valid(obj,field=field,value=value):
                required=EXPECTED[field]
                match=type(value) is type(required) and value==required
                return (set(obj)=={"required","verdict"} and
                        type(obj["required"]) is type(required) and obj["required"]==required and
                        obj["verdict"]==("match" if match else "mismatch"))
            prompt=(SPEC+" Audit ONLY the field "+json.dumps(field)+
                    ". The candidate value is "+json.dumps(value)+
                    ". Derive the required value from the original instructions and amendment, then compare. "
                    'Return only JSON with keys "required" (the required value, correct JSON type) '
                    'and "verdict" ("match" if the candidate equals the requirement, otherwise "mismatch").')
            state,answer=call(stage+"_"+field,"sentinel",prompt,96,valid)
            if state!="passed":
                stages[stage]["recovery_status"]=state
                return state,None
            if answer["verdict"]=="mismatch":found.append(field)
        # The aggregate verdict is explicitly program-derived from validated
        # independent Sentinel judgments, not a replacement model response.
        recovered={"verdict":"reject" if found else "accept","fields":found}
        if not review_ok(recovered,verdict,differences):
            stages[stage]["recovery_status"]="failed"
            return "failed",None
        stages[stage]["recovery_status"]="passed"
        stages[stage]["aggregate_verdict"]=recovered["verdict"]
        stages[stage]["aggregate_fields"]=found
        return "passed",recovered
    status,review=audit("reject_defect",BAD)
    if status!="passed":return finish(status,"Sentinel did not independently reject both seeded defects")
    status,artifact=call("repair","implementation",SPEC+" Defective candidate: "+json.dumps(BAD)+" JANUS plan: "+json.dumps(plan)+" Sentinel review: "+json.dumps(review)+" Repair it. Return the final five-key JSON object only.",160,correct_manifest)
    if status!="passed":return finish(status,"Implementation repair failed independent manifest validation")
    status,_=audit("verify_repair",artifact)
    if status!="passed":return finish(status,"Sentinel did not verify the independently valid repair",artifact)
    try:
        final=health();end_models=resident_roles(final,pid)
        if (final.get("serial_memory_mode") is not False or final.get("memory_retries",0)!=initial.get("memory_retries",0)
                or any(end_models[r]["pid"]!=models[r]["pid"] for r in models)):
            return finish("inconclusive","Workers changed or memory recovery occurred during collaboration",artifact)
    except Exception:
        return finish("blocked","Workers unavailable after collaboration",artifact)
    recovered=any(row.get("recovery_status")=="passed" for row in stages.values())
    detail=("JANUS planned amendment, Sentinel rejected both defects, implementation repaired, independent validator and Sentinel accepted; same three workers retained.")
    if recovered:detail+=" Holistic review failed; validated field-by-field recovery succeeded (see stages)."
    return finish("passed",detail,artifact)
