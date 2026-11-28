"""Bounded presentation preferences only; never persist user content or authority."""
from pathlib import Path
from .diagnostic_evidence import read_snapshot,save_snapshot

SCHEMA='deepthortriad-display-v1'
PAGES=('Chats','Work queue','File review','Tasks','Processes','JANUS & Sentinel',
       'Computer & Tools','Files & Images','Command Centre','Approvals & PC Activity',
       'Knowledge & Memory','Studio','Settings & Integrations')
FILTERS={'job_filter':('All states','Active','Waiting / blocked','Completed / stopped'),
         'task_filter':('All states','Planned','Done'),
         'inventory_filter':('All states','Found','Missing')}
SPLIT_KEYS=('queue','files','tasks','operatives','media','approval_jobs','approval_actions',
            'approval_grants','memory_receipts','memory_library','studio')
DEFAULTS={'schema':SCHEMA,'width':1320,'height':860,'sidebar':290,'page':'Chats',
          'expanded_composer':False,'follow_activity':True,
          'navigation':178,'inspector':250,'inspector_visible':True,'split_ratios':{},
          **{key:values[0] for key,values in FILTERS.items()}}

def validated(raw):
    out=dict(DEFAULTS)
    if not isinstance(raw,dict) or raw.get('schema')!=SCHEMA:return out
    for key,low,high in (('width',1000,7680),('height',650,4320),('sidebar',180,1200),('navigation',150,320),('inspector',180,700)):
        value=raw.get(key)
        if type(value) is int:out[key]=max(low,min(high,value))
    out['split_ratios']={}
    ratios=raw.get('split_ratios')
    if isinstance(ratios,dict):
        for key in SPLIT_KEYS:
            value=ratios.get(key)
            if type(value) in (int,float) and .15<=value<=.85:out['split_ratios'][key]=float(value)
    if raw.get('page') in PAGES:out['page']=raw['page']
    for key in ('expanded_composer','follow_activity','inspector_visible'):
        if type(raw.get(key)) is bool:out[key]=raw[key]
    for key,values in FILTERS.items():
        if raw.get(key) in values:out[key]=raw[key]
    return out

def load(path):
    return validated(read_snapshot(Path(path)))

def save(path,raw):
    return save_snapshot(Path(path),validated(raw))

def geometry(raw,screen_width,screen_height):
    # Window minimum is the established app requirement. Smaller physical
    # displays cannot guarantee the minimum; do not restore offscreen positions.
    return (max(1000,min(raw['width'],max(1000,screen_width-72))),
            max(650,min(raw['height'],max(650,screen_height-110))))

def sidebar_position(raw,width):
    return max(180,min(raw['sidebar'],max(180,width-620)))

def shell_positions(raw,width):
    """Keep the workspace usable at the supported minimum; sizes are display-only."""
    rail=max(150,min(raw['navigation'],max(150,width-620)))
    inspector=max(180,min(raw['inspector'],max(180,width-rail-555)))
    return rail,max(rail+200,width-inspector)
