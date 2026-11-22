"""Low-overhead, local-first diagnostic flight recorder.

Writes structured rotating logs to state/logs. Never records raw prompts,
model replies, file contents, credentials or environment variable values.
The user may export a diagnostic ZIP from the desktop UI for troubleshooting.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import platform
import re
import sqlite3
import sys
import threading
import traceback
import zipfile

LOG_BYTES = 3 * 1024 * 1024
LOG_COPIES = 3
_lock = threading.RLock()
_loggers = {}
_SECRET_PATTERNS = (
    (re.compile(r'(?i)\b(bearer\s+)[a-z0-9._~+/-]+'), r'\1[REDACTED]'),
    (re.compile(r'(?i)\b((?:password|secret|token|api[-_]?key|authorization|cookie)\s*[:=]\s*)[^\s,;]+'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(https?://)[^/@\s]+:[^/@\s]+@'), r'\1[REDACTED]@'),
    (re.compile(r'(?i)\bsk-[a-z0-9_-]{12,}\b'), '[REDACTED_API_KEY]'),
)


def scrub(value):
    """Keep diagnostic descriptions usable while reducing credential exposure."""
    if isinstance(value, str):
        out = value[:8000]
        for regex, replacement in _SECRET_PATTERNS:
            out = regex.sub(replacement, out)
        return out
    if value is None or isinstance(value, (bool, float, int)):
        return value
    if isinstance(value, dict):
        def sensitive(k):
            key=str(k)
            if re.search(r'(?i)(?:_characters|_length|_bytes|_count|_tokens)$',key):
                return False  # A numeric metric is not message content.
            return bool(re.search(r'(?i)secret|password|token|credential|api.?key|cookie|content|prompt|reply|message_body',key))
        return {str(k)[:100]: ('[REDACTED]' if sensitive(k) else scrub(v)) for k,v in list(value.items())[:80]}
    if isinstance(value, (tuple, list)):
        return [scrub(x) for x in value[:60]]
    return scrub(str(value))


class _JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds'),
            'pid': os.getpid(),
            'thread': threading.current_thread().name,
            'component': getattr(record, 'component', record.name),
            'level': record.levelname,
            'event': scrub(record.getMessage()),
        }
        fields = getattr(record,'fields',None)
        if fields: payload['data'] = scrub(fields)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _logger(state, component):
    path = Path(state).resolve() / 'logs'
    key = (str(path), component)
    with _lock:
        if key not in _loggers:
            path.mkdir(parents=True,exist_ok=True)
            name = f'deepthort.{component}.{os.getpid()}.{abs(hash(key))}'
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            handler = RotatingFileHandler(path / f'{component}.jsonl', maxBytes=LOG_BYTES,
                                           backupCount=LOG_COPIES, encoding='utf-8', delay=True)
            handler.setFormatter(_JSONFormatter())
            logger.addHandler(handler)
            _loggers[key] = logger
        return _loggers[key]


def record(state, component, event, level='INFO', **fields):
    try:
        logger = _logger(state, component)
        logger.log(getattr(logging, level.upper(), logging.INFO), str(event),
                   extra={'component': component, 'fields': fields})
    except Exception:
        # Diagnostics are best-effort and MUST NOT break real work.
        pass


def install_crash_hooks(state, component):
    """Record otherwise invisible background-thread and top-level failures."""
    previous_sys = sys.excepthook
    previous_thread = threading.excepthook
    def on_sys(t,v,tb):
        record(state,component,'uncaught_exception',level='ERROR',exception_type=t.__name__,
               stack=''.join(traceback.format_exception(t,v,tb))[-12000:])
        previous_sys(t,v,tb)
    def on_thread(args):
        record(state,component,'uncaught_thread_exception',level='ERROR',
               exception_type=args.exc_type.__name__, thread=args.thread.name if args.thread else None,
               stack=''.join(traceback.format_exception(args.exc_type,args.exc_value,args.exc_traceback))[-12000:])
        previous_thread(args)
    sys.excepthook=on_sys
    threading.excepthook=on_thread


def _db_summary(dbpath, kind):
    if not Path(dbpath).is_file(): return {'exists': False}
    output = {'exists': True, 'file_bytes': Path(dbpath).stat().st_size}
    with sqlite3.connect(f'file:{Path(dbpath).resolve().as_posix()}?mode=ro', uri=True, timeout=1.5) as conn:
        conn.row_factory=sqlite3.Row
        existing={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if kind=='jobs' and 'jobs' in existing:
            output['counts']=[dict(x) for x in conn.execute('SELECT state,COUNT(*) AS count FROM jobs GROUP BY state')]
            output['recent_jobs']=[dict(x) for x in conn.execute('''SELECT id,mode,state,created_at,updated_at,
                length(prompt) AS prompt_characters,length(result) AS result_characters,
                substr(detail,1,400) AS detail, chat_id FROM jobs ORDER BY id DESC LIMIT 100''')]
            if 'job_events' in existing:
                output['job_events']=[dict(x) for x in conn.execute('SELECT job_id,stamp,substr(note,1,600) AS note FROM job_events ORDER BY id DESC LIMIT 200')]
        if kind=='conversations':
            if 'conversation_requests' in existing:
                output['counts']=[dict(x) for x in conn.execute(
                    'SELECT mode,state,COUNT(*) AS count FROM conversation_requests GROUP BY mode,state')]
                output['recent_turns']=[dict(x) for x in conn.execute(
                    "SELECT id,mode,state,chat_id,created_at,updated_at,source_job_id, "
                    "length(prompt) AS prompt_characters,length(response) AS response_characters "
                    "FROM conversation_requests ORDER BY id DESC LIMIT 70")]
            if 'project_drafts' in existing:
                output['drafts']=[dict(x) for x in conn.execute(
                    "SELECT id,state,chat_id,queued_job_id,created_at,updated_at, "
                    "length(steps_json) AS plan_bytes FROM project_drafts ORDER BY id DESC LIMIT 70")]
        if kind=='janus':
            for table in ('janus_status','janus_events','janus_actions'):
                if table in existing:
                    cols=[x[1] for x in conn.execute(f'PRAGMA table_info({table})')]
                    safe=[x for x in ('id','state','detail','last_focus','cycle','updated_at','stamp','level','kind','status','returncode','pid') if x in cols]
                    if safe:
                        output[table]=[dict(x) for x in conn.execute(f'SELECT {",".join(safe)} FROM {table} ORDER BY rowid DESC LIMIT 40')]
        if kind=='sentinel':
            for table in ('sentinel_status','sentinel_events'):
                if table in existing:
                    cols=[x[1] for x in conn.execute(f'PRAGMA table_info({table})')]
                    safe=[x for x in ('id','state','detail','updated_at','stamp','level','description','janus_pid','sentinel_pid','last_janus_cycle','focus','decision','cycle') if x in cols]
                    if safe:
                        output[table]=[dict(x) for x in conn.execute(f'SELECT {",".join(safe)} FROM {table} ORDER BY rowid DESC LIMIT 40')]
    return scrub(output)


def export_diagnostics(state, destination, *, app_root=None, app_state=None):
    """Create ONE bounded support ZIP; never upload, include model weights or copy private SQLite DBs."""
    state = Path(state)
    destination = Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    summary = {
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'diagnostics_format': 1, 'operating_system': platform.platform(),
        'python_version': platform.python_version(),
        'privacy': 'No raw chat prompts, conversation databases, model weights or environment values copied. Short process-output tails may contain code or private project fragments; review ZIP before sharing.',
        'application_state': scrub(app_state or {}),
        'storage': {},
        'installation_checks': {},
    }
    # On-demand, read-only recovery health; no state file is modified.
    try:
        from .state_health import inspect_state
        summary['state_health']=inspect_state(state)
    except (OSError,ValueError) as exc:
        summary['state_health']={'issues':['State health inspection unavailable'],
                                 'error_type':type(exc).__name__}
    if app_root:
        root=Path(app_root)
        for name in ('DeepThorT.exe','desktop_app.py','inference_server.mjs','inference_worker.mjs',
                     'node_modules/@huggingface/transformers',
                     'models/onnx-community/Qwen2.5-Coder-1.5B-Instruct/onnx/model_q4.onnx'):
            target=root/name
            summary['installation_checks'][name]={'exists':target.exists(),
                 'file_bytes':target.stat().st_size if target.is_file() else None}
    for name in ('jobs','conversations','janus','sentinel'):
        try: summary['storage'][name]=_db_summary(state/f'{name}.sqlite3',name)
        except Exception as error: summary['storage'][name]={'inspection_error': scrub(str(error))}
    summary=scrub(summary)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('summary.json',json.dumps(summary,indent=2,ensure_ascii=False,default=str))
        logs=state/'logs'
        if logs.is_dir():
            for item in sorted(logs.glob('*.jsonl*')):
                if item.is_file() and item.stat().st_size <= LOG_BYTES+5000:
                    z.write(item,arcname='logs/'+item.name)
        # Preserve existing action output logs only as short redacted tails; arbitrary tools
        # can output credentials or entire file contents, so NEVER include raw files.
        for item in sorted((state/'janus-process-logs').glob('action-*.log'))[-20:]:
            if item.is_file():
                with item.open('rb') as handle:
                    if item.stat().st_size>4096:handle.seek(-4096,2)
                    tail=handle.read().decode('utf-8',errors='replace')
                z.writestr('action-output-tails/'+item.name+'.redacted.txt', scrub(tail))
    return destination
