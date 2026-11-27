"""Reviewed GitHub draft releases for existing exact lightweight tags."""
from __future__ import annotations
import json
import re
import socket
from urllib.parse import quote
from .github_pull_request import _request,repository,literal
from .website_monitor import PinnedHTTPS,stopped
import time
def checked(s):
    if not isinstance(s,dict) or set(s)!={'repository','tag','commit','title','body'}:
        raise ValueError('Expected repository, existing tag, commit SHA, title and notes')
    repository(s['repository'])
    tag=s['tag']
    if not isinstance(tag,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',tag) or '..' in tag or tag.endswith(('.lock','.')):
        raise ValueError('Use a simple existing tag')
    if not isinstance(s['commit'],str) or not re.fullmatch(r'[0-9a-f]{40}',s['commit']):
        raise ValueError('Enter exact 40-character lowercase Git commit SHA')
    literal(s['title'],160);literal(s['body'],4000,multiline=True)
    return dict(s)
def create(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise ValueError('Explicit approval required')
    s=checked(s);repo=s['repository'];tag=s['tag']
    ref,_=_request('GET','/repos/'+repo+'/git/ref/tags/'+quote(tag,safe=''),None,token,cancelled,
                   resolver=resolver,connection=connection,expected=200)
    if not isinstance(ref,dict) or ref.get('ref')!='refs/tags/'+tag or not isinstance(ref.get('object'),dict) or ref['object'].get('type')!='commit' or ref['object'].get('sha')!=s['commit']:
        raise ValueError('Existing lightweight tag does not match reviewed commit; no release submitted')
    stopped(cancelled,time.monotonic()+1)
    payload=json.dumps({'tag_name':tag,'target_commitish':s['commit'],'name':s['title'],
                        'body':s['body'],'draft':True,'prerelease':False,'generate_release_notes':False},
                       ensure_ascii=True).encode('ascii')
    result,digest=_request('POST','/repos/'+repo+'/releases',payload,token,cancelled,resolver=resolver,connection=connection,expected=201)
    if not isinstance(result,dict) or type(result.get('id')) is not int or result['id']<=0 or result.get('draft') is not True or result.get('tag_name')!=tag:
        raise ValueError('Unconfirmed release receipt; inspect remote before retry')
    return {'status':'remote_draft_release_created','repository':repo,'release_id':result['id'],'tag':tag,
            'observed_tag_commit':s['commit'],'tag_checked_before_submission':True,'draft':True,
            'published':False,'assets_uploaded':False,'response_sha256':digest,
            'url':'https://github.com/'+repo+'/releases','scope':'Tag identity checked immediately before draft creation, not atomically locked. No live release acceptance or CI verification implied.'}
