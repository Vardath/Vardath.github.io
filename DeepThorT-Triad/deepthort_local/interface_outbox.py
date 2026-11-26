"""Durable, local, unsolicited Interface messages from observed new findings.

Each society owns its own outbox in its existing SQLite database. Proposals are
sensory inputs, not authority. Only a completed Front -> Interface pass can
publish a message. Acknowledgement is separate from executing any action.
"""
import hashlib
import json

SOCIETIES={'janus','sentinel'}
MAX_PENDING=8

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

def _table(society):
    if society not in SOCIETIES:raise ValueError('Unknown society')
    return society+'_recommendations'

def ensure_schema(db,society):
    table=_table(society)
    db.execute("""CREATE TABLE IF NOT EXISTS interface_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL UNIQUE,
        source_key TEXT NOT NULL UNIQUE, origin TEXT NOT NULL, stamp TEXT NOT NULL,
        cycle INTEGER NOT NULL, evidence_sha TEXT NOT NULL, body TEXT NOT NULL,
        read_at TEXT)""")
    db.execute("""CREATE TABLE IF NOT EXISTS interface_settings(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), baseline_id INTEGER NOT NULL)""")
    # Existing recommendations remain history on upgrade, not a burst of new
    # messages. Never reset the baseline on reopening an existing store.
    db.execute("INSERT OR IGNORE INTO interface_settings SELECT 1,COALESCE(MAX(id),0) FROM "+table)

def _candidate(row):
    return {'id':int(row[0]),'key':str(row[1]),'origin':str(row[2]),
            'stamp':str(row[3]),'finding':str(row[4])[:500],'proposal':str(row[5])[:1000]}

def pending(db,society):
    table=_table(society)
    field='problem' if society=='janus' else 'finding'
    rows=db.execute(f"""SELECT r.id,r.evidence_key,r.origin,r.recorded_at,r.{field},r.proposal
        FROM {table} r WHERE r.id>(SELECT baseline_id FROM interface_settings WHERE singleton=1)
        AND NOT EXISTS(SELECT 1 FROM interface_messages m WHERE m.source_key=r.evidence_key)
        ORDER BY r.id LIMIT ?""",(MAX_PENDING,)).fetchall()
    return [_candidate(row) for row in rows]

def select(candidates,appraisal,observation):
    """Front chooses one worthwhile finding, not every heartbeat."""
    if observation.get('game_detected'):return None
    for candidate in candidates:
        if (candidate.get('finding','').strip() and candidate.get('proposal','').strip()
                and candidate.get('origin') in ('janus','sentinel','local_model')
                and (appraisal.get('salience',0)>=.4 or candidate['origin']=='local_model')):
            return {'candidate':candidate,'evidence_sha':digest(candidate)}
    return None

def express(front):
    """Interface can see only Front's selected finding."""
    choice=front.get('outward_finding')
    if not choice:return None
    candidate=choice['candidate']
    if choice['evidence_sha']!=digest(candidate):raise ValueError('Finding changed before expression')
    return {'source_id':candidate['id'],'source_key':candidate['key'],
            'origin':candidate['origin'],'evidence_sha':choice['evidence_sha'],
            'body':('Finding (advisory, not verified as resolved): '+candidate['finding']+
                    '\nProposed next step: '+candidate['proposal'])}

def publish(db,society,readout,cycle,stamp):
    if readout.get('society')!=society:raise ValueError('Wrong society')
    cores=readout['cores'];front=cores['Front'];interface=cores['Interface']
    if front.get('input_sources')!=['Left','Right'] or interface.get('input_sources')!=['Front']:
        raise ValueError('Outward route bypassed Front')
    message=interface.get('message')
    if not message:return False
    selected=front.get('outward_finding') or {}
    ref=selected.get('evidence_sha')
    if (not ref or any(ref not in cores[name].get('finding_refs',[]) for name in
            ('Evidence','Safety','Counterpoint','Context','Logic','Novelty','Memory','Left','Right'))):
        raise ValueError('Finding was not propagated through all specialist and hemisphere readouts')
    expected=express(front)
    if expected!=message:raise ValueError('Interface message is not Front-bound')
    table=_table(society);field='problem' if society=='janus' else 'finding'
    row=db.execute(f"SELECT id,evidence_key,origin,recorded_at,{field},proposal FROM {table} WHERE id=?",
                   (message['source_id'],)).fetchone()
    # A recommendation pruned or changed since sensing cannot be sent.
    if row is None or digest(_candidate(row))!=message['evidence_sha']:return False
    baseline=db.execute('SELECT baseline_id FROM interface_settings WHERE singleton=1').fetchone()[0]
    if message['source_id']<=baseline:return False
    result=db.execute("""INSERT OR IGNORE INTO interface_messages
        (source_id,source_key,origin,stamp,cycle,evidence_sha,body) VALUES(?,?,?,?,?,?,?)""",
        (message['source_id'],message['source_key'],message['origin'],stamp,cycle,
         message['evidence_sha'],message['body'])).rowcount
    # Preserve unread messages. Bound old acknowledged history and advance
    # the baseline only past records that can no longer be re-emitted.
    db.execute("""DELETE FROM interface_messages WHERE read_at IS NOT NULL
        AND source_id NOT IN (SELECT id FROM """+table+""")
        AND id NOT IN (SELECT id FROM interface_messages ORDER BY id DESC LIMIT 500)""")
    return bool(result)

def messages(db,limit=20,*,unread_first=False):
    db.row_factory=__import__('sqlite3').Row
    order='(read_at IS NOT NULL), CASE WHEN read_at IS NULL THEN id END, id DESC' if unread_first else 'id DESC'
    return [dict(r) for r in db.execute('SELECT id,stamp,cycle,origin,body,read_at FROM interface_messages ORDER BY '+order+' LIMIT ?',
        (max(1,min(100,int(limit))),))]

def unread(db):
    return int(db.execute('SELECT COUNT(*) FROM interface_messages WHERE read_at IS NULL').fetchone()[0])

def mark_read(db,ids,stamp):
    # Acknowledge only exact message IDs the user saw, not a concurrent arrival.
    ids=tuple(dict.fromkeys(int(i) for i in ids))[:100]
    if not ids:return 0
    return db.execute('UPDATE interface_messages SET read_at=? WHERE read_at IS NULL AND id IN ('+
                      ','.join('?' for _ in ids)+')',(stamp,*ids)).rowcount
