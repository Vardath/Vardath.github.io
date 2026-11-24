"""Model-authored, bounded assembly of structured source documents.

Only a single approved target is assembled. The structural envelope comes
from the model, not a hardcoded game template. Each unit is parsed and
reviewed before admission; final output is parsed and independently reviewed.
No source file is written here.
"""
from __future__ import annotations
import json
import tomllib
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from .staged_source import (StageError,sha,_unit_plan,_check_cancel,_call,
                            _replacement,validate_source)

FORMATS=frozenset({'.xml','.svg','.json','.toml'})
MARKER='<!--DEEPTHORT_UNITS-->'


def strict_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise StageError('Duplicate JSON key: '+key)
            result[key]=value
        return result
    def invalid(value):raise StageError('Non-JSON numeric literal: '+value)
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)


def _xml(text):
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise StageError('DTD/entity declarations are not supported in staged XML')
    try:return ET.fromstring(text)
    except ET.ParseError as exc:raise StageError('Invalid assembled XML: '+str(exc)) from exc


def _envelope(text):
    if not isinstance(text,str) or len(text)>1200 or text.count(MARKER)!=1:
        raise StageError('Expected one bounded XML root with a single unit marker')
    try:root=ET.fromstring(text,parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    except ET.ParseError as exc:raise StageError('Invalid XML envelope') from exc
    _xml(text)
    if (len(root)!=1 or root[0].tag is not ET.Comment or
            root[0].text!='DEEPTHORT_UNITS' or (root.text or '').strip() or
            (root[0].tail or '').strip()):
        raise StageError('XML envelope must contain only the direct-child unit marker')
    return text,root.tag,dict(root.attrib)


def _plan(answer,suffix):
    # A model may return a single JSON fence, but never partial JSON.
    value=_replacement(answer,'').strip()
    data=strict_json(value)
    if suffix in ('.xml','.svg'):
        if not isinstance(data,dict) or set(data)!={'envelope','units'}:
            raise StageError('Expected XML envelope and ordered units')
        envelope=_envelope(data['envelope'])
    elif suffix=='.json':
        if not isinstance(data,dict) or set(data)!={'root','units'} or data['root'] not in ('object','array'):
            raise StageError('Expected JSON root type and ordered units')
        envelope=data['root']
    else:
        if not isinstance(data,dict) or set(data)!={'units'}:
            raise StageError('Expected ordered TOML units')
        envelope=None
    return envelope,_unit_plan(json.dumps({'units':data['units']},ensure_ascii=False))


def assemble(suffix,envelope,fragments):
    """Return exact assembled document and bounded observed structural metadata."""
    if suffix in ('.xml','.svg'):
        template,tag,attrs=envelope
        children=[]
        previous=set()
        for fragment in fragments:
            if MARKER in fragment or '<?xml' in fragment.lower():
                raise StageError('XML fragment may not redefine the document envelope')
            root=_xml(template.replace(MARKER,fragment))
            if (root.tag!=tag or root.attrib!=attrs or not len(root) or (root.text or '').strip()
                    or any((c.tail or '').strip() for c in root)):
                raise StageError('XML unit must consist only of complete child elements')
            fingerprints={ET.tostring(c,encoding='unicode') for c in root}
            if previous.intersection(fingerprints):
                raise StageError('XML unit repeats an earlier child')
            previous.update(fingerprints)
            children.extend({'tag':c.tag,'attributes':dict(c.attrib)} for c in root)
        result=template.replace(MARKER,'\n'.join(fragments))
        parsed=_xml(result)
        if len(parsed)!=len(children) or parsed.tag!=tag or parsed.attrib!=attrs:
            raise StageError('XML assembly changed the approved document envelope')
        return result,{'root':tag,'attributes':attrs,'children':children}
    if suffix=='.json':
        output={} if envelope=='object' else []
        for fragment in fragments:
            part=strict_json(fragment)
            if type(part) is not type(output) or not part:
                raise StageError('JSON unit has wrong root type or is empty')
            if envelope=='object':
                if output.keys() & part.keys():
                    raise StageError('JSON unit redefines earlier top-level keys')
                output.update(part)
            else:output.extend(part)
        return json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n',(
            {'root':'object','keys':list(output)} if envelope=='object' else
            {'root':'array','items':len(output)})
    if suffix=='.toml':
        for part in fragments:
            if not tomllib.loads(part):raise StageError('Empty TOML unit')
        result='\n'.join(fragments)
        data=tomllib.loads(result)
        def paths(table,prefix=''):
            out=[]
            for key,value in table.items():
                name=prefix+json.dumps(key,ensure_ascii=False)
                out.append(name)
                if isinstance(value,dict):out.extend(paths(value,name+'.'))
            return out
        return result,{'keys':paths(data)}
    raise StageError('Unsupported structured format')


def stage_new_document(client,council,advisor,*,session,path,goal,scope,master_sha,
                       review,cancelled=None,stage=None):
    suffix=PurePosixPath(path).suffix.casefold()
    if suffix not in FORMATS:raise StageError('Unsupported structured file format')
    if not goal.strip() or len(goal)>1000 or not scope.strip() or len(scope)>2600:
        raise StageError('Structured assembly needs bounded approved requirements')
    prefix=(f'APPROVED FILE: {path}\nFILE GOAL: {goal}\nMASTER SHA-256: {master_sha}\n'
            f'APPROVED REQUIREMENT CONTEXT:\n{scope}\n')
    identity=sha(json.dumps({'schema':'structured-assembly-v1','path':path,'goal':goal,
                             'scope':scope,'master':master_sha},sort_keys=True,ensure_ascii=False))
    if suffix in ('.xml','.svg'):
        shape=('Return JSON {"envelope":"<actualRoot><!--DEEPTHORT_UNITS--></actualRoot>",'
               '"units":["goal one","goal two"]}. Choose actual root, attributes and namespaces '
               'from requirements and inspected references; example is format only. '
               'Each unit will supply complete direct child elements.')
        instruction='Return only complete direct-child XML elements, not a second root or XML declaration.'
    elif suffix=='.json':
        shape=('Return JSON {"root":"object","units":["goal one","goal two"]}; choose object or array '
               'as required. Each unit contributes distinct object keys or ordered array items.')
        instruction='Return a complete JSON object or array matching the chosen root type; do not repeat earlier keys.'
    else:
        shape=('Return JSON {"units":["goal one","goal two"]}. Place root keys before tables. '
               'Each unit is a complete TOML fragment, with explicit table headers for table entries.')
        instruction='Return standalone TOML with explicit tables where needed; never redefine earlier keys or tables.'
    ask=('JANUS: plan 2 to 8 ordered small units for this exact structured file, not new paths. '
         'Never invent installed game identifiers or claim execution. '+shape+'\n'+prefix)
    feedback=''
    planned=None
    for attempt in range(2):
        _check_cancel(cancelled)
        request=ask+('\nCorrect rejected plan: '+feedback[:300] if feedback else '')
        try:
            envelope,units=_plan(council._run(advisor,role=f'JANUS_DOCUMENT_{attempt}',
                session=session,evidence_sha=sha(identity+sha(request)),prompt=request,stage=stage),suffix)
            review(json.dumps({'path':path,'envelope':envelope,'units':units},ensure_ascii=False),'plan')
        except ValueError as exc:
            feedback=str(exc)
            continue
        planned=(envelope,units)
        break
    if planned is None:raise StageError('Structured file plan rejected: '+feedback[:300])
    envelope,units=planned
    fragments=[]
    observed={}
    for i,unit in enumerate(units):
        _check_cancel(cancelled)
        if stage:stage(f'JANUS assembling {path}: structured unit {i+1}/{len(units)}')
        context=json.dumps({'envelope':envelope,'completed':units[:i],
                            'remaining':units[i+1:],'observed_structure':observed},ensure_ascii=False)
        if len(context)>1800:
            raise StageError('Structured interfaces exceed bounded context; split the approved file')
        request=(instruction+' Implement only this unit. Preserve earlier content. '
                 'No markdown, placeholder values, invented identifiers or claims of testing.\n'+prefix+
                 f'UNIT {i+1}/{len(units)}: {unit}\nSTRUCTURE CONTEXT:\n{context}')
        feedback=''
        for attempt in range(2):
            _check_cancel(cancelled)
            prompt=request+('\nCorrect rejected fragment: '+feedback[:350] if feedback else '')
            try:
                fragment=_replacement(_call(client,f'{session}-document-{i+1}-{attempt+1}-{sha(prompt)[:16]}',
                                            prompt,768),'\n')
                assembled,new_observed=assemble(suffix,envelope,fragments+[fragment])
                validate_source(path,assembled)
                review(f'Structured unit {i+1}: {unit}\n{fragment}','code')
            except ValueError as exc:
                feedback=str(exc)
                continue
            fragments.append(fragment)
            observed=new_observed
            break
        else:raise StageError(f'Structured unit {i+1} rejected: {feedback[:300]}')
    assembled,_=assemble(suffix,envelope,fragments)
    validate_source(path,assembled)
    _check_cancel(cancelled)
    review(assembled,'code')
    _check_cancel(cancelled)
    return {'source':assembled,'before_sha256':None,'after_sha256':sha(assembled),
            'changed_ranges':len(fragments),'ranges':len(fragments),'master_sha256':master_sha}
