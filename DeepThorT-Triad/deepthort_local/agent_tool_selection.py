"""Deterministic task-aware tool ranking and whole-observation budgeting.

This is a lexical shortlist, not an embedding or a learned success model.
It does not grant permissions; only the current job's available registry
may be offered. The caller can expose all permitted tools on request.
"""
import re
import json

KEYWORDS={
    'search':{'find','search','symbol','interface','class','function','definition','api','implement','method'},
    'references':{'caller','callers','call','calls','uses','usage','reference','references','where','used'},
    'read_lines':{'read','inspect','source','line','lines','implementation','body','logic','code','exact'},
    'impact':{'impact','dependencies','dependency','dependent','dependents','break','regression','affected','import','imports'},
    'list_files':{'files','file','folder','directory','path','paths','locate','list','layout'},
    'diagnostics':{'failed','failure','error','errors','traceback','assertionerror','test','diagnostic','repair','crash'},
    'document_search':{'manual','documentation','document','guide','reference','docx','readme','tutorial','library','manuals','docs'},
    'git_history':{'git','commit','commits','history','branch','revision','revisions'},
    'checkpoint_diff':{'diff','compare','baseline','checkpoint','changed','change','previous','regression','difference'},
    'request_verification':{'verify','verification','test','tests','validate','check','retest','regression'}
}
# Explicit evidence is more useful to the implementation model than a
# long directory listing; ties prefer newer observations.
VALUE={'git_history':4,'document_search':5,'read_lines':6,'diagnostics':6,'checkpoint_diff':6,'impact':4,'references':4,'search':3,'list_files':2}
def words(text):
    return set(re.findall(r'[a-z][a-z0-9_]*',str(text).casefold()))

def shortlist(available,goal,observations=(),*,expanded=False):
    if expanded:return dict(available)
    terms=words(goal)
    ranked={}
    for name in available:
        if name=='done':continue
        ranked[name]=3*len(terms&KEYWORDS.get(name,set()))
    if 'search' in ranked:ranked['search']+=2
    if 'list_files' in ranked:ranked['list_files']+=1
    # Respond to concrete returned paths and source positions, not to
    # arbitrary instructions embedded in observations.
    for request,result,_ in observations:
        items=result.get('items',[])
        if not items:continue
        has_path=any('path' in item for item in items)
        has_line=any('line' in item for item in items)
        if has_path and 'read_lines' in ranked:ranked['read_lines']+=5+3*has_line
        if request['tool']=='search' and 'references' in ranked:ranked['references']+=2
        if request['tool']=='diagnostics' and 'checkpoint_diff' in ranked:ranked['checkpoint_diff']+=3
        if request['tool']=='impact' and 'read_lines' in ranked:ranked['read_lines']+=2
        if request['tool'] in ranked:ranked[request['tool']]-=2
    # Search stays available as the general discovery fallback. Three
    # actual tools plus done/catalog is a small bounded selection surface.
    names=['search'] if 'search' in ranked else []
    names.extend(n for n in sorted(ranked,key=lambda n:(-ranked[n],n)) if n not in names)
    chosen={n:available[n] for n in names[:3]}
    if 'done' in available:chosen['done']=available['done']
    if any(n not in chosen for n in available):chosen['more_tools']={}
    return chosen

def compact(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True)

def pack(observations,budget):
    """Select complete distinct observations only. Return in original order."""
    if budget<=0:return []
    candidates=[]
    seen=set()
    for i in reversed(range(len(observations))):
        record=observations[i]
        request,result,_=record
        if not result.get('items'):continue
        encoded=compact(result)
        if encoded in seen:continue
        seen.add(encoded)
        candidates.append((VALUE.get(request['tool'],1),i,len(encoded)+1))
    used=0;chosen=[]
    for _,i,size in sorted(candidates,reverse=True):
        if used+size<=budget:chosen.append(i);used+=size
    return [observations[i] for i in sorted(chosen)]
