"""Read-only, user-authorized online software catalog search via Windows winget.

No model-supplied arguments are executed, and this module never downloads,
installs, approves package IDs, edits system sources or executes a shell.
"""
from __future__ import annotations
import re
import shutil

MAX_SEARCH_RESULTS = 20


def winget_search_command(query: str, *, which=None) -> list[str]:
    """Return a fixed read-only winget query argv; caller must request consent.

    Queries must represent a nonempty human-entered name, not any CLI switches.
    Raw output is untrusted package metadata and cannot authorize installation.
    """
    if not isinstance(query, str):
        raise ValueError('Enter a program name to search for')
    search=query.strip()
    if len(search)<2 or len(search)>100 or not re.fullmatch(r'[\w .()+-]{2,100}',search,flags=re.UNICODE):
        raise ValueError('Use 2–100 letters, numbers, spaces, dots, +, -, or parentheses')
    if search.startswith('-') or search.startswith('.') or not any(c.isalnum() for c in search):
        raise ValueError('Enter a program name rather than a command or option')
    finder=which or shutil.which
    executable=finder('winget.exe') or finder('winget')
    if not executable:
        raise FileNotFoundError('Windows Package Manager (winget) is not installed')
    return [str(executable),'search','--query',search,'--source','winget',
            '--count',str(MAX_SEARCH_RESULTS),'--accept-source-agreements','--disable-interactivity']
