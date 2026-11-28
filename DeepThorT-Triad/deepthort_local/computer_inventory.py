"""Low-impact, local-only Windows capability discovery for DeepThorT.

No network, installer execution or full-drive search occurs during discovery.
The inventory is a *snapshot*; detected programs are not automatically trusted to
execute arbitrary instructions from model output.
"""
from __future__ import annotations
import ctypes
import json
import os
import platform
import shutil
import sys
import subprocess
from ctypes import wintypes
from dataclasses import asdict, dataclass
from pathlib import Path

TOOL_SPECS = {
    'Python': ('Scripting / automation / tests', ('python.exe', 'py.exe'), ('Python',)),
    'Node.js': ('JavaScript / web apps', ('node.exe',), ('nodejs',)),
    'Git': ('Version control', ('git.exe',), ('Git',)),
    'Visual Studio Code': ('Code editor', ('code.cmd', 'code.exe'), ('Microsoft VS Code',)),
    'Blender': ('3D modelling, rendering and animation', ('blender.exe',), ('Blender Foundation', 'Blender')), 
    'Godot': ('2D and 3D game development', ('godot.exe', 'godot_console.exe'), ('Godot',)),
    'Unity Hub': ('Unity game development', ('Unity Hub.exe',), ('Unity Hub',)),
    'Unreal Engine': ('3D game development', ('UnrealEditor.exe',), ('Epic Games', 'UE_')),
    'Android Studio': ('Android game / application development', ('studio64.exe', 'studio.exe'), ('Android',)),
    'Java': ('Android / JVM build tools', ('java.exe',), ('Java', 'jdk-')),
    'Android Debug Bridge': ('Android device deployment', ('adb.exe',), ('platform-tools',)),
    '.NET SDK': ('C# and desktop / game projects', ('dotnet.exe',), ('dotnet',)),
    'MSBuild': ('Visual Studio project builds', ('MSBuild.exe',), ('Microsoft Visual Studio',)),
    'Docker': ('Isolated local build environments', ('docker.exe',), ('Docker',)),
    'Render CLI': ('Render hosting deployment; requires network', ('render.exe',), ('Render',)),
    '7-Zip': ('Project archive tools', ('7z.exe',), ('7-Zip',)),
    'FFmpeg': ('Video/audio encoding and media pipelines', ('ffmpeg.exe',), ('FFmpeg',)),
    'Audacity': ('Audio recording and editing', ('audacity.exe',), ('Audacity',)),
    'LibreOffice': ('Office documents, spreadsheets and book layout', ('soffice.exe',), ('LibreOffice',)),
    'Inkscape': ('SVG and vector illustration', ('inkscape.exe',), ('Inkscape',)),
    'GIMP': ('Raster graphics and image editing', ('gimp.exe',), ('GIMP',)),
    'Krita': ('Painting, illustration and animation', ('krita.exe',), ('Krita',)),
    'FreeCAD': ('CAD models and 3D printing', ('FreeCAD.exe',), ('FreeCAD',)),
    'Pandoc': ('Document conversion and publishing', ('pandoc.exe',), ('Pandoc',)),
}

# Users can choose which software to install. There is no inference-driven command
# assembly and no silent execution; this allowlist is all that winget can install.
INSTALL_CATALOG = {
    'Blender': ('BlenderFoundation.Blender', '3D rendering and modelling'),
    'Godot': ('GodotEngine.GodotEngine', '2D and 3D game engine'),
    'Git': ('Git.Git', 'Version control'),
    'Visual Studio Code': ('Microsoft.VisualStudioCode', 'Editor'),
    'Unity Hub': ('Unity.UnityHub', 'Unity project manager'),
    'Android Studio': ('Google.AndroidStudio', 'Android development IDE'),
    'Node.js': ('OpenJS.NodeJS.LTS', 'JavaScript runtime'),
    'Python': ('Python.Python.3.13', 'Python runtime'),
    'Java': ('EclipseAdoptium.Temurin.21.JDK', 'Java 21 LTS development kit'),
    'FFmpeg': ('Gyan.FFmpeg', 'Audio/video encoding'),
    'Audacity': ('Audacity.Audacity', 'Audio editing'),
    'LibreOffice': ('TheDocumentFoundation.LibreOffice', 'Office and document layout'),
    'Inkscape': ('Inkscape.Inkscape', 'Vector graphics'),
    'GIMP': ('GIMP.GIMP', 'Raster image editor'),
    'Krita': ('KDE.Krita', 'Painting and illustration'),
    'FreeCAD': ('FreeCAD.FreeCAD', 'Parametric CAD'),
    'Pandoc': ('JohnMacFarlane.Pandoc', 'Document conversion'),
    '7-Zip': ('7zip.7zip', 'Archive tool'),
}



@dataclass
class Tool:
    name: str
    purpose: str
    found: bool
    location: str = ''
    source: str = ''


def _win_registry_apps():
    if os.name != 'nt':
        return []
    try:
        import winreg
    except ImportError:
        return []
    records = []
    roots = ((winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
             (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
             (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'))
    for hive, path in roots:
        try:
            with winreg.OpenKey(hive, path) as node:
                for i in range(min(3500, winreg.QueryInfoKey(node)[0])):
                    try:
                        with winreg.OpenKey(node, winreg.EnumKey(node, i)) as child:
                            def get(key):
                                try: return str(winreg.QueryValueEx(child, key)[0])
                                except OSError: return ''
                            name = get('DisplayName')
                            if name:
                                records.append((name.casefold(), get('InstallLocation')))
                    except OSError: continue
        except OSError: continue
    return records


def _common_roots(environ=None):
    env = environ if environ is not None else os.environ
    names = ['ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA', 'APPDATA']
    return [Path(env[n]) for n in names if env.get(n) and Path(env[n]).is_dir()]


def detect_tools(*, which=None, known_locations=None, registry=None):
    """Lightweight targeted discovery; no recursive full-disk scanning."""
    which = which or shutil.which
    roots = known_locations if known_locations is not None else _common_roots()
    records = registry if registry is not None else _win_registry_apps()
    inventory = []
    for label, (purpose, commands, hints) in TOOL_SPECS.items():
        location = ''
        source = ''
        for command in commands:
            match = which(command)
            if match:
                location, source = str(match), 'PATH'
                break
        if not location:
            # Probe exact likely locations. Never traverse the drive.
            for root in roots:
                candidate_names = [root / name / command for name in hints for command in commands]
                candidate_names += [root / name / 'bin' / command for name in hints for command in commands]
                for candidate in candidate_names:
                    if candidate.is_file():
                        location, source = str(candidate), 'Known folder'
                        break
                if location: break
        if not location:
            hints_low = tuple(x.casefold() for x in hints)
            if label=='Python': hints_low = ('python ', 'python 3')
            for name, folder in records:
                if label.casefold() in name or any(h in name for h in hints_low):
                    location, source = folder or '(installed; executable path not found)', 'Windows installed-app registry'
                    break
        # A Windows uninstall entry may contain only a directory or a descriptive
        # string. That is NOT proof the relevant executable can be launched.
        # Keep the metadata for display, but do not mark the tool usable.
        actual_file = bool(location and Path(location).is_file())
        inventory.append(Tool(label, purpose, actual_file, location, source))
    return inventory


def _physical_memory():
    if os.name == 'nt':
        class Mem(ctypes.Structure):
            _fields_ = [('dwLength', wintypes.DWORD), ('dwMemoryLoad', wintypes.DWORD),
                        ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
        m=Mem();m.dwLength=ctypes.sizeof(m)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return int(m.ullTotalPhys), int(m.ullAvailPhys)
    # Unix packaging/test environments; Windows remains the target.
    try:
        lines = Path('/proc/meminfo').read_text().splitlines()
        vals = {l.split(':',1)[0]: int(l.split(':',1)[1].strip().split()[0])*1024 for l in lines if ':' in l}
        return vals.get('MemTotal',0), vals.get('MemAvailable',0)
    except OSError:
        return 0,0


def _drives():
    if os.name == 'nt':
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        # Only fixed drives. Network/removable media can block or wake disks.
        letters = [f'{chr(65+i)}:\\' for i in range(26) if mask&(1<<i) and ctypes.windll.kernel32.GetDriveTypeW(f'{chr(65+i)}:\\')==3]
    else:
        letters = ['/']
    result = []
    for root in letters:
        try:
            capacity = shutil.disk_usage(root)
            result.append({'path':root,'total_bytes':capacity.total,'free_bytes':capacity.free})
        except OSError:
            continue
    return result


def _cpu_name():
    if os.name != 'nt': return platform.processor() or 'Unknown'
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as node:
            return str(winreg.QueryValueEx(node, 'ProcessorNameString')[0]).strip()
    except OSError: return platform.processor() or 'Unknown'


def _gpu_names():
    # A single bounded local WMI query; no GPU load or internet access.
    if os.name != 'nt': return []
    exe = shutil.which('powershell.exe')
    if not exe: return []
    try:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        proc = subprocess.run([exe,'-NoProfile','-NonInteractive','-Command',
             '(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join "`n"'],
             capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,creationflags=flags)
        return [x.strip() for x in proc.stdout.splitlines() if x.strip()][:4]
    except (OSError,subprocess.TimeoutExpired): return []


def scan_computer(install_dir: str | Path, project_dir: str | Path | None = None, *, include_gpu: bool = True,
                  x4_game_dir=None, x4_reference_dir=None):
    total, available = _physical_memory()
    detected_tools = [asdict(t) for t in detect_tools()]
    project_preflight = None
    # The Scan this computer action already runs in a background thread.
    # This is a read-only project probe; never start or install an engine.
    if project_dir and Path(project_dir).is_dir():
        try:
            from .engine_environment import inspect_engine_environment
            project_preflight = inspect_engine_environment(
                project_dir,tools={'tools':detected_tools},
                x4_game_dir=x4_game_dir,x4_reference_dir=x4_reference_dir)
        except (OSError,ValueError) as exc:
            project_preflight = {'engine':'unknown','missing_prerequisites':[],
                                 'static_clean':False,'error':str(exc)[:250]}
    return {
        'hostname': platform.node(), 'operating_system': platform.platform(),
        'application_folder': str(Path(install_dir).resolve()),
        'project_folder': str(Path(project_dir).resolve()) if project_dir else None,
        'cpu': _cpu_name(), 'logical_processors': os.cpu_count(),
        'ram_bytes': total, 'free_ram_bytes': available,
        'deepthort_max_cpu_percent':50, 'deepthort_max_memory_commit_bytes':total*65//100,
        'gpu': _gpu_names() if include_gpu else [], 'drives': _drives(),
        'tools': detected_tools,
        'engine_preflight': project_preflight,
        'privacy':'Local scan only. No network calls, installs or recursive drive searches.'
    }


def format_inventory(data: dict) -> str:
    gib = lambda n: f'{n / (1024**3):.1f} GB'
    s = [f"Computer: {data['hostname']}", f"Windows / OS: {data['operating_system']}",
         f"App installed at: {data['application_folder']}",
         f"Current project: {data['project_folder'] or 'None selected'}",'',
         f"CPU: {data['cpu']} ({data['logical_processors']} logical processors)",
         f"Installed RAM: {gib(data['ram_bytes'])} | Available: {gib(data['free_ram_bytes'])}",
         f"DeepThorT memory-commit budget: {gib(data['deepthort_max_memory_commit_bytes'])} (theoretical maximum 65% of physical RAM; actual admission may be lower; commit ceiling, not working set)",
         'DeepThorTriad configured CPU ceiling: 50% of whole system (when launched under the Windows supervisor)',
         'Disk usage: low-priority / game-aware, NOT an enforced 20% disk bandwidth cap',
         f"GPU: {', '.join(data['gpu']) if data['gpu'] else 'Not detected / optional scan skipped'}", '', 'Disks:']
    for d in data['drives']:
        s.append(f"  {d['path']}  Free {gib(d['free_bytes'])} / Total {gib(d['total_bytes'])}")
    s.extend(['','Programs detected (not automatically granted permission to run):'])
    for t in data['tools']:
        s.append(f"  {'[Found]' if t['found'] else '[Missing]'} {t['name']} — {t['purpose']}" +
                 (f" — {t['location']} ({t['source']})" if t['found'] else ''))
    preflight = data.get('engine_preflight')
    if preflight and preflight.get('engine') != 'general':
        s.extend(['','Selected project engine readiness (read-only):',
                  f"  Type: {preflight.get('engine', 'unknown')}",
                  f"  Static issues: {preflight.get('static_issues','unknown')}; "
                  f"pending planned files: {preflight.get('static_pending','unknown')}"])
        for name,path in preflight.get('tools', {}).items():
            s.append(f"  {name}: {path or 'not found'}")
        for missing in preflight.get('missing_prerequisites', []):
            s.append('  Missing: '+missing)
        links=preflight.get('x4_reference_links')
        if links:
            s.append('  X4 extracted source links: '+(
                f"{links.get('resolved_vanilla_count',0)} verified vanilla; "
                f"{links.get('resolved_local_count',0)} local; "
                f"{links.get('unresolved_count',0)} unresolved" if not links.get('error')
                else 'not fully inspected — '+links['error']))
            s.append('  Unresolved references may require DLC or other extensions.')
        if preflight.get('error'):
            s.append('  Inspection issue: '+preflight['error'])
        s.append('  This does not certify a build, test, APK or playable game.')
    s.extend(['', data['privacy']])
    return '\n'.join(s)


def plan_tool_needs(task: str, inventory: dict):
    """Deterministic local tool needs; may feed bounded approved software automation."""
    phrase = task.casefold()
    needed = []
    if any(word in phrase for word in ('android','apk','mobile game')):
        needed.extend(['Android Studio','Java','Android Debug Bridge','Git'])
    if any(word in phrase for word in ('2d game','2-d game','game from scratch','godot')):
        needed.extend(['Godot','Git'])
    if any(word in phrase for word in ('3d game','3-d game','render','animation','model mesh')):
        needed.extend(['Blender','Godot','Git'])
    if any(word in phrase for word in ('website','javascript','react','typescript')):
        needed.extend(['Node.js','Git'])
    if any(word in phrase for word in ('python','script','automation')):
        needed.extend(['Python','Git'])
    if any(word in phrase for word in ('c#','dotnet','csharp')):
        needed.extend(['.NET SDK','Git'])
    if any(word in phrase for word in ('book','novel','manuscript','ebook','epub','document','spreadsheet','presentation')):
        needed.extend(['LibreOffice','Pandoc'])
    if any(word in phrase for word in ('podcast','voiceover','soundtrack','audio','recording','music')):
        needed.extend(['Audacity','FFmpeg'])
    if any(word in phrase for word in ('video','movie','film','video editing','cinematic')):
        needed.extend(['FFmpeg','Blender'])
    if any(word in phrase for word in ('svg','vector graphic','logo','illustration','drawing','painting')):
        needed.extend(['Inkscape','Krita','GIMP'])
    if any(word in phrase for word in ('3d print','3d-print','cad','engineering drawing','mechanical design')):
        needed.extend(['FreeCAD','Blender'])
    if any(word in phrase for word in ('unity','unreal','simulation')):
        needed.extend(['Unity Hub','Blender','Git'])
    seen=set(); needed=[x for x in needed if not (x in seen or seen.add(x))]
    installed = {t['name']:t['found'] for t in inventory.get('tools',[])}
    return [{'name':x,'found':installed.get(x,False),
             'proposed_install':x in INSTALL_CATALOG and not installed.get(x,False)} for x in needed]


def winget_command(display_name: str, *, which=None):
    """Fixed argv only. Never interpolate language-model instructions into a shell."""
    if display_name not in INSTALL_CATALOG:
        raise ValueError('Software not approved in local install catalog')
    finder = which or shutil.which
    binary = finder('winget.exe') or finder('winget')
    if not binary:
        raise FileNotFoundError('Windows Package Manager (winget) not found; no install attempted')
    return [str(binary),'install','--id',INSTALL_CATALOG[display_name][0],
            '--exact','--source','winget','--accept-source-agreements',
            '--accept-package-agreements','--disable-interactivity']
