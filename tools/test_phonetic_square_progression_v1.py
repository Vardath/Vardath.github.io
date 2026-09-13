#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E, man_grid_exact_data as D
R=Path(__file__).resolve().parents[1]; W=R/'data/phonetic-square-progression-v1-work'; P=W/'prepared.json.gz'; O=R/'data/phonetic-square-progression-v1.json'
S=20; C=list(range(3,10)); B=[2,10,11]; NS=[2,*C,10,11]
PN=[f for f in E.FEATURES if f in E.PRIMARY]; PI=[E.FEATURES.index(f) for f in PN]; HI=[i for i,f in enumerate(E.FEATURES) if f not in E.PRIMARY and f not in {'tone','stress'}]
def dg(p,x): p.parent.mkdir(parents=True,exist_ok=True); gzip.open(p,'wt',encoding='utf8').write(json.dumps(x,separators=(',',':')))
def lg(p): return json.loads(gzip.open(p,'rt',encoding='utf8').read())
def sub(v,I): return [v[i] for i in I]
def pd(a,b): return sum(abs(a[i]-b[i])/2 for i in PI)/len(PI)
def hd(a,b): return sum(abs(a[i]-b[i])/2 for i in HI)/len(HI)
def fit(params):
 v=[sub(q['features'],PI) for q in params.values()]; full=[q['features'] for q in params.values()]; m=E.centroid(v); C0=E.covariance(v,m); d=len(m); a,l=E.eig(C0,[math.sin((i+1)*1.731)+.5 for i in range(d)]); C1=[[C0[i][j]-l*a[i]*a[j] for j in range(d)] for i in range(d)]; b,_=E.eig(C1,[math.cos((i+1)*2.117)+.25 for i in range(d)],a)
 def ori(ax,k):
  sc=0
  for fv,pv in zip(full,v):
   g=lambda n:fv[E.FEATURES.index(n)]; t=(g('back')-g('front')+.5*g('dorsal')-.45*g('labial')) if k=='x' else (g('syllabic')+.65*g('sonorant')+.25*g('continuant')-.5*g('consonantal')); sc+=E.dot(pv,ax)*t
  return [-x for x in ax] if sc<0 else ax
 a,b=ori(a,'x'),ori(b,'y'); xs=[];ys=[]
 for z in v: q=[z[i]-m[i] for i in range(d)]; xs.append(E.dot(q,a));ys.append(E.dot(q,b))
 return {'mean':m,'x':a,'y':b,'x0':E.pct(xs,.01),'x1':E.pct(xs,.99),'y0':E.pct(ys,.01),'y1':E.pct(ys,.99)}
def proj(v,p):
 z=[sub(v,PI)[i]-p['mean'][i] for i in range(len(PI))]; x=(E.dot(z,p['x'])-p['x0'])/((p['x1']-p['x0']) or 1); y=(E.dot(z,p['y'])-p['y0'])/((p['y1']-p['y0']) or 1); return max(0,min(.999999,x)),max(0,min(.999999,y))
def cell(x,n): return int(x[0]*n),int(x[1]*n)
def branches(langs,params):
 by=defaultdict(list); ce={}
 for lid,l in langs.items(): ce[lid]=E.centroid([sub(params[p]['features'],PI) for p in l['inventory'] if p in params]); by[l['family']].append(lid)
 r=[]
 for z in by.values():
  if len(z)>1:
   c=E.centroid([ce[x] for x in z]); r += [E.sub(ce[x],c) for x in z]
 ax,_=E.eig(E.covariance(r),[math.sin((i+1)*.913)+.25 for i in range(len(PI))]); idx={n:PN.index(n) for n in ('front','back','coronal','dorsal')};
 if ax[idx['front']]-ax[idx['back']]+ax[idx['coronal']]-ax[idx['dorsal']]<0: ax=[-x for x in ax]
 br={}; ok=[]
 for f,z in by.items():
  if len(z)<2: continue
  c=E.centroid([ce[x] for x in z]); q=sorted((E.dot(E.sub(ce[x],c),ax),x) for x in z); h=len(q)//2
  for i,(_,x) in enumerate(q): br[x]='L' if i<h else 'R'
  if h and h<len(q): ok.append(f)
 return br,sorted(ok)
def cons(ids,L,r=.5):
 c=defaultdict(int)
 for x in ids:
  for p in L[x]['inventory']: c[p]+=1
 k=max(1,math.ceil(len(ids)*r)); return {p for p,n in c.items() if n>=k}
def pairs(A,B,Q):
 A=sorted(A&Q.keys());B=sorted(B&Q.keys())
 if not A or not B:return []
 ab={a:min(B,key=lambda b:(pd(Q[a]['features'],Q[b]['features']),b)) for a in A}; ba={b:min(A,key=lambda a:(pd(Q[b]['features'],Q[a]['features']),a)) for b in B}
 return [(a,b) for a,b in ab.items() if ba.get(b)==a]
def bm(): return {'pt':0,'ps':0,'ph':0.,'src':0,'out':0,'th':0.}
def add(a,b):
 for k in a:a[k]+=b[k]
def metpair(Ps,Q,n):
 m=bm();m['pt']=len(Ps)
 for a,b in Ps:
  if cell(Q[a]['c'],n)==cell(Q[b]['c'],n):m['ps']+=1;m['ph']+=hd(Q[a]['features'],Q[b]['features'])
 return m
def trans(A,B,Q,n):
 m=bm();A=sorted(A&Q.keys());B=sorted(B&Q.keys());m['src']=len(A); d=defaultdict(list)
 for b in B:d[cell(Q[b]['c'],n)].append(b)
 for a in A:
  z=d.get(cell(Q[a]['c'],n),[])
  if z: b=min(z,key=lambda x:(pd(Q[a]['features'],Q[x]['features']),x));m['out']+=1;m['th']+=hd(Q[a]['features'],Q[b]['features'])
 return m
def bidir(A,B,Q,n): m=bm();add(m,trans(A,B,Q,n));add(m,trans(B,A,Q,n));return m
def struct(f,ids,L,Q):
 a=[x for x in ids if L[x]['branch']=='L'];b=[x for x in ids if L[x]['branch']=='R']
 if not a or not b:return None
 A,B=cons(a,L),cons(b,L)
 return {'A':A,'B':B,'p':pairs(A,B,Q)} if A and B else None
def prepare():
 _,Q,L,_,cov=D.load_phoible(); p=fit(Q); br,ok=branches(L,Q)
 for q in Q.values():q['c']=proj(q['features'],p)
 x={'version':1,'shards':S,'candidate':C,'boundary':B,'coverage':cov,'source':{'dataset':'PHOIBLE','commit':D.PH},'primary':[E.FEATURES[i] for i in PI],'heldout':[E.FEATURES[i] for i in HI],'projection':p,'eligible':ok,'params':{k:{'features':v['features'],'c':v['c']} for k,v in Q.items()},'langs':{k:{'family':v['family'],'branch':br.get(k),'inventory':sorted(v['inventory'])} for k,v in L.items() if br.get(k)},'rules':{'question':'Does 3x3..9x9 act as a progressively refining phonetic hierarchy?','heldout':'Grid and matching use only broad place/manner features; residual features are held out for evaluation.','controls':'Real within-family sibling branches versus unrelated-family controls; 2x2,10x10,11x11 are boundary controls.','magic':'Magic-square number ordering is not used because the earlier Durer/powers-of-3 chance test failed.','support':'Require rho<=-0.75 for resolution vs coverage and held-out loss, positive retention advantage at >=6/7 candidate grids, and 9x9 retention replicated in >=15/20 shards with sign-test p<0.05.','endpoint':'9x9 is special only if it has the best balanced candidate score and is not beaten by 10x10 or 11x11.'}};dg(P,x);print({'families':len(ok),'langs':len(x['langs']),'segments':len(Q)})
def unpack():
 x=lg(P);Q={k:{**v,'c':tuple(v['c'])} for k,v in x['params'].items()};L={k:{**v,'inventory':set(v['inventory'])} for k,v in x['langs'].items()};return x,Q,L
def shard(i):
 x,Q,L=unpack();by=defaultdict(list)
 for k,v in L.items():by[v['family']].append(k)
 st={f:struct(f,by[f],L,Q) for f in x['eligible']};st={f:s for f,s in st.items() if s and s['p']}; order=sorted(st); fs=[f for f in order if D.h64('sqprog1',f)%S==i]; A={str(n):{'r':bm(),'c':bm()} for n in NS};rows=[]
 for f in fs:
  s=st[f];o=st[order[(order.index(f)+1)%len(order)]]; cp=pairs(s['A'],o['B'],Q); row={'family':f,'rp':len(s['p']),'cp':len(cp),'n':{}}
  for n in NS:
   r=metpair(s['p'],Q,n);c=metpair(cp,Q,n);add(r,bidir(s['A'],s['B'],Q,n));add(c,bidir(s['A'],o['B'],Q,n));add(A[str(n)]['r'],r);add(A[str(n)]['c'],c);row['n'][str(n)]={'rr':r['ps']/r['pt'] if r['pt'] else None,'cr':c['ps']/c['pt'] if c['pt'] else None,'rl':r['th']/r['out'] if r['out'] else None,'cl':c['th']/c['out'] if c['out'] else None}
  rows.append(row)
 W.mkdir(parents=True,exist_ok=True);(W/f'result-{i:02}.json').write_text(json.dumps({'shard':i,'agg':A,'rows':rows},separators=(',',':')));print({'shard':i,'families':len(rows)})
def rank(x):
 o=sorted(range(len(x)),key=lambda i:x[i]);r=[0]*len(x);i=0
 while i<len(o):
  j=i+1
  while j<len(o) and x[o[j]]==x[o[i]]:j+=1
  z=(i+j+1)/2
  for k in range(i,j):r[o[k]]=z
  i=j
 return r
def rho(a,b):
 a,b=rank(a),rank(b);ma,mb=statistics.mean(a),statistics.mean(b);da=sum((x-ma)**2 for x in a);db=sum((x-mb)**2 for x in b);return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(da*db) if da and db else 0
def bt(k,n):return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1
def sm(m):
 rr=m['ps']/m['pt'] if m['pt'] else None;cv=m['out']/m['src'] if m['src'] else None;ls=m['th']/m['out'] if m['out'] else None;si=1-ls if ls is not None else None;f=2*cv*si/(cv+si) if cv is not None and si is not None and cv+si else None;return {'retention':rr,'coverage':cv,'heldout_loss':ls,'f1':f,'pairs':m['pt'],'outputs':m['out']}
def merge():
 x,_,_=unpack();ss=[json.loads((W/f'result-{i:02}.json').read_text()) for i in range(S)]; T={str(n):{'r':bm(),'c':bm()} for n in NS};rows=[]
 for s in ss:
  rows+=s['rows']
  for n in NS:add(T[str(n)]['r'],s['agg'][str(n)]['r']);add(T[str(n)]['c'],s['agg'][str(n)]['c'])
 z={}
 for n in NS:
  r,c=sm(T[str(n)]['r']),sm(T[str(n)]['c']);wr=wl=nr=nl=0
  for s in ss:
   a,b=sm(s['agg'][str(n)]['r']),sm(s['agg'][str(n)]['c'])
   if a['retention'] is not None and b['retention'] is not None:nr+=1;wr+=a['retention']>b['retention']
   if a['heldout_loss'] is not None and b['heldout_loss'] is not None:nl+=1;wl+=a['heldout_loss']<b['heldout_loss']
  z[str(n)]={'real':r,'control':c,'retention_advantage':r['retention']-c['retention'],'heldout_advantage':c['heldout_loss']-r['heldout_loss'],'retention_shard_wins':wr,'retention_sign_p':bt(wr,nr),'heldout_shard_wins':wl,'heldout_sign_p':bt(wl,nl)}
 cv=[z[str(n)]['real']['coverage'] for n in C];ls=[z[str(n)]['real']['heldout_loss'] for n in C];rc=rho(C,cv);rl=rho(C,ls);pos=sum(z[str(n)]['retention_advantage']>0 for n in C);n9=z['9'];prog=rc<=-.75 and rl<=-.75 and pos>=6 and n9['retention_shard_wins']>=15 and n9['retention_sign_p']<.05; m81=prog and n9['heldout_advantage']>0 and n9['heldout_shard_wins']>=15 and n9['heldout_sign_p']<.05;best=max(C,key=lambda n:z[str(n)]['real']['f1']);end=best==9 and z['9']['real']['f1']>=z['10']['real']['f1'] and z['9']['real']['f1']>=z['11']['real']['f1']
 out={'version':1,'status':'complete','test':'3x3-to-9x9 progressive phonetic resolution falsification','source':x['source'],'method':x['rules'],'features':{'grid_and_matching':x['primary'],'heldout_evaluation':x['heldout']},'summary':{'families':len({r['family'] for r in rows}),'shards':S,'real_pairs':sum(r['rp'] for r in rows),'control_pairs':sum(r['cp'] for r in rows),'rho_resolution_coverage':rc,'rho_resolution_heldout_loss':rl,'positive_retention_resolutions':pos,'best_balanced_candidate':best,'progressive_supported':prog,'nine_by_nine_81_supported':m81,'nine_special_endpoint_supported':end},'resolutions':z,'boundary':'This run tests square-resolution geometry, not magic-number order and not a pre-labelled throat/tongue/lip-teeth ancestry. A direct ternary anatomical test is only justified as a follow-up if this ladder survives.'};O.write_text(json.dumps(out,indent=2));print(json.dumps(out['summary']))
def main():
 a=argparse.ArgumentParser();s=a.add_subparsers(dest='p',required=True);s.add_parser('prepare');q=s.add_parser('shard');q.add_argument('--id',type=int,required=True);s.add_parser('merge');x=a.parse_args();prepare() if x.p=='prepare' else merge() if x.p=='merge' else shard(x.id)
if __name__=='__main__':main()
