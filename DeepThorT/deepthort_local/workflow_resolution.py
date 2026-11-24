"""Bounded workflow capability resolution; no command or installer authority."""
from __future__ import annotations
import json
import subprocess
from .tool_workflows import digest
from .workflow_design import source_binding

def resolve(drafts,acquisition,janus,council,client,*,request_id,request,goal,
            proposal,manifest,review,design,learn,discovery=None,online=False,
            cancelled=None,stage=None,recovery=None,mixed_task=None):
    if not proposal['missing']:return proposal,manifest,[],[]
    def check():
        if cancelled and cancelled():raise ValueError('Workflow resolution cancelled')
    check()
    original_missing=list(proposal['missing'])
    learned=learn(drafts,acquisition,janus,council,client,
                  request_id=request_id,request=request,proposal=proposal,review=review,
                  cancelled=cancelled,stage=stage)
    check()
    candidates=sorted({x['recipe_id'] for x in learned if x['state']=='candidate'})
    # Reserve before inference. A restart or repeated reply cannot endlessly
    # spend model calls on the same exact missing capabilities.
    if candidates:
        key=digest([source_binding(request),goal,proposal,candidates,mixed_task,recovery])
        if drafts.reserve_resolution(key):
            try:
                replacement,new_manifest=design(acquisition,council,client,request=request,goal=goal,
                    review=review,stage=stage,cancelled=cancelled,recovery=recovery,mixed_task=mixed_task)
                check()
                if len(replacement['missing'])<len(proposal['missing']):
                    proposal,manifest=replacement,new_manifest
                    drafts.save(request_id,proposal,manifest)
            except (ValueError,OSError,KeyError,TypeError):
                check() # retain original durable reviewed proposal on failure
    check()
    found=[]
    # Only a remaining unresolved stage with no installed tool warrants the
    # public catalog. At most one search per exact reviewed gap/specification.
    if online and discovery and proposal['missing']:
        unknown=[original_missing[x['gap']-1] for x in learned if x['state']=='needs_tool' and 1<=x['gap']<=len(original_missing)]
        # Match the original exact gap, not its ordinal after redesign.
        for gap in proposal['missing']:
            if gap not in unknown:continue
            key=digest([source_binding(request),gap,'public-capability-discovery'])
            if not drafts.reserve_resolution(key):continue
            try:
                found=discovery(gap,key,cancelled)
            except (ValueError,OSError,KeyError,subprocess.SubprocessError):
                check()
            break
    return proposal,manifest,learned,found
