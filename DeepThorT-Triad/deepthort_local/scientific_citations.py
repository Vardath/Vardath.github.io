"""Verify supplied bibliographic fields against a Crossref DOI metadata record."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import quote
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.public_json import retrieve
from deepthort_local.web_search import plain

SCHEMA='janus-scientific-citations-v1'
HOST='api.crossref.org'
DOI=re.compile(r'10\.[0-9]{4,9}/[A-Za-z0-9._;()/+:<>-]{1,240}\Z')
def doi_checked(value):
    if not isinstance(value,str) or not DOI.fullmatch(value) or any(p in ('','.','..') for p in value.split('/')):
        raise ValueError('Enter a bare supported DOI, not a URL or command')
    return value.casefold()
def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())
def checked(s):
    if not isinstance(s,dict) or set(s)!={'doi','title','first_author_family','year'}:
        raise ValueError('Expected DOI, title, first author family name and publication year')
    doi_checked(s['doi']);literal(s['title'],500);literal(s['first_author_family'],150)
    if type(s['year']) is not int or not 1000<=s['year']<=9999:raise ValueError('Expected four-digit publication year')
    return s
def first_text(values,limit):
    return plain(values[0],limit) if isinstance(values,list) and values else ''
def record_fields(work):
    if not isinstance(work,dict):raise ValueError('Invalid bibliographic record')
    doi=doi_checked(work.get('DOI'))
    title=first_text(work.get('title'),500)
    authors=work.get('author')
    family=plain(authors[0].get('family'),150) if isinstance(authors,list) and authors and isinstance(authors[0],dict) else ''
    issued=work.get('issued');year=None
    if isinstance(issued,dict):
        dates=issued.get('date-parts')
        if isinstance(dates,list) and dates and isinstance(dates[0],list) and dates[0]:
            candidate=dates[0][0]
            if type(candidate) is int and 1000<=candidate<=9999:year=candidate
    return {'doi':doi,'title':title,'first_author_family':family,'year':year,
            'publication':first_text(work.get('container-title'),500),
            'type':plain(work.get('type'),80),'publisher':plain(work.get('publisher'),300)}
def compare(s,data,raw):
    checked(s)
    if not isinstance(data,dict) or data.get('status')!='ok' or data.get('message-type')!='work':
        raise ValueError('Crossref did not return one work record')
    actual=record_fields(data.get('message'))
    if actual['doi']!=doi_checked(s['doi']):raise ValueError('Returned DOI differs from requested DOI')
    fields={}
    for key in ('title','first_author_family','year'):
        observed=actual[key];expected=s[key]
        status='unavailable' if observed in ('',None) else (
            'match' if (observed==expected if key=='year' else normalized(observed)==normalized(expected)) else 'differs')
        fields[key]={'supplied':expected,'registered':observed,'status':status}
    statuses={f['status'] for f in fields.values()}
    result='differs' if 'differs' in statuses else 'incomplete' if 'unavailable' in statuses else 'matches'
    return {'schema':'janus-citation-verification-result-v1','provider':'Crossref','doi':actual['doi'],
            'provider_response_sha256':hashlib.sha256(raw).hexdigest(),'registered_metadata':actual,
            'comparison':fields,'metadata_result':result,'doi_record_returned':True,
            'scientific_claim_support_verified':False,'full_text_read':False,'reference_only':True,
            'limitations':'Comparison with deposited Crossref metadata only. Issued year and first listed author are used; differences can reflect versions or citation conventions. No full-text, retraction, peer-review or scientific claim verification.'}
def verify(s,*,approved=False,cancelled=None,transport=retrieve):
    checked(s)
    if approved is not True:raise ValueError('Explicit DOI lookup consent required')
    # Only the DOI goes to the provider; supplied citation fields stay local.
    data,raw=transport(HOST,'/works/'+quote(doi_checked(s['doi']),safe='/'),cancelled=cancelled)
    return compare(s,data,raw)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Send only this DOI to Crossref once. Compare supplied title, first author family and issued year locally; publish a new report.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,lookup=verify):
    s,dst,_=validate(root,plan);r=lookup(s,approved=True)
    if r.get('doi')!=doi_checked(s['doi']) or r.get('scientific_claim_support_verified') is not False or r.get('reference_only') is not True:
        raise ValueError('Citation receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    if json.loads(payload)!=r:raise ValueError('Citation report serialization mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'citation_metadata_compared','output':plan['output'],'sha256':digest,
            'metadata_result':r['metadata_result'],'scientific_claim_support_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'DOI lookup unavailable; no finding about citation validity inferred'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
