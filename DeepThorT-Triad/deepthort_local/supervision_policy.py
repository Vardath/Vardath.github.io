"""Proportionate independent supervision, preserving all publication gates.

Reuse a previous *actual* Sentinel verdict only for the unchanged, approved
file intention of an ordinary new-file draft. This never stands in for source
review or runtime verification. Unknown context uses fresh semantic review.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
from .agent_contract import canonical_sha
from .reasoning_council import sha
from .agent_doctrine import fingerprint
from .triad_profiles import PROFILES,RUNTIME_VERSION
from .memory_duty import live_scope,reader

SCHEMA='triad-supervision-v63'

def review_depth(contract,amendments,*,corrective=False,prior_attempt=False,advice=''):
    reasons=[]
    if amendments:reasons.append('explicit user amendment')
    if corrective or prior_attempt:reasons.append('corrective or repeated assignment')
    if contract.get('baseline_sha256') is not None:reasons.append('existing source modification')
    if advice:reasons.append('current advisory context')
    return {'depth':'elevated' if reasons else 'ordinary','reasons':reasons}

def _identity(request,original,proposal,focus):
    return {'schema':SCHEMA,'request_id':request['id'],'project':str(Path(request['project']).resolve()),
            'chat_id':request['chat_id'],'original_sha':sha(original),'proposal_sha':sha(proposal),
            'focus_sha':sha(focus),'sentinel_doctrine':fingerprint('sentinel'),
            'sentinel_model':PROFILES['sentinel'][2],'runtime':RUNTIME_VERSION}

def _valid(receipt,identity):
    return (isinstance(receipt,dict) and receipt.get('accepted') is True and receipt.get('verified') is False
            and receipt.get('original_sha')==identity['original_sha'] and receipt.get('proposal_sha')==identity['proposal_sha']
            and isinstance(receipt.get('evidence_sha'),str) and len(receipt['evidence_sha'])==64
            and all(c in '0123456789abcdef' for c in receipt['evidence_sha']))

def record(path,request,original,proposal,focus,receipt,*,section='',amendments=()):
    # Complete original only; section-scoped large roadmaps require fresh
    # review when their approved milestone is actually dispatched.
    if (section or amendments or len(original)>3000 or request['mode']!='draft_plan'
            or request['prompt']!=original):return False
    identity=_identity(request,original,proposal,focus)
    if not _valid(receipt,identity):return False
    body={'identity':identity,'receipt':receipt}
    with closing(sqlite3.connect(path,timeout=2)) as db,db:
        db.execute("""CREATE TABLE IF NOT EXISTS approved_intent_reviews_v63(
            identity_sha TEXT PRIMARY KEY,body TEXT NOT NULL,receipt_sha TEXT NOT NULL)""")
        db.execute("INSERT OR REPLACE INTO approved_intent_reviews_v63 VALUES(?,?,?)",
                   (canonical_sha(identity),json.dumps(body,sort_keys=True),canonical_sha(body)))
    return True

def prior_plan(path,job_db,job,contract,original,proposal,focus,policy):
    if policy['depth']!='ordinary' or not str(job.get('approval_key','')).startswith('draft:'):return None
    try:
        key=job['approval_key']
        with closing(reader(Path(job_db).parent/'conversations.sqlite3',timeout=.05)) as db:
            draft=db.execute("SELECT request_id FROM project_drafts WHERE id=?",(int(key[6:]),)).fetchone()
        if not draft:return None
        bound=live_scope(job_db,job['id'],draft[0],states=('running',),timeout=.05)
        if (not bound or bound['spec_sha']!=sha(original) or bound['approval_key']!=contract['approval_key']
                or contract['job_id']!=job['id'] or contract['original_sha256']!=sha(original)
                or contract['plan_proposal_sha256']!=sha(proposal)
                or contract['baseline_sha256'] is not None
                or contract['amendments_sha256']!=canonical_sha([])):return None
        identity=_identity({'id':draft[0],'project':bound['project'],'chat_id':bound['chat_id']},original,proposal,focus)
        with closing(reader(path,timeout=.05)) as db:
            row=db.execute("SELECT body,receipt_sha FROM approved_intent_reviews_v63 WHERE identity_sha=?",(canonical_sha(identity),)).fetchone()
        if not row:return None
        body=json.loads(row[0])
        if canonical_sha(body)!=row[1] or body['identity']!=identity or not _valid(body['receipt'],identity):return None
        return {**body['receipt'],'supervision':'reused_exact_prior_sentinel_intention','prior_receipt_sha':row[1]}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return None
