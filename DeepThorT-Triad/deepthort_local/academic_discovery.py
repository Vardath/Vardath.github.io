"""Reviewed academic metadata discovery through Crossref's public works search."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode,quote
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.public_json import retrieve
from deepthort_local.scientific_citations import record_fields,HOST
from deepthort_local.search_interpretation import terms

SCHEMA='janus-academic-discovery-v1'
FIELDS='DOI,title,author,issued,container-title,type,publisher'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'query','count','from_year','to_year'}:
        raise ValueError('Expected query, count and optional year bounds')
    literal(s['query'],450)
    if not terms(s['query']) or type(s['count']) is not int or not 1<=s['count']<=10:
        raise ValueError('Choose a meaningful query and 1–10 results')
    for k in ('from_year','to_year'):
        if s[k] is not None and (type(s[k]) is not int or not 1000<=s[k]<=9999):
            raise ValueError('Expected four-digit year or null')
    if s['from_year'] is not None and s['to_year'] is not None and s['from_year']>s['to_year']:
        raise ValueError('Publication date bounds reversed')
    return s
def normalize(s,data,raw):
    checked(s)
    if not isinstance(data,dict) or data.get('status')!='ok' or data.get('message-type')!='work-list':
        raise ValueError('Expected Crossref work-list')
    msg=data.get('message')
    if not isinstance(msg,dict) or not isinstance(msg.get('items'),list) or len(msg['items'])>s['count']:
        raise ValueError('Invalid or oversized literature results')
    total=msg.get('total-results')
    if type(total) is not int or total<0 or total<len(msg['items']):
        raise ValueError('Invalid provider total')
    q=terms(s['query']);rows=[];seen=set();omitted=0
    for rank,work in enumerate(msg['items'],1):
        try:
            r=record_fields(work)
            if not r['title'] or r['doi'] in seen:raise ValueError('Missing title or duplicate DOI')
            seen.add(r['doi'])
            # Crossref date filters may reflect publication dates differing from issued.
            year=r['year']
            within=None if year is None else ((s['from_year'] is None or year>=s['from_year']) and
                                            (s['to_year'] is None or year<=s['to_year']))
            found=sorted(q&terms(r['title']))
            rows.append({**r,'original_rank':rank,'doi_url':'https://doi.org/'+quote(r['doi'],safe='/'),
                         'matched_title_terms':found,'issued_year_within_requested_bounds':within,
                         'full_text_read':False,'claims_verified':False,'reference_only':True})
        except (ValueError,TypeError,KeyError):omitted+=1
    if msg['items'] and not rows:raise ValueError('Provider returned no usable bibliographic records')
    return {'schema':'janus-academic-discovery-result-v1','provider':'Crossref','query':s['query'],
            'requested_count':s['count'],'from_year':s['from_year'],'to_year':s['to_year'],
            'provider_reported_total':total,'returned_count':len(msg['items']),'omitted_count':omitted,
            'provider_response_sha256':hashlib.sha256(raw).hexdigest(),'results':rows,
            'full_text_read':False,'systematic_review_complete':False,'claims_verified':False,
            'limitations':'One bounded relevance-ranked Crossref metadata page; coverage and date fields may differ across indexes and publication versions. No full text, peer-review, retraction, claim or completeness verification.'}
def discover(s,*,approved=False,cancelled=None,transport=retrieve):
    checked(s)
    if approved is not True:raise ValueError('Explicit academic query consent required')
    params={'query.bibliographic':s['query'],'rows':s['count'],'select':FIELDS}
    filters=[]
    if s['from_year'] is not None:filters.append(f"from-pub-date:{s['from_year']:04d}-01-01")
    if s['to_year'] is not None:filters.append(f"until-pub-date:{s['to_year']:04d}-12-31")
    if filters:params['filter']=','.join(filters)
    data,raw=transport(HOST,'/works?'+urlencode(params),cancelled=cancelled)
    return normalize(s,data,raw)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Send exact bibliographic query, count and optional dates to Crossref once; publish metadata only.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,search=discover):
    s,dst,_=validate(root,plan);r=search(s,approved=True)
    if r.get('query')!=s['query'] or r.get('full_text_read') is not False or r.get('claims_verified') is not False:
        raise ValueError('Literature discovery receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    if json.loads(payload)!=r:raise ValueError('Literature report serialization mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'academic_metadata_discovered','output':plan['output'],'sha256':digest,
            'result_count':len(r['results']),'claims_verified':False,'systematic_review_complete':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Academic search unavailable; no literature completeness claim inferred'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
