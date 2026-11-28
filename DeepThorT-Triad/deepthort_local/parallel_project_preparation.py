"""Conservative bounded concurrent project preparation using existing broker roles."""
from concurrent.futures import ThreadPoolExecutor
from .task_graph import independent_workspaces
from . import queued_prompt_preparation as q

def select(path,health,pid,roles,*,exclude=(),priority=None):
    admitted=tuple(r for r in q.available_roles(health,pid) if r in roles)
    if not admitted:return []
    active=sum(x['generating'] for x in health['models'].values())+health['memory_model']['generating']
    count=min(2,health['admission_slots']-active)
    selected=[];projects=[];excluded=list(exclude)
    for _ in range(count):
        item=q.candidate(path,admitted,exclude=excluded,priority=priority,independent_of=projects,dynamic=True)
        if item is None:break
        row,role=item
        selected.append((row,role));projects.append(row['project']);excluded.append(row['id'])
        admitted=tuple(r for r in admitted if r!=role)
        if not admitted:break
    return selected

def run(path,client_factory,roles,stopped,health,pid,priority,*,exclude=(),on_error=None):
    if stopped():return []
    items=select(path,health(),pid,roles,exclude=exclude,priority=priority())
    if not items:return []
    def worker(item):
        row,role=item
        def blocked():
            return stopped() or not priority().allowed(row)
        try:
            if blocked() or role not in q.available_roles(health(),pid):return None
            return q.run_once(path,client_factory(),(role,),blocked,exclude=exclude,priority=priority(),
                              exact=(row,role),dynamic=True)
        except Exception as exc:
            if on_error:on_error(exc)
            return None
    if len(items)==1:
        result=worker(items[0]);return [result] if result else []
    with ThreadPoolExecutor(max_workers=2,thread_name_prefix='Scoped-project-preparation') as pool:
        futures=[pool.submit(worker,item) for item in items]
        return [r for f in futures if (r:=f.result()) is not None]
