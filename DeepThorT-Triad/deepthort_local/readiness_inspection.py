"""Local readiness observations, never an installation or connectivity test."""
from pathlib import Path
from contextlib import closing
import sqlite3
import json
import time
from . import triad_profiles as profiles
from . import creative_profile, multimedia_profile

def _small_receipt(path):
    return not path.is_symlink() and path.is_file() and path.stat().st_size<=65536

def model_records(root,health,pid,creative_active=False):
    from .lattice_ui import operative_rows
    observations={key:values[2] for key,values in operative_rows(health,pid,creative_active)}
    result=[]
    for role,label in (('janus','JANUS'),('sentinel','Sentinel'),('implementation','Granite'),('memory','Memory')):
        status='Missing or invalid receipt'
        try:
            base=profiles.model_path(role,root)
            if _small_receipt(base/'verified-install.json') and profiles.installed_files(role,root):
                status='File sizes match install receipt'
                if _small_receipt(base/'native-smoke.json') and profiles.smoke_verified(role,root):
                    status='Install and historical smoke receipts match'
        except (OSError,ValueError,KeyError,TypeError,AttributeError):pass
        result.append((role,(label,profiles.ALL_PROFILES[role][0],status,observations[role])))
    result.append(('gemma',('Gemma','Gemma 4 E2B INT4',
        'File sizes match install receipt' if creative_profile.installed(root) else 'Missing or invalid receipt',
        observations['gemma'])))
    result.append(('diffusion',('Production tool','Stable Diffusion 1.5 INT8',
        'File sizes match install receipt' if multimedia_profile.installed(root) else 'Missing or invalid receipt',
        'Not an intelligent operative; no runtime test')))
    marker=Path(root)/'runtime'/'openvino-verified.json'
    runtime=False
    try:
        runtime=_small_receipt(marker) and profiles.runtime_path(root).is_file() and json.loads(marker.read_text('utf-8')).get('version')==profiles.RUNTIME_VERSION
    except (OSError,ValueError,TypeError,AttributeError):pass
    result.append(('runtime',('Shared runtime','OpenVINO '+profiles.RUNTIME_VERSION,
        'Runtime marker and executable present' if runtime else 'Missing or invalid marker','No runtime test')))
    return result

def integration_records(project,janus_path,session=None,shared_busy=False,now=None):
    """No token access, network calls, catalog initialization or tool calls."""
    status='No local session recorded'
    if session is not None:
        expiry=getattr(session,'expires',None)
        status=('Unexpired session object; not revalidated' if type(expiry) in (int,float) and expiry>(time.monotonic() if now is None else now)
                else 'Expired or unavailable session metadata')
    mcp='No selected workspace'
    if project and project!='(general)':
        try:
            with closing(sqlite3.connect(Path(janus_path).resolve(strict=True).as_uri()+'?mode=ro',
                                        uri=True,timeout=.25)) as db:
                db.execute('PRAGMA query_only=ON')
                exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_mcp_catalog'").fetchone()
                count=db.execute('SELECT count(*) FROM local_mcp_catalog WHERE project=?',(str(Path(project).resolve(strict=True)),)).fetchone()[0] if exists else 0
            mcp=f'{count} stored discovery entries; not validated'
        except (OSError,ValueError,sqlite3.Error):mcp='Catalog unavailable'
    return [
        ('github',('GitHub device OAuth',status,'Read-only local session; no token read or provider check')),
        ('mcp',('Local MCP',mcp,'Workspace historical catalog only; no discovery or call')),
        ('drive',('Google Drive','Explicit operation required','Credentials and connectivity not inspected')),
        ('gmail',('Gmail','Explicit operation required','Credentials and connectivity not inspected')),
        ('api',('Local developer API','Explicit temporary session','No listener probe; requires existing reviewed controls')),
        ('webhook',('Local webhook','Explicit temporary session','No listener probe; requires existing reviewed controls')),
        ('shared',('Shared integration activity','Busy flag set' if shared_busy else 'Busy flag not set','Not service-specific readiness or connectivity')),
    ]
