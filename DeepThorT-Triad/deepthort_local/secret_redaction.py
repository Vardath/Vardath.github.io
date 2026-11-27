"""Best-effort diagnostic secret redaction, not a comprehensive DLP boundary."""
import json
import re

REDACTED='[REDACTED]'
MAX_TEXT=128*1024
MAX_RESULT=8000
KEY=re.compile(r'(?i)secret|password|passwd|token|credential|api.?key|authorization|cookie|private.?key|content|prompt|reply|message_body')
METRIC=re.compile(r'(?i)(?:_characters|_length|_bytes|_count|_tokens|_tokens_per_second)$')
BEGIN=re.compile(r'-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z0-9 ]*PRIVATE KEY-----|\Z)')
END=re.compile(r'\A[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----')
PATTERNS=(
    (re.compile(r'(?i)\b(?:bearer|basic)\s+[a-z0-9._~+/=-]+'), REDACTED),
    (re.compile(r'(?i)\b(?:gh[pousr]_[a-z0-9_]{12,}|github_pat_[a-z0-9_]{12,}|sk-[a-z0-9_-]{12,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b'), REDACTED),
    (re.compile(r'\beyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\b'), REDACTED),
    (re.compile(r'(?i)(https?://)[^/@\s]+:[^/@\s]+@'), r'\1[REDACTED]@'),
    (re.compile(r"""(?i)(?<![\w-])(["']?[A-Za-z0-9_-]*(?:password|passwd|secret|token|credential|api[-_]?key|authorization|cookie|private[-_]?key)[A-Za-z0-9_-]*["']?\s*[:=]\s*)(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\r\n]+)"""), r'\1[REDACTED]'),
)

def text(value):
    if len(value)>MAX_TEXT:return '[OMITTED oversized diagnostic text]'
    value=BEGIN.sub('[REDACTED PRIVATE KEY]',value)
    # A bounded tail may begin inside a private-key block.
    if '-----END ' in value:value=END.sub('[REDACTED PRIVATE KEY]',value)
    for pattern,replacement in PATTERNS:value=pattern.sub(replacement,value)
    return value[:MAX_RESULT]

def scrub(value,depth=0):
    if depth>=16:return '[OMITTED nested diagnostic data]'
    if isinstance(value,str):return text(value)
    if value is None or isinstance(value,(bool,float,int)):return value
    if isinstance(value,dict):
        result={}
        for k,v in list(value.items())[:80]:
            key=str(k);safe=text(key)[:100]
            # Only actual numeric metrics (or unavailable numeric values)
            # are exempt; a string labelled "token_count" is not a metric.
            metric=METRIC.search(key) and (v is None or type(v) in (int,float))
            result[safe]=REDACTED if KEY.search(key) and not metric else scrub(v,depth+1)
        return result
    if isinstance(value,(tuple,list)):return [scrub(x,depth+1) for x in value[:60]]
    return text(str(value))

def jsonl(raw):
    """Re-scrub historical structured records; never pass malformed rows through."""
    output=[]
    for line in raw.splitlines():
        if not line.strip():continue
        try:
            if len(line)>MAX_TEXT:raise ValueError('Oversized row')
            row=json.loads(line.decode('utf-8'))
            if not isinstance(row,dict):raise ValueError('Expected object')
            row=scrub(row)
        except (UnicodeError,ValueError,RecursionError):
            row={'event':'diagnostic_row_omitted','data':{'reason':'malformed_or_oversized'}}
        output.append(json.dumps(row,ensure_ascii=True,separators=(',',':')))
    return ('\n'.join(output)+('\n' if output else '')).encode('utf-8')

def tail(path,limit):
    """Drop the first possibly partial line rather than expose an unrecognizable fragment."""
    with path.open('rb') as handle:
        size=handle.seek(0,2);offset=max(0,size-limit);handle.seek(offset);raw=handle.read(limit)
    if offset:
        _,sep,raw=raw.partition(b'\n')
        if not sep:return '[OMITTED partial diagnostic line]'
    return text(raw.decode('utf-8',errors='replace'))
