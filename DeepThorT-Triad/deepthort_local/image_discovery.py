"""Reviewed standalone Commons image discovery, independent of video workflows."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.stock_images import candidates
from deepthort_local.public_json import retrieve

SCHEMA='janus-image-discovery-v1'
HOST='commons.wikimedia.org'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'query','count'}:raise ValueError('Expected image query and count')
    literal(s['query'],450)
    if type(s['count']) is not int or not 1<=s['count']<=6:raise ValueError('Choose 1–6 candidates')
    return s
def discover(s,*,approved=False,cancelled=None,transport=retrieve):
    checked(s)
    if approved is not True:raise ValueError('Explicit query consent required')
    params={'action':'query','generator':'search','gsrsearch':s['query'],'gsrnamespace':'6','gsrlimit':'12',
            'prop':'imageinfo','iiprop':'url|size|mime|sha1|extmetadata',
            'iiextmetadatafilter':'LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription','format':'json'}
    data,raw=transport(HOST,'/w/api.php?'+urlencode(params),cancelled=cancelled)
    if not isinstance(data,dict) or 'error' in data or ('query' not in data and 'batchcomplete' not in data):
        raise ValueError('Invalid Commons response')
    rows=candidates(data)[:s['count']]
    return {'schema':'janus-image-discovery-result-v1','provider':'Wikimedia Commons','query':s['query'],
            'provider_response_sha256':hashlib.sha256(raw).hexdigest(),'candidates':rows,
            'image_downloaded':False,'license_independently_verified':False,'reference_only':True,
            'limitations':'Provider-declared CC0 or CC BY candidates only; verify the source page, attribution and third-party rights before reuse. No image bytes downloaded.'}
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,network_consent='Send this exact query to Wikimedia Commons once, then save candidate metadata. No image bytes downloaded.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan,*,search=discover):
    s,dst,_=validate(root,plan);r=search(s,approved=True)
    if r.get('query')!=s['query'] or r.get('reference_only') is not True or r.get('image_downloaded') is not False:
        raise ValueError('Discovery receipt mismatch')
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    if json.loads(payload)!=r:raise ValueError('Discovery serialization mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'image_candidates_recorded','output':plan['output'],'sha256':digest,
            'candidate_count':len(r['candidates']),'image_downloaded':False,'license_independently_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Image discovery unavailable; inspect query and provider access'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
