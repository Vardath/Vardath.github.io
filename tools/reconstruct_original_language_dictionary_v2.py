#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import statistics
import urllib.parse
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve()
spec=importlib.util.spec_from_file_location('base_reconstruct', HERE.with_name('reconstruct_original_language_dictionary.py'))
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

UA='Vardath-phonetic-research/2.0 (candidate proto-language experiment)'
API='https://en.wiktionary.org/w/api.php'
KAIKKI={
    'Proto-Indo-European':'https://kaikki.org/dictionary/Proto-Indo-European/kaikki.org-dictionary-ProtoIndoEuropean.jsonl',
    'Proto-Uralic':'https://kaikki.org/dictionary/Proto-Uralic/kaikki.org-dictionary-ProtoUralic.jsonl',
}
WIKT={'Proto-Semitic','Proto-Austronesian','Proto-Dravidian'}

def get_json(params,timeout=120):
    q=urllib.parse.urlencode(params)
    req=urllib.request.Request(API+'?'+q,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))

def reconstruction_namespace():
    d=get_json({'action':'query','format':'json','meta':'siteinfo','siprop':'namespaces','formatversion':'2'})
    for ns in d['query']['namespaces'].values():
        names={str(ns.get('name','')).lower(),str(ns.get('canonical','')).lower()}
        if 'reconstruction' in names:return int(ns['id'])
    return 118

def list_reconstruction_titles(fam):
    ns=reconstruction_namespace(); prefix=fam+'/'
    titles=[]; cont=None
    while True:
        p={'action':'query','format':'json','formatversion':'2','list':'allpages','apnamespace':ns,'apprefix':prefix,'aplimit':'max'}
        if cont:p['apcontinue']=cont
        d=get_json(p)
        titles.extend(x['title'] for x in d.get('query',{}).get('allpages',[]))
        cont=d.get('continue',{}).get('apcontinue')
        if not cont:break
        if len(titles)>10000:break
    print('listed',fam,len(titles),'reconstruction pages',flush=True)
    return titles

def clean_wikitext(s):
    s=re.sub(r'<!--.*?-->',' ',s,flags=re.S)
    # Keep visible text of ordinary wiki links.
    s=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',r'\1',s)
    # A few common semantic templates retain their final display argument.
    s=re.sub(r'\{\{(?:m|l|mention|term)\|[^{}|]*\|([^{}|]+)(?:\|[^{}]*)?\}\}',r'\1',s)
    # Remove remaining simple templates iteratively.
    old=None
    while old!=s:
        old=s; s=re.sub(r'\{\{[^{}]*\}\}',' ',s)
    s=re.sub(r"'{2,}",'',s)
    s=re.sub(r'<[^>]+>',' ',s)
    s=re.sub(r'\s+',' ',s).strip(' ;:.,')
    return s

def fetch_wikitext_rows(fam):
    titles=list_reconstruction_titles(fam); rows=[]
    for start in range(0,len(titles),40):
        chunk=titles[start:start+40]
        d=get_json({'action':'query','format':'json','formatversion':'2','prop':'revisions','rvprop':'content','rvslots':'main','titles':'|'.join(chunk)})
        for page in d.get('query',{}).get('pages',[]):
            title=page.get('title',''); revs=page.get('revisions') or []
            if not revs:continue
            txt=(revs[0].get('slots') or {}).get('main',{}).get('content','')
            defs=[]
            for line in txt.splitlines():
                # Top-level dictionary definitions only; descendant lists use * and are excluded.
                if line.startswith('# '):
                    g=clean_wikitext(line[2:])
                    if g and len(g)<500:defs.append(g)
            if not defs:continue
            form=title.split('/',1)[1] if '/' in title else title
            if form and len(form)<60:rows.append((form,defs,''))
        if start and start%400==0:print('fetched',fam,start,'/',len(titles),flush=True)
    print('loaded',fam,len(rows),'lexical reconstruction entries from Wiktionary',flush=True)
    return rows

def fetch_kaikki(fam,url):
    print('download',fam,url,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=180) as r: raw=r.read().decode('utf-8','replace')
    rows=[]
    for line in raw.splitlines():
        try:o=json.loads(line)
        except Exception:continue
        w=str(o.get('word') or '').strip(); gs=base.glosses(o)
        if w and len(w)<60 and gs:rows.append((w,gs,o.get('pos','')))
    print('loaded',fam,len(rows),'Kaikki entries',flush=True);return rows

def load_family(fam):
    if fam in KAIKKI:return fetch_kaikki(fam,KAIKKI[fam])
    if fam in WIKT:return fetch_wikitext_rows(fam)
    raise KeyError(fam)

def main():
    famrows={};famfound={}; source_counts={}
    for fam in base.FAMILIES:
        try:
            famrows[fam]=load_family(fam); source_counts[fam]=len(famrows[fam]); famfound[fam]=base.best_forms(famrows[fam])
            print('concept matches',fam,len(famfound[fam]),flush=True)
        except Exception as e:
            print('FAILED',fam,repr(e),flush=True);famfound[fam]={};source_counts[fam]=0
    rootg=base.load_root_gates();entries=[]
    for concept in base.CONCEPTS:
        ev=[]
        for fam in base.FAMILIES:
            x=famfound.get(fam,{}).get(concept)
            if not x:continue
            p=base.path_for(x['form'])
            if len(p)<2:continue
            ev.append({'family':fam,**x,'path':p})
        if len(ev)<3:continue
        paths=[x['path'] for x in ev]
        cand,fit,ops,fs=base.reconstruct(paths);stab=base.loo_stability(paths,cand)
        gates=[cand[i]+'→'+cand[i+1] for i in range(len(cand)-1)];hits=[g for g in gates if g in rootg]
        for x,op,sc in zip(ev,ops,fs):x['best_from_candidate_operator']=op;x['candidate_fit']=round(sc,4)
        coverage=len(ev)/len(base.FAMILIES);stability=stab if stab is not None else fit
        conf=.35*coverage+.4*fit+.25*stability
        form=''.join(base.PHONE[c] for c in cand)
        entries.append({'meaning':concept,'form':form,'ipa':'/'+form+'/','path':cand,'families':len(ev),'fit':round(fit,4),
                        'loo_stability':round(stability,4),'confidence':round(conf,4),
                        'root_gate_overlap':round(len(hits)/max(1,len(gates)),4),'root_gate_hits':hits,'evidence':ev})
    entries.sort(key=lambda x:(-x['confidence'],-x['families'],x['meaning']))
    res={'version':3,'title':'Candidate original-language dictionary','method':{
        'concept_inventory':len(base.CONCEPTS),'minimum_independent_proto_families':3,'families':base.FAMILIES,
        'source_counts':source_counts,
        'source':'Kaikki/Wiktionary machine-readable reconstruction entries; missing Kaikki family dumps are enumerated directly from Wiktionary Reconstruction namespace',
        'reconstruction':'semantic gloss match -> broad 4x4 phonetic path -> cross-family latent candidate optimized under validated lexical operator bank',
        'research_boundary':'Candidate latent reconstructions under the experiment. They are not historically established Proto-World forms.'},
        'summary':{'entries':len(entries),'five_family_entries':sum(x['families']==5 for x in entries),
                   'four_or_more':sum(x['families']>=4 for x in entries),
                   'mean_confidence':round(statistics.mean([x['confidence'] for x in entries]),4) if entries else 0},'entries':entries}
    base.OUTJ.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Candidate original-language dictionary','',f"Entries: **{len(entries)}** from {len(base.CONCEPTS)} tested basic meanings.",'',
           'These are model reconstructions, not historically established Proto-World words.','',
           '| Meaning | Candidate | Families | Fit | Stability | Confidence |','|---|---|---:|---:|---:|---:|']
    for x in entries:lines.append(f"| {x['meaning']} | {x['ipa']} | {x['families']} | {x['fit']:.3f} | {x['loo_stability']:.3f} | {x['confidence']:.3f} |")
    base.OUTM.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'source_counts':source_counts,**res['summary']},indent=2),flush=True)
    if len(entries)<10:raise RuntimeError(f'Only {len(entries)} entries reconstructed; refusing to accept a weak/empty dictionary build')

if __name__=='__main__':main()
