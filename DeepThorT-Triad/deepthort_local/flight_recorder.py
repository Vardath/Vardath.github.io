"""Low-overhead, local-first diagnostic flight recorder.

Writes structured rotating logs to state/logs. Never records raw prompts,
model replies, file contents, credentials or environment variable values.
The user may export a diagnostic ZIP from the desktop UI for troubleshooting.
"""
from __future__ import annotations

from contextlib import closing
import datetime as dt
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import platform
import tempfile
import hashlib
import shutil
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


class _WindowsRotatingHandler(RotatingFileHandler):
    """Release the Windows file lock between events so another process can rotate the log."""
    def emit(self, event):
        try:
            super().emit(event)
        finally:
            if self.stream is not None:
                self.stream.close()
                self.stream = None


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
            handler_type = _WindowsRotatingHandler if os.name == 'nt' else RotatingFileHandler
            handler = handler_type(path / f'{component}.jsonl', maxBytes=LOG_BYTES,
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
    with closing(sqlite3.connect(f'file:{Path(dbpath).resolve().as_posix()}?mode=ro', uri=True, timeout=1.5)) as conn, conn:
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
                    safe=[x for x in ('id','state','detail','last_focus','cycle','paused','updated_at','stamp','level','kind','status','returncode','pid') if x in cols]
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


def verify_diagnostics_archive(path):
    """Verify completed ZIP, CRC and readable summary before reporting success."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size < 120:
        raise OSError('Diagnostic ZIP is missing or too small')
    with zipfile.ZipFile(path, 'r') as z:
        names=z.namelist()
        if 'summary.json' not in names:
            raise ValueError('Diagnostic ZIP lacks summary.json')
        bad=z.testzip()
        if bad:
            raise ValueError('Diagnostic ZIP has a corrupt member: '+bad)
        info=json.loads(z.read('summary.json'))
        if not isinstance(info,dict) or info.get('diagnostics_format') != 1:
            raise ValueError('Unrecognized diagnostic format')
    return {'path':str(path.resolve()),'size':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def retain_diagnostic_copy(source, backup, receipt_path):
    """Always keep a predictable copy and an exact path receipt.

    Does not invent a success if the primary export or retained copy is missing.
    """
    src=verify_diagnostics_archive(source)
    target=Path(backup)
    target.parent.mkdir(parents=True,exist_ok=True)
    if Path(src['path']) != target.resolve():
        fd,tmp=tempfile.mkstemp(prefix='.deepthort-diagnostic-',suffix='.zip',dir=target.parent)
        try:
            with os.fdopen(fd,'wb') as out, open(source,'rb') as inp:
                shutil.copyfileobj(inp,out)
                out.flush();os.fsync(out.fileno())
            verify_diagnostics_archive(tmp)
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    retained=verify_diagnostics_archive(target)
    if src['sha256'] != retained['sha256']:
        raise ValueError('Retained diagnostic copy failed SHA-256 comparison')
    receipt={'chosen_path':src['path'],'retained_path':retained['path'],
             'sha256':src['sha256'],'bytes':src['size'],
             'saved_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    destination=Path(receipt_path)
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.diagnostic-receipt-',suffix='.json',dir=destination.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as out:
            json.dump(receipt,out,indent=2)
            out.flush();os.fsync(out.fileno())
        os.replace(tmp,destination)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return receipt


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
    try:
        from .planning_metrics import inference_report
        summary['inference_metrics']=inference_report(state/'logs')
    except (OSError,ValueError,TypeError):
        summary['inference_metrics']={'status':'unavailable'}
    # On-demand, read-only recovery health; no state file is modified.
    try:
        from .state_health import inspect_state
        summary['state_health']=inspect_state(state)
    except (OSError,ValueError) as exc:
        summary['state_health']={'issues':['State health inspection unavailable'],
                                 'error_type':type(exc).__name__}
    if app_root:
        root=Path(app_root)
        from .triad_profiles import PROFILES,model_path,runtime_path
        for name in ('START TRIAD.cmd','desktop_app.py','triad_server.py',
                     str(runtime_path(root).relative_to(root)),
                     *(str((model_path(role,root)/'openvino_model.bin').relative_to(root)) for role in PROFILES),
                     *(str((model_path(role,root)/'verified-install.json').relative_to(root)) for role in PROFILES)):
            target=root/name
            summary['installation_checks'][name]={'exists':target.exists(),
                 'file_bytes':target.stat().st_size if target.is_file() else None}
    for name in ('jobs','conversations','janus','sentinel'):
        try: summary['storage'][name]=_db_summary(state/f'{name}.sqlite3',name)
        except Exception as error: summary['storage'][name]={'inspection_error': scrub(str(error))}
    summary=scrub(summary)
    fd,temp_path=tempfile.mkstemp(prefix='.deepthort-export-',suffix='.zip',dir=destination.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temp_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            z.writestr('summary.json',json.dumps(summary,indent=2,ensure_ascii=False,default=str))
            logs=state/'logs'
            if logs.is_dir():
                for item in sorted(logs.glob('*.jsonl*')):
                    if item.is_file() and item.stat().st_size <= LOG_BYTES+5000:
                        z.write(item,arcname='logs/'+item.name)
            # Native worker logs are essential when a process exits before
            # reporting an HTTP error; include only bounded scrubbed tails.
            for item in sorted(logs.glob('triad-*.log'))[:24]:
                if item.is_file():
                    try:
                        with item.open('rb') as handle:
                            handle.seek(max(0,item.stat().st_size-8192))
                            tail=handle.read(8192).decode('utf-8',errors='replace')
                        z.writestr('native-log-tails/'+item.name+'.txt',scrub(tail))
                    except OSError:pass
            # Preserve existing action output logs only as short redacted tails; arbitrary tools
            # can output credentials or entire file contents, so NEVER include raw files.
            for item in sorted((state/'janus-process-logs').glob('action-*.log'))[-20:]:
                if item.is_file():
                    with item.open('rb') as handle:
                        if item.stat().st_size>4096:handle.seek(-4096,2)
                        tail=handle.read().decode('utf-8',errors='replace')
                    z.writestr('action-output-tails/'+item.name+'.redacted.txt', scrub(tail))
        verify_diagnostics_archive(temp_path)
        # Windows scanners may hold a newly written archive briefly.
        import time
        for attempt in range(5):
            try:
                os.replace(temp_path,destination)
                break
            except PermissionError:
                if attempt==4:raise
                time.sleep(.2*(attempt+1))
        verify_diagnostics_archive(destination)
    finally:
        if os.path.exists(temp_path):
            try:os.unlink(temp_path)
            except OSError:pass  # Keep the original failure, not a cleanup error.
    return destination
