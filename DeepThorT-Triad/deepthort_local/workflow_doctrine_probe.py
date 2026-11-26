"""Exercise real doctrine binding and typed artifact handoff with scripted output.

This is a structural/runtime-contract probe, not proof of native model reasoning.
"""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from .agent_doctrine import ROLES,VERSION,role_instruction,fingerprint,bind_creative
from .agent_contract import validate_creative_assignment
from .creative_core import request_packet,create_midi
from .role_inbox import RoleInbox,serial_rank
from .triad_errors import WorkerFailure

def exercise(health=None,cancelled=lambda:False):
    if cancelled():return {'status':'cancelled','detail':'Doctrine check stopped'}
    try:
        from triad_openvino_worker import model_messages
        source=[{'role':'system','content':'Follow the exact requested schema.'},
                {'role':'user','content':'Create the player-owned ship. Output JSON.'}]
        original=copy.deepcopy(source)
        if set(ROLES)!={'janus','sentinel','implementation','multimedia','memory'}:
            raise ValueError('Five distinct intelligent roles required')
        for role in ('janus','sentinel','implementation','memory'):
            bound=model_messages(role,source)
            if (not bound[0]['content'].startswith(role_instruction(role))
                    or source[0]['content'] not in bound[0]['content']
                    or bound[1:]!=source[1:] or source!=original):
                raise ValueError('Role binding changed authoritative task content')
        brief='Compose a short ascending score at 100 BPM.'
        if not bind_creative(brief).endswith(brief):raise ValueError('Creative brief changed')
        if len({fingerprint(r) for r in ROLES})!=5:raise ValueError('Role fingerprints not distinct')
        request=request_packet('janus','synthetic-project:job-1',brief)
        identity=validate_creative_assignment(request)
        forged=copy.deepcopy(request);forged['assignment']['publication_authorized']=True
        try:validate_creative_assignment(forged)
        except ValueError:pass
        else:raise ValueError('Forged publication authority accepted')
        with tempfile.TemporaryDirectory(prefix='triad-doctrine-') as tmp:
            def generate(folder,cancel,notify):
                data=json.loads((folder/'request.json').read_text('utf-8'))
                if validate_creative_assignment(data)!=identity:raise ValueError('Assignment changed')
                return json.dumps({'bpm':100,'notes':[[60,480],[62,480],[64,480],[65,480]]}),42
            folder,receipt=create_midi(root=tmp,requester='janus',scope='synthetic-project:job-1',brief=brief,generate=generate)
            if (receipt['assignment_sha256']!=identity or receipt['assigned_role']!='multimedia'
                    or receipt['requester']!='janus' or receipt['project_publication_authorized']
                    or receipt['native_inference_verified']
                    or receipt['sha256']!=hashlib.sha256((folder/'score.mid').read_bytes()).hexdigest()):
                raise ValueError('Artifact handoff was not bound to the requester and exact scope')
        primary=RoleInbox('implementation');other=RoleInbox('janus');memory=RoleInbox('memory')
        with primary,other,memory:
            if not all(x.locked() for x in (primary,other,memory)):raise ValueError('Independent role admission failed')
            try:
                with memory:raise ValueError('Duplicate memory call should defer')
            except WorkerFailure as e:
                if e.code!='worker_busy':raise
        a=(0,1,'implementation');b=(1,2,'sentinel')
        if not serial_rank(b,1)<serial_rank(a,1) or not serial_rank(a,61)<serial_rank(b,61):
            raise ValueError('Protected review priority or starvation prevention failed')
        if cancelled():return {'status':'cancelled','detail':'Doctrine check stopped'}
        if health is not None:
            value=health()
            if not isinstance(value,dict) or value.get('ready') is not True or value.get('doctrine_version')!=VERSION:
                return {'status':'blocked','detail':'Local contracts passed; running broker has not reported the installed doctrine'}
        return {'status':'passed','detail':'Five role bindings, preserved user instructions, typed staged MIDI handoff, independent inboxes and protected priority/aging passed. Scripted output only; native model understanding not certified.','evidence':{'count':5}}
    except Exception as exc:
        return {'status':'failed','detail':'Doctrine contract: '+type(exc).__name__+': '+str(exc)[:200]}
