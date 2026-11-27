"""Reviewed replacements of unique whole text runs in existing PPTX slides."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-presentation-edit-v1'
EXTRA=('presentation','.pptx')
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'p':P,'a':A,'r':R}
MAX_SLIDES=100
MAX_EXPANDED=64*1024*1024
MAX_PARTS=1000

def literal(value):
    if not isinstance(value,str) or not 1<=len(value)<=1000 or not value.strip() or any(
        ord(c)<32 or 0xd800<=ord(c)<=0xdfff or ord(c) in (0xfffe,0xffff) for c in value):
        raise ValueError('Use nonblank single-run text without control characters')
    return value

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'presentation','edits'} or not isinstance(spec['presentation'],str):
        raise ValueError('Expected presentation and edits')
    if not isinstance(spec['edits'],list) or not 1<=len(spec['edits'])<=100:
        raise ValueError('Invalid edit count')
    seen=set()
    for e in spec['edits']:
        if not isinstance(e,dict) or set(e)!={'slide','before','after'} or type(e['slide']) is not int or not 1<=e['slide']<=MAX_SLIDES:
            raise ValueError('Invalid slide edit')
        old=literal(e['before']);new=literal(e['after'])
        key=(e['slide'],old)
        if key in seen or old==new:raise ValueError('Duplicate or unchanged replacement')
        seen.add(key)
    return spec

def package(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=z.infolist()
        if not 1<=len(files)<=MAX_PARTS or sum(f.file_size for f in files)>MAX_EXPANDED:
            raise ValueError('PPTX archive exceeds bounds')
        seen=set();parts={}
        for f in files:
            n=f.filename;pieces=n.split('/')
            if (any(not x or x in ('.','..') or '\\' in x or ':' in x for x in pieces)
                or f.flag_bits&1 or n.casefold() in seen or n.casefold().startswith('_xmlsignatures/')
                or 'vbaproject' in n.casefold() or f.is_dir()):
                raise ValueError('Unsafe, signed, macro or duplicate PPTX entry')
            seen.add(n.casefold());parts[n]=z.read(f)
        return parts

def xml(data):
    from lxml import etree
    if b'\0' in data or re.search(br'<!\s*(?:DOCTYPE|ENTITY)',data,re.I):raise ValueError('Unsafe XML')
    return etree.fromstring(data,parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,huge_tree=False))

def slide_parts(parts):
    root=xml(parts['ppt/presentation.xml'])
    if root.tag!='{'+P+'}presentation':raise ValueError('Unsupported presentation namespace')
    rels=xml(parts['ppt/_rels/presentation.xml.rels'])
    lookup={}
    for rel in rels:
        if rel.tag!='{'+REL+'}Relationship':raise ValueError('Invalid presentation relationship')
        ident=rel.get('Id')
        if not ident or ident in lookup:raise ValueError('Ambiguous presentation relationship')
        lookup[ident]=rel
    names=[]
    for node in root.xpath('./p:sldIdLst/p:sldId',namespaces=NS):
        rel=lookup.get(node.get('{'+R+'}id'))
        if rel is None or rel.get('TargetMode','Internal')!='Internal' or rel.get('Type')!=R+'/slide':
            raise ValueError('Unsupported slide relationship')
        target=rel.get('Target','')
        name=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('ppt',target))
        if not re.fullmatch(r'ppt/slides/slide[0-9]+\.xml',name) or name not in parts or name in names:
            raise ValueError('Unsafe slide relationship')
        names.append(name)
    if not 1<=len(names)<=MAX_SLIDES:raise ValueError('Slide count outside bound')
    return names

def apply(raw,spec):
    from lxml import etree
    original=package(raw)
    names=slide_parts(original)
    trees={};targets=[]
    for e in spec['edits']:
        if e['slide']>len(names):raise ValueError('Slide number outside presentation')
        name=names[e['slide']-1]
        if name not in trees:trees[name]=xml(original[name])
        # Only ordinary text runs in shapes; no charts, tables, fields or notes.
        matches=[n for n in trees[name].xpath('.//p:sp/p:txBody/a:p/a:r/a:t',namespaces=NS)
                 if n.text==e['before']]
        if len(matches)!=1:raise ValueError('Expected exactly one matching whole text run on selected slide')
        targets.append((matches[0],e['after']))
    # Resolve all targets against original trees before changing any values.
    for node,value in targets:node.text=value
    changed={name:etree.tostring(tree,encoding='UTF-8',xml_declaration=True,standalone=True) for name,tree in trees.items()}
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in original.items():z.writestr(name,changed.get(name,data))
    payload=out.getvalue()
    verified=package(payload)
    if set(verified)!=set(original) or slide_parts(verified)!=names:
        raise ValueError('PPTX package structure changed')
    for name,data in original.items():
        if verified[name]!=changed.get(name,data):raise ValueError('PPTX part verification failed')
    for name,tree in trees.items():
        if etree.tostring(xml(verified[name]),method='c14n')!=etree.tostring(tree,method='c14n'):
            raise ValueError('Slide XML verification failed')
    # Independent presentation parser checks the resulting file can be opened.
    from pptx import Presentation
    if len(Presentation(io.BytesIO(payload)).slides)!=len(names):raise ValueError('Reopened slide count mismatch')
    return payload,len(names),len(changed)

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.pptx',extra=EXTRA)
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.pptx',extra=EXTRA)
def execute(root,plan):
    spec,dst,source=validate(root,plan)
    payload,count,changed=apply(guard.exact(source,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-presentation-edit-result-v1','status':'presentation_structure_verified','output':plan['output'],'sha256':sha,
            'slides':count,'changed_slide_parts':changed,'text_edits':len(spec['edits']),'source_unchanged':True,
            'untouched_part_bytes_verified':True,'visual_render_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Slide editing unavailable; inspect exact unique text runs and installed presentation tools'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
