"""Bounded error classification for native worker, broker and fixed acceptance."""
import json
import re
from urllib.error import HTTPError

CODES=frozenset(('memory_pressure','context_limit','native_error','invalid_request','transport_error','worker_exit','reasoning_budget','empty_answer'))
WORDS={'implementation':'CODE_READY','janus':'PLAN_READY','sentinel':'REVIEW_READY'}

def synthetic(role,messages):
    return messages==[{'role':'user','content':'Return exactly '+WORDS.get(role,'')+' and nothing else.'}]

def native_error(error):
    text=str(error).casefold()
    if isinstance(error,MemoryError) or any(x in text for x in (
        'bad_alloc','out of memory','not enough memory','insufficient memory',
        'cannot allocate memory','failed to allocate','allocation failed',
        'not enough storage','commitment limit','paging file is too small')):
        return 'memory_pressure'
    # Exact local validation messages only; never expose generated text.
    if isinstance(error,ValueError):
        if text in ('sentinel reasoning budget ended without completed thought block',
                    'model exhausted its reasoning budget before a final answer'):
            return 'reasoning_budget'
        if text=='empty model response':return 'empty_answer'
    if re.search(r'exceeds \d+-token triad profile',text):return 'context_limit'
    return 'native_error'

class WorkerFailure(RuntimeError):
    def __init__(self,code,detail=''):
        self.code=code if code in CODES else 'transport_error'
        self.detail=str(detail)[:500]
        super().__init__(self.code+(': '+self.detail if self.detail else ''))

def http_failure(error,*,include_detail=False):
    try:
        obj=json.loads(error.read(4096))
        if not isinstance(obj,dict):raise ValueError('not object')
        code=obj.get('code','transport_error')
        detail=obj.get('detail','') if include_detail else ''
        return WorkerFailure(code,detail if isinstance(detail,str) else '')
    except (ValueError,OSError,TypeError):
        return WorkerFailure('transport_error','HTTP '+str(error.code))

def error_record(error):
    if isinstance(error,WorkerFailure):return {'code':error.code,'detail':error.detail}
    if isinstance(error,HTTPError):return {'code':'transport_error','detail':'HTTP '+str(error.code)}
    # No arbitrary exception text from real project requests.
    return {'code':'transport_error','detail':type(error).__name__[:80]}
