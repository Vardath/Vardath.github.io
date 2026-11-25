"""Exercise actual production semantic guard and reviewed-generation in isolation."""
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from .client import LocalModelClient
from .reasoning_council import ReasoningCouncil,sha
from .specification_guard import inspect_proposal,SpecificationRejected
from .reviewed_generation import generate_reviewed
from .staged_source import validate_source
from .workspace import strip_single_code_fence
from .triad_acceptance import resident_roles

ORIGINAL=("Create a synthetic XML ship manifest (not a real X4 game file). "
          "Root element ship, exactly three attributes: id=demo_pe, owner=player, speed=480. "
          "No child elements or text. User amendment: speed must now be 360 instead of 480; "
          "preserve the id and owner.")
BAD='<ship id="demo_pe" owner="npc" speed="480"/>'

def correct(text):
    try:
        validate_source('ship.xml',text)
        root=ET.fromstring(text)
        return (root.tag=='ship' and root.attrib=={'id':'demo_pe','owner':'player','speed':'360'}
                and not list(root) and not (root.text or '').strip())
    except (ValueError,ET.ParseError):return False

def exercise(health,pid,cancelled,notify=None,client_factory=LocalModelClient):
    stages={}
    def done(status,detail,artifact=None):
        evidence={'production_stages':stages.copy()}
        if artifact is not None:evidence['artifact_sha256']=sha(artifact)
        return {'status':status,'detail':detail,'evidence':evidence}
    try:
        initial=health();models=resident_roles(initial,pid)
        if initial.get('serial_memory_mode') is not False or any(m.get('busy') for m in models.values()):
            return done('inconclusive','Parallel workers must be idle before production review')
    except Exception:return done('blocked','Resident models unavailable')
    if cancelled.is_set():return done('cancelled','Test stopped')
    try:
        with tempfile.TemporaryDirectory(prefix='deepthort-production-review-') as folder:
            root=Path(folder)
            client=client_factory(root/'sessions.sqlite3')
            council=ReasoningCouncil(root/'review.sqlite3')
            focus='ship.xml: implement the complete specified manifest'
            def review(candidate):
                if cancelled.is_set():raise SpecificationRejected('Test cancelled')
                if notify:notify('source review')
                validate_source('ship.xml',candidate)
                result=inspect_proposal(council,client,original=ORIGINAL,project=root,
                    session='production-probe',focus=focus,proposal=candidate,kind='code',
                    cancelled=cancelled.is_set)
                if candidate==BAD:
                    stages['seeded_defect_review']={'status':'failed' if result['accepted'] else 'passed'}
                    if result['accepted']:
                        raise RuntimeError('Seeded defective source was falsely accepted')
                else:
                    stages['generated_source_review']={'status':'passed' if result['accepted'] else 'failed'}
                if not result['accepted']:raise SpecificationRejected(result['reason'])
                # A semantic acceptance alone is not enough even in this fixture.
                if not correct(candidate):
                    stages['independent_validation']={'status':'failed'}
                    raise SpecificationRejected('Independent XML validator rejected candidate')
                stages['independent_validation']={'status':'passed'}
            # Seed the first proposal explicitly; every later proposal is a
            # real implementation model call through the production retry helper.
            class Seeded:
                def __init__(self):self.calls=0
                def chat(self,session,prompt,max_tokens):
                    self.calls+=1
                    if self.calls==1:return BAD
                    stages['implementation']={'status':'called','attempts':self.calls-1}
                    if notify:notify('Granite regeneration')
                    return client.chat_as('implementation',session,prompt,max_tokens=max_tokens)
            try:
                artifact=generate_reviewed(Seeded(),'production-probe',
                    ORIGINAL+' Return only the complete XML source.',review,
                    attempts=3,max_tokens=192,transform=strip_single_code_fence,
                    cancelled=cancelled.is_set)
            except RuntimeError:
                return done('failed','Production guard falsely accepted seeded defective XML')
            except SpecificationRejected:
                return done('cancelled' if cancelled.is_set() else 'failed','Production review or regeneration did not produce accepted source')
            if cancelled.is_set():return done('cancelled','Test stopped')
            if not correct(artifact) or stages.get('seeded_defect_review',{}).get('status')!='passed':
                return done('failed','Independent acceptance contract failed')
            stages['implementation']['status']='passed'
        final=health();end=resident_roles(final,pid)
        if (final.get('serial_memory_mode') is not False or final.get('memory_retries',0)!=initial.get('memory_retries',0)
                or any(end[k]['pid']!=models[k]['pid'] for k in models)):
            return done('inconclusive','Worker configuration changed during production review')
        return done('passed','Production guard rejected seeded bad XML, Granite regenerated it, Sentinel and independent XML checks accepted; no project files written.',artifact)
    except Exception as exc:
        return done('cancelled' if cancelled.is_set() else 'blocked','Production probe unavailable: '+type(exc).__name__)
