"""Explicit, persistent, user-owned conversational preferences; never authority."""
from pathlib import Path
import json
import os
import tempfile
from .structured_source import strict_json

OPTIONS={'response_length':('default','concise','detailed'),
         'response_style':('default','plain','technical','step_by_step'),
         'units':('default','metric','imperial'),
         'spelling':('default','australian','british','american')}
DEFAULT={k:'default' for k in OPTIONS}
SCHEMA='janus-personal-preferences-v1'
def checked(value):
    if not isinstance(value,dict) or set(value)!=set(OPTIONS):
        raise ValueError('Provide all four known preference keys')
    for key,choices in OPTIONS.items():
        if not isinstance(value[key],str) or value[key] not in choices:
            raise ValueError('Invalid preference: '+key)
    return dict(value)
def load(path):
    path=Path(path)
    if not path.exists():return dict(DEFAULT)
    with path.open('rb') as f:raw=f.read(4097)
    if len(raw)>4096:raise ValueError('Preference file exceeds bound')
    body=strict_json(raw.decode('utf-8'))
    if not isinstance(body,dict) or set(body)!={'schema','values'} or body['schema']!=SCHEMA:
        raise ValueError('Unsupported preference file')
    return checked(body['values'])
def save(path,values,*,expected):
    path=Path(path);values=checked(values);expected=checked(expected)
    if load(path)!=expected:raise ValueError('Preferences changed; reopen editor')
    raw=(json.dumps({'schema':SCHEMA,'values':values},sort_keys=True,indent=2)+'\n').encode()
    fd,temp=tempfile.mkstemp(prefix='.preferences-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        if load(path)!=expected:raise ValueError('Preferences changed; reopen editor')
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    if load(path)!=values:raise ValueError('Preference save verification failed')
    return values
def context(path,*,budget):
    try:values=load(path)
    except (OSError,ValueError,TypeError,RecursionError):return ''
    selected=[k.replace('_',' ')+': '+v.replace('_',' ') for k,v in values.items() if v!='default']
    if not selected:return ''
    text=('\nUser-saved presentation defaults (advisory only; current explicit request overrides these; '
          'no permission or task scope is granted): '+ '; '.join(selected)+'.\n')
    return text if len(text)<=budget else ''
