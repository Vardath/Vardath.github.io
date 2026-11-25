"""Repair a ship filename collision using a local-model choice and fresh inspection records."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .agent_plan import PlanError, extension_id
from .engine_acceptance import read_asset_xml
from .workspace import safe_target


@dataclass(frozen=True)
class VariantSource:
    package: str
    path: PurePosixPath
    digest: str

    @classmethod
    def inspected(cls, request: str, evidence: str, source: str):
        package = extension_id(request)
        path = PurePosixPath(source)
        if not package or not re.fullmatch(r'assets/(?:[a-z0-9_]+/)*macros/[a-z0-9_]+_macro\.xml', source):
            return None
        if not re.search(r'(?<![\w])' + re.escape(path.stem) + r'(?![\w])', request, re.I):
            return None
        for line in evidence.splitlines():
            record = re.fullmatch(r'ship_candidates: (\S+) IDs ([\w, ]+) SHA ([a-f0-9]{12,64})', line)
            if record and record[1] == source and path.stem in record[2].split(', '):
                return cls(package, path, record[3])
        return None

    def prompt(self):
        return (f'Choose a new X4 ship macro identifier for the extension {self.package}. '
                f'The base {self.path.stem} already exists. The new name must contain '
                f'{self.package.replace("-", "_")}, end with _macro, and use only lowercase letters, '
                'digits and underscores. This name will be used for the new ship XML and '
                'its entry in index/macros.xml. Reply with the identifier only.')

    def proposal(self, reply: str, evidence: str) -> str:
        name = reply.strip()
        if name.startswith('`') and name.endswith('`') and name.count('`') == 2:
            name = name[1:-1]
        if (not re.fullmatch(r'[a-z][a-z0-9_]{0,116}_macro', name)
                or self.package.replace('-', '_') not in name
                or re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', evidence, re.I)):
            raise PlanError('Choose one new lowercase macro identifier containing the extension name and ending in _macro.')
        return json.dumps({'files': self.steps(name)})

    def steps(self, name: str) -> list[dict]:
        destination = self.path.with_name(name + '.xml')
        lookup = (PurePosixPath('extensions') / self.package / destination.with_suffix('')).as_posix()
        return [
            {'path': str(destination),
             'description': f'Define the independent ship macro {name} using the inspected vanilla base '
                            f'{self.path} (SHA-256 prefix {self.digest}). Preserve its component and equipment connections.'},
            {'path': 'index/macros.xml',
             'description': f'Add an entry to /index with name="{name}" and value="{lookup}". '
                            'Verify that the target XML declares the same macro.'},
        ]

    def render(self, name: str, relative: str, reference_dir: str | Path) -> str:
        """Render only a new identity and registration from the previously inspected vanilla XML."""
        index_path = safe_target(reference_dir, 'index/macros.xml', must_exist=True)
        index, _ = read_asset_xml(index_path)
        if index.tag != 'index':
            raise PlanError('Expected the extracted vanilla macro index')
        base_values = []
        for entry in index.findall('entry'):
            identity = (entry.get('name') or '').casefold()
            if identity == name.casefold():
                raise PlanError('The selected variant name already exists in the vanilla macro index')
            if identity == self.path.stem.casefold():
                base_values.append((entry.get('value') or '').replace('\\','/').removesuffix('.xml').casefold())
        if base_values != [str(self.path.with_suffix('')).casefold()]:
            raise PlanError('The vanilla index does not resolve the inspected ship macro to its source')
        source = safe_target(reference_dir, str(self.path), must_exist=True)
        document, digest = read_asset_xml(source)
        if not digest.startswith(self.digest):
            raise PlanError('The inspected ship source has changed. Inspect and review the variant again.')
        macros = document.findall('macro')
        if (document.tag != 'macros' or len(macros) != 1 or macros[0].get('name') != self.path.stem
                or not (macros[0].get('class') or '').startswith('ship_')
                or macros[0].find('component') is None):
            raise PlanError('Expected exactly one inspected ship macro with a component')
        if not macros[0].find('component').get('ref'):
            raise PlanError('Inspected ship has no component reference')
        target = self.path.with_name(name + '.xml')
        if relative == str(target):
            macros[0].set('name', name)
        elif relative == 'index/macros.xml':
            document = ET.Element('diff')
            add = ET.SubElement(document,'add',sel='/index')
            value = (PurePosixPath('extensions') / self.package / target.with_suffix('')).as_posix()
            ET.SubElement(add,'entry',name=name,value=value.replace('/','\\'))
            ET.indent(document, space='  ')
        else:
            raise PlanError('Outside the reviewed ship variant files')
        return ET.tostring(document,encoding='utf-8',xml_declaration=True).decode('utf-8')+'\n'
