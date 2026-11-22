"""v29: bounded, read-only X4/Godot/Android artifact acceptance audit.

Checks only evidence available in the project. It does not run a game, execute
project scripts, attest successful gameplay, or mark requirements implemented.
Existing and intended file paths are not interchangeable: absent planned files
are pending, while broken references in existing artifacts are findings.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .workspace import safe_target

MAX_FILES = 256
MAX_BYTES = 2_000_000
_XML_EXTENSIONS = {'.xml', '.tscn', '.tres'}
_RESOURCE = re.compile(r'\bpath\s*=\s*"(res://[^"]+)"')
_MAIN = re.compile(r'(?m)^\s*run/main_scene\s*=\s*"([^"]+)"')
_ANDROID_PRESET = re.compile(r'(?m)^\s*platform\s*=\s*"Android"\s*$')
_TEST_FUNC = re.compile(r'(?m)^\s*func\s+test_[A-Za-z0-9_]+\s*\(')


def _read(path: Path, *, max_bytes: int = MAX_BYTES) -> tuple[bytes, str]:
    if path.stat().st_size > max_bytes:
        raise ValueError('File exceeds bounded acceptance audit size')
    data = path.read_bytes()
    return data, hashlib.sha256(data).hexdigest()


def _xml(path: Path) -> tuple[ET.Element, str]:
    data, digest = _read(path)
    # No DTD, entity expansion, or external resources accepted in this audit.
    if re.search(rb'<!\s*(?:DOCTYPE|ENTITY)\b', data, re.I):
        raise ValueError('XML DTD or entity declarations cannot be audited safely')
    return ET.fromstring(data), digest


def _local(root: Path, relative: str) -> Path:
    # Reject absolute paths, traversal, UNC and symlink escapes using the
    # established DeepThorT workspace boundary.
    return safe_target(root, relative.replace('\\', '/'))


def _issue(path: str, code: str, detail: str = '') -> dict:
    return {'path': path, 'code': code, 'detail': detail[:220]}


def _x4(root: Path, planned: set[str], max_files: int) -> dict:
    issues = []; pending = []; observations = []; fingerprints = {}
    candidates = {'content.xml'} | {p for p in planned if p.lower().endswith('.xml')}
    # Also audit *all existing local XML* in relevant extension folders.
    # A planned-only scan would miss a broken MD file or obsolete index entry
    # produced by a preceding milestone and falsely certify the extension.
    allowed = ('md', 'assets', 'libraries', 'index', 'aiscripts', 'maps', 't')
    for folder in allowed:
        directory = root / folder
        if not directory.is_dir() or directory.is_symlink():
            continue
        for parent, dirs, filenames in os.walk(directory, followlinks=False):
            dirs[:] = [name for name in sorted(dirs) if not (Path(parent)/name).is_symlink()]
            for filename in sorted(filenames):
                if filename.lower().endswith('.xml'):
                    target = Path(parent) / filename
                    if target.is_symlink():
                        issues.append(_issue(target.relative_to(root).as_posix(),
                                             'symlink_not_audited','Refuse linked XML input'))
                        continue
                    candidates.add(target.relative_to(root).as_posix())
            if len(candidates)>max_files:
                issues.append(_issue(folder,'audit_scope_exceeded',f'More than {max_files} extension XML files'))
                break
        if len(candidates)>max_files:
            break
    # Fail closed if the scan was incomplete rather than silently inspecting
    # only the first N files or claiming a complete static audit.
    if len(candidates)>max_files:
        return {'engine':'x4_extension','issues':issues,'pending':[],
                'observations':observations,'source_hashes':{}}
    parsed = {}
    for rel in sorted(candidates):
        target = _local(root, rel)
        if not target.is_file():
            pending.append(rel);continue
        try:
            element, digest = _xml(target)
            parsed[rel] = element
            fingerprints[rel] = digest
        except (ET.ParseError, OSError, UnicodeError, ValueError) as exc:
            issues.append(_issue(rel, 'xml_invalid', str(exc)));continue
        if rel == 'content.xml':
            if element.tag != 'content' or not element.get('id'):
                issues.append(_issue(rel, 'manifest_invalid', 'Root <content> with nonempty id required'))
        elif rel.startswith('md/') and rel.endswith('.xml'):
            if element.tag not in ('mdscript', 'diff'):
                issues.append(_issue(rel, 'md_root_invalid', f'Expected mdscript/diff, got {element.tag}'))
        elif rel in ('index/macros.xml', 'index/components.xml'):
            if element.tag not in ('index', 'diff'):
                issues.append(_issue(rel, 'index_root_invalid', f'Expected index/diff, got {element.tag}'))
    for index_name, tag in (('index/macros.xml', 'macro'), ('index/components.xml', 'component')):
        tree = parsed.get(index_name)
        if tree is None or tree.tag != 'index':
            continue
        seen = set()
        entries = list(tree.iter('entry'))
        if len(entries) > 1600:
            issues.append(_issue(index_name,'index_too_many_entries','Bounded audit: 1600 entries per index'))
            continue
        for item in entries:
            name = (item.get('name') or '').strip()
            value = (item.get('value') or '').strip().replace('\\', '/')
            if not name or not value:
                issues.append(_issue(index_name, 'index_entry_incomplete', name));continue
            if name.casefold() in seen:
                issues.append(_issue(index_name,'index_duplicate_name',name));continue
            seen.add(name.casefold())
            # A real index can reference base-game assets, other extensions or
            # this extension. Only a self-prefixed value is asserted local.
            local_prefix = f'extensions/{root.name}/'
            if value.lower().startswith(local_prefix.lower()):
                rel = value[len(local_prefix):] + ('' if value.endswith('.xml') else '.xml')
                explicit_local = True
            elif value.startswith('assets/'):
                rel = value + ('' if value.endswith('.xml') else '.xml')
                explicit_local = False
            else:
                observations.append({'path':index_name,'code':'external_index_reference_unverified','name':name})
                continue
            try:
                target = _local(root, rel)
            except (ValueError, OSError) as exc:
                issues.append(_issue(index_name,'unsafe_index_reference',str(exc)));continue
            if not target.is_file():
                if explicit_local:
                    issues.append(_issue(index_name,'missing_local_index_target',rel))
                else:
                    observations.append({'path':index_name,'code':'external_or_unavailable_index_target','name':name})
                continue
            if rel not in fingerprints:
                try:
                    obj, digest = _xml(target)
                    fingerprints[rel] = digest
                except (ET.ParseError, OSError, UnicodeError, ValueError) as exc:
                    issues.append(_issue(rel,'xml_invalid',str(exc)));continue
            else:
                obj = parsed.get(rel)
                if obj is None:
                    try: obj, _ = _xml(target)
                    except (ET.ParseError, OSError, ValueError) as exc:
                        issues.append(_issue(rel,'xml_invalid',str(exc)));continue
            declared = {entry.get('name') for entry in obj.iter(tag)}
            if obj.tag != 'diff' and name not in declared:
                issues.append(_issue(index_name,'index_name_not_defined',f'{name} absent from {rel}'))
    return {'engine':'x4_extension','issues':issues,'pending':pending,
            'observations':observations,'source_hashes':fingerprints}


def _resource_path(root: Path, uri: str) -> Path:
    if not uri.startswith('res://'):
        raise ValueError('Not a project-local Godot resource URI')
    return _local(root, uri[len('res://'):])


def _godot(root: Path, planned: set[str], max_files: int) -> dict:
    issues = [];pending = []; observations = [];fingerprints = {}
    project_file = root / 'project.godot'
    if project_file.is_file():
        try:
            data, digest = _read(project_file)
            text = data.decode('utf-8-sig')
            fingerprints['project.godot'] = digest
            match = _MAIN.search(text)
            if match:
                uri = match.group(1)
                if uri.startswith('res://'):
                    target = _resource_path(root, uri)
                    if not target.is_file():
                        issues.append(_issue('project.godot','missing_main_scene',uri))
                elif uri.startswith('uid://'):
                    observations.append({'path':'project.godot','code':'main_scene_uid_unresolved'})
                else:
                    issues.append(_issue('project.godot','invalid_main_scene_uri',uri))
        except (ValueError,UnicodeError,OSError) as exc:
            issues.append(_issue('project.godot','godot_config_invalid',str(exc)))
    else:
        pending.append('project.godot')
    included = {p for p in planned if p.lower().endswith(('.tscn', '.tres', '.gd'))}
    if project_file.is_file():
        # Review scene referenced by project settings even when it was made in
        # an earlier milestone.
        try:
            text = project_file.read_text(encoding='utf-8-sig')
            match = _MAIN.search(text)
            if match and match.group(1).startswith('res://'):
                included.add(match.group(1)[6:])
        except (OSError,UnicodeError):pass
    if len(included)>max_files:
        raise ValueError('Godot acceptance audit requires a smaller milestone scope')
    tests_found=0
    for rel in sorted(included):
        target = _local(root, rel)
        if not target.is_file():
            pending.append(rel);continue
        try:
            data,digest = _read(target)
            source = data.decode('utf-8-sig')
            fingerprints[rel] = digest
        except (OSError, UnicodeError, ValueError) as exc:
            issues.append(_issue(rel,'source_unavailable',str(exc)));continue
        if rel.lower().endswith(('.tscn','.tres')):
            if not source.lstrip().startswith('[gd_scene' if rel.endswith('.tscn') else '[gd_resource'):
                issues.append(_issue(rel,'scene_header_invalid','Expected Godot text-resource header'))
            for uri in _RESOURCE.findall(source):
                try:
                    reference = _resource_path(root, uri)
                except (ValueError,OSError):
                    issues.append(_issue(rel,'unsafe_resource_reference',uri));continue
                if not reference.is_file():
                    issues.append(_issue(rel,'missing_resource_reference',uri))
        elif ('/test' in '/' + rel.casefold() or 'tests/' in rel.casefold()):
            tests_found += len(_TEST_FUNC.findall(source))
    export = root/'export_presets.cfg'
    if export.is_file():
        try:
            data,digest = _read(export)
            fingerprints['export_presets.cfg']=digest
            if _ANDROID_PRESET.search(data.decode('utf-8-sig')):
                observations.append({'path':'export_presets.cfg','code':'android_export_preset_declared_not_built'})
            else:
                observations.append({'path':'export_presets.cfg','code':'no_android_export_preset'})
        except (OSError,UnicodeError,ValueError) as exc:
            issues.append(_issue('export_presets.cfg','export_presets_invalid',str(exc)))
    return {'engine':'godot','issues':issues,'pending':pending,'observations':observations,
            'source_hashes':fingerprints,'static_test_functions':tests_found}


def _android_gradle(root:Path, planned:set[str], max_files:int)->dict:
    issues=[];pending=[];observations=[];fingerprints={}
    manifest_files={p for p in planned if p.endswith('AndroidManifest.xml')}
    manifest_files.update(p.relative_to(root).as_posix() for p in root.glob('*/src/main/AndroidManifest.xml'))
    if len(manifest_files)>max_files:
        raise ValueError('Android audit requires a smaller milestone scope')
    for rel in sorted(manifest_files):
        target=_local(root,rel)
        if not target.is_file():
            pending.append(rel);continue
        try:
            element,digest=_xml(target)
            fingerprints[rel]=digest
            if element.tag!='manifest':
                issues.append(_issue(rel,'android_manifest_invalid','Expected <manifest> root'))
        except (OSError,ValueError,ET.ParseError) as exc:
            issues.append(_issue(rel,'xml_invalid',str(exc)))
    observations.append({'path':'settings.gradle','code':'gradle_tests_and_apk_not_executed'})
    return {'engine':'android_gradle','issues':issues,'pending':pending,
            'observations':observations,'source_hashes':fingerprints}


def audit_engine_project(project: str | Path, steps: list[dict] | None = None,
                         *, max_files:int=MAX_FILES)->dict:
    """Read-only artifact checks; issues block a verification gate, not drafts.

    A missing planned file is pending, not proof of success or a hard error;
    existing broken references and syntax are hard issues. No external tool
    or installed engine is called. Keep all source descriptions immutable.
    """
    if not 1<=max_files<=2000:
        raise ValueError('Invalid audit file limit')
    root=Path(project).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Project must be a local directory')
    planned=set()
    for step in steps or []:
        rel=step['path'].replace('\\','/')
        _local(root,rel)
        planned.add(rel)
    if (root/'project.godot').is_file() or 'project.godot' in planned:
        report=_godot(root,planned,max_files)
    elif (root/'content.xml').is_file() or 'content.xml' in planned:
        report=_x4(root,planned,max_files)
    elif any((root/x).exists() for x in ('settings.gradle','settings.gradle.kts')) or any(
            x.endswith('AndroidManifest.xml') for x in planned):
        report=_android_gradle(root,planned,max_files)
    else:
        report={'engine':'general','issues':[],'pending':[],
                'observations':[],'source_hashes':{}}
    report['accepted']=not report['issues'] and not report['pending']
    report['acceptance_confirmed']=False
    report['assurance']='Static engine artifact inspection only; no editor, export, runtime, or gameplay verification'
    return report


def main(argv:list[str]|None=None)->int:
    import argparse
    parser=argparse.ArgumentParser(description='Read-only X4/Godot/Android project artifact audit')
    parser.add_argument('project',help='Local project folder; never executed')
    parser.add_argument('--plan',help='Optional JSON plan file to scope checks to intended files')
    parser.add_argument('--summary',action='store_true',help='One bounded machine-readable result for an approved verification run')
    args=parser.parse_args(argv)
    plan=[]
    if args.plan:
        path=Path(args.plan)
        if not path.is_file() or path.stat().st_size>4_000_000:
            parser.error('Plan file unavailable or exceeds bound')
        parsed=json.loads(path.read_text(encoding='utf-8'))
        plan=parsed.get('files') if isinstance(parsed,dict) else parsed
        if not isinstance(plan,list) or any(not isinstance(s,dict) or not isinstance(s.get('path'),str) for s in plan):
            parser.error('Plan requires a list of file path entries')
    report=audit_engine_project(args.project,plan)
    if args.summary:
        # The desktop captures only 300 output lines, 2,000 chars each.
        # A full index report would otherwise be silently truncated and parsed
        # as a failed response. The full local audit still runs above.
        output={'engine':report['engine'],'accepted':report['accepted'],
                'issues':report['issues'][:3],'issue_count':len(report['issues']),
                'pending':report['pending'][:3], 'pending_count':len(report['pending'])}
        encoded=json.dumps(output,ensure_ascii=False,separators=(',',':'))
        # Never truncate raw JSON: shrink advisory samples until the desktop
        # can retain the complete one-line report. Counts remain authoritative.
        while len(encoded)>1800 and (output['issues'] or output['pending']):
            if output['pending'] and (not output['issues'] or
                    len(str(output['pending'][-1]))>len(str(output['issues'][-1]))):
                output['pending'].pop()
            elif output['issues']:
                output['issues'].pop()
            encoded=json.dumps(output,ensure_ascii=False,separators=(',',':'))
        print(encoded)
    else:
        print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return 2 if report['issues'] else 0


if __name__=='__main__':
    raise SystemExit(main())