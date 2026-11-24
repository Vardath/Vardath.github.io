"""v43: bounded post-install executable discovery and independent version evidence.

An installer exit code, Windows uninstall registry row and a file on disk are
NOT proof of functionality. Only a small immutable list of noninteractive CLI
version commands may run automatically, from the local curated WinGet catalog.
Graph/project acceptance and vendor signature verification are separate tasks.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .computer_inventory import INSTALL_CATALOG, TOOL_SPECS
from .diagnostic_evidence import read_snapshot, save_snapshot

SCHEMA = 'deepthort-tool-verification-v43'
MAX_RECORDS = 120
MAX_OUTPUT = 10000
PROBE_TIMEOUT = 12
MAX_CANDIDATES = 160
VALID_STATUSES = frozenset({'version_verified','located_only','not_found',
                            'probe_failed','changed_since_verification'})

# Every parameter is coded here, not derived from a model, website or WinGet output.
# Desktop-only tools deliberately have no unattended probe: --version may open UI.
PROBES = {
    'Python': (('--version',), r'\bPython\s+\d+\.\d+'),
    'Node.js': (('--version',), r'\bv\d+\.\d+'),
    'Git': (('--version',), r'\bgit version\s+\d+'),
    'Blender': (('--background','--version'), r'\bBlender\s+\d+\.\d+'),
    'Godot': (('--headless','--version'), r'\b(?:Godot Engine\s*)?v?\d+\.\d+'),
    'Java': (('-version',), r'\b(?:openjdk|java)\s+version\s+["\']?\d+'),
    'FFmpeg': (('-version',), r'\bffmpeg version\s+\S+'),
    '7-Zip': (('-h',), r'\b7-Zip\s+\S+'),
    'Pandoc': (('--version',), r'\bpandoc\s+\d+\.\d+'),
    'Inkscape': (('--version',), r'\bInkscape\s+\d+\.\d+'),
    'LibreOffice': (('--version',), r'\bLibreOffice\s+\d+\.\d+'),
}
# Some commonly used catalog executables have variable filenames after WinGet.
ADDITIONAL_NAMES = {'Godot': ('godot', 'Godot_v4.6-stable_win64_console.exe')}


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _safe_digest(path: Path) -> str:
    """Stable stat receipt, not a cryptographic authenticity / publisher proof."""
    st = path.stat()
    return hashlib.sha256(json.dumps([str(path.resolve()).casefold(), st.st_size,
                                      st.st_mtime_ns], separators=(',',':')).encode()).hexdigest()


def _windows_registry_paths():
    if os.name != 'nt':
        return []
    try:
        import winreg
        paths=[]
        for key, subkey in ((winreg.HKEY_LOCAL_MACHINE,
                             r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
                            (winreg.HKEY_CURRENT_USER, r'Environment')):
            try:
                with winreg.OpenKey(key, subkey) as node:
                    entry = winreg.QueryValueEx(node, 'Path')[0]
                    if isinstance(entry, str): paths += entry.split(';')
            except OSError:
                continue
        return paths
    except ImportError:
        return []


def refreshed_path(environ=None, *, registry_paths=None):
    """Refresh prospective child PATH; do not modify global environment or registry."""
    env = dict(os.environ if environ is None else environ)
    separator = ';' if os.name == 'nt' else os.pathsep
    paths = env.get('PATH', '').split(separator)
    paths += (_windows_registry_paths() if registry_paths is None else list(registry_paths))
    local = env.get('LOCALAPPDATA')
    if local:
        paths.append(str(Path(local)/'Microsoft'/'WinGet'/'Links'))
    seen=set();out=[]
    for item in paths:
        item=os.path.expandvars(str(item).strip().strip('"'))
        key=os.path.normcase(os.path.normpath(item))
        if item and key not in seen and Path(item).is_dir():
            out.append(item);seen.add(key)
    env['PATH']=separator.join(out)
    return env


def _allowed_basename(name, path):
    spec=TOOL_SPECS.get(name)
    if not spec:return False
    filename=Path(path).name.casefold()
    names={v.casefold() for v in spec[1]}
    if filename in names or filename in {v.casefold() for v in ADDITIONAL_NAMES.get(name,())}:
        return True
    return name=='Godot' and bool(re.fullmatch(r'godot_v\d+[a-z0-9._-]*\.exe',filename))


def _candidate_paths(name, *, environ=None, which=None, extra_roots=()):
    """Only exact known locations and bounded WinGet package subtrees; no disk crawl."""
    env=dict(os.environ if environ is None else environ)
    resolver=which or (lambda exe: shutil.which(exe,path=env.get('PATH')))
    filenames=TOOL_SPECS[name][1]+ADDITIONAL_NAMES.get(name,())
    found=[];seen=set()
    def add(path):
        if not path or len(found)>=MAX_CANDIDATES:return
        p=Path(path)
        try:
            if not _allowed_basename(name,p) or not p.is_file() or p.is_symlink():return
            resolved=p.resolve(strict=True)
            key=str(resolved).casefold()
            if key not in seen:seen.add(key);found.append(resolved)
        except (OSError,ValueError):pass
    for exe in filenames:
        add(resolver(exe))
    for prefix in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        root=env.get(prefix)
        if not root:continue
        base=Path(root)
        hints=TOOL_SPECS[name][2]
        for hint in hints:
            for exe in filenames:
                add(base/hint/exe)
                add(base/hint/'bin'/exe)
        if name=='Python' and prefix=='LOCALAPPDATA':
            for folder in sorted((base/'Programs'/'Python').glob('Python3*'))[:16]:
                add(folder/'python.exe')
        if name=='Java' and prefix.startswith('ProgramFiles'):
            for folder in sorted((base/'Eclipse Adoptium').glob('jdk-*'))[:16]:
                add(folder/'bin'/'java.exe')
    local=env.get('LOCALAPPDATA')
    if local:
        packages=Path(local)/'Microsoft'/'WinGet'/'Packages'
        package_id=INSTALL_CATALOG[name][0]
        for folder in sorted(packages.glob(package_id+'_*'))[:12]:
            if not folder.is_dir() or folder.is_symlink():continue
            # The package may wrap the binary in one or two subfolders.
            containers=[folder]
            for sub in sorted(folder.iterdir())[:24]:
                if sub.is_dir() and not sub.is_symlink():
                    containers.append(sub)
                    for nested in sorted(sub.iterdir())[:24]:
                        if nested.is_dir() and not nested.is_symlink():containers.append(nested)
            for container in containers[:70]:
                for exe in filenames:
                    add(container/exe);add(container/'bin'/exe)
    for root in list(extra_roots)[:8]:
        for exe in filenames:
            add(Path(root)/exe);add(Path(root)/'bin'/exe)
    return found


def verify_catalog_tool(name, *, environ=None, which=None, extra_roots=(),
                        runner=None, timeout=PROBE_TIMEOUT, project='',
                        install_plan_sha256='', install_exit_code=None):
    """Check an actual executable with an immutable, bounded version probe.

    runner may be substituted only by tests. Never accept argv from a model or
    installer stdout. Unprobed GUI apps remain *located only*.
    """
    if name not in INSTALL_CATALOG or name not in TOOL_SPECS:
        raise ValueError('Only fixed curated WinGet catalog tools may be checked')
    if timeout>PROBE_TIMEOUT or timeout<=0:
        raise ValueError('Unbounded version probe refused')
    env=refreshed_path(environ)
    candidates=_candidate_paths(name,environ=env,which=which,extra_roots=extra_roots)
    row={'schema':SCHEMA,'tool':name,'package_id':INSTALL_CATALOG[name][0],
         'project':str(project)[:1024], 'install_plan_sha256':str(install_plan_sha256)[:64],
         'install_exit_code':install_exit_code, 'observed_at':_utc(),
         'status':'not_found','executable':'','identity_sha256':'',
         'version':'','probe_argv':[], 'probe_exit_code':None,
         'probe_output_sha256':'','probe_excerpt':'',
         'publisher_signature_verified':False,'functional_project_test_passed':False}
    if not candidates:return row
    row['executable']=str(candidates[0]);row['identity_sha256']=_safe_digest(candidates[0])
    if name not in PROBES:
        row['status']='located_only'
        row['probe_excerpt']='GUI application: no safe noninteractive version probe approved'
        return row
    argv_tail,pattern=PROBES[name]
    execute=runner or subprocess.run
    # PATH refresh for the child only; no global environment mutation.
    env['PATH']=str(candidates[0].parent)+(';' if os.name=='nt' else os.pathsep)+env.get('PATH','')
    for path in candidates[:5]:
        cmd=[str(path),*argv_tail]
        try:
            result=execute(cmd,shell=False,capture_output=True,text=True,
                           encoding='utf-8',errors='replace',timeout=timeout,
                           env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)
                           if os.name=='nt' else 0)
            output=((result.stdout or '')+'\n'+(result.stderr or ''))[:MAX_OUTPUT]
            match=re.search(pattern,output,re.IGNORECASE)
            row.update(executable=str(path),identity_sha256=_safe_digest(path),
                       probe_argv=cmd,probe_exit_code=result.returncode,
                       probe_output_sha256=hashlib.sha256(output.encode()).hexdigest(),
                       probe_excerpt=' '.join(output.split())[:300])
            if result.returncode==0 and match:
                row['status']='version_verified'
                row['version']=match.group(0)[:120]
                return row
        except (OSError,subprocess.TimeoutExpired) as exc:
            row['probe_excerpt']=type(exc).__name__[:80]
            row['probe_argv']=cmd
    row['status']='probe_failed'
    return row


class ToolVerificationStore:
    """Durable bounded receipts. A receipt never implies sandboxed/signed code."""
    def __init__(self, path):
        self.path=Path(path)

    def get(self, name):
        data=read_snapshot(self.path)
        if not isinstance(data,dict) or data.get('schema')!=SCHEMA:return None
        value=(data.get('tools') or {}).get(name)
        return value if isinstance(value,dict) and value.get('schema')==SCHEMA else None

    def record(self,row):
        if not isinstance(row,dict) or row.get('schema')!=SCHEMA or \
                row.get('tool') not in INSTALL_CATALOG or row.get('status') not in VALID_STATUSES:
            raise ValueError('Invalid tool verification receipt')
        previous=read_snapshot(self.path)
        if not isinstance(previous,dict) or previous.get('schema')!=SCHEMA:
            previous={'schema':SCHEMA,'tools':{},'history':[]}
        tools=dict(previous.get('tools') or {});tools[row['tool']]=row
        history=list(previous.get('history') or [])
        history.append({'tool':row['tool'],'status':row['status'],
                        'observed_at':row.get('observed_at'),'identity_sha256':row.get('identity_sha256')})
        entry={'schema':SCHEMA,'tools':tools,'history':history[-MAX_RECORDS:]}
        if not save_snapshot(self.path,entry):raise OSError('Could not persist tool verification evidence')
        return row

    def current(self,name,*,max_age_days=14):
        """Read-only invalidation when executable changed or proof got stale."""
        row=self.get(name)
        if not row or row.get('status')!='version_verified':return None
        try:
            when=datetime.fromisoformat(row['observed_at'])
            if when.tzinfo is None or datetime.now(timezone.utc)-when>timedelta(days=max_age_days):return None
            path=Path(row['executable'])
            if not path.is_file() or path.is_symlink() or not _allowed_basename(name,path):return None
            if _safe_digest(path)!=row['identity_sha256']:return None
        except (ValueError,TypeError,KeyError,OSError):return None
        return row
