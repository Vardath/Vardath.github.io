"""Bridge reviewed missing workflow stages to the existing catalog policy.

Only exact catalog names that also have a fixed CLI probe and learned-tool
interface qualify. Unknown packages and help execution require separate review.
"""
from __future__ import annotations
import json
from .computer_inventory import INSTALL_CATALOG
from .tool_acquisition import HELP_FLAGS
from .tool_verification import PROBES
from .workflow_design import current_source,source_binding
from .verifier_recovery import recovery_action,install_plan

ELIGIBLE=set(INSTALL_CATALOG)&set(HELP_FLAGS)&set(PROBES)

def required_tools(drafts,conversations,source):
    if not source:return []
    binding=source_binding(source)
    if not current_source(binding,conversations):return []
    row=drafts.latest(binding)
    if not row or row['state']!='missing':return []
    request=conversations.get(row['request_id'])
    if not request or request['state']!='responded':return []
    proposal=json.loads(row['proposal'])
    names={g['capability'].strip().casefold() for g in proposal['missing']}
    return [(name,row['request_id']) for name in sorted(ELIGIBLE) if name.casefold() in names]

def next_operation(drafts,conversations,acquisition,verification,source,policy,history,*,which=None,now=None):
    if policy.get('enabled') is not True or policy.get('catalog_only') is not True or policy.get('source')!='winget':
        return None
    for name,ident in required_tools(drafts,conversations,source):
        try:acquisition.tool(name)
        except (ValueError,OSError):pass
        else:continue # Installed already; learning/help, not installation.
        receipt=verification.get(name)
        action,reason=recovery_action(name,policy,history,receipt,now=now)
        if action=='blocked':continue
        if action=='restore':
            current=verification.current(name)
            if not current:action='probe'
            else:return dict(action='restore',name=name,request_id=ident,receipt=current)
        if action=='probe':
            return dict(action='probe',name=name,request_id=ident)
        if action=='install':
            plan=install_plan(name,source['project'],policy,history,receipt,which=which,now=now)
            return dict(action='install',name=name,request_id=ident,plan=plan)
    return None

def still_required(drafts,conversations,source,request_id,name):
    return (name,request_id) in required_tools(drafts,conversations,source)


def review_recovery(operation,source,conversations,drafts,review,next_current,*,enabled):
    """Review exact workflow-originated probe/restore; no install authorization.
    A changed receipt, missing requirement or policy invalidates the decision.
    """
    if operation['action'] not in ('probe','restore'):
        raise ValueError('Not a workflow capability check')
    binding=source_binding(source)
    name=operation['name'];ident=operation['request_id']
    if not enabled() or not still_required(drafts,conversations,source,ident,name):
        raise ValueError('Workflow capability check no longer required')
    proposal={'action':operation['action'],'tool':name,
              'purpose':'Fixed catalog version probe or restore existing verified executable; no installation'}
    if operation['action']=='restore':
        proposal['receipt']=operation['receipt']
    if not review(binding,[ident,operation], 'Workflow capability '+operation['action']+' '+name,
                  'workflow_capability_'+operation['action'],proposal):
        return False
    if (not enabled() or not still_required(drafts,conversations,source,ident,name)
            or next_current()!=operation):
        raise ValueError('Workflow capability or evidence changed during review')
    return True
