#!/usr/bin/env python3
"""Static validation only. Does not run X4 or prove any gameplay effect."""
from pathlib import Path
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parents[1]
MOD = BASE / 'vardath_galactic_occupations'
JOBS = ['escort','taxi','scanner','mapper','tour','crystal','lure','demolition','morale','inspection','recruit','patrol','hacker']
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference', type=Path, help='Extracted installed X4 root: libraries/*.xsd and aiscripts/*.xml')
parser.add_argument('--report', type=Path)
parser.add_argument('--zip', type=Path, help='Also compare archive contents byte-for-byte with installed source')
args = parser.parse_args()
api = json.loads((BASE / 'tools/api_contracts.json').read_text())
errors, counts = [], {'xml_files': 0, 'commands': 0, 'script_calls': 0, 'behaviours': 0, 'ui_addons': 0}
trees, scripts = {}, {}

def error(path, message):
    errors.append(f'{path.relative_to(BASE)}: {message}')

for path in sorted(MOD.rglob('*.xml')):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        error(path, str(exc))
        continue
    trees[path] = root
    counts['xml_files'] += 1
    if root.tag == 'aiscript':
        if root.get('name') != path.stem:
            error(path, 'script name and filename differ')
        if root.get('name') in scripts:
            error(path, 'duplicate script name')
        scripts[root.get('name')] = root

structural = {'aiscript','order','params','param','requires','location','interrupts','handler','actions','attention','init',
              'mdscript','cues','cue','library','conditions','language','page','t','content','dependency','input_param','patch'}
for path, root in trees.items():
    parents = {child: parent for parent in root.iter() for child in parent}
    for node in root.iter():
        if node.tag in ('event_object_dropped_objects','event_object_changed_room','event_object_destroyed') and not (node.get('object') or node.get('group')):
            error(path, f'{node.tag} requires an explicit object or dynamic group')
        if node.tag == 'create_order' and 'default' in node.attrib and 'immediate' in node.attrib:
            error(path, 'create_order cannot specify default and immediate together, even when false (confirmed by debug(7).log)')
        if node.tag == 'shoot_at':
            ancestor = node
            while ancestor in parents and ancestor.tag != 'attention': ancestor = parents[ancestor]
            if ancestor.tag != 'attention' or ancestor.get('min') != 'visible':
                error(path, 'shoot_at requires a visible attention block')
        if root.tag == 'mdscript' and node.tag == 'cue':
            conditions = node.find('conditions')
            if conditions is not None and len(conditions) and not node.get('checkinterval'):
                if not any(isinstance(c.tag,str) and c.tag.startswith('event_') for c in conditions.iter()):
                    error(path, f"cue {node.get('name')} needs a polling interval for non-event conditions")
        if node.tag == 'run_script' and node.get('name') in ("'order.fight.escort'", "'order.fight.attack.object'"):
            error(path, 'occupation must not borrow a native combat/fleet order as a subroutine; it may cancel the caller')
        for value in node.attrib.values():
            if re.search(r'illegalto\.\{[^}]+\}\.count',value):
                error(path, 'illegalto is a boolean, not a counted collection')
        if node.tag == 'location'  and node.get('object','').startswith('player.entity.$vgo_objects'):
            error(path, 'order location must have a valid component fallback before worker initialization')
        for value in node.attrib.values():
            if re.search(r'@[\w.$]+(?:\.\{[^{}]*\})?[\w.$]*\?', value):
                error(path, 'X4 expressions cannot combine @ optional lookup with ? presence testing')
            if re.search(r'(this\.ship|\$(?:ship|turret|target|candidate|module|station|deposit|poi|component))\.\$vgo_', value):
                error(path, 'Only entities have blackboards; component state belongs in the persistent player table')
    if root.tag == 'diff' and path == MOD/'libraries/icons.xml':
        for op in root:
            if op.tag != 'add' or op.get('sel') != '/icons': error(path, 'icon integration may add aliases only')
            for icon in op:
                if icon.tag != 'icon' or not icon.get('name','').startswith('order_vgo_'):
                    error(path, 'icon aliases must be namespaced')
        continue
    if root.tag == 'addon':
        counts['ui_addons'] += 1
        if root.get('name') != MOD.name:
            error(path, 'UI addon name must match extension ID')
        for env in root.findall('./environment'):
            if env.get('type') != 'menus':
                error(path, 'unsupported UI environment')
            for node in env.findall('./file'):
                target = MOD / node.get('name', '')
                if not target.is_file() or target.suffix != '.lua' or not target.resolve().is_relative_to(MOD.resolve()):
                    error(path, 'missing or unsafe UI script path')
        continue
    context = 'aiscripts' if root.tag == 'aiscript' else 'md'
    for node in root.iter():
        spec = api['commands'].get(node.tag)
        if spec:
            counts['commands'] += 1
            if context not in spec['contexts']:
                error(path, f'{node.tag} is not allowed in {context}')
            attrs = spec['attributes']
            for name, info in attrs.items():
                if info.get('required') and name not in node.attrib:
                    error(path, f'{node.tag} requires attribute {name}')
            for name, value in node.attrib.items():
                if name not in attrs:
                    error(path, f'{node.tag} has unknown attribute {name}')
                    continue
                enum = api['enum_types'].get(attrs[name].get('type'), {})
                if enum and not enum.get('patterns') and value not in [x['v'] for x in enum['values']]:
                    error(path, f'{node.tag}/{name} has invalid literal {value}')
        elif node.tag not in structural:
            variants = api['children'].get(node.tag, [])
            if not variants or not any(set(node.attrib) <= set(v['attributes']) for v in variants):
                error(path, f'undocumented element or child signature: {node.tag} {node.attrib}')
    if root.tag == 'aiscript':
        native_param_types = {'internal','bool','object','number','time','list','length','position','sector','ware','trade','money','formationshape','build'}
        for parameter in root.findall('./order/params/param'):
            if parameter.get('type') not in native_param_types:
                error(path, f"unsupported native order parameter type {parameter.get('type')}")
            if 'internal' in parameter.attrib:
                error(path, 'native hidden order parameters use type=internal, not an internal attribute')
        labels = {n.get('name') for n in root.findall('.//label')}
        for node in root.findall('.//resume') + root.findall('.//abort_called_scripts'):
            label = node.get('label') or node.get('resume')
            if label and label not in labels:
                error(path, f'unknown local resume label {label}')
    for node in root.findall('.//run_script'):
        counts['script_calls'] += 1
        target = node.get('name', '').strip("'")
        if target in scripts:
            targetroot = scripts[target]
            params = targetroot.find('./params')
            if params is None:
                params = targetroot.find('./order/params')
            declarations = {p.get('name'): p.attrib for p in params} if params is not None else {}
        elif target in api['native_scripts']:
            declarations = api['native_scripts'][target]['parameters']
            if args.reference:
                native = args.reference / 'aiscripts' / f'{target}.xml'
                if not native.is_file():
                    error(path, f'installed native script missing: {target}')
                else:
                    nr = ET.parse(native).getroot()
                    params = nr.find('./params')
                    if params is None:
                        params = nr.find('./order/params')
                    declarations = {p.get('name'):p.attrib for p in params} if params is not None else {}
        else:
            error(path, f'missing script target: {target}')
            continue
        supplied = {p.get('name') for p in node.findall('./param')}
        for name in supplied - declarations.keys():
            error(path, f'{target} does not declare parameter {name}')
        for name, info in declarations.items():
            if info.get('required') == 'true' and name not in supplied and 'default' not in info:
                error(path, f'{target} requires parameter {name}')

texts = {n.get('id') for r in trees.values() if r.tag == 'language' for n in r.findall('.//t')}
for path, root in trees.items():
    for node in root.iter():
        for value in node.attrib.values():
            for tid in re.findall(r'\{191180,\s*(\d+)\}', value):
                if tid not in texts:
                    error(path, f'missing English text 191180,{tid}')

for key in JOBS:
    path = MOD / 'aiscripts' / f'order.vardath.go.{key}.xml'
    root = trees.get(path)
    if root is None:
        error(path, 'behaviour definition missing')
        continue
    order = root.find('./order')
    if order is None or order.get('id') != f'VGO_{key}' or order.get('infinite') != 'true':
        error(path, 'persistent default order registration missing')
    elif root.find('.//set_order_syncpoint_reached') is None:
        error(path, 'infinite order lacks native sync point')
    else:
        counts['behaviours'] += 1
    if f'vardath.go.task.{key}' not in scripts:
        error(path, 'occupation task script missing')

# No vanilla replacement or patch files are permitted in this standalone extension.
for path, root in trees.items():
    if root.tag == 'diff' and path != MOD/'libraries/icons.xml':
        error(path, 'unexpected vanilla/mod patch')
    if path.parent.name == 'aiscripts' and 'vardath.go.' not in path.stem:
        error(path, 'non-namespaced AI script')

schema_status = 'NOT RUN: installed X4 schemas unavailable'
if args.reference:
    try:
        from lxml import etree
        schema_cache = {}
        for family, tag in [('aiscripts','aiscript'), ('md','mdscript')]:
            schema_path = args.reference / 'libraries' / f'{family}.xsd'
            if not schema_path.is_file():
                errors.append(f'installed schema missing: {schema_path}')
                continue
            print(f'Compiling installed {schema_path}; this can take several minutes.', flush=True)
            schema_cache[family] = etree.XMLSchema(etree.parse(str(schema_path)))
            for path, root in trees.items():
                if root.tag == tag:
                    schema = schema_cache[family]
                    if not schema.validate(etree.parse(str(path))):
                        error(path, str(schema.error_log))
        schema_status = 'PASS' if not errors else 'FAIL'
    except Exception as exc:
        errors.append(f'official XSD validation unavailable: {exc}')
        schema_status = 'FAIL'

if args.zip:
    try:
        with zipfile.ZipFile(args.zip) as archive:
            if archive.testzip():
                errors.append('archive CRC failure')
            expected = {'extensions/'+str(p.relative_to(MOD.parent)): p for p in MOD.rglob('*') if p.is_file()}
            if set(archive.namelist()) != set(expected):
                errors.append('archive file list differs from installable source')
            for name in set(archive.namelist()) & set(expected):
                if archive.read(name) != expected[name].read_bytes():
                    errors.append(f'archive content differs: {name}')
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(str(exc))

report = {'static_result':'FAIL' if errors else 'PASS', 'counts':counts, 'installed_schema_validation':schema_status,
          'reference_provenance':api['provenance'], 'runtime':'NOT RUN: no X4 installation, executable or save available; supplied debug(2).log through debug(6).log reviewed for actual failures',
          'runtime_jobs':{key:'UNVERIFIED' for key in JOBS}, 'errors':errors}
if args.report:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['static_result','counts','installed_schema_validation','runtime','errors']},indent=2))
sys.exit(bool(errors))
