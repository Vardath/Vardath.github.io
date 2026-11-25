"""Bounded, extractive context compaction. The durable transcript is untouched.

Historical exchanges are optional context, not authoritative requirements.
Current task instructions and system messages must remain byte-for-byte
unchanged. Never manufacture summaries or orphan an assistant reply.
"""
import re

MAX_HISTORY_CHARS=4800
MAX_HISTORY_PAIRS=3
STOP={'the','and','for','with','that','this','from','what','how','have','please','can','could','would','you','your','are','was','not','then','into','make'}

def words(text):
    return set(re.findall(r'[a-z0-9_]{3,}',text.casefold()))-STOP

def exchanges(rows):
    pairs=[]
    i=0
    while i+1<len(rows):
        first,second=rows[i:i+2]
        if first['role']=='user' and second['role']=='assistant':
            if not second['content'].startswith('LOCAL COMPUTER DIAGNOSTIC'):
                pairs.append((first,second))
            i+=2
        else:i+=1
    return pairs

def select_history(rows,prompt,budget):
    """Select whole exchanges: newest first, then relevant older exchanges.
    Restore chronological order so later user corrections follow earlier text.
    """
    pairs=exchanges(rows)
    remaining=min(MAX_HISTORY_CHARS,max(0,budget))
    selected=[];seen=set()
    query=words(prompt[:8000])
    if not pairs:return []
    def relevance(i):
        u,a=pairs[i]
        return 3*len(query&words(u['content']))+len(query&words(a['content']))
    recent=len(pairs)-1
    ranked=[recent]+sorted(range(recent),key=lambda i:(-relevance(i),-i))
    for i in ranked:
        u,a=pairs[i]
        if i!=recent and relevance(i)==0 and i<recent-1:continue
        identity=(u['content'],a['content'])
        if identity in seen:continue
        size=len(u['content'])+len(a['content'])
        if size>remaining or any(len(x['content'])>8000 for x in (u,a)):continue
        seen.add(identity);selected.append(i);remaining-=size
        if len(selected)>=MAX_HISTORY_PAIRS:break
    return [{'role':row['role'],'content':row['content']}
            for i in sorted(selected) for row in pairs[i]]

def fit_native(messages,tokens,limit,prepare):
    """Use the actual native chat template/tokenizer. Drop only complete
    oldest historical user/assistant pairs. Never cut the active request.
    prepare returns (native_history, actual_input_token_count).
    """
    current=[dict(m) for m in messages]
    removed=0
    while True:
        history,count=prepare(current)
        if count+tokens<=limit:return history,count,removed
        start=0
        while start<len(current)-1 and current[start]['role']=='system':start+=1
        if (start+1>=len(current)-1 or current[start]['role']!='user'
                or current[start+1]['role']!='assistant'):
            raise ValueError(f'Input {count} + output {tokens} exceeds {limit}-token Triad profile; use indexed planning')
        del current[start:start+2]
        removed+=1
