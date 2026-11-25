"""Merge durable conversation requests, approved work and legacy chat history chronologically.

This is a DISPLAY concern. Neither message storage nor execution approval is changed.
Legacy model-history entries can be written AFTER requests (at generation completion),
so presenting the entire legacy database before the inbox falsely reverses chronology.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone


def _moment(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except (TypeError, ValueError):
        return datetime.min


def merged_chat_timeline(legacy_messages, requests, approved_jobs=()):
    """Yield chronologically ordered events. Older messages first, newest at bottom.

    An answer may also exist in the model's own successful-exchange history.
    Consume duplicates as complete user/assistant PAIRS, not by text membership:
    repeated legitimate prompts and separately saved diagnostic replies must survive.
    """
    completed_pairs = Counter(
        (r['prompt'], r['response']) for r in requests
        if r.get('mode') == 'chat' and r.get('state') == 'responded' and r.get('response')
    )
    timeline = []
    messages = list(legacy_messages)
    i = 0
    while i < len(messages):
        current = messages[i]
        next_one = messages[i + 1] if i + 1 < len(messages) else None
        if (current.get('role') == 'user' and next_one and
                next_one.get('role') == 'assistant'):
            pair = (current.get('content', ''), next_one.get('content', ''))
            if completed_pairs[pair]:
                completed_pairs[pair] -= 1
            else:
                timeline.append({'kind': 'legacy', 'created_at': current.get('created_at'),
                                 'seq': int(current.get('id') or i),
                                 'messages': [('user', pair[0]), ('assistant', pair[1])]})
            i += 2
            continue
        timeline.append({'kind': 'legacy', 'created_at': current.get('created_at'),
                         'seq': int(current.get('id') or i),
                         'messages': [(current.get('role', 'warning'), current.get('content', ''))]})
        i += 1
    for r in requests:
        timeline.append({'kind': 'request', 'created_at': r.get('created_at'),
                         'seq': int(r.get('id') or 0), 'row': r})
    for j in approved_jobs:
        if j.get('mode') == 'build' and j.get('state') in ('queued', 'running', 'paused', 'needs_input', 'failed'):
            timeline.append({'kind': 'job', 'created_at': j.get('created_at'),
                             'seq': int(j.get('id') or 0), 'row': j})
    timeline.sort(key=lambda e: (_moment(e.get('created_at')),
                                 # When tied, requests with an older ID are always stable.
                                 e.get('seq', 0),
                                 {'legacy': 0, 'request': 1, 'job': 2}[e['kind']]))
    return timeline
