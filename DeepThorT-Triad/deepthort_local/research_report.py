"""Offline evidence-linked research report publication, not autonomous fact checking."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.source_credibility import load_report,MAX_REPORT

SCHEMA='janus-research-report-v1'
EXTRA=('research','.json')
MARKER=re.compile(r'\[\[(S[1-5])\]\]')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'research','title','sections','limitations'} or not isinstance(s['research'],str):
        raise ValueError('Expected source report, title, sections and limitations')
    literal(s['title'],200)
    if not isinstance(s['sections'],list) or not 1<=len(s['sections'])<=12:
        raise ValueError('Choose 1–12 report sections')
    if not isinstance(s['limitations'],list) or not 1<=len(s['limitations'])<=12:
        raise ValueError('Explicit limitations required')
    for value in s['limitations']:literal(value,600)
    for section in s['sections']:
        if not isinstance(section,dict) or set(section)!={'heading','paragraphs'}:
            raise ValueError('Invalid section')
        literal(section['heading'],160)
        ps=section['paragraphs']
        if not isinstance(ps,list) or not 1<=len(ps)<=12:raise ValueError('Choose 1–12 paragraphs per section')
        for p in ps:
            if not isinstance(p,dict) or set(p)!={'text','evidence'}:
                raise ValueError('Expected narrative and exact evidence references')
            literal(p['text'],3000)
            refs=p['evidence']
            if not isinstance(refs,list) or not 1<=len(refs)<=5:raise ValueError('Each narrative paragraph needs 1–5 references')
            markers=set(MARKER.findall(p['text']))
            residue=MARKER.sub('',p['text'])
            if '[[' in residue or ']]' in residue:raise ValueError('Invalid citation marker')
            seen=set()
            for ref in refs:
                if (not isinstance(ref,dict) or set(ref)!={'source_id','line','start','quote'}
                        or not isinstance(ref['source_id'],str) or not re.fullmatch(r'S[1-5]',ref['source_id'])
                        or type(ref['line']) is not int or not 1<=ref['line']<=100000
                        or type(ref['start']) is not int or not 0<=ref['start']<=100000):
                    raise ValueError('Invalid evidence locator')
                literal(ref['quote'],480)
                key=(ref['source_id'],ref['line'],ref['start'],ref['quote'])
                if key in seen:raise ValueError('Repeated evidence reference')
                seen.add(key)
            if markers!={r['source_id'] for r in refs}:raise ValueError('Citation markers must match attached evidence')
    return s

def render(s,raw):
    checked(s);report=load_report(raw);sources={r['id']:r for r in report['sources']}
    esc=lambda x:html.escape(str(x),quote=True)
    h=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
       '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">',
       '<title>'+esc(s['title'])+'</title>',
       '<style>body{font:16px/1.65 system-ui,sans-serif;max-width:900px;margin:3rem auto;padding:0 1.5rem;color:#243247;background:#fff}h1,h2{line-height:1.2}h2{border-bottom:1px solid #d9e1eb;padding-bottom:.4rem}blockquote{margin:1rem 0;padding:.6rem 1rem;border-left:3px solid #789;background:#f4f6f9}small,.muted{color:#526175}code{overflow-wrap:anywhere}a{color:#165b8d}article{margin:1.5rem 0}li{margin:.4rem 0}</style>',
       '<body><h1>'+esc(s['title'])+'</h1><p class="muted">Reviewed research narrative · Evidence links verified for exact quotation, not factual support.</p>',
       '<p><strong>Research question:</strong> '+esc(report['question'])+'</p>',
       '<p>Retrieved sources: '+str(report['retrieved_count'])+' of '+str(len(sources))+'; distinct text: '+str(report['distinct_text_count'])+'. Source independence and claims are not independently verified.</p>']
    count=0
    for section in s['sections']:
        h.append('<section><h2>'+esc(section['heading'])+'</h2>')
        for p in section['paragraphs']:
            for ref in p['evidence']:
                source=sources.get(ref['source_id'])
                if not source or source['status']!='retrieved':raise ValueError('Citation requires retrieved source')
                lines=source['evidence']['text'].split('\n');i=ref['line']-1
                if i>=len(lines) or lines[i][ref['start']:ref['start']+len(ref['quote'])]!=ref['quote']:
                    raise ValueError('Exact report quote mismatch')
            parts=[];cursor=0
            for m in MARKER.finditer(p['text']):
                parts.append(esc(p['text'][cursor:m.start()]))
                parts.append('<a href="#source-'+m.group(1)+'">['+m.group(1)+']</a>')
                cursor=m.end()
            parts.append(esc(p['text'][cursor:]))
            h.append('<article><p>'+''.join(parts)+'</p>')
            for ref in p['evidence']:
                h.append('<blockquote>'+esc(ref['quote'])+'<br><small>'+esc(ref['source_id'])+' · line '+str(ref['line'])+' · offset '+str(ref['start'])+'</small></blockquote>')
                count+=1
            h.append('</article>')
        h.append('</section>')
    h.append('<section><h2>Limitations</h2><ul>')
    h.extend('<li>'+esc(x)+'</li>' for x in s['limitations'])
    h.append('<li>All narrative conclusions are supplied interpretations. Exact quote matches do not establish semantic or scientific support.</li></ul></section>')
    h.append('<section><h2>Source register</h2><ol>')
    for ident,source in sources.items():
        h.append('<li id="source-'+ident+'"><strong>'+ident+'</strong> · '+esc(source['status'])+'<br><code>'+esc(source['url'])+'</code>')
        if source['status']=='retrieved':
            page=source['evidence']
            h.append('<br>'+esc(page['title'])+'<br><small>Text SHA-256: <code>'+esc(page['text_sha256'])+'</code></small>')
            if source['duplicate_text_of']:h.append('<br>Identical text to '+esc(source['duplicate_text_of'])+'; not independent corroboration.')
        h.append('</li>')
    h.append('</ol><p class="muted">Input research SHA-256: <code>'+hashlib.sha256(raw).hexdigest()+'</code></p></section></body></html>')
    return '\n'.join(h).encode('utf-8'),count

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
    _,_,path=validate(root,plan);payload,count=render(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    return plan,{'research':s['research'],'title':s['title'],'sections':s['sections'],'limitations':s['limitations'],
                 'quote_count':count,'output_bytes':len(payload),'scope':'Exact quotes verified; supplied narrative not independently fact checked.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.html',extra=EXTRA)
def execute(root,plan):
    s,dst,path=validate(root,plan);payload,count=render(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'research_report_published','output':plan['output'],'sha256':digest,'sections':len(s['sections']),
            'verified_quote_count':count,'claims_verified':False,'network_performed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Report unavailable; inspect exact narrative, citations and evidence'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
