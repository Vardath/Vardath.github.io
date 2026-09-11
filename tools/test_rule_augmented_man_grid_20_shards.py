#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, gzip, hashlib, io, json, math, os, random, re, sqlite3, statistics, time, unicodedata, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import reconstruct_original_language_all_dictionaries as core

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data' / 'rule-augmented-man-grid'
DB = WORK / 'prepare.sqlite'
PREP = WORK / 'prepared.jsonl'
META = WORK / 'prepared-meta.json'
BANKS = WORK / 'rule-banks.json'
RULE_RESULTS = ROOT / 'data' / 'all-language-historical-transformation-rules.json'
OLD_DICT = ROOT / 'data' / 'phonetic-original-language-dictionary.json'
OUT = ROOT / 'data' / 'rule-augmented-man-grid-reconstruction-results.json'
OUTDICT = ROOT / 'data' / 'rule-augmented-original-language-dictionary.json'
RAW = os.environ.get('WIKTEXTRACT_URL', 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP = 'https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
N_SHARDS = 20
MAX_RULES_PER_BANK = 36
MAX_BACKTRACK_STEPS = 2


def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf-8','ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big')


def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).lower()
    return ''.join(c for c in s if not unicodedata.combining(c)).strip()


def clean(s):
    s=re.sub(r'^\*+','',str(s or '').strip())
    s=re.sub(r'\([^)]*\)','',s)
    s=s.replace('[[','').replace(']]','')
    return re.split(r'[,;/]',s,1)[0].strip()


def spelling_path(s):
    out=[]
    for ch in clean(s):
        c=core.token_cell(ch)
        if c and (not out or out[-1]!=c): out.append(c)
    return tuple(out)


def ptxt(p): return ','.join(p)
def pparse(s): return tuple(x for x in str(s or '').split(',') if x)


def concepts(o):
    out=[]
    for g in core.get_glosses(o)[:8]:
        c=core.concept_key(g)
        if c and c not in out: out.append(c)
        if len(out)>=4: break
    return out


def inherited_sources(o):
    out=[]
    for t in o.get('etymology_templates') or []:
        name=str(t.get('name') or '').lower().strip()
        if name not in {'inh','inh+','inherited'}: continue
        a=t.get('args') or {}
        src=str(a.get('2') or a.get('source') or a.get('from') or '').strip()
        term=str(a.get('3') or a.get('term') or a.get('tr') or a.get('transliteration') or '').strip()
        if src and term: out.append((src,clean(term)))
    return out


def load_asjp(cache: Path):
    if not cache.exists(): urllib.request.urlretrieve(ASJP,cache)
    iso2fam={}; name2fam={}
    with cache.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            fam=(r.get('Glottolog_Family') or r.get('Family') or r.get('family') or r.get('Classification') or '').strip()
            if not fam: continue
            iso=(r.get('ISO639P3code') or r.get('ISO639P3') or '').strip()
            name=(r.get('Name') or '').strip().lower()
            if iso: iso2fam[iso]=fam
            if name: name2fam[name]=fam
    return iso2fam,name2fam


def weighted_medoid(counter,limit=24):
    items=counter.most_common(limit)
    if not items: return None
    den=sum(w for _,w in items)
    best=None
    for p,w in items:
        sc=sum(core.sim(p,q)*v for q,v in items)/den
        key=(sc,w,-len(p),p)
        if best is None or key>best[0]: best=(key,p,sc)
    return best[1],best[2]


def aggregate_rules(rows):
    agg=defaultdict(lambda:{'support':0.0,'weighted_conf':0.0,'groups':set(),'quality_sum':0.0})
    for group,rule,quality in rows:
        sig=(rule.get('type'),rule.get('source'),rule.get('target'),rule.get('left'),rule.get('right'))
        sup=float(rule.get('support') or rule.get('total_support') or 0)
        conf=float(rule.get('confidence') or rule.get('mean_route_confidence') or 0)
        if not sig[0] or conf<=0 or sup<=0: continue
        a=agg[sig]; a['support']+=sup; a['weighted_conf']+=conf*sup; a['groups'].add(group); a['quality_sum']+=quality
    out=[]
    for sig,a in agg.items():
        typ,src,tgt,left,right=sig
        conf=a['weighted_conf']/a['support']
        groups=len(a['groups'])
        quality=a['quality_sum']/max(1,groups)
        strength=conf*(1-math.exp(-a['support']/30.0))*(0.85+0.15*min(1.0,quality))
        out.append({'type':typ,'source':src,'target':tgt,'left':left,'right':right,
                    'support':round(a['support'],3),'confidence':round(conf,6),'groups':groups,
                    'quality':round(quality,6),'strength':round(strength,6)})
    out.sort(key=lambda r:(-r['strength'],-r['groups'],-r['support'],str(r)))
    return out[:MAX_RULES_PER_BANK]


def build_banks(rule_data,family_of):
    desc_rows=defaultdict(list); fam_rows=defaultdict(list)
    positive=[r for r in rule_data.get('all_routes',[]) if r.get('positive')]
    for r in positive:
        dc=r.get('descendant_code'); fam=family_of.get(dc)
        quality=max(0.0,float(r.get('learned_gain') or 0))+max(0.0,float(r.get('learned_minus_shuffled') or 0))
        quality=min(1.0,quality*4.0+0.5)
        for q in r.get('forward_rules') or []:
            desc_rows[dc].append((r.get('route'),q,quality))
            if fam: fam_rows[fam].append((dc,q,quality))
    descendant={k:aggregate_rules(v) for k,v in desc_rows.items()}
    family={k:aggregate_rules(v) for k,v in fam_rows.items()}
    universal=[]
    for q in rule_data.get('universal_forward_rule_candidates') or []:
        routes=int(q.get('routes') or 0); conf=float(q.get('mean_route_confidence') or 0); sup=float(q.get('total_support') or 0)
        if routes<5 or conf<0.65 or sup<40: continue
        strength=conf*(1-math.exp(-sup/50.0))*min(1.0,routes/12.0)
        universal.append({'type':q.get('type'),'source':q.get('source'),'target':q.get('target'),'left':q.get('left'),'right':q.get('right'),
                          'support':sup,'confidence':conf,'groups':routes,'quality':1.0,'strength':strength})
    universal.sort(key=lambda r:(-r['strength'],-r['groups'],-r['support'],str(r)))
    universal=universal[:MAX_RULES_PER_BANK]
    desc_codes=sorted(descendant)
    shuffled={}
    if desc_codes:
        for i,lc in enumerate(desc_codes): shuffled[lc]=desc_codes[(i+137)%len(desc_codes)]
    fams=sorted(family)
    family_shuffled={}
    if fams:
        for i,f in enumerate(fams): family_shuffled[f]=fams[(i+17)%len(fams)]
    return {'version':1,'positive_routes_used':len(positive),'descendant':descendant,'family':family,'universal':universal,
            'shuffled_descendant':shuffled,'shuffled_family':family_shuffled}


def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    old=json.loads(OLD_DICT.read_text(encoding='utf-8'))
    old_entries=old.get('entries') or []
    target={e['meaning']:tuple(e['path']) for e in old_entries if e.get('meaning') and e.get('path')}
    target_set=set(target)
    rule_data=json.loads(RULE_RESULTS.read_text(encoding='utf-8'))
    if DB.exists(): DB.unlink()
    con=sqlite3.connect(DB)
    con.execute('PRAGMA journal_mode=WAL'); con.execute('PRAGMA synchronous=OFF'); con.execute('PRAGMA temp_store=MEMORY')
    con.execute('CREATE TABLE raw(concept TEXT, lang_code TEXT, path TEXT, source TEXT, n REAL, PRIMARY KEY(concept,lang_code,path,source)) WITHOUT ROWID')
    con.execute('CREATE INDEX raw_concept ON raw(concept)')
    names={}; edges=Counter(); stats=Counter(); batch=[]; start=time.time()
    upsert='INSERT INTO raw VALUES(?,?,?,?,?) ON CONFLICT(concept,lang_code,path,source) DO UPDATE SET n=n+excluded.n'
    req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-rule-augmented-man-grid/1.0'})
    with urllib.request.urlopen(req) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
        for line in f:
            stats['dictionary_entries']+=1
            try:o=json.loads(line)
            except Exception:
                stats['json_errors']+=1; continue
            lc=str(o.get('lang_code') or '').strip(); ln=str(o.get('lang') or '').strip()
            if not lc: continue
            if ln and lc not in names: names[lc]=ln
            inh=inherited_sources(o)
            for src,_ in inh: edges[(src,lc)]+=1
            cs=[c for c in concepts(o) if c in target_set]
            if not cs: continue
            ips=[]
            for ipa in core.get_ipa(o):
                p=core.ipa_path(ipa)
                if len(p)>=2 and p not in ips: ips.append(p)
            if ips:
                stats['target_entries_with_mappable_ipa']+=1
                for c in cs:
                    for p in ips[:2]: batch.append((c,lc,ptxt(p),'ipa',3.0))
            if inh:
                for src,aform in inh:
                    ap=spelling_path(aform)
                    if len(ap)<2: continue
                    stats['historical_forms_extracted']+=1
                    for c in cs: batch.append((c,src,ptxt(ap),'historical-spelling',1.0))
            if len(batch)>=8000:
                con.executemany(upsert,batch); con.commit(); batch=[]
            if stats['dictionary_entries']%1000000==0:
                print(json.dumps({'entries':stats['dictionary_entries'],'target_ipa':stats['target_entries_with_mappable_ipa'],
                                  'historical_forms':stats['historical_forms_extracted'],'minutes':round((time.time()-start)/60,1)}),flush=True)
    if batch: con.executemany(upsert,batch); con.commit()

    iso2fam,name2fam=load_asjp(WORK/'asjp-languages.csv')
    all_codes=set(names)
    for a,b in edges: all_codes.add(a); all_codes.add(b)
    family_of={}
    for lc in all_codes:
        fam=iso2fam.get(lc) or name2fam.get(str(names.get(lc,'')).lower())
        if fam: family_of[lc]=fam
    inferred=0
    adjacency=defaultdict(Counter)
    for (a,b),w in edges.items():
        adjacency[a][b]+=w; adjacency[b][a]+=w
    for _ in range(10):
        add={}
        for lc in all_codes:
            if lc in family_of: continue
            votes=Counter()
            for nb,w in adjacency.get(lc,{}).items():
                fam=family_of.get(nb)
                if fam: votes[fam]+=w
            if not votes: continue
            ranked=votes.most_common()
            topf,topw=ranked[0]; total=sum(votes.values()); second=ranked[1][1] if len(ranked)>1 else 0
            if topw>=second*1.5 and topw/total>=0.60:
                add[lc]=topf
        if not add: break
        family_of.update(add); inferred+=len(add)
    stats['language_codes_seen']=len(all_codes); stats['family_labeled_codes']=len(family_of); stats['family_inferred_codes']=inferred

    banks=build_banks(rule_data,family_of)
    BANKS.write_text(json.dumps(banks,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

    lines=[]; prep_stats=Counter(); source_family=Counter()
    for ix,(meaning,oldroot) in enumerate(target.items(),1):
        langc=defaultdict(lambda:defaultdict(Counter))
        for lc,ps,src,n in con.execute('SELECT lang_code,path,source,n FROM raw WHERE concept=?',(meaning,)):
            langc[lc][src][pparse(ps)]+=float(n)
        fam_langs=defaultdict(list)
        for lc,srcs in langc.items():
            source='ipa' if srcs.get('ipa') else 'historical-spelling'
            cnt=srcs.get(source)
            if not cnt: continue
            m=weighted_medoid(cnt,16)
            if not m: continue
            lp,fit=m; fam=family_of.get(lc)
            if not fam:
                prep_stats['unclassified_language_evidence']+=1; continue
            fam_langs[fam].append((lc,lp,fit,source,sum(cnt.values())))
        families=[]
        for fam,rows in fam_langs.items():
            fc=Counter(r[1] for r in rows)
            fm=weighted_medoid(fc,24)
            if not fm: continue
            fp,ffit=fm
            scored=[]
            for lc,lp,lfit,src,n in rows:
                s=core.sim(lp,fp)
                has_rule=1 if lc in banks['descendant'] else 0
                scored.append((s,has_rule,n,lc,src,lp))
            scored.sort(reverse=True,key=lambda z:(z[0],z[1],z[2],z[3]))
            bests=scored[0][0]; candidates=[z for z in scored if z[0]>=bests-0.04]
            candidates.sort(reverse=True,key=lambda z:(z[1],z[0],z[2],z[3]))
            rep=candidates[0]
            lc,src=rep[3],rep[4]
            families.append({'family':fam,'path':list(fp),'lang_code':lc,'lang_name':names.get(lc,lc),'source':src,
                             'languages':len(rows),'medoid_fit':round(ffit,6),'direct_rule_bank':bool(banks['descendant'].get(lc)),
                             'family_rule_bank':bool(banks['family'].get(fam))})
            source_family[src]+=1
        families.sort(key=lambda x:x['family'])
        prep_stats['prepared_meanings']+=1
        prep_stats['prepared_family_evidence']+=len(families)
        if any(f['source']=='historical-spelling' for f in families): prep_stats['meanings_with_historical_family_evidence']+=1
        lines.append(json.dumps({'meaning':meaning,'old_root':list(oldroot),'families':families},ensure_ascii=False,separators=(',',':')))
        if ix%500==0: print(json.dumps({'medoids':ix,'of':len(target)}),flush=True)
    PREP.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    con.close()
    meta={'version':1,'test':'Rule-augmented Man-grid reconstruction using empirically learned historical transformations',
          'source_audit':dict(stats),'prepared':dict(prep_stats),'family_evidence_sources':dict(source_family),
          'target_meanings':len(target),'positive_rule_routes_used':banks['positive_routes_used'],
          'rule_banks':{'descendant_languages':len(banks['descendant']),'families':len(banks['family']),'universal_rules':len(banks['universal'])},
          'design':{
              'all_language_scope':'The complete Wiktextract stream is scanned. All target-meaning IPA evidence is considered; explicit inherited historical/proto forms are added as fallback evidence when a language has no IPA for that meaning.',
              'family_control':'Evidence is compressed to one medoid per inferred genealogical family. Historical/proto language codes inherit a family only when the inheritance graph gives a >=60% and 1.5x-majority family vote; otherwise they do not count as independent families.',
              'known_rules':'Only ancestor→descendant routes that previously passed held-out reversible-rule testing are admitted. Their contextual substitution/deletion/insertion rules are aggregated by descendant language and family. Recurrent cross-route rules form a separate universal bank.',
              'backtracking':'Rules are inverted before reconstruction: historical substitutions reverse, historical deletions restore a cell, and historical insertions remove a cell. Up to two high-confidence context-matched changes are applied per family medoid without consulting the target root.',
              'primary_validation':'For each meaning with >=4 families, deterministically hold out one family. Reconstruct from the others using baseline Man-grid, correct historical rules, shuffled wrong-language/family rules, and universal rules. Score every reconstruction against the untouched raw held-out family.',
              'primary_success':'Correct-rule held-out mean must exceed baseline and shuffled-rule means, with both paired bootstrap 95% confidence intervals entirely above zero.',
              'full_reconstruction':'All 12,000 target meanings are also reconstructed with correct historical rules using all available family evidence; the existing root remains the untouched baseline.',
              'no_custom_timeout':True}}
    META.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':'prepare',**meta['source_audit'],**meta['prepared'],'rule_banks':meta['rule_banks']},ensure_ascii=False),flush=True)


def context_match(path,i,left,right):
    prev=path[i-1] if i>0 else '^'; nxt=path[i+1] if i+1<len(path) else '$'
    return prev==left and nxt==right


def inverse_applications(path,rule):
    p=tuple(path); typ=rule.get('type'); src=rule.get('source'); tgt=rule.get('target'); left=rule.get('left'); right=rule.get('right')
    out=[]
    if typ=='substitution' and src and tgt:
        for i,c in enumerate(p):
            if c==tgt and context_match(p,i,left,right):
                q=list(p); q[i]=src; out.append(tuple(q))
    elif typ=='deletion' and src:
        if left=='^':
            if p and p[0]==right: out.append((src,)+p)
        elif right=='$':
            if p and p[-1]==left: out.append(p+(src,))
        else:
            for i in range(len(p)-1):
                if p[i]==left and p[i+1]==right: out.append(p[:i+1]+(src,)+p[i+1:])
    elif typ=='insertion' and tgt:
        for i,c in enumerate(p):
            if c==tgt and context_match(p,i,left,right):
                q=p[:i]+p[i+1:]
                if q: out.append(q)
    z=[]; seen=set()
    for q in out:
        qq=[]
        for c in q:
            if not qq or qq[-1]!=c: qq.append(c)
        q=tuple(qq)
        if 2<=len(q)<=14 and q not in seen and q!=p: seen.add(q); z.append(q)
    return z


def rule_key(r): return (r.get('type'),r.get('source'),r.get('target'),r.get('left'),r.get('right'))


def combine_rules(banks,lc,fam,mode):
    rows=[]
    if mode=='universal': rows.extend((r,0.0,'universal') for r in banks.get('universal',[]))
    elif mode=='correct':
        rows.extend((r,0.0,'language') for r in banks.get('descendant',{}).get(lc,[]))
        rows.extend((r,0.025,'family') for r in banks.get('family',{}).get(fam,[]))
        rows.extend((r,0.05,'universal') for r in banks.get('universal',[]))
    elif mode=='shuffled':
        wrong_lc=banks.get('shuffled_descendant',{}).get(lc)
        wrong_fam=banks.get('shuffled_family',{}).get(fam)
        if wrong_lc: rows.extend((r,0.0,'wrong-language') for r in banks.get('descendant',{}).get(wrong_lc,[]))
        if wrong_fam: rows.extend((r,0.025,'wrong-family') for r in banks.get('family',{}).get(wrong_fam,[]))
        rows.extend((r,0.05,'universal') for r in banks.get('universal',[]))
    ded={}
    for r,pen,kind in rows:
        k=rule_key(r); score=float(r.get('strength') or 0)-pen
        if k not in ded or score>ded[k][0]: ded[k]=(score,r,kind)
    vals=sorted(ded.values(),key=lambda z:(-z[0],-float(z[1].get('confidence') or 0),-float(z[1].get('support') or 0),str(z[1])))
    return vals[:MAX_RULES_PER_BANK]


def backtrack(path,lc,fam,mode,banks):
    p=tuple(path); applied=[]
    if mode=='baseline': return p,applied
    used=set()
    for _ in range(MAX_BACKTRACK_STEPS):
        best=None
        for score,r,kind in combine_rules(banks,lc,fam,mode):
            k=rule_key(r)
            if k in used: continue
            conf=float(r.get('confidence') or 0); sup=float(r.get('support') or 0); groups=int(r.get('groups') or 1)
            min_conf=0.70 if kind not in {'universal'} else 0.74
            if conf<min_conf or sup<12: continue
            for q in inverse_applications(p,r):
                strength=score + 0.015*min(10,groups) + 0.01*math.log1p(sup)
                cand=(strength,conf,sup,-abs(len(q)-len(p)),q,r,kind)
                if best is None or cand[:5]>best[:5]: best=cand
        if best is None: break
        _,conf,sup,_,q,r,kind=best
        p=q; used.add(rule_key(r))
        applied.append({'type':r.get('type'),'source':r.get('source'),'target':r.get('target'),'left':r.get('left'),'right':r.get('right'),
                        'confidence':round(conf,4),'support':round(sup,1),'kind':kind})
    return p,applied


def reconstruct_paths(families,mode,banks):
    fam_paths={}; transforms=[]
    for f in families:
        raw=tuple(f['path'])
        q,ap=backtrack(raw,f['lang_code'],f['family'],mode,banks)
        fam_paths[f['family']]=q
        if ap: transforms.append({'family':f['family'],'lang_code':f['lang_code'],'from':list(raw),'to':list(q),'rules':ap})
    z=core.reconstruct(fam_paths)
    return z,fam_paths,transforms


def fit_to(cand,paths):
    if not cand or not paths: return 0.0
    return statistics.mean(core.bestfit(tuple(cand),tuple(p))[0] for p in paths.values())


def form(path): return ''.join(core.PHONE.get(c,c) for c in path)


def load_prepared():
    out=[]
    with PREP.open(encoding='utf-8') as f:
        for line in f:
            if line.strip(): out.append(json.loads(line))
    return out


def reconstruct_shard(i):
    banks=json.loads(BANKS.read_text(encoding='utf-8')); rows=load_prepared(); out=[]
    chosen=[r for r in rows if h64('reconstruct',r['meaning'])%N_SHARDS==i]
    for j,r in enumerate(chosen,1):
        fams=r['families']; raw={f['family']:tuple(f['path']) for f in fams}; old=tuple(r['old_root'])
        z,normed,trans=reconstruct_paths(fams,'correct',banks)
        if z:
            cand=tuple(z[2])
        else: cand=old
        out.append({'meaning':r['meaning'],'old_root':list(old),'rule_root':list(cand),'old_form':form(old),'rule_form':form(cand),
                    'families':len(fams),'historical_family_evidence':sum(f['source']=='historical-spelling' for f in fams),
                    'transformed_families':len(trans),'rules_applied':sum(len(t['rules']) for t in trans),
                    'old_raw_family_fit':round(fit_to(old,raw),6),'rule_raw_family_fit':round(fit_to(cand,raw),6),
                    'old_backtracked_family_fit':round(fit_to(old,normed),6),'rule_backtracked_family_fit':round(fit_to(cand,normed),6),
                    'root_similarity':round(core.sim(old,cand),6),'changed':cand!=old})
        if j%50==0: print(json.dumps({'phase':'reconstruct','shard':i,'done':j,'total':len(chosen)}),flush=True)
    p=WORK/f'reconstruction-{i:02d}.json'; p.write_text(json.dumps({'shard':i,'entries':out},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'phase':'reconstruct-shard','shard':i,'entries':len(out),'changed':sum(x['changed'] for x in out)}),flush=True)


def validation_shard(i):
    banks=json.loads(BANKS.read_text(encoding='utf-8')); rows=load_prepared(); out=[]
    chosen=[r for r in rows if h64('validate',r['meaning'])%N_SHARDS==i]
    for j,r in enumerate(chosen,1):
        fams=r['families']
        if len(fams)<4: continue
        k=h64('holdout',r['meaning'])%len(fams); held=fams[k]; train=fams[:k]+fams[k+1:]
        hp=tuple(held['path'])
        models={}
        for mode in ('baseline','correct','shuffled','universal'):
            z,paths,trans=reconstruct_paths(train,mode,banks)
            if not z: continue
            cand=tuple(z[2]); models[mode]=(cand,trans)
        if len(models)<4: continue
        scores={m:core.bestfit(c,hp)[0] for m,(c,_) in models.items()}
        hnorm,hap=backtrack(hp,held['lang_code'],held['family'],'correct',banks)
        normalized_scores={m:core.bestfit(c,hnorm)[0] for m,(c,_) in models.items()}
        correct_trans=models['correct'][1]
        out.append({'meaning':r['meaning'],'held_family':held['family'],'held_lang_code':held['lang_code'],'held_source':held['source'],
                    'families_train':len(train),'train_historical_families':sum(f['source']=='historical-spelling' for f in train),
                    'train_transformed_families':len(correct_trans),'train_rules_applied':sum(len(t['rules']) for t in correct_trans),
                    'heldout_rule_applicable':bool(hap),'raw_scores':{m:round(v,6) for m,v in scores.items()},
                    'normalized_scores':{m:round(v,6) for m,v in normalized_scores.items()},
                    'correct_minus_baseline':round(scores['correct']-scores['baseline'],6),
                    'correct_minus_shuffled':round(scores['correct']-scores['shuffled'],6),
                    'universal_minus_baseline':round(scores['universal']-scores['baseline'],6)})
        if j%40==0: print(json.dumps({'phase':'validate','shard':i,'done':j,'total':len(chosen),'tests':len(out)}),flush=True)
    p=WORK/f'validation-{i:02d}.json'; p.write_text(json.dumps({'shard':i,'tests':out},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'phase':'validation-shard','shard':i,'tests':len(out)}),flush=True)


def bootstrap(vals,seed,reps=5000):
    if not vals: return [None,None]
    rng=random.Random(seed); n=len(vals); arr=[]
    for _ in range(reps): arr.append(sum(vals[rng.randrange(n)] for _ in range(n))/n)
    arr.sort(); return [arr[int(.025*reps)],arr[int(.975*reps)-1]]


def mean_key(tests,model,key='raw_scores'):
    return statistics.mean(t[key][model] for t in tests) if tests else None


def subgroup(tests,pred):
    z=[t for t in tests if pred(t)]
    if not z: return {'n':0}
    db=[t['correct_minus_baseline'] for t in z]; ds=[t['correct_minus_shuffled'] for t in z]
    return {'n':len(z),'baseline':mean_key(z,'baseline'),'correct':mean_key(z,'correct'),'shuffled':mean_key(z,'shuffled'),'universal':mean_key(z,'universal'),
            'correct_minus_baseline':statistics.mean(db),'correct_minus_baseline_95':bootstrap(db,70000+len(z),2500),
            'correct_minus_shuffled':statistics.mean(ds),'correct_minus_shuffled_95':bootstrap(ds,71000+len(z),2500)}


def merge():
    meta=json.loads(META.read_text(encoding='utf-8')); rec=[]; tests=[]
    for i in range(N_SHARDS):
        rec += json.loads((WORK/f'reconstruction-{i:02d}.json').read_text(encoding='utf-8'))['entries']
        tests += json.loads((WORK/f'validation-{i:02d}.json').read_text(encoding='utf-8'))['tests']
    rec.sort(key=lambda x:x['meaning']); tests.sort(key=lambda x:x['meaning'])
    db=[t['correct_minus_baseline'] for t in tests]; ds=[t['correct_minus_shuffled'] for t in tests]; ub=[t['universal_minus_baseline'] for t in tests]
    overall={'n':len(tests),'baseline_raw':mean_key(tests,'baseline'),'correct_rules_raw':mean_key(tests,'correct'),'shuffled_rules_raw':mean_key(tests,'shuffled'),'universal_rules_raw':mean_key(tests,'universal'),
             'correct_minus_baseline':statistics.mean(db) if db else None,'correct_minus_baseline_bootstrap_95':bootstrap(db,61001),
             'correct_minus_shuffled':statistics.mean(ds) if ds else None,'correct_minus_shuffled_bootstrap_95':bootstrap(ds,61002),
             'universal_minus_baseline':statistics.mean(ub) if ub else None,'universal_minus_baseline_bootstrap_95':bootstrap(ub,61003)}
    subgroups={
        'no_training_family_transformed':subgroup(tests,lambda t:t['train_transformed_families']==0),
        'one_or_two_training_families_transformed':subgroup(tests,lambda t:1<=t['train_transformed_families']<=2),
        'three_plus_training_families_transformed':subgroup(tests,lambda t:t['train_transformed_families']>=3),
        'historical_variant_in_training':subgroup(tests,lambda t:t['train_historical_families']>0),
        'heldout_has_historical_rule':subgroup(tests,lambda t:t['heldout_rule_applicable'])}
    full={'entries':len(rec),'changed_entries':sum(r['changed'] for r in rec),'changed_fraction':sum(r['changed'] for r in rec)/len(rec) if rec else 0,
          'mean_root_similarity':statistics.mean(r['root_similarity'] for r in rec) if rec else None,
          'mean_old_raw_family_fit':statistics.mean(r['old_raw_family_fit'] for r in rec) if rec else None,
          'mean_rule_raw_family_fit':statistics.mean(r['rule_raw_family_fit'] for r in rec) if rec else None,
          'mean_old_backtracked_family_fit':statistics.mean(r['old_backtracked_family_fit'] for r in rec) if rec else None,
          'mean_rule_backtracked_family_fit':statistics.mean(r['rule_backtracked_family_fit'] for r in rec) if rec else None,
          'entries_with_transformed_evidence':sum(r['transformed_families']>0 for r in rec),'total_rules_applied':sum(r['rules_applied'] for r in rec),
          'entries_with_historical_family_evidence':sum(r['historical_family_evidence']>0 for r in rec)}
    ci1=overall['correct_minus_baseline_bootstrap_95']; ci2=overall['correct_minus_shuffled_bootstrap_95']
    verdict=bool(ci1[0] is not None and ci1[0]>0 and ci2[0] is not None and ci2[0]>0)
    result={'version':1,'test':'Rule-augmented Man-grid reconstruction — full 12k reconstruction plus 20-shard leave-one-family-out validation',
            'source_audit':meta['source_audit'],'prepared':meta['prepared'],'rule_banks':meta['rule_banks'],'design':meta['design'],
            'validation':overall,'validation_subgroups':subgroups,'full_reconstruction':full,
            'verdict':{'supports_historical_rules_improving_man_grid_reconstruction':verdict,
                       'boundary':'The primary score is prediction of an untouched held-out family from the remaining families. Correct historical rules must beat both the original Man-grid baseline and a same-complexity shuffled-rule control. Historical/proto spelling evidence is family-compressed and never used as the held-out target after transformation.'}}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    OUTDICT.write_text(json.dumps({'version':1,'title':'Rule-augmented candidate original-language dictionary','summary':full,
                                   'research_boundary':result['verdict']['boundary'],'entries':rec},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':'merge','validation':overall,'full_reconstruction':full,'verdict':result['verdict']},ensure_ascii=False),flush=True)


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('prepare'); a=sub.add_parser('reconstruct'); a.add_argument('--id',type=int,required=True)
    b=sub.add_parser('validate'); b.add_argument('--id',type=int,required=True); sub.add_parser('merge')
    x=ap.parse_args()
    if x.cmd=='prepare': prepare()
    elif x.cmd=='reconstruct': reconstruct_shard(x.id)
    elif x.cmd=='validate': validation_shard(x.id)
    else: merge()

if __name__=='__main__': main()
