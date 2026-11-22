"""Reviewed publisher pages for supported optional software.

This fixed list is an informational first step, NOT autonomous web discovery or
install authorization. A language-model response must never be used as an URL,
installer identity, command line, or executable without separate validation.
"""
from __future__ import annotations
from urllib.parse import urlparse
from .computer_inventory import INSTALL_CATALOG

# Direct publisher pages: deliberately no redirects, shorteners or model URLs.
OFFICIAL_SOURCES = {
    'Blender': ('Blender Foundation', 'https://www.blender.org/download/'),
    'Godot': ('Godot Engine', 'https://godotengine.org/download/windows/'),
    'Git': ('The Git Project', 'https://git-scm.com/install/win'),
    'Visual Studio Code': ('Microsoft', 'https://code.visualstudio.com/download'),
    'Unity Hub': ('Unity Technologies', 'https://unity.com/developer-tools'),
    'Android Studio': ('Google', 'https://developer.android.com/studio'),
    'Node.js': ('OpenJS Foundation', 'https://nodejs.org/en/download'),
    'Python': ('Python Software Foundation', 'https://www.python.org/downloads/windows/'),
}


def official_source(name: str):
    """Resolve a pre-reviewed official publisher URL, never an arbitrary input."""
    if not isinstance(name, str) or name not in INSTALL_CATALOG:
        return None
    row = OFFICIAL_SOURCES.get(name)
    if not row:
        return None
    publisher, url = row
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.fragment:
        return None
    if p.hostname not in {'www.blender.org','godotengine.org','git-scm.com',
                          'code.visualstudio.com','unity.com',
                          'developer.android.com','nodejs.org','www.python.org'}:
        return None
    return {'name': name, 'publisher': publisher, 'url': url,
            'package_id': INSTALL_CATALOG[name][0],
            'action': 'information_only; require separate user approval for installer'}
