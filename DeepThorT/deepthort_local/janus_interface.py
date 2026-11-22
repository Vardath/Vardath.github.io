"""Read-only JANUS Interface replies from verified local state, without Qwen.

This is an outward Interface report about the existing JANUS Front and durable
queues, NOT unrestricted neural text generation. It never schedules or approves
work and never infers unseen progress. The single ONNX worker can remain busy.
"""
from __future__ import annotations

import json
import re


def addressed_to_janus(prompt: str) -> bool:
    """Only route an explicitly addressed chat turn; ordinary chats stay on Qwen."""
    return bool(re.match(r'^\s*(?:@janus|janus)\b(?=\s|[:!?.,]|$)', prompt or '', re.I))


def janus_state_reply(prompt: str, *, status: dict, goal: str,
                      sentinel: dict, job_counts: dict, model_health: dict | None,
                      active_reply: bool = False,
                      latest_action: dict | None = None,
                      latest_recommendation: dict | None = None) -> str:
    """Format evidence already stored by JANUS/Sentinel and the local model.

    It must not give the impression the deterministic coordinator can write an
    arbitrary prose answer or operate on behalf of the busy language model.
    """
    try:
        cores = json.loads(status.get('cores_json') or '{}')
    except (ValueError, TypeError):
        cores = {}
    front = cores.get('Front') if isinstance(cores, dict) else None
    front = front if isinstance(front, dict) else {}
    health = model_health if isinstance(model_health, dict) else {}
    is_busy = bool(health.get('inference_busy') or active_reply)
    if is_busy:
        model = 'Qwen is occupied by another inference request.'
    elif health.get('ready') is True:
        model = 'Qwen reports ready and not currently busy.'
    elif health.get('phase') == 'failed':
        model = 'Qwen reports a failed worker; see Processes/Diagnose AI.'
    else:
        model = 'Qwen readiness is not verified from the current status sample.'
    lines = [
        'JANUS LOCAL INTERFACE — verified status, no language-model inference',
        f'JANUS: {"paused" if status.get("paused") else "active"}; recorded cycles: {int(status.get("cycle") or 0)}.',
        f'Primary goal: {(goal or front.get("goal") or "not set")[:240]}',
        f'Front focus: {str(status.get("last_focus") or front.get("focus") or "not recorded")[:180]}',
        f'Front decision: {str(status.get("last_action") or front.get("priority") or "not recorded")[:180]}',
        f'Sentinel: {str(sentinel.get("state") or "unknown")[:60]}; {str(sentinel.get("detail") or "no detail")[:160]}',
        model,
        f'Approved-work queue states: {job_counts}.',
    ]
    if latest_action:
        lines.append('Latest approved process: '
                     f'{str(latest_action.get("label") or "unnamed")[:100]} '
                     f'[{str(latest_action.get("status") or "unknown")[:40]}].')
    if latest_recommendation:
        lines.append('Most recent JANUS recommendation (advisory, not executed): '
                     + str(latest_recommendation.get('proposal') or 'none')[:240])
    request = (prompt or '').casefold()
    if re.search(r'\b(stop|cancel|close|kill|terminate|pause|start|run|execute|build|approve)\b', request):
        lines.append('No action was taken. Use the existing Stop reply, Close chat or '
                     'approval controls; this status interface cannot authorize commands.')
    else:
        lines.append('JANUS can report recorded state while Qwen is busy. '
                     'It is not an independent general-purpose language model; '
                     'open-ended explanations and code planning still require inference.')
    return '\n'.join(lines)
