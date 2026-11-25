"""Read-only carry-forward evidence from the exact predecessor revision chain.

No earlier approval, test result or saved step state transfers to the new plan.
The model sees historical intentions alongside observed current file hashes.
"""
from __future__ import annotations
import json
from pathlib import Path
from .workspace import safe_target
from .reasoning_council import sha
from .agent_plan import PlanError

MAX_HISTORY_FILES=120
MAX_FILE_BYTES=2_000_000


def predecessor_steps(conversations,index,hierarchies,request_id):
    current=conversations.get(request_id)
    history=conversations.amendment_history(request_id)
    if not current or not history:return []
    # Search nearest usable predecessor; an interrupted amendment may not have
    # a plan yet. Never import files from another project/chat.
    for item in reversed(history):
        previous=conversations.get(item['parent_request_id'])
        if not previous or (previous['project'],previous['chat_id'])!=(current['project'],current['chat_id']):
            raise PlanError('Historical specification belongs to another project or chat')
        draft=conversations.historical_draft(previous['id'])
        if draft:
            if draft['original_prompt']!=previous['prompt'] or draft['project']!=previous['project'] or draft['chat_id']!=previous['chat_id']:
                raise PlanError('Historical draft differs from its original request')
            return draft['steps'][:MAX_HISTORY_FILES]
        if hierarchies.has_roadmap(previous['id']):
            return hierarchies.milestone(index,previous['id'],previous['prompt'],1)['master_steps'][:MAX_HISTORY_FILES]
        try:
            steps=index.merged_steps(previous['id'],previous['prompt'])
        except (ValueError,PlanError):
            continue
        if steps:return steps[:MAX_HISTORY_FILES]
    return []


def historical_context(project,steps,focus='',*,max_chars=1400):
    if not steps or max_chars<250:return ''
    root=Path(project).resolve(strict=True)
    words=set(str(focus).casefold().split())
    ranked=sorted(steps,key=lambda step:-sum(w in (step['path']+' '+step['description']).casefold() for w in words if len(w)>3))
    result='PRIOR PLAN AND CURRENT WORKSPACE (historical evidence, not approval):\nPreserve compatible work; revise only what user amendments require. Existing files are not proof of completion.\n'
    for step in ranked[:MAX_HISTORY_FILES]:
        try:
            dest=safe_target(root,step['path'])
            if dest.is_file() and dest.stat().st_size<=MAX_FILE_BYTES:
                import hashlib
                digest=hashlib.sha256(dest.read_bytes()).hexdigest()
                state='exists sha256='+digest
            elif dest.exists():state='exists; content not inspected'
            else:state='not present'
        except (OSError,ValueError):continue
        line=json.dumps({'path':step['path'],'prior_intention':step['description'][:240],
                         'observed':state},ensure_ascii=False)+'\n'
        if len(result)+len(line)>max_chars:continue
        result+=line
    return result


def attach_history(prompt,project,steps,focus='',*,max_chars=7500):
    history=historical_context(project,steps,focus,max_chars=min(1400,max_chars-len(prompt)-2))
    return prompt+'\n\n'+history if history else prompt


def revision_context(original,history,focus='',*,max_chars=1300):
    """Chronological exact excerpts from the recorded amendment ledger.

    Always prioritize the newest correction and use remaining space for earlier
    relevant corrections. A bounded excerpt is labelled, never a replacement
    for the complete immutable revision. No model summaries are trusted here.
    """
    if not history:return ''
    import re
    from .recovery_council import select_source_section
    words=set(re.findall(r'[a-z0-9_]{4,}',str(focus).casefold()))
    checked=[]
    for n,row in enumerate(history,1):
        text=row['amendment']
        if row['ordinal']!=n or sha(text)!=row['amendment_sha256'] or text not in original:
            raise PlanError('Recorded user amendment is inconsistent with current specification')
        checked.append((n,text))
    header=('USER AMENDMENTS (exact stored text or labelled excerpts; newest explicit '
            'correction wins only where it conflicts; preserve all unaffected requirements):\n')
    if max_chars<len(header)+100:return ''
    newest=checked[-1]
    ranked=[newest]+sorted(checked[:-1],key=lambda x:(
        -sum(w in x[1].casefold() for w in words),-x[0]))
    selected=[]
    room=max_chars-len(header)
    for n,text in ranked:
        label=f'Amendment {n}: '
        if len(label)+len(text)+1<=room:
            entry=label+text+'\n'
        elif n==newest[0] and room>=340:
            limit=min(3200,room-len(label)-35)
            excerpt=select_source_section(text,focus,limit)
            entry=label+'[verbatim excerpt, not complete] '+excerpt+'\n'
            if len(entry)>room:continue
        else:continue
        selected.append((n,entry))
        room-=len(entry)
    if not selected:return ''
    return header+''.join(x[1] for x in sorted(selected))


def attach_revision_context(prompt,original,history,focus='',*,max_chars=7500):
    context=revision_context(original,history,focus,max_chars=min(1300,max_chars-len(prompt)-2))
    return prompt+'\n\n'+context if context else prompt
