"""Read-only graphical review of actual frozen multimedia/tool workflow dataflow.

The graph is a projection of the existing manifest, not an execution plan,
permission, new scheduler or independent source of truth.
"""
from .tool_workflows import MAX_STAGES,digest

def project_graph(manifest):
    if not isinstance(manifest,dict):raise ValueError('Missing frozen workflow')
    stages=manifest.get('stages')
    if not isinstance(stages,list) or not 1<=len(stages)<=MAX_STAGES:
        raise ValueError('Invalid frozen stage count')
    nodes=[];edges=[];outputs=set()
    for i,s in enumerate(stages,1):
        if not isinstance(s,dict) or not {'recipe_id','tool','title','input','output','predecessor'}<=set(s):
            raise ValueError('Incomplete frozen stage')
        if type(s['recipe_id']) is not int or s['recipe_id']<1:
            raise ValueError('Invalid recipe identity')
        if any(not isinstance(s[k],str) or len(s[k])>4096 or any(ord(c)<32 for c in s[k])
               for k in ('tool','title','input','output')):
            raise ValueError('Invalid graph label')
        inp,out,prev=s['input'],s['output'],s['predecessor']
        if not out or not s['tool'] or not s['title'] or out.casefold() in outputs:
            raise ValueError('Invalid or repeated output')
        expected=next((n['ordinal'] for n in nodes if inp and n['output'].casefold()==inp.casefold()),None)
        if prev is not None and (type(prev) is not int or not 1<=prev<i or prev!=expected):
            raise ValueError('Invalid predecessor')
        if prev!=expected:raise ValueError('Missing predecessor')
        if inp.casefold()==out.casefold():raise ValueError('In-place dependency')
        nodes.append({'ordinal':i,'recipe_id':s['recipe_id'],'tool':s['tool'],'title':s['title'],
                      'input':inp,'output':out,'predecessor':prev})
        if prev is not None:edges.append({'from':prev,'to':i,'artifact':inp})
        outputs.add(out.casefold())
    return {'manifest_sha256':digest(manifest),'nodes':nodes,'edges':edges,
            'execution_order':[n['ordinal'] for n in nodes],
            'scope':'Read-only actual frozen workflow. No execution or approval.'}

def preview(parent,manifest):
    import tkinter as tk
    from tkinter import ttk
    graph=project_graph(manifest)
    dlg=tk.Toplevel(parent);dlg.title('Review workflow dataflow');dlg.transient(parent)
    dlg.geometry('900x600');dlg.minsize(540,320)
    ttk.Label(dlg,text='Frozen recipe dataflow. Arrows show artifact dependencies; execution remains ordered. No commands are approved here.',
              wraplength=800).pack(padx=10,pady=8)
    frame=ttk.Frame(dlg);frame.pack(fill='both',expand=True,padx=10)
    canvas=tk.Canvas(frame,background='#f4f6f8',highlightthickness=0)
    scroll=ttk.Scrollbar(frame,orient='vertical',command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    inner=ttk.Frame(canvas);window=canvas.create_window(0,0,anchor='nw',window=inner)
    inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
    for node in graph['nodes']:
        i=node['ordinal'];prev=node['predecessor']
        if prev is not None:
            ttk.Label(inner,text=f"Stage {prev} → Stage {i}  |  {node['input']}",wraplength=740).pack(anchor='w',padx=24,pady=(8,2))
        elif node['input']:
            ttk.Label(inner,text='Existing input → '+node['input'],wraplength=740).pack(anchor='w',padx=24,pady=(8,2))
        else:
            ttk.Label(inner,text='No input artifact',wraplength=740).pack(anchor='w',padx=24,pady=(8,2))
        card=ttk.LabelFrame(inner,text=f"{i}. {node['tool']}  ·  Recipe #{node['recipe_id']}")
        card.pack(fill='x',padx=12,pady=4)
        ttk.Label(card,text=node['title'],wraplength=740).pack(anchor='w',padx=8,pady=3)
        ttk.Label(card,text='Output: '+node['output'],wraplength=740).pack(anchor='w',padx=8,pady=(0,6))
    footer=ttk.Frame(dlg);footer.pack(fill='x',padx=10,pady=10)
    accepted=False
    def proceed():
        nonlocal accepted
        accepted=True;dlg.destroy()
    ttk.Button(footer,text='Cancel',command=dlg.destroy).pack(side='right',padx=4)
    ttk.Button(footer,text='Continue to exact command review',command=proceed).pack(side='right',padx=4)
    dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    dlg.grab_set();parent.wait_window(dlg)
    return accepted and project_graph(manifest)==graph
