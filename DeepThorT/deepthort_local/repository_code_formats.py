"""Bounded lexical JS/TS and C# observations, not compiler/type resolution."""
from __future__ import annotations
import posixpath
import re

JS_SUFFIXES={'.js','.jsx','.mjs','.cjs','.ts','.tsx','.mts','.cts'}
SUFFIXES=JS_SUFFIXES|{'.cs'}
IDENT=r'[A-Za-z_$][A-Za-z0-9_$]*'
NAMESPACE=r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*'
MODULE=re.compile(r'\.{1,2}/[A-Za-z0-9_./-]{1,240}\Z')
# Each token is either a complete literal or a code token. Multiline
# comments and opaque strings are never searched for declarations.
LEX=re.compile(r"""//[^\n]*|/\*[\s\S]*?(?:\*/|\Z)|@"(?:""|[^"])*"|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|[A-Za-z_$][\w$]*|=>|[^\s]""")

def parse(data,suffix):
    from .repository_formats import empty
    try:text=data.decode('utf-8-sig')
    except UnicodeError:return empty()
    # Complex template interpolation and C# raw/interpolated literals need
    # a real parser. Refuse those files rather than index their embedded text.
    if (suffix in JS_SUFFIXES and ('\x60' in text or re.search(r'/[^/*\n][^\n]*/[gimsuyd]*\s*[;,.)]',text))
        or suffix=='.cs' and ('"""' in text or '$"' in text or '$@"' in text or '@$"' in text)):
        return empty()
    out=empty('cs_lexical' if suffix=='.cs' else 'js_lexical')
    out.update(module_paths=[],namespaces=[],namespace_uses=[])
    lines=text.splitlines()
    by_line={}
    line=1;end=0
    for m in LEX.finditer(text):
        line+=text.count('\n',end,m.start())
        token=m[0]
        if not token.startswith(('//','/*')):
            # A naked quote means an unsupported or unterminated literal.
            if token in ("'",'"'):return empty()
            by_line.setdefault(line,[]).append(token)
        line+=token.count('\n');end=m.end()
    def symbol(name,kind,lineno,signature):
        if len(out['symbols'])<200 and len(name)<=180 and len(signature)<=320:
            out['symbols'].append({'name':name,'kind':kind,'line':lineno,'signature':signature})
    def literal(t):
        return t[1:-1] if len(t)>1 and t[0] in ("'",'"') and t[-1]==t[0] and MODULE.fullmatch(t[1:-1]) else None
    for lineno,ts in by_line.items():
        # Mask literal contents in the declaration signature. Source lines
        # themselves are not copied, and only bounded declarations are kept.
        masked=['<literal>' if t.startswith(("'",'"','@"')) else t for t in ts]
        statement=' '.join(masked)
        if suffix in JS_SUFFIXES:
            match=re.match(r'^(?:(?:export|default|declare|abstract|async)\s+)*(class|interface|type|enum|function|const|let|var)\s+('+IDENT+r')\b',statement)
            if match:
                kind,name=match.groups()
                # Variables represent observed declarations, not inferred callable APIs.
                symbol(name,'js_'+kind,lineno,statement.split('{',1)[0].strip())
            if ts[0] in ('import','export'):
                values=[]
                if ts[0]=='import' and len(ts)>1 and literal(ts[1]):values=[ts[1]]
                else:values=[ts[i+1] for i,t in enumerate(ts[:-1]) if t=='from']
                for value in values:
                    p=literal(value)
                    if p and len(out['module_paths'])<100:out['module_paths'].append(p)
            # Exports via explicit named export lists are lexical observations.
            if ts[:2]==['export','{']:
                for name in re.findall(IDENT,statement.split('}',1)[0][8:]):
                    if name not in ('as',) and len(out['symbols'])<200:
                        symbol(name,'js_export',lineno,'export '+name)
        else:
            m=re.match(r'^(?:global\s+)?(namespace|using)\s+('+NAMESPACE.replace(r'\.',r'\s*\.\s*')+r')\s*([;{])',statement)
            if m:
                kind,name,_=m.groups();name=name.replace(' ','')
                key='namespaces' if kind=='namespace' else 'namespace_uses'
                if len(out[key])<100:out[key].append(name)
                if kind=='namespace':symbol(name,'cs_namespace',lineno,'namespace '+name)
            m=re.match(r'^(?:(?:public|private|protected|internal|static|sealed|abstract|partial|readonly|file|new)\s+)*(class|struct|interface|enum|record)\s+('+IDENT+r')\b',statement)
            if m:symbol(m[2],'cs_'+m[1],lineno,statement.split('{',1)[0].strip())
            # Only explicitly access-modified, single-line method declarations.
            m=re.match(r'^(?:public|private|protected|internal)\s+(?:(?:static|virtual|override|async|sealed|abstract|new|unsafe|extern|partial)\s+)*[\w.<>?,\[\] ]+\s+('+IDENT+r')\s+\(',statement)
            if m and ')' in statement:symbol(m[1],'cs_method',lineno,statement.split('{',1)[0].split('=>',1)[0].strip())
        for i,t in enumerate(ts[:-1]):
            if ts[i+1]=='(' and re.fullmatch(IDENT,t) and t not in ('if','for','while','switch','function','catch','using') and len(out['references'])<300:
                out['references'].append({'name':t,'line':lineno})
    return out

def module_targets(path,spec,paths):
    """Resolve exact existing local modules only, no package/alias guessing."""
    if not MODULE.fullmatch(spec):return []
    rel=posixpath.normpath(posixpath.join(posixpath.dirname(path),spec))
    if rel in ('.','..') or rel.startswith('../') or rel.startswith('/'):return []
    if posixpath.splitext(rel)[1]:
        return [rel] if rel in paths and posixpath.splitext(rel)[1] in JS_SUFFIXES else []
    candidates={rel+s for s in JS_SUFFIXES}|{rel+'/index'+s for s in JS_SUFFIXES}
    return sorted(candidates&paths)
