"""Read-only bounded role assignment evidence, independent of process readiness."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .agent_contract import canonical_sha
from .delegation import binding

LIMIT = 60
ROLE_NAMES = {'janus':'JANUS','sentinel':'Sentinel','implementation':'Granite',
              'multimedia':'Gemma','memory':'Memory','host':'Host (not AI)'}


@contextmanager
def _reader(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=.25)
    db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON')
        yield db
    finally:db.close()


def assignment_rows(project, graph_path, conversation_path):
    """Return separate source and delegation snapshots; no leases or mutations."""
    rows=[]
    with _reader(graph_path) as db:
        for item in db.execute("""SELECT a.*,g.project AS graph_project,g.plan_sha256 AS graph_sha
            FROM project_assignments_v43 a JOIN graphs g ON g.job_id=a.job_id
            WHERE g.project=? ORDER BY a.rowid DESC LIMIT ?""",(project,LIMIT)):
            contract=json.loads(item['contract'])
            if (canonical_sha(contract)!=item['contract_sha'] or
                contract.get('job_id')!=item['job_id'] or contract.get('step_id')!=item['step_id'] or
                contract.get('project')!=project or contract.get('graph_sha256')!=item['graph_sha'] or
                (contract.get('requester'),contract.get('assignee'),contract.get('reviewer'))!=
                ('janus','implementation','sentinel')):
                raise ValueError('Source assignment contract identity mismatch')
            rows.append(('source:'+item['attempt'],
                ('Granite','Job #'+str(item['job_id']),str(contract['path']),item['state'],
                 'JANUS → Granite → Sentinel',item['attempt'])))
    with _reader(conversation_path) as db:
        for item in db.execute("""SELECT s.request_id,s.attempt,s.stage,s.role,s.state,
            b.binding AS batch_binding,b.state AS batch_state,c.*
            FROM agent_stages_v39 s JOIN agent_batches_v39 b ON s.request_id=b.request_id AND s.attempt=b.attempt
            JOIN conversation_requests c ON c.id=s.request_id
            WHERE c.project=? ORDER BY s.request_id DESC,s.stage LIMIT ?""",(project,LIMIT)):
            if binding(item)!=item['batch_binding']:
                raise ValueError('Delegated request identity mismatch')
            role=ROLE_NAMES.get(item['role'],item['role'])
            ident=f"delegation:{item['request_id']}:{item['attempt']}:{item['stage']}"
            rows.append((ident,(role,'Request #'+str(item['request_id']),item['stage'],
                 item['state'],'Batch '+item['batch_state'],str(item['attempt']))))
    return rows
