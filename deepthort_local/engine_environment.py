"""Read-only, bounded discovery of local build prerequisites (v30).

This module never runs an executable, searches whole disks, downloads tools,
changes configuration or authorizes execution. In particular, a registry entry
or directory is not evidence that an executable exists. An invocation is chosen
and confirmed separately by the desktop's existing approval dialog.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from .engine_acceptance import audit_engine_project


def _executable(value: str | os.PathLike | None, names: tuple[str, ...]) -> str:
    if not value:
        return ''
    try:
        candidate = Path(value).expanduser()
        name = candidate.name.casefold()
        allowed = name in {item.casefold() for item in names}
        # Official Windows Godot zip executables typically retain their version
        # in the filename (Godot_v4.x-stable_win64.exe).
        if 'godot.exe' in names and re.fullmatch(r'godot_v[0-9][a-z0-9._-]*\.exe', name):
            allowed = True
        if not candidate.is_file() or candidate.is_symlink() or not allowed:
            return ''
        return str(candidate.resolve(strict=True))
    except (OSError, ValueError, TypeError):
        return ''


def _which(executable: str, resolver) -> str:
    try:
        result = resolver(executable)
        return _executable(result, (executable,))
    except (OSError, TypeError, ValueError):
        return ''


def godot_executable(*, tools=None, environ=None, which=None) -> str:
    """Find a *real file* for Godot, not an installed-software registry hint."""
    environ = os.environ if environ is None else environ
    which = shutil.which if which is None else which
    names = ('godot.exe', 'godot_console.exe', 'godot')
    candidate = _executable(environ.get('GODOT_EXECUTABLE'), names)
    if candidate:
        return candidate
    for name in names:
        candidate = _which(name, which)
        if candidate:
            return candidate
    records = tools.get('tools', []) if isinstance(tools, dict) else tools or []
    for item in records:
        if isinstance(item, dict) and item.get('name') == 'Godot':
            candidate = _executable(item.get('location'), names)
            if candidate:
                return candidate
    return ''


def _android_sdk(environ: dict) -> str:
    candidates = [environ.get('ANDROID_SDK_ROOT'), environ.get('ANDROID_HOME')]
    local = environ.get('LOCALAPPDATA')
    if local:
        candidates.append(str(Path(local)/'Android'/'Sdk'))
    for value in candidates:
        if not value:
            continue
        try:
            root = Path(value).resolve(strict=True)
            if root.is_dir() and (root/'platforms').is_dir() and (root/'build-tools').is_dir():
                return str(root)
        except (OSError, ValueError):
            continue
    return ''


def _java(environ: dict, resolver) -> str:
    root = environ.get('JAVA_HOME')
    if root:
        for name in ('java.exe','java'):
            result = _executable(Path(root)/'bin'/name, (name,))
            if result:
                return result
    for name in ('java.exe','java'):
        result = _which(name,resolver)
        if result:
            return result
    return ''


def _gradle(environ: dict, resolver) -> str:
    # Avoid invoking project-controlled Gradle wrappers automatically. An
    # explicitly approved build can select a trusted installed Gradle instead.
    root = environ.get('GRADLE_HOME')
    if root:
        for name in ('gradle.bat','gradle.cmd','gradle'):
            path = _executable(Path(root)/'bin'/name, (name,))
            if path:
                return path
    for name in ('gradle.bat','gradle.cmd','gradle'):
        path = _which(name,resolver)
        if path:
            return path
    return ''


def inspect_engine_environment(project: str | Path, *, tools=None, environ=None,
                               which=None, x4_game_dir=None, x4_reference_dir=None) -> dict:
    """Observe actual paths for an existing project; never invoke the tools.

    Missing requirements are *blockers to meaningful execution*, not an
    instruction to silently download an SDK or substitute another game engine.
    The only recursive scan is the already-bounded engine artifact audit.
    """
    root = Path(project).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Project must be an existing directory')
    environ = os.environ if environ is None else environ
    resolver = shutil.which if which is None else which
    audit = audit_engine_project(root)
    engine = audit['engine']
    found = {}
    missing = []
    if engine == 'godot':
        found['godot'] = godot_executable(tools=tools,environ=environ,which=resolver)
        if not found['godot']:
            missing.append('Godot executable unavailable: editor-load and GUT verification cannot run')
    elif engine == 'android_gradle':
        found['java'] = _java(environ,resolver)
        found['android_sdk'] = _android_sdk(environ)
        found['gradle'] = _gradle(environ,resolver)
        for key,label in (('java','Java executable'),('android_sdk','Android SDK with platforms and build-tools'),
                          ('gradle','installed Gradle executable')):
            if not found[key]:
                missing.append(f'{label} not located for an approved, offline Android build')
    elif engine == 'x4_extension':
        for key,candidate in (('game',x4_game_dir),('extracted_reference',x4_reference_dir)):
            path = ''
            if candidate:
                try:
                    obj = Path(candidate).resolve(strict=True)
                    if obj.is_dir():
                        path = str(obj)
                except (OSError,ValueError):
                    pass
            found[key] = path
        # A selected folder alone does not prove that X4 is installed there.
        if not found['game']:
            missing.append('X4 game directory not selected or unavailable; cannot perform in-game checks')
        else:
            game=Path(found['game'])
            executable=any((game/name).is_file() for name in ('X4.exe','x4.exe'))
            catalogs=any(p.with_suffix('.dat').is_file() for p in list(game.glob('[0-9][0-9].cat'))[:30])
            found['game_executable_present']=executable
            found['game_catalog_pair_present']=catalogs
            if not executable and not catalogs:
                missing.append('Selected X4 folder contains no X4 executable or paired game catalogs')
        if not found['extracted_reference']:
            missing.append('Extracted X4 source directory unavailable; vanilla identifiers cannot be confirmed')
    x4_links = None
    if engine == 'x4_extension' and found.get('extracted_reference'):
        from .x4_reference_links import inspect_x4_reference_links
        try:
            x4_links = inspect_x4_reference_links(root,found['extracted_reference'])
            indexes=x4_links.get('vanilla_index_available',{})
            if not indexes.get('macro') or not indexes.get('component'):
                missing.append('Extracted X4 references lack a usable macros or components index')
        except (OSError,ValueError) as exc:
            x4_links = {'assurance':'Reference-link scan incomplete; no game proof',
                        'error':str(exc)[:250], 'gameplay_verified':False}
    return {
        'engine':engine,'project':str(root),'tools':found,'missing_prerequisites':missing,
        'x4_reference_links':x4_links,
        'static_issues':len(audit['issues']),'static_pending':len(audit['pending']),
        'static_clean':audit['accepted'],
        'can_perform_engine_check':engine=='godot' and bool(found.get('godot')),
        'assurance':'Read-only local file discovery. No executable run, build, gameplay or APK certification',
    }


def main(argv=None) -> int:
    import argparse
    import json
    parser=argparse.ArgumentParser(description='Discover installed engine prerequisites (read-only)')
    parser.add_argument('project',help='Existing project folder')
    parser.add_argument('--x4-game',help='Previously selected X4 installation directory')
    parser.add_argument('--x4-reference',help='Previously extracted X4 source directory')
    args=parser.parse_args(argv)
    result=inspect_engine_environment(args.project,x4_game_dir=args.x4_game,
                                      x4_reference_dir=args.x4_reference)
    print(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True))
    return 2 if result['static_issues'] else 0


if __name__=='__main__':
    raise SystemExit(main())
