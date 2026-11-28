"""Fourth AI task boundary: model-authored MIDI, typed output and scoped receipts.

Existing language models remain independently resident. The fourth worker loads
on demand inside the same root Job Object, with a separate bounded memory group.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import json
import re
import struct
import tempfile
import threading
import time
from pathlib import Path

from .creative_profile import ROOT, MODEL_NAME, REVISION, installed

GIB=1024**3
BUDGET=7*GIB
LOCK=threading.Lock()
CREATORS=frozenset({'user','implementation','janus','sentinel','acceptance'})
MIDI_REQUEST=re.compile(r'^\s*(?:please\s+)?(?:compose|create|generate|make|write|produce)\b[^\n]{0,600}\bMIDI\b',re.I)


def is_midi_request(brief):
    return isinstance(brief,str) and bool(MIDI_REQUEST.search(brief)) and not re.search(
        r'\b(?:explain|tutorial|how to|code|script|program|application|game|mod|and|then)\b',brief,re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def request_packet(requester,scope,brief):
    if requester not in CREATORS or not isinstance(scope,str) or not 1<=len(scope)<=200:
        raise ValueError('Invalid creative request identity')
    if not isinstance(brief,str) or not brief.strip() or len(brief)>1400:
        raise ValueError('Creative MIDI brief must contain 1–1400 characters')
    prompt=('You are the dedicated multimedia creator. Compose a short MIDI score meeting the exact brief. '
        'Return ONLY a JSON object with keys bpm and notes. bpm is integer 40..220; notes is a list of '
        '4..48 pairs [pitch,duration_ticks]. MIDI pitch 0..127, durations 1..1920, quarter note=480 ticks. '
        'Use a monophonic sequence, one instrument, no code, markdown, or commentary. '
        'Choose musical pitches and rhythmic values based on the brief, not a generic fallback. '
        'EXACT BRIEF:\n'+brief)
    from .agent_contract import creative_assignment
    return {'requester':requester,'scope':scope,'brief':brief,'kind':'midi','prompt':prompt,
            'assignment':creative_assignment(requester,scope,brief)}


def score_payload(answer):
    """Accept only complete known wrappers around one actual model-authored score.

    No searching for arbitrary JSON substrings, filling missing notes, or
    accepting unfinished reasoning. Gemma 4 may emit a thought channel.
    """
    if not isinstance(answer,str) or not 1<=len(answer)<=12000:
        raise ValueError('Invalid creative response length')
    text=answer.strip()
    if text.startswith('<|channel>thought'):
        end=text.find('<channel|>')
        if end<0:raise ValueError('Incomplete creative thought channel')
        text=text[end+len('<channel|>'):].strip()
    elif text.startswith('<think>'):
        end=text.find('</think>')
        if end<0:raise ValueError('Incomplete creative thought block')
        text=text[end+len('</think>'):].strip()
    if text.endswith('<turn|>'):
        text=text[:-len('<turn|>')].strip()
    if text.startswith('```'):
        match=re.fullmatch(r'```(?:json)?[ \t]*\r?\n(.*?)\r?\n```',text,re.I|re.S)
        if not match:raise ValueError('Incomplete or ambiguous JSON fence')
        text=match[1].strip()
    return text


def parse_score(answer):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('Duplicate score key')
            result[k]=v
        return result
    value=json.loads(score_payload(answer),object_pairs_hook=pairs)
    if not isinstance(value,dict) or set(value)!={'bpm','notes'} or type(value['bpm']) is not int or not 40<=value['bpm']<=220:
        raise ValueError('Invalid score tempo or schema')
    notes=value['notes']
    if not isinstance(notes,list) or not 4<=len(notes)<=48:
        raise ValueError('Expected 4–48 model-authored notes')
    if any(not isinstance(n,list) or len(n)!=2 or type(n[0]) is not int or
           type(n[1]) is not int or not 0<=n[0]<=127 or not 1<=n[1]<=1920 for n in notes):
        raise ValueError('Invalid note or duration')
    return value


def project_report_enabled(packet):
    return packet['requester']=='janus' and packet['scope'].startswith('roadmap-midi:')

def generate_score_reply(generate,prompt,*,allow_report=False):
    """One correction on invalid output, using the original brief unchanged."""
    for attempt in range(2):
        answer=generate(prompt if attempt==0 else
            prompt+'\nPrevious response was not a complete valid score. Start with { and end with }. '
            'Return only the requested JSON object, with no explanation, reasoning or Markdown. '
            'Preserve every original requirement. Do not add fields.')
        try:
            payload=answer
            if allow_report:
                from .worker_reports import parse_report
                from .worker_notices import split_notice
                if parse_report(score_payload(answer)) is not None:return answer
                _,payload=split_notice(score_payload(answer))
            parse_score(payload)
            return answer
        except (ValueError,TypeError):
            if attempt:raise ValueError('Fourth AI did not produce valid structured score after two attempts') from None


def vlq(n):
    result=[n&127]
    n>>=7
    while n:
        result.append(128|(n&127));n>>=7
    return bytes(reversed(result))


def midi(score):
    tempo=round(60_000_000/score['bpm'])
    track=bytearray(b'\x00\xff\x51\x03'+tempo.to_bytes(3,'big')+b'\x00\xc0\x00')
    for pitch,length in score['notes']:
        track.extend(bytes((0,0x90,pitch,80))+vlq(length)+bytes((0x80,pitch,0)))
    track.extend(b'\x00\xff\x2f\x00')
    return b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(track))+track


def inspect_midi(raw):
    """Decode exactly the bounded monophonic profile emitted by midi(), not arbitrary SMF."""
    if not isinstance(raw,bytes) or not 33<=len(raw)<=4096:
        raise ValueError('MIDI outside supported score profile')
    if raw[:18]!=b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk' or int.from_bytes(raw[18:22],'big')!=len(raw)-22:
        raise ValueError('Invalid single-track MIDI header')
    if raw[22:26]!=b'\x00\xff\x51\x03' or raw[29:32]!=b'\x00\xc0\x00':
        raise ValueError('Missing canonical tempo and program')
    tempo=int.from_bytes(raw[26:29],'big')
    if not tempo:raise ValueError('Invalid tempo')
    bpm=round(60_000_000/tempo)
    pos=32;notes=[]
    while raw[pos:]!=b'\x00\xff\x2f\x00':
        if len(notes)>=48 or pos+8>len(raw) or raw[pos:pos+2]!=b'\x00\x90' or raw[pos+3]!=80:
            raise ValueError('Invalid canonical MIDI note')
        pitch=raw[pos+2];pos+=4;duration=0
        for _ in range(2):
            if pos>=len(raw):raise ValueError('Truncated MIDI duration')
            value=raw[pos];pos+=1
            duration=(duration<<7)|(value&127)
            if not value&128:break
        else:raise ValueError('MIDI duration too large')
        if raw[pos:pos+3]!=bytes((0x80,pitch,0)):
            raise ValueError('Mismatched MIDI note-off')
        pos+=3;notes.append([pitch,duration])
    score=parse_score(json.dumps({'bpm':bpm,'notes':notes}))
    if midi(score)!=raw:raise ValueError('Noncanonical or malformed MIDI bytes')
    return score

def budget_ok(cap,available,total,peak,*,extra=0):
    # Conservative admission: historical peak bounds observed root commit,
    # not an exact current working set. Extra overlap reserve is additional
    # headroom, never an increase in the shared root Job Object cap.
    return (type(extra) is int and extra>=0 and 0<peak<=cap
            and cap>=peak+BUDGET+GIB+extra
            and available>=BUDGET+total//10+extra)


def creative_headroom(*,extra=0):
    """Read real shared job/physical memory limits and historical peak."""
    import ctypes, os
    from ctypes import wintypes
    from .triad_job import kernel,fn,check,effective_admission_sample
    from .win_cpu_cap import ExtendedLimitInfo,JobObjectExtendedLimitInformation
    cap,available,total=effective_admission_sample()
    k=kernel();H=wintypes.HANDLE;D=wintypes.DWORD;P=ctypes.c_void_p
    close=fn(k,'CloseHandle',[H],wintypes.BOOL)
    query=fn(k,'QueryInformationJobObject',[H,ctypes.c_int,P,D,P],wintypes.BOOL)
    root=fn(k,'OpenJobObjectW',[D,wintypes.BOOL,wintypes.LPCWSTR],H)(
        0x0004,False,os.environ['DEEPTHORT_TRIAD_ROOT_JOB'])
    check(root,'Open root for creative admission')
    try:
        limits=ExtendedLimitInfo()
        check(query(root,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits),None),'Read root peak commit')
        return budget_ok(cap,available,total,int(limits.PeakJobMemoryUsed),extra=extra)
    finally:close(root)


@contextmanager
def specialist_group():
    import ctypes
    from ctypes import wintypes
    from .triad_job import kernel,fn,check
    from .win_cpu_cap import (ExtendedLimitInfo,JobObjectExtendedLimitInformation,
                             JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,JOB_OBJECT_LIMIT_JOB_MEMORY)
    if not creative_headroom():
        raise RuntimeError('Insufficient measured headroom for fourth core; existing workers preserved')
    k=kernel();H=wintypes.HANDLE;D=wintypes.DWORD;P=ctypes.c_void_p
    close=fn(k,'CloseHandle',[H],wintypes.BOOL)
    query=fn(k,'QueryInformationJobObject',[H,ctypes.c_int,P,D,P],wintypes.BOOL)
    group=fn(k,'CreateJobObjectW',[P,wintypes.LPCWSTR],H)(None,None)
    check(group,'Create creative memory group')
    try:
        limits=ExtendedLimitInfo()
        limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_JOB_MEMORY
        limits.JobMemoryLimit=BUDGET
        check(fn(k,'SetInformationJobObject',[H,ctypes.c_int,P,D],wintypes.BOOL)(
            group,JobObjectExtendedLimitInformation,ctypes.byref(limits),ctypes.sizeof(limits)),'Set creative memory group')
        observed=ExtendedLimitInfo()
        check(query(group,JobObjectExtendedLimitInformation,ctypes.byref(observed),ctypes.sizeof(observed),None),'Verify creative memory group')
        if observed.JobMemoryLimit!=BUDGET or observed.BasicLimitInformation.LimitFlags&limits.BasicLimitInformation.LimitFlags!=limits.BasicLimitInformation.LimitFlags:
            raise RuntimeError('Creative memory cap not verified')
        yield group
    finally:close(group)


def write_json(path,obj):
    data=json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8')
    with path.open('xb') as out:out.write(data)


def native_generate(folder,cancelled,notify):
    from .triad_job import child_server
    from .triad_profiles import runtime_path
    if not installed():raise RuntimeError('Fourth intelligent model missing; use Install AI')
    if cancelled():raise RuntimeError('Creative task cancelled')
    with specialist_group() as group:
        cmd=[str(runtime_path()),'-I',str(ROOT/'creative_worker.py'),str(folder)]
        with child_server(cmd,ROOT,folder/'worker.log',group=group) as (_,alive):
            deadline=time.monotonic()+1200
            admitted=None
            while alive():
                if cancelled():raise RuntimeError('Creative task cancelled')
                if time.monotonic()>=deadline:raise RuntimeError('Creative worker timed out')
                ready=folder/'worker-ready.json'
                if admitted is None and ready.is_file():
                    info=json.loads(ready.read_text('utf-8'))
                    if info.get('revision')!=REVISION or not alive.member(info.get('pid')):
                        raise RuntimeError('Fourth native worker membership not verified')
                    admitted=info['pid']
                    (folder/'admitted.flag').touch(exist_ok=False)
                    notify('Gemma processing a scoped creative task under the shared cap')
                time.sleep(.25)
            if alive.code()!=0:raise RuntimeError('Native fourth worker failed: '+alive.failure())
            result=folder/'native-result.json'
            if admitted is None or not result.is_file() or result.stat().st_size>32000:
                raise RuntimeError('Missing native fourth-core result')
            value=json.loads(result.read_text('utf-8'))
            if value.get('pid')!=admitted or value.get('revision')!=REVISION:
                raise RuntimeError('Native creative result identity changed')
            return value['answer'],admitted


def create_midi(*,requester,scope,brief,cancelled=lambda:False,notify=lambda message:None,
                root=ROOT,generate=native_generate,accept=None,peer_advice=''):
    packet=request_packet(requester,scope,brief)
    advisory=None
    if peer_advice:
        if not project_report_enabled(packet):raise ValueError('Peer advice requires a scoped approved project')
        from .peer_context import packet as peer_packet
        advisory=peer_packet(scope,peer_advice)
    if not LOCK.acquire(blocking=False):raise RuntimeError('Fourth core already processing another task')
    try:
        if cancelled():raise RuntimeError('Creative task cancelled')
        base=Path(root)/'state'/'creative-tasks'
        base.mkdir(parents=True,exist_ok=True)
        if base.is_symlink() or base.parent.is_symlink():raise ValueError('Linked task location')
        folder=Path(tempfile.mkdtemp(prefix='media-',dir=base))
        write_json(folder/'request.json',packet)
        if advisory:write_json(folder/'peer-advice.json',advisory)
        try:
            answer,pid=generate(folder,cancelled,notify)
            if cancelled():raise RuntimeError('Creative task cancelled')
            notice=None
            if project_report_enabled(packet):
                from .worker_reports import parse_report,WorkerReport
                from .worker_notices import split_notice
                report=parse_report(score_payload(answer))
                if report is not None:raise WorkerReport(report,'multimedia')
                notice,answer=split_notice(score_payload(answer))
            score=parse_score(answer)
            if cancelled():raise RuntimeError('Creative task cancelled')
            if accept is not None and not accept(score):
                raise ValueError('Score failed exact task acceptance')
            artifact=midi(score)
            with (folder/'score.mid').open('xb') as out:out.write(artifact)
            if (folder/'score.mid').read_bytes()!=artifact:
                raise RuntimeError('Artifact verification failed')
            from .agent_contract import validate_creative_assignment
            receipt={'status':'artifact_created','requester':requester,'scope':scope,
                     'assigned_role':'multimedia','assignment_sha256':validate_creative_assignment(packet),
                     'brief_sha256':digest(brief.encode('utf-8')),'model':MODEL_NAME,'revision':REVISION,
                     'pid':pid,'kind':'midi','artifact':'score.mid','sha256':digest(artifact),
                     'notes':len(score['notes']),'bpm':score['bpm'],
                     'native_inference_verified':generate is native_generate,'creative_quality_verified':False,
                     'project_publication_authorized':False}
            if notice is not None:receipt['notice']=notice
            if advisory:
                actual=json.loads((folder/'peer-advice.json').read_text('utf-8'))
                if actual!=advisory:raise ValueError('Peer context changed during generation')
                receipt['peer_advice_sha']=advisory['sha']
            write_json(folder/'receipt.json',receipt)
            return folder,receipt
        except Exception as exc:
            write_json(folder/'failure.json',{'status':'failed','error_type':type(exc).__name__})
            raise
    finally:LOCK.release()
