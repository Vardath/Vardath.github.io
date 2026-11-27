"""Explicitly approved public HTTPS content-hash monitoring; no page instructions."""
from __future__ import annotations
from hashlib import sha256
from urllib.parse import urlsplit
import http.client
import ipaddress
import re
import socket
import ssl
import time

MAX_BODY=512*1024
MIN_INTERVAL=15*60
MAX_INTERVAL=7*86400
MAX_ACTIVE=32
MAX_CHECKS=1000

def checked_url(url):
    if not isinstance(url,str) or not 10<=len(url)<=1000 or any(ord(c)<33 or ord(c)>126 for c in url) or '\\' in url:
        raise ValueError('Enter an exact public HTTPS page URL')
    p=urlsplit(url)
    host=p.hostname
    if (p.scheme!='https' or not host or p.netloc!=host or p.username or p.password or p.port is not None
            or p.fragment or p.query or '?' in url or '#' in url or len(host)>253
            or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+',host)
            or not re.fullmatch(r'[a-z]{2,63}',host.rsplit('.',1)[-1])
            or host.endswith(('.local','.internal','.localhost','.test','.invalid','.onion'))):
        raise ValueError('Use a lowercase public DNS hostname, default HTTPS port, and no query, credentials or fragment')
    return host,p.path or '/'

def public_ip(value):
    ip=ipaddress.IPv4Address(value)
    if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_loopback or ip.is_link_local or ip.is_unspecified:
        raise ValueError('Nonpublic network destination refused')
    return str(ip)

def resolve_public(host,resolver=socket.getaddrinfo):
    rows=resolver(host,443,socket.AF_INET,socket.SOCK_STREAM)
    if not rows or len(rows)>32:raise ValueError('No bounded public IPv4 resolution')
    # Fail closed even on mixed private and public DNS answers.
    ips=tuple(dict.fromkeys(public_ip(row[4][0]) for row in rows))
    return ips[0]

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,443,timeout=6,context=ssl.create_default_context())
        self.ip=public_ip(ip)
    def connect(self):
        # No second DNS resolution, proxy or redirect. Verify TLS against the original DNS name.
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            sock.settimeout(self.timeout)
            sock.connect((self.ip,443))
            self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except BaseException:
            sock.close();raise

def stopped(cancelled,deadline):
    if (cancelled and cancelled()) or time.monotonic()>deadline:
        raise TimeoutError('Website check stopped')

def fetch(url,cancelled=None,*,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    host,path=checked_url(url)
    deadline=time.monotonic()+25
    stopped(cancelled,deadline)
    ip=resolve_public(host,resolver)
    stopped(cancelled,deadline)
    conn=connection(host,ip)
    try:
        conn.request('GET',path,headers={'User-Agent':'JANUS-local-monitor/1.0','Accept':'text/html, text/plain',
                                        'Accept-Encoding':'identity','Connection':'close'})
        response=conn.getresponse()
        stopped(cancelled,deadline)
        if response.status!=200:raise ValueError('Only exact HTTP 200 responses accepted; redirects refused')
        mime=response.headers.get_content_type()
        if mime not in ('text/html','text/plain'):raise ValueError('Unsupported response type')
        if response.getheader('Content-Encoding','identity').lower()!='identity':raise ValueError('Compressed response refused')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdecimal() or not 0<=int(length)<=MAX_BODY):
            raise ValueError('Website response exceeds byte bound')
        digest=sha256();total=0
        while True:
            stopped(cancelled,deadline)
            block=response.read1(min(32768,MAX_BODY-total+1))
            stopped(cancelled,deadline)
            if not block:break
            total+=len(block)
            if total>MAX_BODY:raise ValueError('Website response exceeds byte bound')
            digest.update(block)
        if length is not None and total!=int(length):raise ValueError('Incomplete website response')
        return {'sha256':digest.hexdigest(),'bytes':total,'mime':mime}
    finally:conn.close()

def epoch(now):
    if now is None:return int(time.time())
    if type(now) is not int or now<0:raise ValueError('Invalid monitoring clock')
    return now

class WebsiteMonitors:
    def __init__(self,conversations):
        self.conversations=conversations
        with conversations._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS website_monitors_v1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, chat_id TEXT NOT NULL,
                    url TEXT NOT NULL, interval_seconds INTEGER NOT NULL, remaining INTEGER NOT NULL,
                    due_utc INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'active',
                    last_sha256 TEXT, last_status TEXT NOT NULL DEFAULT 'awaiting baseline',
                    last_checked_utc INTEGER, changed_count INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS website_checks_v1 (
                    monitor_id INTEGER NOT NULL,due_utc INTEGER NOT NULL,checked_utc INTEGER NOT NULL,
                    status TEXT NOT NULL,sha256 TEXT,bytes INTEGER,
                    PRIMARY KEY(monitor_id,due_utc));
            """)
    def create(self,project,chat,url,interval,checks,*,approved=False,now=None):
        checked_url(url);now=epoch(now)
        if approved is not True or not isinstance(project,str) or not project or not isinstance(chat,str) or not chat:
            raise ValueError('Explicit network consent and chat binding required')
        if type(interval) is not int or not MIN_INTERVAL<=interval<=MAX_INTERVAL or type(checks) is not int or not 2<=checks<=MAX_CHECKS:
            raise ValueError('Choose 15 minutes–7 days and 2–1000 checks')
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT count(*) FROM website_monitors_v1 WHERE state='active'").fetchone()[0]>=MAX_ACTIVE:
                raise ValueError('Active website monitor limit reached')
            return db.execute("""INSERT INTO website_monitors_v1(project,chat_id,url,interval_seconds,remaining,due_utc)
                VALUES(?,?,?,?,?,?)""",(project,chat,url,interval,checks,now)).lastrowid
    def rows(self,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT * FROM website_monitors_v1 WHERE project=? AND chat_id=?
                ORDER BY CASE WHEN state='active' THEN 0 ELSE 1 END,id DESC LIMIT 100""",(project,chat))]
    def due(self,project,open_chats,*,now=None):
        now=epoch(now);allowed=set(open_chats)
        with self.conversations._db() as db:
            rows=db.execute("""SELECT * FROM website_monitors_v1 WHERE state='active' AND project=? AND due_utc<=?
                ORDER BY due_utc,id LIMIT ?""",(project,now,MAX_ACTIVE)).fetchall()
            return next((dict(r) for r in rows if r['chat_id'] in allowed),None)
    def cancel(self,ident,project,chat):
        with self.conversations._db() as db:
            return bool(db.execute("UPDATE website_monitors_v1 SET state='cancelled' WHERE id=? AND project=? AND chat_id=? AND state='active'",(ident,project,chat)).rowcount)
    def cancel_chat(self,project,chat):
        with self.conversations._db() as db:
            return db.execute("UPDATE website_monitors_v1 SET state='cancelled' WHERE project=? AND chat_id=? AND state='active'",(project,chat)).rowcount
    def history(self,ident,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT c.* FROM website_checks_v1 c JOIN website_monitors_v1 m ON m.id=c.monitor_id
                WHERE m.id=? AND m.project=? AND m.chat_id=? ORDER BY c.due_utc DESC LIMIT 30""",(ident,project,chat))]
    def finish(self,snapshot,result=None,*,now=None):
        now=epoch(now)
        if result is not None:
            if (not isinstance(result,dict) or set(result)!={'sha256','bytes','mime'} or not isinstance(result['sha256'],str)
                    or not re.fullmatch(r'[0-9a-f]{64}',result['sha256']) or type(result['bytes']) is not int
                    or not 0<=result['bytes']<=MAX_BODY or result['mime'] not in ('text/plain','text/html')):
                raise ValueError('Invalid website observation')
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT * FROM website_monitors_v1 WHERE id=?",(snapshot['id'],)).fetchone()
            if row is None or dict(row)!=snapshot or row['state']!='active' or now<row['due_utc']:return None
            due=row['due_utc'];remaining=row['remaining']-1;interval=row['interval_seconds']
            digest=result['sha256'] if result else None
            status=('error' if result is None else 'baseline' if row['last_sha256'] is None else
                    'unchanged' if row['last_sha256']==digest else 'changed')
            next_due=due+((now-due)//interval+1)*interval
            db.execute("INSERT INTO website_checks_v1 VALUES(?,?,?,?,?,?)",
                       (row['id'],due,now,status,digest,result['bytes'] if result else None))
            db.execute("""UPDATE website_monitors_v1 SET remaining=?,due_utc=?,state=?,last_sha256=?,
                last_status=?,last_checked_utc=?,changed_count=changed_count+? WHERE id=?""",
                (remaining,next_due,'active' if remaining else 'finished',digest or row['last_sha256'],
                 status,now,int(status=='changed'),row['id']))
            return {'monitor_id':row['id'],'status':status,'checked_utc':now,'sha256':digest,
                    'remaining':remaining,'project':row['project'],'chat_id':row['chat_id']}
