"""Bounded, read-only conversation stimulus registration for each society.

The request store remains authoritative for exact full specifications.
A preview is sensory evidence, never a replacement specification or grant.
"""
from contextlib import closing
from pathlib import Path
import sqlite3

MAX_EVENTS=8

def observe_stimuli(job_db,previous=None):
    previous=previous if isinstance(previous,dict) else {}
    cursor=previous.get('cursor')
    if type(cursor) is not int or cursor<0:cursor=None
    path=Path(job_db).parent/'conversations.sqlite3'
    if not path.is_file():return previous or {'cursor':0,'events':[]}
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.5)) as db:
            if cursor is None:
                # On upgrade, register only the most recent bounded context.
                rows=db.execute("""SELECT id,mode,length(prompt),substr(prompt,1,360)
                    FROM conversation_requests ORDER BY id DESC LIMIT ?""",(MAX_EVENTS,)).fetchall()[::-1]
            else:
                rows=db.execute("""SELECT id,mode,length(prompt),substr(prompt,1,360)
                    FROM conversation_requests WHERE id>? ORDER BY id LIMIT ?""",
                    (cursor,MAX_EVENTS)).fetchall()
        if not rows:return previous or {'cursor':0,'events':[]}
        return {'cursor':rows[-1][0],'events':[
            {'id':r[0],'mode':r[1],'characters':r[2],'preview':r[3]} for r in rows]}
    except (sqlite3.Error,OSError,ValueError,TypeError):
        return previous or {'cursor':0,'events':[]}

def stimulus_frame(snapshot):
    from .janus_cognition import SenseFrame
    events=snapshot.get('events',[])
    if not events:return None
    # No raw paths or global identity supplied to these advisory frames.
    text=' | '.join(f"Request #{r['id']} ({r['mode']}, {r['characters']} characters; preview only): {r['preview']}"
                    for r in events[-3:])
    return SenseFrame('text','conversation_stimuli',text,salience=.75,uncertainty=.5)
