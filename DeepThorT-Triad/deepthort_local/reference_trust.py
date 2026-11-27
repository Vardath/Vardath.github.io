"""Heuristic indicators at automatic untrusted evidence boundaries, not a security proof."""
from __future__ import annotations
import re
import unicodedata
MARKERS=re.compile(r'(?i)<\s*/?\s*(?:system|developer|assistant|tool_call|tool_result)\s*>|'
                   r'<\|(?:im_start|im_end|system|assistant|developer|endoftext|eot_id|start_header_id|end_header_id)\|>|'
                   r'\[\s*/?\s*(?:INST|SYSTEM|DEVELOPER)\s*\]|<<\s*/?\s*SYS\s*>>')
OVERRIDE=re.compile(r'(?i)\b(?:ignore|disregard|forget|override|bypass|replace|supersede)\s+'
                    r'(?:(?:all|any|the|your|earlier|existing|original|previous|prior|above|following|current|higher.priority)\s+){0,6}'
                    r'(?:instructions?|polic(?:y|ies)|rules?|system\s+prompt|developer\s+message|user\s+request|user\s+requirements?)\b|'
                    r'\b(?:system|developer|administrator)\s+(?:message|instruction|override)\s*:|'
                    r'\b(?:you are now|act as the system|new highest priority|do not tell the user)\b|'
                    r'\b(?:reveal|print|send|upload|expose|disclose)\s+(?:the\s+|your\s+|all\s+){0,3}'
                    r'(?:system prompt|private key|access token|credentials|passwords?|secrets?)\b')
MAX_TEXT=256*1024

def normalized(text):
    if not isinstance(text,str) or len(text)>MAX_TEXT:raise ValueError('Reference text outside screening bound')
    text=unicodedata.normalize('NFKC',text)
    text=''.join(c for c in unicodedata.normalize('NFKD',text) if unicodedata.category(c) not in ('Cf','Mn','Me'))
    return re.sub(r'\s+',' ',text).strip()

def suspicious(text):
    try:value=normalized(text)
    except ValueError:return True
    return bool(MARKERS.search(value) or OVERRIDE.search(value))

def unsafe_at(lines,i):
    """Inspect exact line and bounded adjacent boundaries before selecting a quote."""
    line=lines[i]
    if suspicious(line):return True
    if i and suspicious(lines[i-1][-400:]+' '+line[:400]):return True
    if i+1<len(lines) and suspicious(line[-400:]+' '+lines[i+1][:400]):return True
    return False

def unsafe_lines(lines):
    return {i for i in range(len(lines)) if unsafe_at(lines,i)}

def observation_suspicious(value):
    """Screen complete string values, including multiline source excerpts."""
    pending=[value];visited=0
    while pending:
        item=pending.pop();visited+=1
        if visited>2000:return True
        if isinstance(item,str):
            if suspicious(item):return True
        elif isinstance(item,dict):
            pending.extend(item.values())
        elif isinstance(item,(list,tuple)):
            pending.extend(item)
            if item and all(isinstance(x,str) for x in item):
                if any(unsafe_at(item,i) for i in range(len(item))):return True
    return False
