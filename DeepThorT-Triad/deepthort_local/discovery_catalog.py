"""Read-only recovery discovery for software outside the curated install list.

Only fixed generic public queries leave the machine. Search output is catalog
metadata, never executable arguments or approval. Exact package inspection
and explicit install selection remain separate operations.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import subprocess
import threading
from pathlib import Path

from .online_tool_search import winget_search_command,validate_package_id

QUERIES={
    'mesh':'3D modeling','cad':'CAD','image':'image editor',
    'vector':'vector graphics','audio':'audio editor','video':'video editor',
    'archive':'archive','compiler':'compiler','android':'Android SDK',
    'build':'build tool','xml':'XML editor','game':'game engine',
    'document':'document converter','database':'database',
    'debug':'debugger','test':'testing',
}
MAX_OUTPUT=65536


def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()


def candidates(text):
    """Accept only rows under an observed English WinGet table header."""
    if not isinstance(text,str) or len(text.encode('utf-8'))>MAX_OUTPUT:
        raise ValueError('Oversized catalog search result')
    lines=text.splitlines()
    header=None
    results=[]
    for line in lines:
        if any(ord(c)<32 for c in line):continue
        if header is None:
            m=re.match(r'^\s*Name\s+Id\s+Version(?:\s|$)',line)
            if m:
                id_start=line.index('Id',line.index('Name')+4)
                header=(id_start,line.index('Version',id_start+2))
            continue
        if not line.strip() or line.strip().startswith('-'):continue
        a,b=header
        if len(line)<b:continue
        ident=line[a:b].strip()
        name=line[:a].strip()
        try:validate_package_id(ident)
        except ValueError:continue
        if name and len(name)<=130 and ident not in {r['package_id'] for r in results}:
            results.append({'name':name,'package_id':ident})
        if len(results)>=20:break
    return results


def search(query_key,*,cancelled=None):
    if query_key not in QUERIES:raise ValueError('Unknown public capability category')
    argv=winget_search_command(QUERIES[query_key])
    if cancelled and cancelled():raise ValueError('Catalog search cancelled')
    proc=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL,shell=False,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    chunks=[]
    total=0
    truncated=False
    def stop():
        if proc.poll() is None:
            try:proc.kill()
            except OSError:pass
    timer=threading.Timer(45,stop);timer.start()
    try:
        while True:
            if cancelled and cancelled():raise ValueError('Catalog search cancelled')
            chunk=proc.stdout.read(4096)
            if not chunk:break
            total+=len(chunk)
            if total>MAX_OUTPUT:
                truncated=True
                stop()
                break
            chunks.append(chunk)
        code=proc.wait(timeout=5)
    finally:
        timer.cancel()
        stop()
        proc.stdout.close()
    if truncated or code!=0:raise ValueError('Catalog search did not finish with bounded successful output')
    return b''.join(chunks).decode('utf-8',errors='replace')


class DiscoveryStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS searches(
                evidence TEXT PRIMARY KEY,project TEXT NOT NULL,category TEXT,
                output_sha TEXT,results TEXT,status TEXT NOT NULL)''')
    def reserve(self,evidence,project):
        with sqlite3.connect(self.path) as db:
            return bool(db.execute("INSERT OR IGNORE INTO searches(evidence,project,status) VALUES(?,?,'started')",
                                   (evidence,str(project))).rowcount)
    def finish(self,evidence,category,output_sha,rows,status):
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE searches SET category=?,output_sha=?,results=?,status=? WHERE evidence=?',
                       (category,output_sha,json.dumps(rows),status,evidence))
    def recent(self,project):
        with sqlite3.connect(self.path) as db:
            rows=db.execute("SELECT results FROM searches WHERE project=? AND status='discovered' ORDER BY rowid DESC LIMIT 10",
                            (str(project),)).fetchall()
        result={}
        for row in rows:
            for item in json.loads(row[0]):result.setdefault(item['package_id'],item)
        return list(result.values())[:30]


def discover(store,council,client,*,session,project,master,goal,failure,baseline,
             cancelled=None,stage=None,fetch=search):
    evidence=sha(json.dumps([session,sha(master),goal,baseline],ensure_ascii=False))
    if cancelled and cancelled():return []
    if not store.reserve(evidence,project):return []
    category=None;output_sha=None;rows=[];status='inconclusive'
    try:
        from .recovery_council import select_source_section
        context=master if len(master)<=1200 else select_source_section(master,goal,1200)
        prompt=('JANUS: is a new software capability genuinely needed for this task? '
                'Choose exactly one public capability identifier below or NONE. '
                'Do not propose an installer, package ID, path or command. '
                'Only the generic category will be sent to the public software catalog.\n'
                +json.dumps(QUERIES)+'\nRequirements:\n'+context+
                '\nCurrent goal:\n'+goal[:700]+'\nFailure:\n'+failure[:500])
        category=council._run(client,role='JANUS_DISCOVERY_CATEGORY',session=session,
                              evidence_sha=evidence,prompt=prompt,stage=stage).strip()
        if category not in QUERIES or (cancelled and cancelled()):return []
        output=fetch(category,cancelled=cancelled)
        output_sha=sha(output)
        rows=candidates(output)
        if cancelled and cancelled():return []
        status='discovered' if rows else 'no_parseable_candidates'
        return rows
    finally:store.finish(evidence,category,output_sha,rows,status)
