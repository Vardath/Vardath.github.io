"""Bounded static Godot and XML repository observations; never executes source."""
import re
from xml.parsers import expat

from .repository_code_formats import SUFFIXES as CODE_SUFFIXES, parse as parse_code
SUFFIXES={'.gd','.tscn','.tres','.xml'}|CODE_SUFFIXES
IDENT=re.compile(r'[A-Za-z_][A-Za-z0-9_.-]{0,179}\Z')
RESOURCE=re.compile(r'res://[A-Za-z0-9_./ -]{1,240}\Z')
TOKEN=re.compile(r"""#[^\n]*|r?\"\"\"|r?\'\'\'|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_]\w*|[^\s]""")

def empty(kind='unparsed'):
    return {'symbols':[],'imports':[],'references':[],'resource_paths':[],
            'definitions':[],'xml_refs':[],'parse':kind}

def resource(value):
    if not RESOURCE.fullmatch(value):return None
    path=value[6:]
    if any(part in ('','.','..') for part in path.split('/')):return None
    return path

def godot(data,suffix):
    try:text=data.decode('utf-8-sig')
    except UnicodeError:return empty()
    result=empty('godot_lexical')
    triple=None
    for lineno,line in enumerate(text.splitlines(),1):
        if suffix in ('.tscn','.tres'):
            if not line.lstrip().startswith('[ext_resource '):continue
            match=re.search(r'\bpath="([^"\\]+)"',line)
            p=resource(match[1]) if match else None
            if p and len(result['resource_paths'])<100:result['resource_paths'].append(p)
            continue
        ts=[];cursor=0
        if triple:
            pos=line.find(triple)
            if pos<0:continue
            cursor=pos+3;triple=None
        for m in TOKEN.finditer(line,cursor):
            t=m[0]
            if t.startswith('#'):break
            if t in ('"""',"'''",'r"""',"r'''"):
                delimiter=t[-3:]
                if delimiter not in line[m.end():]:triple=delimiter
                break
            ts.append(t)
        if not ts:continue
        offset=1 if ts[0]=='static' else 0
        if len(ts)>offset+1 and ts[offset] in ('func','class','class_name','signal'):
            kind=ts[offset];name=ts[offset+1]
            if IDENT.fullmatch(name) and len(result['symbols'])<200:
                signature=line.strip().split('#',1)[0].strip()
                if len(signature)<=320:result['symbols'].append({'name':name,'kind':'gd_'+kind,'line':lineno,'signature':signature})
        for i,t in enumerate(ts):
            if t=='extends' and i==0 and i+1<len(ts):v=ts[i+1]
            elif t in ('load','preload') and i+3<len(ts) and ts[i+1]=='(' and ts[i+3]==')':v=ts[i+2]
            else:continue
            if len(v)>=2 and v[0] in ("'",'"') and v[-1]==v[0]:
                p=resource(v[1:-1])
                if p and len(result['resource_paths'])<100:result['resource_paths'].append(p)
        for i,t in enumerate(ts[:-1]):
            if ts[i+1]=='(' and IDENT.fullmatch(t) and len(result['references'])<300:
                if t not in ('if','while','for','match','func','signal') and not (i and ts[i-1] in ('func','signal')):
                    result['references'].append({'name':t,'line':lineno})
    return result

def xml(data):
    result=empty('xml_static')
    parser=expat.ParserCreate()
    count=0
    def reject(*args):raise ValueError('DTD or external entity prohibited')
    def start(tag,attrs):
        nonlocal count
        count+=1
        if count>10000:raise ValueError('XML node limit')
        line=parser.CurrentLineNumber
        name=attrs.get('name','')
        if tag in ('macro','component','cue','entry') and IDENT.fullmatch(name):
            if len(result['symbols'])<200:
                result['symbols'].append({'name':name,'kind':'xml_'+tag,'line':line,'signature':f'{tag} name="{name}"'})
            if tag in ('macro','component') and len(result['definitions'])<200:
                result['definitions'].append([tag,name])
        refs=[]
        if tag in ('macro','component'):refs.append((tag,attrs.get('ref','')))
        refs.extend((kind,attrs.get(kind,'')) for kind in ('macro','component'))
        for kind,value in refs:
            if IDENT.fullmatch(value) and len(result['xml_refs'])<300:
                result['xml_refs'].append([kind,value])
                if len(result['references'])<300:result['references'].append({'name':value,'line':line})
    parser.StartDoctypeDeclHandler=reject
    parser.EntityDeclHandler=reject
    parser.ExternalEntityRefHandler=reject
    parser.StartElementHandler=start
    try:parser.Parse(data,True)
    except (expat.ExpatError,ValueError,UnicodeError,OverflowError):return empty()
    return result

def parse(data,suffix):
    if suffix in CODE_SUFFIXES:return parse_code(data,suffix)
    return xml(data) if suffix=='.xml' else godot(data,suffix)
