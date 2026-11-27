"""Assess observable source-transparency cues and quote-bound reviewer findings."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.structured_source import strict_json
from deepthort_local.long_form_writing import literal
from deepthort_local.multi_source_research import assemble,REPORT_SCHEMA

SCHEMA='janus-source-credibility-v1'
EXTRA=('research','.json')
MAX_REPORT=4*1024*1024
DIMENSIONS={
    'authorship':r'\b(?:written by|authored by|author\s*:|byline\s*:|editor\s*:|corresponding author)\b|\b(?:author|editor|byline)\s*:',
    'publication_date':r'\b(?:published|posted|last updated|updated|revised|publication date|date published)\s*(?:on\s+|:\s*|\s+)(?:\d{4}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}|\d{1,2}\s+[A-Za-z]+|[A-Za-z]+\s+\d{1,2}|\d{4}\b)',
    'references':r'\b(?:references|bibliography|works cited|source materials|citations|doi\s*:|https://doi\.org/)',
    'methodology':r'\b(?:methods|methodology|sample size|data collection|study design|experimental procedure|statistical analysis)\b',
    'conflicts_funding':r'\b(?:conflicts? of interest|competing interests|funding statement|funded by|sponsored by|advertisement|affiliate links?|financial disclosure)\b',
    'corrections':r'\b(?:correction policy|corrections|erratum|corrigendum|retraction|retracted|editorial policy)\b',
}
PATTERNS={k:re.compile(v,re.I) for k,v in DIMENSIONS.items()}
ASSESSMENTS=('supports_credibility','raises_concern','unclear')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'research','findings'} or not isinstance(s['research'],str):
        raise ValueError('Expected research report path and optional quote-bound findings')
    rows=s['findings']
    if not isinstance(rows,list) or len(rows)>30:raise ValueError('Choose at most 30 reviewer findings')
    seen=set()
    for r in rows:
        if (not isinstance(r,dict) or set(r)!={'source_id','dimension','assessment','line','start','quote','reason'}
                or not isinstance(r['source_id'],str) or not re.fullmatch(r'S[1-5]',r['source_id'])
                or not isinstance(r['dimension'],str) or r['dimension'] not in DIMENSIONS
                or r['assessment'] not in ASSESSMENTS or type(r['line']) is not int or not 1<=r['line']<=100000
                or type(r['start']) is not int or not 0<=r['start']<=100000):
            raise ValueError('Invalid source finding')
        literal(r['quote'],480);literal(r['reason'],600)
        key=(r['source_id'],r['dimension'])
        if key in seen:raise ValueError('One reviewer finding per source and dimension')
        seen.add(key)
    return s

def load_report(raw):
    if not isinstance(raw,bytes) or not raw or len(raw)>MAX_REPORT:raise ValueError('Research report exceeds bound')
    report=strict_json(raw.decode('utf-8-sig'))
    if not isinstance(report,dict) or report.get('schema')!=REPORT_SCHEMA or not isinstance(report.get('sources'),list):
        raise ValueError('Use a multi-source research evidence report')
    rows=report['sources']
    if not 2<=len(rows)<=5 or any(not isinstance(r,dict) or r.get('status') not in ('retrieved','unavailable') for r in rows):
        raise ValueError('Invalid research source rows')
    observations=[r.get('evidence') if r['status']=='retrieved' else None for r in rows]
    # Rebuild all derived fields and validate each extracted text digest. This is
    # consistency verification, not a signature or independent proof of origin.
    if assemble({'question':report.get('question'),'urls':report.get('reviewed_urls')},observations)!=report:
        raise ValueError('Research report consistency check failed')
    return report

def cues(text,pattern):
    results=[]
    for n,line in enumerate(text.split('\n'),1):
        for match in pattern.finditer(line):
            start=max(0,match.start()-80);end=min(len(line),match.end()+240)
            results.append({'line':n,'start':start,'quote':line[start:end],'matched_cue':match.group(0)})
            if len(results)>=3:return results
    return results

def assess(s,raw):
    checked(s);report=load_report(raw);by_id={r['id']:r for r in report['sources']}
    findings={}
    for f in s['findings']:
        source=by_id.get(f['source_id'])
        if not source or source['status']!='retrieved':raise ValueError('Reviewer finding requires retrieved source')
        lines=source['evidence']['text'].split('\n');i=f['line']-1
        if i>=len(lines) or lines[i][f['start']:f['start']+len(f['quote'])]!=f['quote']:
            raise ValueError('Reviewer quote does not match exact source line/offset')
        findings[(f['source_id'],f['dimension'])]=f
    rows=[]
    for source in report['sources']:
        row={k:source[k] for k in ('id','url','hostname','status')}
        if source['status']=='unavailable':
            row.update({'assessment_status':'unavailable','dimensions':{},'cautions':['Source could not be retrieved; no assessment possible.']})
            rows.append(row);continue
        page=source['evidence'];text=page['text'];dimensions={}
        for name,pattern in PATTERNS.items():
            hits=cues(text,pattern);finding=findings.get((source['id'],name))
            dimensions[name]={'cue_status':'literal_cue_found' if hits else 'no_literal_cue_detected',
                'observed_excerpts':hits,'reviewer_finding':finding,
                'verified_as_true':False}
        cautions=['Literal cues can be incidental, misleading or absent from extracted text.',
                  'HTTPS and response hashes do not establish author identity, authority, truth or independence.']
        if source['duplicate_text_of']:
            cautions.append('Identical extracted text to '+source['duplicate_text_of']+'; do not count as independent corroboration.')
        if any(f['assessment']=='raises_concern' for f in findings.values() if f['source_id']==source['id']):
            cautions.append('Reviewer recorded a concern; examine the cited quote and reasoning.')
        row.update({'assessment_status':'transparency_cues_reviewed','title':page['title'],'text_sha256':page['text_sha256'],
                    'duplicate_text_of':source['duplicate_text_of'],'dimensions':dimensions,'cautions':cautions})
        rows.append(row)
    return {'schema':'janus-source-credibility-result-v1','question':report['question'],
            'research_report_sha256':hashlib.sha256(raw).hexdigest(),'sources':rows,
            'reviewer_findings_count':len(findings),'network_performed':False,
            'credibility_independently_verified':False,'claims_verified':False,'reference_only':True,
            'limitations':'Transparency and accountability cues are literal observations, not truth tests. A missing cue is not proof of absence. Optional reviewer judgments are attributed to the supplied specification and quote-checked, not independently validated. No aggregate credibility score or domain-based trust ranking.'}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,path=validate(root,plan);r=assess(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    return plan,{'research':s['research'],'question':r['question'],'findings':s['findings'],
                 'sources':len(r['sources']),'scope':r['limitations']}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    s,dst,path=validate(root,plan);r=assess(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'source_transparency_assessed','output':plan['output'],'sha256':digest,
            'source_count':len(r['sources']),'reviewer_findings_count':r['reviewer_findings_count'],
            'credibility_independently_verified':False,'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Credibility assessment unavailable; inspect exact evidence and quote-bound findings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
