"""Check literal external MD cue identifiers against pinned native cue names.

MD cue identifiers are script-wide. XML parent nesting is not a dotted property
path. This catches Manager.SelectMission while permitting Manager.$variables.
It is not a runtime/merged-load-order resolver.
"""
import re


def invalid_native_cue_refs(expression, index):
    errors=[]
    for script, data in index.items():
        pattern=r'\bmd\.'+re.escape(script)+r'\.([A-Z][A-Za-z_0-9]*(?:\.[A-Z][A-Za-z_0-9]*)*)'
        for name in re.findall(pattern, expression):
            if name not in data['identifiers']:
                errors.append('md.'+script+'.'+name)
    return errors
