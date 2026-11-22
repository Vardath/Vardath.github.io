"""Strict, consent-gated read-only WinGet discovery and package inspection.

The only permitted network-capable operations are fixed `winget search` and
`winget show` commands, each separately approved in the GUI. Manifest details
are untrusted metadata, not independent verification, a download command, or
permission to install the package. No shell or model-generated argv is used.
"""
from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime, timezone
from urllib.parse import urlsplit

MAX_SEARCH_RESULTS = 20
MAX_INSPECTION_BYTES = 64 * 1024
PACKAGE_ID_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_+.-]{0,126}[A-Za-z0-9]')
SHA256_PATTERN = re.compile(r'[0-9a-fA-F]{64}')
SHOW_HEADER = re.compile(r'^Found (?P<name>[^\[\]\r\n]{1,130}) \[(?P<id>[^\[\]\r\n]{3,128})\]\s*$')
# Only keys from the winget show documentation are recorded. All are UNTRUSTED.
SHOW_FIELDS = {
    'Version': 'version',
    'Publisher': 'publisher',
    'Publisher Url': 'publisher_url',
    'Homepage': 'homepage',
    'License': 'license',
    'License Url': 'license_url',
    'Installer Url': 'installer_url',
    'Installer URL': 'installer_url',
    'Installer SHA256': 'installer_sha256',
    'Installer Type': 'installer_type',
    'Description': 'description',
}


def _winget(which=None):
    finder = which or shutil.which
    executable = finder('winget.exe') or finder('winget')
    if not executable:
        raise FileNotFoundError('Windows Package Manager (winget) is not installed')
    return str(executable)


def winget_search_command(query: str, *, which=None) -> list[str]:
    """Return fixed read-only winget search argv; caller must obtain consent."""
    if not isinstance(query, str):
        raise ValueError('Enter a program name to search for')
    search=query.strip()
    if len(search)<2 or len(search)>100 or not re.fullmatch(r'[\w .()+-]{2,100}',search,flags=re.UNICODE):
        raise ValueError('Use 2–100 letters, numbers, spaces, dots, +, -, or parentheses')
    if search.startswith('-') or search.startswith('.') or not any(c.isalnum() for c in search):
        raise ValueError('Enter a program name rather than a command or option')
    return [_winget(which),'search','--query',search,'--source','winget',
            '--count',str(MAX_SEARCH_RESULTS),'--accept-source-agreements','--disable-interactivity']


def validate_package_id(value: str) -> str:
    """Validate one exact WinGet ID (not a path, CLI option, URL, or shell string)."""
    if not isinstance(value,str) or not (3<=len(value)<=128):
        raise ValueError('Enter a complete package ID (3–128 ASCII characters)')
    if not PACKAGE_ID_PATTERN.fullmatch(value) or '..' in value or '.' not in value:
        raise ValueError('Expected an exact vendor.package ID from the winget catalog')
    if any(part == '' for part in value.split('.')):
        raise ValueError('Empty package ID segments are not allowed')
    return value


def winget_show_command(package_id: str, *, which=None) -> list[str]:
    """Only asks official WinGet source for information about ONE exact package."""
    package_id=validate_package_id(package_id)
    return [_winget(which),'show','--id',package_id,'--exact','--source','winget',
            '--locale','en-US','--accept-source-agreements','--disable-interactivity']


def _safe_https(url: str) -> bool:
    """Validate display-only URL; never authorize a fetch or execution."""
    if not url or len(url)>1200 or any(ord(c)<32 for c in url):
        return False
    try:
        p=urlsplit(url)
        return (p.scheme=='https' and bool(p.hostname) and p.port in (None,443)
                and not (p.username or p.password) and not p.fragment
                and p.hostname.lower() not in {'localhost','localhost.localdomain'}
                and not p.hostname.endswith(('.local','.internal'))
                and ':' not in p.hostname  # no literal IPv6 / loopback URL
                and not re.fullmatch(r'\d+(?:\.\d+){3}',p.hostname))
    except (ValueError,TypeError):
        return False


def inspect_show_output(package_id: str, output: str, *, exit_code=0) -> dict:
    """Fail-closed parse of bounded *untrusted* CLI output.

    A complete receipt proves only that a trusted locally selected WinGet client
    produced this exact text for the exact submitted query and exited 0. It does
    NOT prove publisher identity, installer safety, valid signatures or licenses.
    The caller must not use this result to grant install permission.
    """
    package_id=validate_package_id(package_id)
    if exit_code != 0:
        raise ValueError(f'WinGet inspection failed with exit code {exit_code}')
    if not isinstance(output,str) or not output.strip():
        raise ValueError('WinGet produced no package details')
    data=output.encode('utf-8',errors='replace')
    if len(data)>MAX_INSPECTION_BYTES:
        raise ValueError('Package detail output exceeds the 64 KiB review limit')
    if any(ord(c)<32 and c not in ('\r','\n','\t') for c in output) or '\x1b' in output:
        raise ValueError('Package metadata contained control characters; review raw log')
    lines=output.splitlines()
    headers=[SHOW_HEADER.match(line.strip()) for line in lines]
    headers=[match for match in headers if match]
    if len(headers)!=1 or headers[0].group('id')!=package_id:
        raise ValueError('Package result did not contain exactly the requested ID')
    matched_name=headers[0].group('name').strip()
    fields={}
    for line in lines:
        if len(line)>2000:
            raise ValueError('Unusually long package field; inspect raw log')
        key, sep, value = line.strip().partition(':')
        key=key.strip()
        if not sep or key not in SHOW_FIELDS:
            continue
        field=SHOW_FIELDS[key]
        value=value.strip()
        if field in fields and fields[field]!=value:
            raise ValueError('Conflicting package metadata: '+field)
        if len(value)>1200:
            raise ValueError('Unusually long package metadata: '+field)
        fields[field]=value
    version=fields.get('version','')
    publisher=fields.get('publisher','')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+\-]{0,80}',version):
        raise ValueError('Package version missing or unrecognized; cannot pin a version')
    if not (2<=len(publisher)<=160) or any(ord(c)<32 for c in publisher):
        raise ValueError('Package publisher missing or invalid')
    sha=fields.get('installer_sha256','')
    if sha and not SHA256_PATTERN.fullmatch(sha):
        raise ValueError('Manifest installer SHA256 is malformed')
    unsafe_urls={field:value for field,value in fields.items()
                 if (field.endswith('_url') or field=='homepage') and value and not _safe_https(value)}
    # An invalid URL is not made clickable; parsing remains useful for diagnosis.
    for field in unsafe_urls:
        fields[field]=''
    return {
        'schema':'deepthort-winget-show-inspection-v1',
        'package_id':package_id,
        'source':'winget',
        'name':matched_name,
        'version':version,
        'publisher':publisher,
        'homepage':fields.get('homepage',''),
        'publisher_url':fields.get('publisher_url',''),
        'license':fields.get('license',''),
        'installer_url':fields.get('installer_url',''),
        'installer_sha256_manifest':sha.lower(),
        'installer_type':fields.get('installer_type',''),
        'unsafe_urls_rejected':sorted(unsafe_urls),
        'observed_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'confidence':'UNVERIFIED CATALOG METADATA — NOT INSTALL AUTHORIZATION',
        'install_authorized':False,
        'download_authorized':False,
    }


def format_inspection(receipt: dict) -> str:
    """Readable review summary only; no install or download action."""
    def field(name):
        return str(receipt.get(name) or 'Not provided')
    result=[f"Exact package ID: {field('package_id')}",
            f"Package name: {field('name')}",
            f"Manifest version: {field('version')}",
            f"Claimed publisher: {field('publisher')}",
            f"Publisher page: {field('publisher_url')}",
            f"Project homepage: {field('homepage')}",
            f"License: {field('license')}",
            f"Installer type: {field('installer_type')}",
            f"Manifest installer URL: {field('installer_url')}",
            f"Manifest SHA256: {field('installer_sha256_manifest')}",
            f"Catalog output SHA256: {field('output_sha256')}"]
    if receipt.get('unsafe_urls_rejected'):
        result.append('Rejected unsafe metadata URLs: '+', '.join(receipt['unsafe_urls_rejected']))
    result.extend(['',
        'READ ONLY: this is catalog-supplied metadata, not independently verified',
        'publisher identity, a verified installer, or permission to install.'])
    return '\n'.join(result)
