"""Fixed reviewed Blender native mesh workflow; no arbitrary scripts or .blend inputs."""
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import time
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions,linked
from .mesh_geometry import parse,triangle
from .neural_speech import exact_file
from .speaker_diarisation import stopped,MEMORY_LIMIT,MAX_LOG

EXE='blender.exe'
SCRIPT=Path(__file__).resolve().parent/'asset_probes'/'blender_build_mesh.py'
MAX_FILE=256*1024**2
MAX_VERTICES=10000
MAX_FACES=10000
MARKER='JANUS_BLEND_VERIFIED '
def packet(raw):
    vertices,faces,_,_=parse(raw)
    if len(vertices)>MAX_VERTICES or len(faces)>MAX_FACES:raise ValueError('Mesh exceeds Blender workflow bound')
    # Blender Mesh coordinates are IEEE single precision. Review exact quantized geometry.
    v=[[float(struct.unpack('<f',struct.pack('<f',x))[0]) for x in row] for row in vertices]
    # Canonicalize signed zero because it is not a geometric distinction.
    v=[[x if x else 0.0 for x in row] for row in v]
    f=[list(row) for row in faces]
    for face in f:triangle(v,face)
    if len({tuple(sorted(x)) for x in f})!=len(f):raise ValueError('Duplicate triangles; repair mesh first')
    return {'vertices':v,'faces':f}
def expected(p):
    raw=json.dumps([p['vertices'],p['faces']],separators=(',',':'),allow_nan=False).encode('ascii')
    return {'vertices':len(p['vertices']),'triangles':len(p['faces']),'geometry_sha256':hashlib.sha256(raw).hexdigest()}
def installed(root,exe):
    root=Path(root).resolve(strict=True);exe=Path(exe)
    if exe.name.casefold()!=EXE or exe.resolve(strict=True).is_relative_to(root):
        raise ValueError('Select trusted installed Blender outside project')
    return [exact_file(exe,MAX_FILE),exact_file(SCRIPT,65536)]
def review(root,source,output,exe,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.obj'},exists=True)
    guard.path_for(root,output,exclude,{'.blend'},exists=False)
    pin=snapshot_file(src);data=packet(guard.exact(src,pin,guard.MAX_INPUT))
    return {'schema':'janus-blender-mesh-workflow-v1','root':str(root),'source':source,'output':output,'exclude':exclude,
        'guard':pin,'files':installed(root,exe),'geometry':expected(data),'expires_at':int(time.time())+1800}
def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','files','geometry','expires_at'} or plan['schema']!='janus-blender-mesh-workflow-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid Blender workflow review')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.obj'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.blend'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed mesh changed')
    raw=guard.exact(src,plan['guard'],guard.MAX_INPUT);data=packet(raw)
    if expected(data)!=plan['geometry']:raise ValueError('Reviewed geometry changed')
    if not isinstance(plan['files'],list) or len(plan['files'])!=2 or installed(root,plan['files'][0]['path'])!=plan['files']:
        raise ValueError('Installed Blender or bundled script changed')
    return data,dst
def command(plan,folder):
    return [plan['files'][0]['path'],'--background','--factory-startup','--disable-autoexec','--threads','1',
        '--python-exit-code','19','--python',str(folder/'build.py'),'--',str(folder/'geometry.json'),str(folder/'output.blend')]
def verify(payload,log,geometry):
    if not isinstance(payload,bytes) or not 64<=len(payload)<=guard.MAX_OUTPUT or not payload.startswith(b'BLENDER'):
        raise ValueError('Expected bounded uncompressed Blender file')
    if not isinstance(log,bytes) or not 1<=len(log)<=MAX_LOG:raise ValueError('Engine log outside bound')
    matches=[line[len(MARKER):] for line in log.decode('utf-8',errors='replace').splitlines() if line.startswith(MARKER)]
    if len(matches)!=1:raise ValueError('Expected exact reload receipt')
    report=json.loads(matches[0])
    if report!=geometry or any(type(report[k]) is not int for k in ('vertices','triangles')):
        raise ValueError('Reloaded geometry receipt mismatch')
    return report
class Blender:
    def run(self,plan,data,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary engine required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-blender-') as td:
            folder=Path(td);log=folder/'engine.log';out=folder/'output.blend'
            source=guard.read_bound(SCRIPT,65536)
            if hashlib.sha256(source).hexdigest()!=plan['files'][1]['sha256']:raise ValueError('Bundled script changed')
            (folder/'build.py').write_bytes(source)
            (folder/'geometry.json').write_text(json.dumps(data,allow_nan=False),encoding='utf-8')
            with child_server(command(plan,folder),Path(plan['files'][0]['path']).parent,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+180
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Blender workflow timed out')
                    for path,limit in ((log,MAX_LOG),(out,guard.MAX_OUTPUT)):
                        if path.exists() and path.stat().st_size>limit:raise ValueError('Blender output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed Blender failed under cap')
            stopped(cancelled)
            if not out.is_file() or linked(out):raise ValueError('Missing regular staged blend')
            return guard.read_bound(out,guard.MAX_OUTPUT),guard.read_bound(log,MAX_LOG)
def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit Blender workflow approval required')
    stopped(cancelled);data,dst=validate(root,plan)
    payload,log=(backend or Blender()).run(plan,data,cancelled)
    stopped(cancelled);r=verify(payload,log,expected(data))
    def revalidate():
        stopped(cancelled);validate(root,plan)
    sha=guard.publish(payload,dst,revalidate)
    return {'schema':'janus-blender-mesh-result-v1','status':'blend_reload_receipt_verified','output':plan['output'],'sha256':sha,
        **r,'source_unchanged':True,'native_engine_used':backend is None,'script_sha256':plan['files'][1]['sha256'],
        'visual_quality_verified':False,'scope':'Single editable mesh from plain triangular OBJ, no rendering, material, UV or rig claims.'}
