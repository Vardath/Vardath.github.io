"""Small corpus-trained latent semantic vectors (TF-IDF and truncated SVD).
No remote inference, additional resident model, or third-party numeric dependency.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal,ID
from deepthort_local.search_interpretation import STOP

SCHEMA='janus-semantic-vectors-v1'
MAX_VOCAB=2048
MAX_DOCS=32

def tokens(text):
    return [t for t in re.findall(r'[^\W_]+',text.casefold()) if 2<=len(t)<=80 and t not in STOP]

def checked(s):
    if not isinstance(s,dict) or set(s)!={'documents','query','dimensions','top_k'}:
        raise ValueError('Expected local corpus, query, latent dimensions and top-k')
    docs=s['documents']
    if not isinstance(docs,list) or not 4<=len(docs)<=MAX_DOCS:
        raise ValueError('Choose 4–32 reviewed corpus entries')
    if type(s['dimensions']) is not int or not 2<=s['dimensions']<=min(16,len(docs)-1):
        raise ValueError('Dimensions must be 2–16 and less than corpus size')
    if type(s['top_k']) is not int or not 1<=s['top_k']<=len(docs):raise ValueError('Invalid result count')
    literal(s['query'],600)
    if not tokens(s['query']):raise ValueError('Query has no eligible terms')
    seen=set();bodies=set()
    for doc in docs:
        if not isinstance(doc,dict) or set(doc)!={'id','text'} or not isinstance(doc['id'],str) or not ID.fullmatch(doc['id']) or doc['id'] in seen:
            raise ValueError('Invalid or repeated document ID')
        literal(doc['text'],4000)
        ts=tokens(doc['text'])
        if not ts or tuple(ts) in bodies:raise ValueError('Empty or duplicate normalized corpus entry')
        seen.add(doc['id']);bodies.add(tuple(ts))
    return s

def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def unit(v):
    norm=math.sqrt(dot(v,v))
    if norm<=1e-10:return None
    return [x/norm for x in v]

def eigen_symmetric(matrix):
    """Cyclic Jacobi eigensolver for small real symmetric Gram matrices."""
    n=len(matrix);a=[list(r) for r in matrix];v=[[float(i==j) for j in range(n)] for i in range(n)]
    scale=max(1.0,max(abs(x) for r in a for x in r));tol=scale*1e-11
    for _ in range(60):
        if max(abs(a[p][q]) for p in range(n) for q in range(p+1,n))<=tol:break
        for p in range(n-1):
            for q in range(p+1,n):
                off=a[p][q]
                if abs(off)<=tol:continue
                theta=(a[q][q]-a[p][p])/(2*off)
                t=math.copysign(1.0,theta)/(abs(theta)+math.hypot(1,theta))
                c=1/math.hypot(1,t);sn=t*c
                app=a[p][p];aqq=a[q][q]
                a[p][p]=app-t*off;a[q][q]=aqq+t*off;a[p][q]=a[q][p]=0.0
                for k in range(n):
                    if k!=p and k!=q:
                        kp,kq=a[k][p],a[k][q]
                        a[k][p]=a[p][k]=c*kp-sn*kq
                        a[k][q]=a[q][k]=sn*kp+c*kq
                    vp,vq=v[k][p],v[k][q]
                    v[k][p]=c*vp-sn*vq;v[k][q]=sn*vp+c*vq
    else:raise ValueError('Latent eigensolver did not converge')
    ordered=sorted(range(n),key=lambda i:(-a[i][i],i));result=[]
    for j in ordered:
        col=[v[i][j] for i in range(n)]
        # Fix arbitrary eigenvector sign for repeatability.
        k=max(range(n),key=lambda i:abs(col[i]))
        if col[k]<0:col=[-x for x in col]
        value=a[j][j]
        if not math.isfinite(value) or any(not math.isfinite(x) for x in col):raise ValueError('Non-finite latent basis')
        residual=math.sqrt(math.fsum((dot(row,col)-value*col[i])**2 for i,row in enumerate(matrix)))
        if residual>scale*1e-7:raise ValueError('Latent eigenpair residual exceeds tolerance')
        result.append((value,col))
    return result

def fit(s):
    checked(s)
    counters=[Counter(tokens(d['text'])) for d in s['documents']];n=len(counters)
    df=Counter(t for counter in counters for t in counter)
    # Stable feature ordering, no query-dependent fitting.
    vocab=sorted(df,key=lambda t:(-df[t],t))[:MAX_VOCAB]
    if len(vocab)<s['dimensions']:raise ValueError('Insufficient corpus vocabulary')
    idf=[math.log((1+n)/(1+df[t]))+1 for t in vocab]
    def vector(counts):
        return unit([(1+math.log(counts[t]))*w if counts[t] else 0.0 for t,w in zip(vocab,idf)])
    x=[vector(c) for c in counters]
    if any(row is None for row in x):raise ValueError('A corpus entry has no retained vocabulary')
    gram=[[dot(a,b) for b in x] for a in x]
    pairs=eigen_symmetric(gram);rank=sum(value>1e-9 for value,_ in pairs)
    dims=s['dimensions']
    if rank<dims:raise ValueError('Corpus has insufficient independent dimensions')
    pairs=pairs[:dims]
    # X = U Sigma V^T. Project weighted term vectors into V, not raw counts.
    basis=[]
    for value,col in pairs:
        sigma=math.sqrt(value)
        basis.append([math.fsum(col[i]*x[i][j] for i in range(n))/sigma for j in range(len(vocab))])
    for i,b in enumerate(basis):
        if abs(dot(b,b)-1)>1e-6 or any(abs(dot(b,a))>1e-6 for a in basis[:i]):
            raise ValueError('Latent basis orthogonality check failed')
    def project(row):
        return unit([dot(row,b) for b in basis]) if row is not None else None
    docs=[project(row) for row in x]
    qcounter=Counter(tokens(s['query']));q=project(vector(qcounter))
    if q is None:raise ValueError('Query has no usable projection into this corpus')
    rows=[]
    for doc,v in zip(s['documents'],docs):
        # Some documents may lie outside the retained latent subspace.
        similarity=None if v is None else max(-1.0,min(1.0,dot(q,v)))
        rows.append({'id':doc['id'],'text_sha256':hashlib.sha256(doc['text'].encode()).hexdigest(),
                     'vector':None if v is None else [round(z,10) for z in v],
                     'cosine_similarity':None if similarity is None else round(similarity,10)})
    ranked=sorted((r for r in rows if r['cosine_similarity'] is not None),key=lambda r:(-r['cosine_similarity'],r['id']))[:s['top_k']]
    known=set(vocab)
    return {'schema':'janus-latent-semantic-vectors-result-v1','algorithm':'corpus TF-IDF / truncated SVD (LSA)',
            'dimensions':dims,'corpus_rank':rank,'vocabulary_size':len(vocab),'omitted_vocabulary_terms':len(df)-len(vocab),
            'corpus_sha256':hashlib.sha256(json.dumps(s['documents'],ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'vocabulary':vocab,'idf':[round(w,10) for w in idf],
            'basis':[[round(z,10) for z in b] for b in basis],
            'query':s['query'],'query_vector':[round(z,10) for z in q],
            'unknown_query_terms':sorted(set(qcounter)-known),'documents':rows,
            'ranked_ids':[r['id'] for r in ranked],
            'network_performed':False,'pretrained_embedding_model':False,
            'limitations':'Corpus-trained distributional latent vectors only; not a pretrained contextual neural model. Small corpus, unknown terms, latent dimensionality and repeated wording affect similarity. No factual relevance or general semantic accuracy guarantee.'}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,{'documents':len(s['documents']),'query':s['query'],'dimensions':s['dimensions'],
                 'top_k':s['top_k'],'scope':'Train a small local LSA basis from these exact corpus entries; no network or additional AI model.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=fit(s)
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,allow_nan=False,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'local_latent_vectors_trained','output':plan['output'],'sha256':digest,'dimensions':r['dimensions'],
            'documents':len(r['documents']),'ranked_ids':r['ranked_ids'],'network_performed':False,'pretrained_embedding_model':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Local latent vectors unavailable; inspect corpus rank, query and dimensions'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
