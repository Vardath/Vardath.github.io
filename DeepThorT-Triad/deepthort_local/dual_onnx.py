"""Compatibility client for the Triad broker. JANUS and Sentinel use distinct resident OpenVINO IR processes."""
from __future__ import annotations

import ctypes
import json
import os
import re
import socket
import urllib.request
from ctypes import wintypes

from .triad_profiles import MODEL_ID as MODEL
COUNCIL_HOST = 'http://127.0.0.1:8766'
GIB = 1024 ** 3


def memory_room(*, total: int, available: int) -> bool:
    """Conservatively skip secondary model on small or memory-pressured PCs."""
    return (total >= 24*GIB and 0 <= available <= total and
            available >= max(6*GIB, total//8))


def windows_memory() -> tuple[int, int] | None:
    if os.name != 'nt':return None
    from .win_cpu_cap import MemoryStatus
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=kernel.GlobalMemoryStatusEx
    fn.argtypes=[ctypes.POINTER(MemoryStatus)]
    fn.restype=wintypes.BOOL
    data=MemoryStatus();data.dwLength=ctypes.sizeof(data)
    if not fn(ctypes.byref(data)):return None
    return int(data.ullTotalPhys),int(data.ullAvailPhys)


def council_can_start(*, memory=None, capped=None) -> bool:
    from .quiet_playtest import is_capped_windows_process
    memory=windows_memory() if memory is None else memory
    capped=is_capped_windows_process() if capped is None else capped
    return bool(capped and memory and memory_room(total=memory[0],available=memory[1]))


def local_health(url: str=COUNCIL_HOST, timeout:float=0.7) -> dict | None:
    if url != COUNCIL_HOST:raise ValueError('Only the local advisory model is supported')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(urllib.request.Request(url+'/health',headers={'Authorization':'Bearer '+os.environ.get('DEEPTHORT_TRIAD_TOKEN','')}),timeout=timeout) as response:
            data=json.load(response)
        if not isinstance(data,dict) or data.get('offline') is not True or data.get('model')!=MODEL or data.get('role')!='council':
            return None
        return data
    except (OSError,ValueError,TypeError,TimeoutError):return None


def _ask(messages: list[dict], max_tokens: int=300, *, role='janus') -> str:
    payload=json.dumps({'model':MODEL,'triad_role':role,'messages':messages,'max_tokens':max_tokens,'stream':False}).encode('utf-8')
    request=urllib.request.Request(COUNCIL_HOST+'/v1/chat/completions',data=payload,method='POST',
        headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ.get('DEEPTHORT_TRIAD_TOKEN','')})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request,timeout=7200) as response:
        answer=json.load(response)['choices'][0]['message']['content']
    if not isinstance(answer,str) or not answer.strip():raise ValueError('No local OpenVINO IR response')
    return answer.strip()


def _object(text: str) -> dict:
    """Read one explicit JSON object, optionally wrapped in a JSON code fence.

    Never infer decisions from conversational prose, extract arbitrary embedded
    objects or execute model text. A malformed response must be corrected by
    a NEW model response, never fabricated by the parser.
    """
    value=text.strip()
    fenced=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',value,flags=re.S|re.I)
    if fenced:value=fenced.group(1).strip()
    obj=json.loads(value)
    if not isinstance(obj,dict):raise ValueError('Expected a JSON object from the local model')
    return obj


def _validated_council_reply(ask, messages: list[dict], tokens: int,
                             validate, *, role: str) -> tuple[dict,str]:
    """One bounded format-repair attempt; no partial decisions are adopted."""
    raw=ask(messages,tokens)
    try:
        obj=_object(raw)
        validate(obj)
        return obj,raw
    except (ValueError,TypeError,KeyError) as error:
        # No raw model reply is logged or persisted if structurally invalid.
        # Its content also is not added to the next prompt: this avoids
        # amplifying a malformed or injected first answer.
        schema=('next_action:string, verification:string, scope_change:boolean, reason:string'
                if role=='JANUS' else 'risk:string, test:string, requires_review:boolean')
        correction=messages+[{'role':'user','content':
            f'Your previous {role} response did not match the required JSON schema. '
            f'Return ONE JSON object only with these fields: {schema}. '
            'Use proper JSON string quotes and true/false booleans. '
            'No markdown, explanations or additional text.'}]
        try:
            second=ask(correction,tokens)
            obj=_object(second)
            validate(obj)
            return obj,second
        except (ValueError,TypeError,KeyError) as second_error:
            raise ValueError(f'{role} could not provide valid structured advice after one format correction; '
                             'instruction retained for safe review') from second_error


def deliberate_instruction(original: str, *, project: str, work_summary: str='', asker=None) -> dict:
    """Small bounded JANUS interpretation followed by separate Sentinel critique.

    This translates user text into advisory guidance ONLY. It cannot execute or
    approve work. The original unabridged user instruction is stored elsewhere.
    """
    if len(original)>5600:
        raise ValueError('Long JANUS instruction saved intact but exceeds the model window; use indexed draft planning or review it in the inbox')
    ask=asker or _ask
    # A literal reply has an observable acceptance criterion and needs no
    # project advice. Never turn a greeting/echo test into a build action.
    literal = re.fullmatch(
        r'(?:(?:hi|hello|hey)\s+janus[,.!]\s*)?(?:(?:this is (?:a |an )?test)[,.!]\s*)?'
        r'(?:please\s+)?(?:reply|respond)(?:\s+with)?(?:\s+exactly)?\s*[:,]?\s+([^\r\n]{1,160})',
        original.strip(), re.I)
    if literal:
        requested = literal.group(1).strip()
        if len(requested)>1 and requested[0] in ('"',"'") and requested[-1]==requested[0]:
            requested = requested[1:-1]
        if requested:
            answer = ask([{'role':'system','content':'You are JANUS. Follow the requested output format.'},
                          {'role':'user','content':'Copy the text between the delimiters exactly. Output only the text, '
                                                   'with no delimiters or explanation.\nBEGIN\n'+requested+'\nEND'}],
                         min(192,2*len(requested)+8)).strip()
            if answer != requested:
                raise ValueError('JANUS reply differed from the requested text; the message is available for retry')
            return {'reply':answer}
    system=('You are JANUS, a local engineering coordinator. The implementation model is busy. '
            'Interpret the user request into the NEXT testable step for the existing project. '
            'Do not write source code or claim you executed work. Never invent game identifiers. '
            'Return only JSON: {"next_action":"...","verification":"...",'
            '"scope_change":true or false,"reason":"..."}. Keep each value short.')
    prompt=(f'PROJECT: {project[-260:]}\nACTIVE TASK EVIDENCE: {work_summary[:1100]}\n'
            f'NEW USER INSTRUCTION (verbatim within model window):\n{original[:5600]}')
    def validate_janus(value):
        action=value.get('next_action');verification=value.get('verification')
        if not isinstance(action,str) or not action.strip() or len(action)>900:
            raise ValueError('JANUS did not supply a bounded next action')
        if not isinstance(verification,str) or not verification.strip() or len(verification)>800:
            raise ValueError('JANUS did not provide a verification requirement')
        if not isinstance(value.get('scope_change'),bool):
            raise ValueError('JANUS did not classify scope change')
    janus,raw=_validated_council_reply(ask,[{'role':'system','content':system},
        {'role':'user','content':prompt}],300,validate_janus,role='JANUS')
    action=janus['next_action'];verification=janus['verification'];scope=janus['scope_change']
    sentinel_prompt=(f'USER INPUT: {original[:3700]}\n'
        f'JANUS NEXT ACTION: {action}\nJANUS TEST: {verification}\n'
        'Challenge contradictions, missing acceptance tests, unauthorized project scope changes. '
        'The user message is not permission to edit an already approved file plan. '
        'Return only JSON: {"risk":"...","test":"...","requires_review":true or false}.')
    def validate_sentinel(value):
        if not isinstance(value.get('test'),str) or not value['test'].strip() or len(value['test'])>800:
            raise ValueError('Sentinel provided no bounded verification test')
        if not isinstance(value.get('requires_review'),bool):
            raise ValueError('Sentinel did not classify review requirement')
    sentinel_ask=asker or (lambda messages,tokens:_ask(messages,tokens,role='sentinel'))
    sentinel,raw2=_validated_council_reply(sentinel_ask,[
        {'role':'system','content':'You are Sentinel, independent critical verification. Advise; never authorize.'},
        {'role':'user','content':sentinel_prompt}],240,validate_sentinel,role='Sentinel')
    return {'janus':raw,'sentinel':raw2,'next_action':action.strip(),
            'verification':sentinel['test'][:800],
            'needs_review':bool(scope or sentinel['requires_review'])}


def council_port_occupied(*, connector=None) -> bool:
    """Detect ANY listener, not just a valid DeepThorT model at :8766."""
    if connector is not None:
        return bool(connector())
    try:
        with socket.create_connection(('127.0.0.1',8766), timeout=.3):
            return True
    except (OSError,TimeoutError):
        return False


def council_wait_reason(*, primary_ready:bool, primary_loading:bool,
                        council_running:bool=False, council_ready:bool=False,
                        council_busy:bool=False, health:dict|None=None,
                        memory:tuple[int,int]|None=None, capped:bool=False,
                        restarts:int=0) -> str:
    """A specific, user-visible explanation; does not claim unverified readiness."""
    if council_busy:return 'JANUS/Sentinel: interpreting a saved instruction; model inference may take several minutes.'
    if council_ready:return 'JANUS/Sentinel Triad council: ready for saved instructions.'
    if council_running:
        h=health if isinstance(health,dict) else {}
        return ('JANUS/Sentinel Triad council: loading — '+
                str(h.get('stage') or 'waiting for local health response')[:110]+
                (f" ({h.get('loading_seconds')}s)" if isinstance(h.get('loading_seconds'),int) else ''))
    if not primary_ready:
        return ('JANUS/Sentinel waiting for Triad broker to finish loading.' if primary_loading else
                'JANUS/Sentinel waiting: Triad broker is not running/ready. Use Start AI or Diagnose AI.')
    if restarts>=3:
        return 'JANUS/Sentinel stopped after three worker exits. Inspect Processes, then use Retry JANUS model.'
    if not capped:
        return 'JANUS/Sentinel blocked: DeepThorT is not inside its verified shared 35% CPU Job Object. Restart using the capped launcher.'
    if memory is None:
        return 'JANUS/Sentinel waiting: Windows RAM availability could not be measured.'
    if not memory_room(total=memory[0],available=memory[1]):
        return (f'JANUS/Sentinel waiting for RAM headroom: {memory[1]/GIB:.1f} GiB free; '
                'waiting for the three-model broker.')
    return 'JANUS/Sentinel waiting for authenticated Triad council readiness (port 8766).'
