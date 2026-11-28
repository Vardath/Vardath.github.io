"""Fixed five-model integrated production probe; no model-authored code execution."""
import hashlib
import json
from pathlib import Path
from .triad_acceptance import resident_roles
from .memory_core_probe import resident_memory
from .triad_collaboration import decode
from .creative_core import create_midi,inspect_midi

EXPECTED={'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}
PLAN={'bpm':100,'pitches':[60,62,64,65],'ticks':480}
RECALL={'keep':['N1']}
SPEC='Produce a four-note MIDI score, pitches 60, 62, 64, 65 in order; each is one quarter note (480 ticks). Original tempo 90 BPM; apply the latest relevant amendment.'

def equal(a,b):
    # JSON encoding distinguishes booleans, integers and floats.
    return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)

def exercise(health,pid,ask,root,*,cancelled=lambda:False,notify=lambda message:None,creative=create_midi):
    stages={}
    def finish(status,detail,sha=None):
        evidence={'collaboration_stages':stages.copy()}
        if sha:evidence['artifact_sha256']=sha
        return {'status':status,'detail':detail,'evidence':evidence}
    def identities(value):
        models=resident_roles(value,pid);memory=resident_memory(value,pid)
        return {**{k:v['pid'] for k,v in models.items()},'memory':memory['pid']}
    try:
        initial=health();ids=identities(initial)
        if any(row.get('busy') for row in (*initial['models'].values(),initial['memory_model'])):
            return finish('inconclusive','Real work active; integrated probe deferred')
    except Exception:
        return finish('blocked','Four text workers not resident')
    retries=initial.get('memory_retries',0);serial=initial.get('serial_memory_mode')
    def stable():
        current=health()
        return identities(current)==ids and current.get('memory_retries',0)==retries and current.get('serial_memory_mode')==serial
    def stage(name,role,prompt,expected,tokens=160):
        if cancelled():return 'cancelled',None
        try:
            if not stable():return 'inconclusive',None
            notify(name)
            raw=ask(role,prompt,tokens)
            if cancelled():return 'cancelled',None
            if not stable():return 'inconclusive',None
            try:obj=decode(raw)
            except (TypeError,ValueError):
                stages[name]={'role':role,'status':'failed','reason':'invalid structured reply'}
                return 'failed',None
            status='passed' if equal(obj,expected) else 'failed'
            stages[name]={'role':role,'status':status}
            return status,obj
        except Exception as exc:
            stages[name]={'role':role,'status':'blocked','error_type':type(exc).__name__}
            return 'cancelled' if cancelled() else 'blocked',None
    if cancelled():return finish('cancelled','Integrated probe stopped')
    records={'N1':'Latest score amendment: use 100 BPM instead of 90 BPM.','N2':'Unrelated interface theme is blue.'}
    status,recall=stage('recall','memory','Choose the relevant record ID for this score: '+SPEC+' Records: '+json.dumps(records)+' Return only JSON {"keep":["record ID"]}.',RECALL)
    if status!='passed':return finish(status,'Memory did not establish the relevant amendment')
    context=records[recall['keep'][0]]
    status,plan=stage('plan','janus',SPEC+' Recalled amendment: '+context+' Return only JSON keys bpm, pitches (integer array), ticks (integer duration).',PLAN)
    if status!='passed':return finish(status,'JANUS plan did not satisfy the amended specification')
    status,score=stage('implementation','implementation','Convert this approved MIDI plan to JSON containing exactly bpm and notes (pairs [pitch,ticks]): '+json.dumps(plan),EXPECTED)
    if status!='passed':return finish(status,'Granite score contract failed the independent oracle')
    wrong={'bpm':90,'notes':score['notes']}
    status,_=stage('reject_defect','sentinel',SPEC+' Amendment: '+context+' Candidate score: '+json.dumps(wrong)+' Independently review. Return only JSON {"verdict":"accept or reject","fields":["mismatched field names"]}.',{'verdict':'reject','fields':['bpm']})
    if status!='passed':return finish(status,'Sentinel did not reject the intentionally stale tempo')
    if cancelled():return finish('cancelled','Integrated probe stopped before creative generation')
    try:
        if not stable():return finish('inconclusive','Text worker configuration changed')
        notify('multimedia')
        brief='Produce exactly this MIDI score (bpm and note pitch/tick pairs): '+json.dumps(score,sort_keys=True)+'. No extra notes.'
        folder,receipt=creative(requester='acceptance',scope='five-model-native',brief=brief,root=root,
            cancelled=cancelled,notify=notify,accept=lambda result:equal(result,score))
        if cancelled():return finish('cancelled','Integrated probe stopped after creative generation')
        if not stable():return finish('inconclusive','Text workers changed during creative generation')
        artifact=Path(folder)/'score.mid'
        raw=artifact.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        from .creative_profile import MODEL_NAME,REVISION
        if (receipt.get('native_inference_verified') is not True or receipt.get('assigned_role')!='multimedia'
            or receipt.get('model')!=MODEL_NAME or receipt.get('revision')!=REVISION
            or type(receipt.get('pid')) is not int or receipt['pid']<=0 or receipt['pid'] in {pid,*ids.values()}
            or receipt.get('sha256')!=sha or receipt.get('scope')!='five-model-native'
            or receipt.get('brief_sha256')!=hashlib.sha256(brief.encode()).hexdigest()
            or receipt.get('project_publication_authorized') is not False
            or not equal(inspect_midi(raw),EXPECTED)):
            stages['multimedia']={'role':'multimedia','status':'failed'}
            return finish('failed','Native creative receipt or independently decoded MIDI did not match')
        stages['multimedia']={'role':'multimedia','status':'passed','pid':receipt['pid']}
    except Exception as exc:
        stages['multimedia']={'role':'multimedia','status':'blocked','error_type':type(exc).__name__}
        return finish('cancelled' if cancelled() else 'blocked','Creative model or artifact unavailable')
    status,_=stage('verify_artifact','sentinel',SPEC+' Amendment: '+context+' Independently decoded actual score: '+json.dumps(inspect_midi(raw))+' Return only JSON {"verdict":"accept or reject","fields":["mismatched field names"]}.',{'verdict':'accept','fields':[]})
    if status!='passed':return finish(status,'Sentinel final artifact review failed',sha)
    if cancelled():return finish('cancelled','Integrated probe stopped',sha)
    return finish('passed','Five native roles completed one linked fixed MIDI task with independent recall, plan, contract, defect rejection, decoded artifact and final review. Not simultaneous five-way inference or broad production acceptance.',sha)
