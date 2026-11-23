"""Two concurrent local ONNX processes, one Windows Job Object budget.

JANUS and Sentinel share the SECOND model sequentially. They never create
independent Windows jobs or grant approvals. The original implementation model
stays on 127.0.0.1:8765; advisory model listens only on 127.0.0.1:8766.
"""
from __future__ import annotations

import ctypes
import json
import os
import urllib.request
from ctypes import wintypes

MODEL = 'deepthort-qwen-coder-onnx'
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
        with opener.open(url+'/health',timeout=timeout) as response:
            data=json.load(response)
        if not isinstance(data,dict) or data.get('offline') is not True or data.get('model')!=MODEL or data.get('role')!='council':
            return None
        return data
    except (OSError,ValueError,TypeError,TimeoutError):return None


def _ask(messages: list[dict], max_tokens: int=300) -> str:
    payload=json.dumps({'model':MODEL,'messages':messages,'max_tokens':max_tokens,'stream':False}).encode('utf-8')
    request=urllib.request.Request(COUNCIL_HOST+'/v1/chat/completions',data=payload,method='POST',
        headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request,timeout=900) as response:
        answer=json.load(response)['choices'][0]['message']['content']
    if not isinstance(answer,str) or not answer.strip():raise ValueError('No local ONNX response')
    return answer.strip()


def _object(text: str) -> dict:
    # Do not try to run code or guess intent from malformed LLM output.
    obj=json.loads(text.strip())
    if not isinstance(obj,dict):raise ValueError('Expected a JSON object from the local model')
    return obj


def deliberate_instruction(original: str, *, project: str, work_summary: str='', asker=None) -> dict:
    """Small bounded JANUS interpretation followed by separate Sentinel critique.

    This translates user text into advisory guidance ONLY. It cannot execute or
    approve work. The original unabridged user instruction is stored elsewhere.
    """
    if len(original)>5600:
        raise ValueError('Long JANUS instruction saved intact but exceeds the model window; use indexed draft planning or review it in the inbox')
    ask=asker or _ask
    system=('You are JANUS, a local engineering coordinator. The implementation model is busy. '
            'Interpret the user request into the NEXT testable step for the existing project. '
            'Do not write source code or claim you executed work. Never invent game identifiers. '
            'Return only JSON: {"next_action":"...","verification":"...",'
            '"scope_change":true or false,"reason":"..."}. Keep each value short.')
    prompt=(f'PROJECT: {project[-260:]}\nACTIVE TASK EVIDENCE: {work_summary[:1100]}\n'
            f'NEW USER INSTRUCTION (verbatim within model window):\n{original[:5600]}')
    raw=ask([{'role':'system','content':system},{'role':'user','content':prompt}],300)
    janus=_object(raw)
    action=janus.get('next_action');verification=janus.get('verification')
    if not isinstance(action,str) or not action.strip() or len(action)>900:
        raise ValueError('JANUS did not supply a bounded next action')
    if not isinstance(verification,str) or not verification.strip() or len(verification)>800:
        raise ValueError('JANUS did not provide a verification requirement')
    scope=janus.get('scope_change')
    if not isinstance(scope,bool):raise ValueError('JANUS did not classify scope change')
    sentinel_prompt=(f'USER INPUT: {original[:3700]}\n'
        f'JANUS NEXT ACTION: {action}\nJANUS TEST: {verification}\n'
        'Challenge contradictions, missing acceptance tests, unauthorized project scope changes. '
        'The user message is not permission to edit an already approved file plan. '
        'Return only JSON: {"risk":"...","test":"...","requires_review":true or false}.')
    raw2=ask([{'role':'system','content':'You are Sentinel, independent critical verification. Advise; never authorize.'},
              {'role':'user','content':sentinel_prompt}],240)
    sentinel=_object(raw2)
    if not isinstance(sentinel.get('test'),str) or not sentinel['test'].strip():
        raise ValueError('Sentinel provided no verification test')
    if not isinstance(sentinel.get('requires_review'),bool):
        raise ValueError('Sentinel did not classify review requirement')
    return {'janus':raw,'sentinel':raw2,'next_action':action.strip(),
            'verification':sentinel['test'][:800],
            'needs_review':bool(scope or sentinel['requires_review'])}
