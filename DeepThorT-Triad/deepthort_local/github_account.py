"""Read-only bounded public repository inventory for a verified GitHub session."""
import re
import socket
from urllib.parse import quote
from .github_pull_request import _request,repository,branch
from .website_monitor import PinnedHTTPS
from .github_oauth import Session

MAX_PAGE=10
PAGE_SIZE=30
def account(value,session):
    if not isinstance(value,dict) or type(value.get('id')) is not int or value['id']!=session.account_id or not isinstance(value.get('login'),str) or value['login'].casefold()!=session.login.casefold():
        raise ValueError('Connected account identity changed')
    return {'login':session.login,'account_id':session.account_id}

def repositories(rows,login):
    if not isinstance(rows,list) or len(rows)>PAGE_SIZE:raise ValueError('Unexpected repository page')
    seen=set();ids=set();result=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid repository record')
        name=repository(row.get('full_name'));ident=row.get('id')
        owner=row.get('owner')
        if not isinstance(owner,dict) or not isinstance(owner.get('login'),str) or owner['login'].casefold()!=login.casefold() or name.split('/')[0].casefold()!=login.casefold():
            raise ValueError('Unexpected repository owner')
        if type(ident) is not int or ident<=0 or ident in ids or name.casefold() in seen or row.get('private') is not False:
            raise ValueError('Invalid duplicate or nonpublic repository')
        if any(type(row.get(k)) is not bool for k in ('fork','archived','disabled')):
            raise ValueError('Invalid repository flags')
        default=branch(row.get('default_branch'))
        seen.add(name.casefold());ids.add(ident)
        result.append({'repository':name,'repository_id':ident,'default_branch':default,'fork':row['fork'],'archived':row['archived'],'disabled':row['disabled'],'url':'https://github.com/'+name})
    return result

def inspect(session,page,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit account inventory approval required')
    if not isinstance(session,Session) or not re.fullmatch(r'[A-Za-z0-9-]{1,39}',session.login) or type(session.account_id) is not int or session.account_id<=0:
        raise ValueError('Verified connected session required')
    if type(page) is not int or not 1<=page<=MAX_PAGE:raise ValueError('Choose page 1–10')
    def get(path):
        if cancelled and cancelled():raise ValueError('Account inventory cancelled')
        return _request('GET',path,None,session.token(),cancelled,resolver=resolver,connection=connection,expected=200)
    identity,first_sha=get('/user');profile=account(identity,session)
    rows,repo_sha=get('/users/'+quote(session.login,safe='')+'/repos?type=owner&sort=full_name&direction=asc&per_page=30&page='+str(page))
    found=repositories(rows,session.login)
    last,last_sha=get('/user')
    if account(last,session)!=profile:raise ValueError('Connected account changed')
    return {'status':'public_repository_page_retrieved','account':profile,'page':page,'page_size':PAGE_SIZE,
            'repositories':found,'possible_more':len(found)==PAGE_SIZE,'complete_inventory_verified':False,
            'response_sha256':[first_sha,repo_sha,last_sha],'remote_changed':False}
