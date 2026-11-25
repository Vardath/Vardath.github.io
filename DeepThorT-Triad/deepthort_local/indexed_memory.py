"""Scoped recall for indexed planning suboperations.
Current requirements, measured options and validators remain authoritative.
"""
from .reasoning_council import sha

def recall(provider,*,phase,identity,focus,section='',budget=600,cancelled=None,client=None):
    if cancelled and cancelled():raise ValueError('Indexed memory review cancelled')
    if provider is None:return ''
    from .memory_governor import fit
    room=min(600,max(0,budget))
    context=provider(phase,sha(str(identity)),str(focus)[:500],section,room,client=client)
    if cancelled and cancelled():raise ValueError('Indexed memory review cancelled')
    return fit(context,room)

def append(prompt,provider,*,phase,identity,focus,section='',limit=7500,cancelled=None):
    if len(prompt)>limit:raise ValueError('Indexed operation exceeds local prompt bound')
    return prompt+recall(provider,phase=phase,identity=identity,focus=focus,section=section,
                         budget=limit-len(prompt),cancelled=cancelled)
