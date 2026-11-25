"""Wake a durable blocked design only after relevant, positive capability evidence.

No inference, command, installer or new project authority in this scheduler.
"""
from __future__ import annotations
import json
from .tool_workflows import digest
from .workflow_design import current_source,source_binding
from .tool_acquisition import HELP_FLAGS

def observations(acquisition,janus,project,proposal):
    gaps=proposal['missing']
    outputs={g['output'] for g in gaps}
    names=set(HELP_FLAGS)|{r['name'] for r in acquisition.enrolled()}
    exact={g['capability'].strip().casefold() for g in gaps}
    generic=any(n not in {s.casefold() for s in names} for n in exact)
    tokens=[]
    for name in sorted(names)[:40]:
        if not generic and name.casefold() not in exact:continue
        try:
            row=acquisition.tool(name)
            tokens.append(digest(['installed',name,row['executable_signature']]))
            if row.get('probe_action'):
                help_record=acquisition.probe_evidence(name,janus)
                if help_record:
                    tokens.append(digest(['help',name,row['executable_signature'],help_record['sha256']]))
        except (ValueError,OSError,KeyError,TypeError):continue
    for row in acquisition.recipes(project):
        if row['artifact'] not in outputs:continue
        try:
            args=json.loads(row['args_json'])
            if '{{output}}' not in args or acquisition.script_needs_review(row['id'],project):continue
            acquisition._build_recipe_command(row,'placeholder.input' if '{{input}}' in args else '',
                                               allow_future_input=True)
            tokens.append(digest(['recipe',row['id'],row['executable_signature'],row['args_json'],
                                  row['artifact'],row.get('script_saved_sha','')]))
        except (ValueError,OSError,KeyError,TypeError):continue
    return sorted(set(tokens))

def resume(drafts,conversations,acquisition,janus,source):
    if not source:return None
    binding=source_binding(source)
    if not current_source(binding,conversations):return None
    draft=drafts.latest(binding)
    if not draft or draft['state']!='missing':return None
    req=conversations.get(draft['request_id'])
    if not req or req['state']!='responded':return None
    proposal=json.loads(draft['proposal'])
    if not proposal['missing']:return None
    tokens=observations(acquisition,janus,source['project'],proposal)
    if not current_source(binding,conversations):return None
    if not drafts.reserve_resume(req['id'],tokens):return None
    if conversations.change(req['id'],'pending','New tool capability evidence; resume the same reviewed workflow',
                            allowed=('responded',)):
        return req['id']
    return None
