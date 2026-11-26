"""Read-only, bounded sensory projection of the durable V39/V40 team graph.

Both societies independently observe the authoritative conversation DB. This
projection never queues work, replays leases, exposes prompts/paths/receipts,
or treats a worker's stage completion as project acceptance.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
from .delegation import eligible

ROLES=('janus','sentinel','implementation','multimedia','host')
STATES=('queued','running','complete','failed','interrupted')
BATCH_STATES=('running','complete','failed','interrupted')

def observe_delegation(job_db):
    path=Path(job_db).parent/'conversations.sqlite3'
    empty={'available':False,'pending':0,'active':[],'recent':[],'failed':0}
    if not path.is_file():return empty
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.row_factory=sqlite3.Row
            db.execute('BEGIN')
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'conversation_requests','agent_batches_v39','agent_stages_v39','agent_edges_v39'}<=tables:
                return empty
            pending=sum(eligible(r) for r in db.execute("""SELECT c.* FROM conversation_requests c
                WHERE c.state='pending' AND c.mode='chat' AND NOT EXISTS(
                    SELECT 1 FROM conversation_requests old WHERE old.chat_id=c.chat_id
                    AND old.project=c.project AND old.id<c.id
                    AND old.state IN ('pending','running','waiting_sources'))
                ORDER BY c.id LIMIT 32"""))
            rows=db.execute("""SELECT b.request_id,b.attempt,b.state,c.state AS conversation_state
                FROM agent_batches_v39 b JOIN conversation_requests c ON c.id=b.request_id
                ORDER BY CASE WHEN b.state='running' THEN 0 ELSE 1 END,b.request_id DESC LIMIT 16""").fetchall()
            active=[];recent=[]
            for b in rows:
                if b['state'] not in BATCH_STATES:continue
                args=(b['request_id'],b['attempt'])
                stages=db.execute("""SELECT s.role,s.state,
                    NOT EXISTS(SELECT 1 FROM agent_edges_v39 e
                      LEFT JOIN agent_stages_v39 d ON d.request_id=e.request_id
                      AND d.attempt=e.attempt AND d.stage=e.dependency
                      WHERE e.request_id=s.request_id AND e.attempt=s.attempt
                      AND e.stage=s.stage AND (d.state IS NULL OR d.state!='complete')) AS ready
                    FROM agent_stages_v39 s WHERE s.request_id=? AND s.attempt=?""",args).fetchall()
                counts={state:sum(s['state']==state for s in stages) for state in STATES}
                ready={role:sum(s['role']==role and s['state']=='queued' and s['ready'] for s in stages)
                       for role in ROLES}
                running={role:sum(s['role']==role and s['state']=='running' for s in stages)
                         for role in ROLES}
                item={'id':b['request_id'],'attempt':b['attempt'],'state':b['state'],
                      'conversation_state':b['conversation_state'],'stages':counts,
                      'ready_roles':ready,'running_roles':running,
                      'inconsistent':b['state']=='running' and b['conversation_state']!='running'}
                (active if b['state']=='running' else recent).append(item)
            # Only the latest batch of each thread is a current failure. Older
            # failed requests remain history, not an eternal active warning.
            failed=db.execute("""SELECT COUNT(*) FROM agent_batches_v39 b
                JOIN conversation_requests c ON c.id=b.request_id
                WHERE b.state IN ('failed','interrupted') AND c.state='failed'
                AND NOT EXISTS(SELECT 1 FROM conversation_requests n
                  WHERE n.chat_id=c.chat_id AND n.project=c.project AND n.id>c.id)""").fetchone()[0]
            return {'available':True,'pending':pending,'active':active,'recent':recent[:8],'failed':failed}
    except (sqlite3.Error,OSError,ValueError,TypeError,KeyError):
        return empty

def active_work(snapshot):
    return bool(snapshot['pending'] or snapshot['active'])

def conflict(snapshot):
    return any(b['inconsistent'] for b in snapshot['active'])


def observe_project_assignments(job_db):
    """Bounded role-state evidence, not source content or executable authority."""
    path=Path(job_db).parent/'task-graph.sqlite3'
    empty={'available':False,'active':[],'recent':[]}
    if not path.is_file():return empty
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.5)) as db:
            db.row_factory=sqlite3.Row
            rows=db.execute("""SELECT a.job_id,a.step_id,a.state,a.review_mode,
                (SELECT COUNT(*) FROM project_reviews_v43 r WHERE r.attempt=a.attempt AND r.kind='plan') AS plan_reviews,
                (SELECT COUNT(*) FROM project_reviews_v43 r WHERE r.attempt=a.attempt AND r.kind IN ('code','behavior_test')) AS source_reviews
                FROM project_assignments_v43 a ORDER BY
                CASE WHEN a.state IN ('assigned','reviewed','committing') THEN 0 ELSE 1 END,a.rowid DESC LIMIT 24""").fetchall()
        active=[];recent=[]
        for row in rows:
            item=dict(row)
            item['requester']='janus';item['assignee']='implementation';item['reviewer']='sentinel'
            (active if row['state'] in ('assigned','reviewed','committing') else recent).append(item)
        return {'available':True,'active':active,'recent':recent[:8]}
    except (sqlite3.Error,OSError,ValueError,TypeError):
        return empty
