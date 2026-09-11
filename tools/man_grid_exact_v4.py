#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, gzip, hashlib, io, json, os, re, sqlite3, statistics, unicodedata, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import man_grid_exact_data as D
import man_grid_exact_engine as E

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data' / 'man-grid-exact-v4-work'
WORK.mkdir(parents=True, exist_ok=True)
T1 = ROOT / 'data' / 'man-grid-original-phonetics-exact-v3.json'
N = 20
RAW = os.environ.get('WIKTEXTRACT_URL', 'https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP = 'https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
MAX_CONCEPTS = int(os.environ.get('MAX_CONCEPTS', '12000'))
CORE_CONCEPTS = int(os.environ.get('CORE_CONCEPTS', '2000'))
MIN_LANGUAGES = int(os.environ.get('MIN_LANGUAGES', '5'))
MIN_FAMILIES = int(os.environ.get('MIN_FAMILIES', '3'))
GAP = 0.70
SKIP = set("/[](){}<>ˈˌːˑ.·‿#_=+~ |\t\r\n")

def h64(*parts):
    b = '\x1f'.join(map(str, parts)).encode('utf-8', 'ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8], 'big')

def gzwrite(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8', compresslevel=6) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))

def gzread(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)

def jread(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def jwrite(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def out_path(test):
    return ROOT / 'data' / f'man-grid-test-{test:02d}-exact-v4.json'

def result_path(test, shard):
    return WORK / f't{test:02d}-result-{shard:02d}.json.gz'

def load_test(test):
    p = out_path(test)
    if not p.exists():
        raise RuntimeError(f'missing dependency {p}')
    return jread(p)

def norm_text(s):
    s = unicodedata.normalize('NFC', str(s or '')).strip().lower()
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'\[[^]]*\]', ' ', s)
    s = re.sub(r'^(to|a|an|the)\s+', '', s)
    s = s.split(';')[0].strip()
    s = re.sub(r'\s+', ' ', s)
    if len(s) < 2 or len(s) > 90:
        return ''
    bad = ('alternative form of ', 'inflection of ', 'plural of ', 'past participle of ',
           'misspelling of ', 'obsolete spelling of ')
    return '' if any(s.startswith(x) for x in bad) else s

def get_ipa(o):
    z = []
    for s in o.get('sounds') or []:
        x = s.get('ipa')
        if isinstance(x, str):
            z.append(x)
        elif isinstance(x, list):
            z += [str(q) for q in x if q]
    return z

def get_glosses(o):
    z = []
    for s in o.get('senses') or []:
        z += [str(q) for q in (s.get('glosses') or []) if q]
        z += [str(q) for q in (s.get('raw_glosses') or []) if q]
    return z

def parse_inheritance(o):
    z = []
    for t in o.get('etymology_templates') or []:
        n = str(t.get('name') or '').lower()
        a = t.get('args') or {}
        if n not in {'inh', 'inh+', 'inherited'}:
            continue
        src = str(a.get('2') or a.get('source') or a.get('from') or '').strip()
        word = re.sub(r'^\*+', '', str(a.get('3') or a.get('term') or '').strip()).strip()
        if src and word:
            z.append((src, word))
    return z

def family_map():
    p = WORK / 'asjp-languages.csv'
    if not p.exists():
        urllib.request.urlretrieve(ASJP, p)
    iso, name = {}, {}
    with p.open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            fam = (r.get('Glottolog_Family') or r.get('Family') or r.get('family') or
                   r.get('Classification') or 'Unclassified').strip() or 'Unclassified'
            code = (r.get('ISO639P3code') or r.get('ISO639P3') or '').strip()
            nm = (r.get('Name') or '').strip().lower()
            if code:
                iso[code] = fam
            if nm:
                name[nm] = fam
    return iso, name

def build_models():
    spec, params, langs, P, cov = D.load_phoible()
    t1 = jread(T1)
    roots = t1['original_phoneme_inventory']
    root_ids = [r['parameter_id'] for r in roots if r['parameter_id'] in params]
    if len(root_ids) != len(roots):
        missing = [r['parameter_id'] for r in roots if r['parameter_id'] not in params]
        raise RuntimeError(f'Test 1 root inventory does not fully resolve against pinned PHOIBLE: {missing[:8]}')
    nearest = {}
    for pid, p in params.items():
        nearest[pid] = min(root_ids, key=lambda q: (E.dist(p['features'], params[q]['features']), q))
    byfirst = defaultdict(list)
    for pid, p in params.items():
        nm = unicodedata.normalize('NFC', p['name'])
        if nm and not any(ch.isspace() for ch in nm):
            byfirst[nm[0]].append((nm, pid))
    for k in byfirst:
        byfirst[k].sort(key=lambda x: (-len(x[0]), x[0], x[1]))
    branches, eligible, axis = D.assign_branches(langs, params)
    branch_by_iso = {}
    for lid, side in branches.items():
        iso = (langs.get(lid) or {}).get('iso')
        if iso:
            branch_by_iso[iso] = side
    model = {
        'version': 4,
        'grid': spec,
        'params': {pid: {'name': p['name'], 'features': p['features'], 'grid': p['grid']} for pid, p in params.items()},
        'root_ids': root_ids,
        'nearest_root': nearest,
        'branch_by_iso': branch_by_iso,
        'sibling_axis': axis,
        'phoible_commit': D.PH,
    }
    return model, byfirst

def load_model():
    return gzread(WORK / 'model.json.gz')

def tokenize_ipa(raw, model, byfirst):
    s = unicodedata.normalize('NFC', str(raw or '').strip())
    nearest = model['nearest_root']
    out, i, unknown = [], 0, 0
    while i < len(s):
        ch = s[i]
        if ch in SKIP or ch.isspace():
            i += 1
            continue
        hit = None
        for nm, pid in byfirst.get(ch, []):
            if s.startswith(nm, i):
                hit = (nm, pid)
                break
        if hit:
            rid = nearest[hit[1]]
            if not out or out[-1] != rid:
                out.append(rid)
            i += len(hit[0])
            continue
        if unicodedata.combining(ch):
            i += 1
            continue
        unknown += 1
        i += 1
    return tuple(out), unknown

def featdist(a, b, model):
    return E.dist(model['params'][a]['features'], model['params'][b]['features'])

def seqdist(a, b, model):
    a, b = tuple(a), tuple(b)
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    m = len(b)
    dp = [j * GAP for j in range(m + 1)]
    for i, x in enumerate(a, 1):
        nd = [i * GAP] + [0.0] * m
        for j, y in enumerate(b, 1):
            sub = featdist(x, y, model)
            nd[j] = min(dp[j] + GAP, nd[j-1] + GAP, dp[j-1] + sub)
        dp = nd
    return min(1.0, dp[m] / max(len(a), len(b)))

def align(a, b, model):
    a, b = tuple(a), tuple(b)
    n, m = len(a), len(b)
    dp = [[0.0]*(m+1) for _ in range(n+1)]
    bt = [[None]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1):
        dp[i][0] = i*GAP; bt[i][0] = 'D'
    for j in range(1, m+1):
        dp[0][j] = j*GAP; bt[0][j] = 'I'
    for i in range(1, n+1):
        for j in range(1, m+1):
            vals = [
                (dp[i-1][j-1] + featdist(a[i-1], b[j-1], model), 'M'),
                (dp[i-1][j] + GAP, 'D'),
                (dp[i][j-1] + GAP, 'I'),
            ]
            dp[i][j], bt[i][j] = min(vals, key=lambda x: (x[0], x[1]))
    out = []
    i, j = n, m
    while i or j:
        op = bt[i][j]
        if op == 'M':
            out.append((a[i-1], b[j-1])); i -= 1; j -= 1
        elif op == 'D':
            out.append((a[i-1], None)); i -= 1
        else:
            out.append((None, b[j-1])); j -= 1
    return list(reversed(out))

def medoid(counter, model, limit=24):
    items = counter.most_common(limit)
    if not items:
        return None
    den = sum(w for _, w in items)
    best = None
    for s, w in items:
        d = sum(seqdist(s, t, model)*v for t, v in items)/den
        key = (d, -w, len(s), s)
        if best is None or key < best[0]:
            best = (key, s, d)
    return best[1], best[2]

def family_reps(item, model):
    fam, within = {}, {}
    for f, rows in item.get('family_sequences', {}).items():
        cnt = Counter({tuple(seq): int(n) for seq, n in rows})
        m = medoid(cnt, model)
        if m:
            fam[f], within[f] = m
    return fam, within

def reconstruct_from_fam(fam, model, prior=None):
    if len(fam) < MIN_FAMILIES:
        return None
    candidates = set(fam.values())
    if prior:
        candidates.add(tuple(prior))
    scored = []
    for c in sorted(candidates):
        ds = [seqdist(c, s, model) for s in fam.values()]
        scored.append((statistics.mean(ds), statistics.median(ds), len(c), c, ds))
    scored.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    best = scored[0]
    loo_d = []
    keys = sorted(fam)
    if len(keys) >= 4:
        for k in keys[:min(12, len(keys))]:
            sub = {x:y for x,y in fam.items() if x != k}
            cands = sorted(set(sub.values()))
            if prior:
                cands = sorted(set(cands+[tuple(prior)]))
            if not cands:
                continue
            r = min(cands, key=lambda c: (statistics.mean(seqdist(c, s, model) for s in sub.values()), len(c), c))
            loo_d.append(seqdist(best[3], r, model))
    stability = max(0.0, 1.0-(statistics.mean(loo_d) if loo_d else best[0]))
    alternatives = [{'seq': list(x[3]), 'mean_distance': round(x[0], 6)} for x in scored[1:4]]
    return best[3], best[0], stability, alternatives

def phoneme_payload(seq, model):
    z = []
    for pid in seq:
        p = model['params'][pid]
        g = p['grid']
        z.append({
            'parameter_id': pid,
            'ipa': p['name'],
            'x': g['x'], 'y': g['y'],
            'path_left': g['all_left'],
            'path_right': g['all_right'],
        })
    return z

def entry_from_item(item, model, prior=None):
    fam, within = family_reps(item, model)
    r = reconstruct_from_fam(fam, model, prior=prior)
    if not r:
        return None
    seq, md, stability, alts = r
    evidence = [{'family': f, 'seq': list(fam[f]), 'distance_to_root': round(seqdist(seq, fam[f], model), 6),
                 'within_family_medoid_distance': round(within[f], 6)}
                for f in sorted(fam)]
    conf = max(0.0, min(1.0, 0.50*(1-md) + 0.25*stability + 0.15*min(1, len(fam)/12) +
                        0.10*min(1, int(item.get('languages', 0))/40)))
    return {
        'rank': item.get('rank'),
        'meaning': item['meaning'],
        'seq': list(seq),
        'ipa': '/' + ''.join(model['params'][p]['name'] for p in seq) + '/',
        'languages': int(item.get('languages', 0)),
        'families': len(fam),
        'mean_family_distance': round(md, 6),
        'stability': round(stability, 6),
        'confidence': round(conf, 6),
        'alternatives': alts,
        'family_evidence': evidence,
        'phonemes': phoneme_payload(seq, model),
    }

def wrong_meaning_control(entries, model):
    if len(entries) < 2:
        return None
    real, wrong = [], []
    for i, e in enumerate(entries):
        fam = [tuple(x['seq']) for x in e.get('family_evidence', [])]
        if fam:
            real.extend(seqdist(e['seq'], s, model) for s in fam)
        w = entries[(i+1) % len(entries)]
        wfam = [tuple(x['seq']) for x in w.get('family_evidence', [])]
        if wfam:
            wrong.extend(seqdist(e['seq'], s, model) for s in wfam)
    return {
        'real_mean_distance': statistics.mean(real) if real else None,
        'wrong_meaning_mean_distance': statistics.mean(wrong) if wrong else None,
        'real_better': bool(real and wrong and statistics.mean(real) < statistics.mean(wrong)),
    }

def init_db():
    db = WORK / 'lexicon.sqlite3'
    if db.exists():
        db.unlink()
    c = sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=OFF')
    c.execute('PRAGMA temp_store=MEMORY')
    c.executescript('''
      CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,word TEXT,concept TEXT,seq TEXT);
      CREATE INDEX lex_concept ON lex(concept);
      CREATE INDEX lex_word ON lex(lang_code,word);
      CREATE INDEX lex_family ON lex(family);
      CREATE TABLE inheritance(child_lang TEXT,child_word TEXT,parent_lang TEXT,parent_word TEXT);
      CREATE INDEX inh_child ON inheritance(child_lang,child_word);
    ''')
    return c

def prepare():
    model, byfirst = build_models()
    gzwrite(WORK/'model.json.gz', model)
    iso, name = family_map()
    con = init_db(); cur = con.cursor()
    batch, edges = [], []
    stats = Counter()
    req = urllib.request.Request(RAW, headers={'User-Agent':'Vardath-ManGrid-Exact-v4/4.0'})
    with urllib.request.urlopen(req) as resp, gzip.GzipFile(fileobj=resp) as gz, io.TextIOWrapper(gz, encoding='utf-8', errors='replace') as f:
        for line in f:
            stats['dictionary_entries'] += 1
            try:
                o = json.loads(line)
            except Exception:
                stats['json_errors'] += 1
                continue
            lc = str(o.get('lang_code') or '').strip()
            ln = str(o.get('lang') or '').strip()
            word = str(o.get('word') or '').strip()
            if not lc or not word:
                continue
            fam = iso.get(lc) or name.get(ln.lower()) or 'Unclassified'
            seqs = []
            for raw in get_ipa(o)[:3]:
                q, u = tokenize_ipa(raw, model, byfirst)
                stats['ipa_unknown_symbols'] += u
                if len(q) >= 2 and q not in seqs:
                    seqs.append(q)
            concepts = []
            for g in get_glosses(o)[:8]:
                c = norm_text(g)
                if c and c not in concepts:
                    concepts.append(c)
                if len(concepts) >= 4:
                    break
            if seqs and concepts:
                stats['entries_with_exact_mappable_ipa'] += 1
                for c in concepts:
                    for q in seqs[:2]:
                        batch.append((lc, ln, fam, word, c, ' '.join(q)))
            for pl, pw in parse_inheritance(o):
                edges.append((lc, word, pl, pw))
            if len(batch) >= 15000:
                cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)', batch); batch.clear()
            if len(edges) >= 15000:
                cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)', edges); edges.clear()
            if stats['dictionary_entries'] % 500000 == 0:
                con.commit()
                print(json.dumps({'entries':stats['dictionary_entries'], 'mappable':stats['entries_with_exact_mappable_ipa']}), flush=True)
    if batch:
        cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)', batch)
    if edges:
        cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)', edges)
    con.commit()
    stats['languages'] = con.execute('SELECT COUNT(DISTINCT lang_code) FROM lex').fetchone()[0]
    stats['families'] = con.execute("SELECT COUNT(DISTINCT family) FROM lex WHERE family!='Unclassified'").fetchone()[0]

    concepts = list(con.execute('''
      SELECT concept,COUNT(DISTINCT lang_code),COUNT(DISTINCT family)
      FROM lex WHERE family!='Unclassified'
      GROUP BY concept
      HAVING COUNT(DISTINCT lang_code)>=? AND COUNT(DISTINCT family)>=?
      ORDER BY COUNT(DISTINCT family) DESC,COUNT(DISTINCT lang_code) DESC,concept
      LIMIT ?''', (MIN_LANGUAGES, MIN_FAMILIES, MAX_CONCEPTS)))
    lexsh = [[] for _ in range(N)]
    for rank, (concept, nlang, nfam) in enumerate(concepts):
        fc = defaultdict(Counter); lcmap = defaultdict(Counter)
        for fam, code, lang, seq, n in con.execute(
            "SELECT family,lang_code,lang,seq,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,lang_code,lang,seq",
            (concept,)):
            q = tuple(seq.split()); fc[fam][q] += int(n); lcmap[(code,lang,fam)][q] += int(n)
        item = {
            'rank': rank, 'meaning': concept, 'languages': int(nlang), 'families_reported': int(nfam),
            'family_sequences': {fam:[[list(q),n] for q,n in cnt.items()] for fam,cnt in fc.items()},
            'language_sequences': [
                {'code':k[0], 'name':k[1], 'family':k[2], 'sequences':[[list(q),n] for q,n in cnt.items()]}
                for k,cnt in lcmap.items()
            ],
        }
        lexsh[h64('meaning', concept)%N].append(item)

    lang_acc = defaultdict(lambda: {'name':'','family':'Unclassified','meanings':defaultdict(Counter)})
    fam_acc = defaultdict(lambda: defaultdict(Counter))
    for i in range(N):
        for item in lexsh[i]:
            m = item['meaning']
            for lr in item['language_sequences']:
                a = lang_acc[lr['code']]; a['name'] = lr['name']; a['family'] = lr['family']
                for seq,n in lr['sequences']:
                    a['meanings'][m][tuple(seq)] += int(n)
            for fam, rows in item['family_sequences'].items():
                for seq,n in rows:
                    fam_acc[fam][m][tuple(seq)] += int(n)
    langsh = [[] for _ in range(N)]
    for code, a in lang_acc.items():
        langsh[h64('language',code)%N].append({
            'code':code,'name':a['name'],'family':a['family'],
            'meanings':{m:[[list(q),n] for q,n in cnt.items()] for m,cnt in a['meanings'].items()}
        })
    famsh = [[] for _ in range(N)]
    for fam, meanings in fam_acc.items():
        famsh[h64('family',fam)%N].append({
            'family':fam,
            'meanings':{m:[[list(q),n] for q,n in cnt.items()] for m,cnt in meanings.items()}
        })

    histsh = [[] for _ in range(N)]
    hist_seen = set(); hist_n = 0
    q = '''SELECT c.lang_code,c.lang,c.family,c.word,c.concept,c.seq,i.parent_lang,i.parent_word,p.lang,p.family,p.seq
           FROM inheritance i JOIN lex c ON c.lang_code=i.child_lang AND c.word=i.child_word
           JOIN lex p ON p.lang_code=i.parent_lang AND p.word=i.parent_word AND p.concept=c.concept
           WHERE c.family!='Unclassified'
           GROUP BY c.lang_code,c.word,c.concept,c.seq,i.parent_lang,i.parent_word,p.seq'''
    for cl,cln,cf,cw,concept,cs,pl,pw,pln,pf,ps in con.execute(q):
        k = (cl,cw,pl,pw,concept,cs,ps)
        if k in hist_seen:
            continue
        hist_seen.add(k)
        r = {'child_code':cl,'child_language':cln,'child_family':cf,'child_word':cw,
             'parent_code':pl,'parent_language':pln,'parent_family':pf,'parent_word':pw,
             'meaning':concept,'descendant':cs.split(),'ancestor':ps.split()}
        histsh[h64('history',cl,cw,pl,pw,concept)%N].append(r); hist_n += 1

    for i in range(N):
        gzwrite(WORK/f'lexical-shard-{i:02d}.json.gz', lexsh[i])
        gzwrite(WORK/f'language-shard-{i:02d}.json.gz', langsh[i])
        gzwrite(WORK/f'family-shard-{i:02d}.json.gz', famsh[i])
        gzwrite(WORK/f'historical-shard-{i:02d}.json.gz', histsh[i])
    manifest = {
        'version':4,'status':'prepared','shards':20,'grid_cells':model['grid']['counts']['total_cells'],
        'all_rectangles_mirrored':True,'test1_phonemes':len(model['root_ids']),
        'source':{'wiktextract':RAW,'phoible_commit':model['phoible_commit']},
        'scan':dict(stats),'eligible_meaning_groups':len(concepts),'core_test4_meanings':min(CORE_CONCEPTS,len(concepts)),
        'historical_pairs':hist_n,
        'lexical_shard_sizes':[len(x) for x in lexsh],
        'language_shard_sizes':[len(x) for x in langsh],
        'family_shard_sizes':[len(x) for x in famsh],
        'historical_shard_sizes':[len(x) for x in histsh],
        'execution':{
            'version':'exact-v4','tests':'4-16','shards_per_test':20,
            'partition':'deterministic disjoint ownership, never 20 repetitions of the full test',
            'merge_requires_all_20':True,'workflow_custom_timeout_minutes':None,
            'invalid_old_mapping_reused':False,
        }
    }
    jwrite(WORK/'prepared-manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)

def test4(shard):
    model = load_model()
    items = [x for x in gzread(WORK/f'lexical-shard-{shard:02d}.json.gz') if int(x['rank']) < CORE_CONCEPTS]
    entries = [e for e in (entry_from_item(x, model) for x in items) if e]
    gzwrite(result_path(4,shard), {'test':4,'shard':shard,'input':len(items),'entries':entries,'control':wrong_meaning_control(entries,model)})

def test13(shard):
    model = load_model()
    rows = gzread(WORK/f'historical-shard-{shard:02d}.json.gz')
    real=[]; wrong=[]; events=Counter(); details=[]
    for i,r in enumerate(rows):
        a,b = r['ancestor'], r['descendant']
        d = seqdist(a,b,model); real.append(d)
        wb = rows[(i+1)%len(rows)]['descendant'] if len(rows)>1 else b
        wd = seqdist(a,wb,model); wrong.append(wd)
        ev=[]
        for x,y in align(a,b,model):
            if x is None: key=('insert',None,y)
            elif y is None: key=('delete',x,None)
            elif x==y: key=('identity',x,y)
            else: key=('substitute',x,y)
            events[key]+=1; ev.append(key)
        if len(details)<250:
            details.append({'meaning':r['meaning'],'ancestor':a,'descendant':b,'distance':round(d,6),'wrong_distance':round(wd,6)})
    payload={'test':13,'shard':shard,'pairs':len(rows),
             'real_mean_distance':statistics.mean(real) if real else None,
             'wrong_mean_distance':statistics.mean(wrong) if wrong else None,
             'real_better':bool(real and wrong and statistics.mean(real)<statistics.mean(wrong)),
             'events':[[list(k),n] for k,n in events.items()],'examples':details}
    gzwrite(result_path(13,shard),payload)

def dictionary_map(test):
    x=load_test(test)
    return {e['meaning']:e for e in x.get('entries',[])}

def test5(shard):
    model=load_model(); t4=dictionary_map(4)
    items=gzread(WORK/f'lexical-shard-{shard:02d}.json.gz')
    entries=[]
    for x in items:
        prior=(t4.get(x['meaning']) or {}).get('seq')
        e=entry_from_item(x,model,prior=prior)
        if e: entries.append(e)
    gzwrite(result_path(5,shard),{'test':5,'shard':shard,'input':len(items),'entries':entries,'control':wrong_meaning_control(entries,model)})

def test6(shard):
    model=load_model(); roots=dictionary_map(5)
    langs=gzread(WORK/f'language-shard-{shard:02d}.json.gz'); out=[]
    root_keys=sorted(roots)
    for lr in langs:
        ds=[];ctrl=[]
        for m,rows in lr['meanings'].items():
            if m not in roots: continue
            cnt=Counter({tuple(q):int(n) for q,n in rows}); mm=medoid(cnt,model)
            if not mm: continue
            ds.append(seqdist(mm[0],roots[m]['seq'],model))
            wm=root_keys[(h64('wrong6',lr['code'],m)%len(root_keys))] if root_keys else m
            ctrl.append(seqdist(mm[0],roots[wm]['seq'],model))
        if len(ds)>=10:
            out.append({'code':lr['code'],'name':lr['name'],'family':lr['family'],
                        'branch':model['branch_by_iso'].get(lr['code']),
                        'shared_meanings':len(ds),'mean_distance':statistics.mean(ds),
                        'similarity':1-statistics.mean(ds),'wrong_meaning_distance':statistics.mean(ctrl) if ctrl else None})
    gzwrite(result_path(6,shard),{'test':6,'shard':shard,'languages':out})

def test7(shard):
    model=load_model(); roots=dictionary_map(5)
    fams=gzread(WORK/f'family-shard-{shard:02d}.json.gz'); out=[]
    for fr in fams:
        fam=fr['family']; real=[];control=[]
        for m,rows in fr['meanings'].items():
            e=roots.get(m)
            if not e: continue
            target=next((tuple(x['seq']) for x in e.get('family_evidence',[]) if x['family']==fam),None)
            others=[tuple(x['seq']) for x in e.get('family_evidence',[]) if x['family']!=fam]
            if target is None or len(others)<3: continue
            pred=min(set(others),key=lambda c:(statistics.mean(seqdist(c,s,model) for s in others),len(c),c))
            real.append(seqdist(pred,target,model))
            control.append(seqdist(pred,others[h64('ctrl7',fam,m)%len(others)],model))
        if len(real)>=20:
            out.append({'family':fam,'heldout_meanings':len(real),'mean_heldout_distance':statistics.mean(real),
                        'control_distance':statistics.mean(control),'advantage':statistics.mean(control)-statistics.mean(real)})
    gzwrite(result_path(7,shard),{'test':7,'shard':shard,'families':out})

def substitution_map(train_pairs, model):
    counts=defaultdict(Counter)
    for src,tgt in train_pairs:
        for x,y in align(src,tgt,model):
            if x is not None and y is not None:
                counts[x][y]+=1
    return {x:c.most_common(1)[0][0] for x,c in counts.items() if c}

def apply_map(seq, mp):
    return tuple(mp.get(x,x) for x in seq)

def test8(shard):
    model=load_model(); roots=dictionary_map(5)
    fams=gzread(WORK/f'family-shard-{shard:02d}.json.gz'); out=[]
    for fr in fams:
        pairs=[]
        for m,rows in fr['meanings'].items():
            e=roots.get(m)
            if not e: continue
            cnt=Counter({tuple(q):int(n) for q,n in rows}); mm=medoid(cnt,model)
            if mm: pairs.append((m,mm[0],tuple(e['seq'])))
        if len(pairs)<30: continue
        ident=[];rev=[];shuffle=[]
        for fold in range(5):
            train=[(s,r) for m,s,r in pairs if h64('fold8',m)%5!=fold]
            test=[(m,s,r) for m,s,r in pairs if h64('fold8',m)%5==fold]
            mp=substitution_map(train,model)
            vals=sorted(mp.items()); shuffled={x:vals[(i+1)%len(vals)][1] for i,(x,_) in enumerate(vals)} if vals else {}
            for m,s,r in test:
                ident.append(seqdist(s,r,model)); rev.append(seqdist(apply_map(s,mp),r,model)); shuffle.append(seqdist(apply_map(s,shuffled),r,model))
        if rev:
            out.append({'family':fr['family'],'heldout_meanings':len(rev),'identity_distance':statistics.mean(ident),
                        'reverse_distance':statistics.mean(rev),'shuffled_map_distance':statistics.mean(shuffle),
                        'reverse_gain':statistics.mean(ident)-statistics.mean(rev)})
    gzwrite(result_path(8,shard),{'test':8,'shard':shard,'families':out})

def test9(shard):
    t6=load_test(6)
    rows=[x for x in t6.get('languages',[]) if x.get('branch') in {'L','R'}]
    rows=sorted(rows,key=lambda x:(-x['similarity'],-x['shared_meanings'],x['code']))[:160]
    lefts=[x for x in rows if x['branch']=='L']; rights=[x for x in rows if x['branch']=='R']; pairs=[]
    for a in lefts:
        for b in rights:
            if h64('pair9',a['code'],b['code'])%N!=shard: continue
            fam_bonus=0.02 if a['family']!=b['family'] else 0.0
            balance=abs(a['similarity']-b['similarity'])
            score=(a['similarity']+b['similarity'])/2 + fam_bonus - 0.15*balance
            pairs.append({'left':a,'right':b,'score':score,'different_families':a['family']!=b['family']})
    pairs.sort(key=lambda x:(-x['score'],x['left']['code'],x['right']['code']))
    gzwrite(result_path(9,shard),{'test':9,'shard':shard,'candidate_pairs':pairs[:100]})

def midpoint_seq(a,b,model):
    out=[]
    roots=model['root_ids']
    for x,y in align(a,b,model):
        if x is None: z=y
        elif y is None: z=x
        elif x==y: z=x
        else:
            fx=model['params'][x]['features']; fy=model['params'][y]['features']
            mid=[(u+v)/2 for u,v in zip(fx,fy)]
            z=min(roots,key=lambda q:(E.dist(mid,model['params'][q]['features']),q))
        if z and (not out or out[-1]!=z): out.append(z)
    return tuple(out)

def anchor_pair():
    t9=load_test(9)
    p=t9.get('best_pair')
    if not p: raise RuntimeError('Test 9 produced no sibling anchor pair')
    return p['left'],p['right']

def find_lang_seq(item,code,model):
    lr=next((x for x in item.get('language_sequences',[]) if x['code']==code),None)
    if not lr:return None
    cnt=Counter({tuple(q):int(n) for q,n in lr['sequences']}); m=medoid(cnt,model)
    return m[0] if m else None

def test10(shard):
    model=load_model(); roots=dictionary_map(5); left,right=anchor_pair()
    items=gzread(WORK/f'lexical-shard-{shard:02d}.json.gz'); eligible=[]
    for item in items:
        if item['meaning'] not in roots: continue
        a=find_lang_seq(item,left['code'],model); b=find_lang_seq(item,right['code'],model)
        if a and b: eligible.append((item,a,b))
    real=[];wrong=[];examples=[]
    for i,(item,a,b) in enumerate(eligible):
        root=tuple(roots[item['meaning']]['seq']); p=midpoint_seq(a,b,model); real.append(seqdist(p,root,model))
        wb=eligible[(i+1)%len(eligible)][2] if len(eligible)>1 else b
        wp=midpoint_seq(a,wb,model); wrong.append(seqdist(wp,root,model))
        if len(examples)<200: examples.append({'meaning':item['meaning'],'parent':list(p),'root':list(root),'distance':real[-1],'wrong_distance':wrong[-1]})
    gzwrite(result_path(10,shard),{'test':10,'shard':shard,'meanings':len(real),
                                  'real_parent_distance':statistics.mean(real) if real else None,
                                  'wrong_anchor_distance':statistics.mean(wrong) if wrong else None,
                                  'real_better':bool(real and wrong and statistics.mean(real)<statistics.mean(wrong)),
                                  'examples':examples})

def test11(shard):
    model=load_model(); base=dictionary_map(5); left,right=anchor_pair()
    items=gzread(WORK/f'lexical-shard-{shard:02d}.json.gz'); entries=[]
    for item in items:
        bentry=base.get(item['meaning'])
        if not bentry: continue
        a=find_lang_seq(item,left['code'],model); c=find_lang_seq(item,right['code'],model)
        prior=midpoint_seq(a,c,model) if a and c else None
        e=entry_from_item(item,model,prior=prior)
        if e:
            e['anchor_midpoint']=list(prior) if prior else None
            e['baseline_seq']=bentry['seq']
            e['changed_by_anchor']=bool(prior and e['seq']!=bentry['seq'])
            entries.append(e)
    gzwrite(result_path(11,shard),{'test':11,'shard':shard,'entries':entries})

def test12(shard):
    model=load_model(); left,right=anchor_pair()
    items=gzread(WORK/f'lexical-shard-{shard:02d}.json.gz'); correct=[];base=[];wrong=[];n=0
    eligible=[]
    for item in items:
        fam,_=family_reps(item,model)
        if len(fam)<4: continue
        keys=sorted(fam); hold=keys[h64('hold12',item['meaning'])%len(keys)]
        train={k:v for k,v in fam.items() if k!=hold}; target=fam[hold]
        b=reconstruct_from_fam(train,model)
        if not b: continue
        a=find_lang_seq(item,left['code'],model); r=find_lang_seq(item,right['code'],model)
        eligible.append((item,train,target,b[0],a,r))
    for i,(item,train,target,bseq,a,r) in enumerate(eligible):
        base.append(seqdist(bseq,target,model))
        if a and r:
            mid=midpoint_seq(a,r,model); cr=reconstruct_from_fam(train,model,prior=mid); cseq=cr[0] if cr else bseq
        else:cseq=bseq
        correct.append(seqdist(cseq,target,model))
        wr=eligible[(i+1)%len(eligible)][5] if len(eligible)>1 else r
        if a and wr:
            wmid=midpoint_seq(a,wr,model); rr=reconstruct_from_fam(train,model,prior=wmid); wseq=rr[0] if rr else bseq
        else:wseq=bseq
        wrong.append(seqdist(wseq,target,model)); n+=1
    gzwrite(result_path(12,shard),{'test':12,'shard':shard,'heldout_cases':n,
                                  'correct_anchor_distance':statistics.mean(correct) if correct else None,
                                  'no_anchor_distance':statistics.mean(base) if base else None,
                                  'wrong_anchor_distance':statistics.mean(wrong) if wrong else None})

def test14(shard):
    model=load_model(); rows=gzread(WORK/f'historical-shard-{shard:02d}.json.gz')
    real=Counter(); ctrl=Counter(); contexts=Counter()
    def add(cnt,a,b):
        ali=align(a,b,model)
        for i,(x,y) in enumerate(ali):
            if x is None:key=('insert','-',y)
            elif y is None:key=('delete',x,'-')
            elif x==y:key=('identity',x,y)
            else:key=('substitute',x,y)
            cnt[key]+=1
            if key[0]=='substitute':
                prev=ali[i-1][0] if i else None; nxt=ali[i+1][0] if i+1<len(ali) else None
                contexts[(x,y,prev or '#',nxt or '#')]+=1
    for i,r in enumerate(rows):
        add(real,r['ancestor'],r['descendant'])
        wb=rows[(i+1)%len(rows)]['descendant'] if len(rows)>1 else r['descendant']
        add(ctrl,r['ancestor'],wb)
    gzwrite(result_path(14,shard),{'test':14,'shard':shard,'pairs':len(rows),
                                  'real_rules':[[list(k),n] for k,n in real.items()],
                                  'control_rules':[[list(k),n] for k,n in ctrl.items()],
                                  'contexts':[[list(k),n] for k,n in contexts.items()]})

def reverse_rules(test14):
    rules={}
    for r in test14.get('rules',[]):
        if r.get('type')!='substitute' or r.get('support',0)<20 or r.get('lift',0)<1.2: continue
        desc=r['to']; anc=r['from']
        q=rules.get(desc)
        if q is None or (r['support'],r['lift'])>(q[1],q[2]): rules[desc]=(anc,r['support'],r['lift'])
    return {k:v[0] for k,v in rules.items()}

def test15(shard):
    model=load_model(); base=dictionary_map(5); rules=reverse_rules(load_test(14))
    items=gzread(WORK/f'lexical-shard-{shard:02d}.json.gz'); entries=[]; db=[]; da=[]; ds=[]
    vals=sorted(rules.items()); shuffled={x:vals[(i+1)%len(vals)][1] for i,(x,_) in enumerate(vals)} if vals else {}
    for item in items:
        fam,_=family_reps(item,model)
        if len(fam)<4 or item['meaning'] not in base: continue
        keys=sorted(fam); hold=keys[h64('hold15',item['meaning'])%len(keys)]
        target=fam[hold]; train={k:v for k,v in fam.items() if k!=hold}
        b=reconstruct_from_fam(train,model)
        augfam={k:apply_map(v,rules) for k,v in train.items()}
        af=reconstruct_from_fam(augfam,model,prior=base[item['meaning']]['seq'])
        shfam={k:apply_map(v,shuffled) for k,v in train.items()}
        sf=reconstruct_from_fam(shfam,model,prior=base[item['meaning']]['seq'])
        if not b or not af or not sf: continue
        bd=seqdist(b[0],target,model); ad=seqdist(af[0],target,model); sd=seqdist(sf[0],target,model)
        db.append(bd);da.append(ad);ds.append(sd)
        entries.append({'meaning':item['meaning'],'baseline_seq':list(b[0]),'augmented_seq':list(af[0]),
                        'shuffled_rule_seq':list(sf[0]),'heldout_family':hold,
                        'baseline_distance':bd,'augmented_distance':ad,'shuffled_distance':sd,
                        'baseline_full_dictionary_seq':base[item['meaning']]['seq']})
    gzwrite(result_path(15,shard),{'test':15,'shard':shard,'cases':len(entries),'entries':entries,
                                  'baseline_distance':statistics.mean(db) if db else None,
                                  'augmented_distance':statistics.mean(da) if da else None,
                                  'shuffled_rule_distance':statistics.mean(ds) if ds else None})

def test16(shard):
    model=load_model(); t5=dictionary_map(5); t15=load_test(15); chosen=t15.get('selected_system','baseline')
    aug={e['meaning']:e for e in t15.get('entries',[])}
    entries=[]; errors=[]
    for m,e in t5.items():
        if h64('final16',m)%N!=shard: continue
        if chosen=='augmented' and m in aug: seq=aug[m]['augmented_seq']
        else: seq=e['seq']
        bad=[p for p in seq if p not in model['root_ids']]
        if bad: errors.append({'meaning':m,'error':'non-Test1 phoneme','ids':bad});continue
        pp=phoneme_payload(seq,model)
        if any(len(x['path_left'])!=10 or len(x['path_right'])!=10 for x in pp):
            errors.append({'meaning':m,'error':'invalid exact-grid path'});continue
        entries.append({'meaning':m,'seq':seq,'ipa':'/'+''.join(model['params'][p]['name'] for p in seq)+'/',
                        'confidence':e.get('confidence'),'languages':e.get('languages'),'families':e.get('families'),
                        'phonemes':pp,'selected_system':chosen})
    gzwrite(result_path(16,shard),{'test':16,'shard':shard,'entries':entries,'errors':errors,
                                  'checked':len(entries)+len(errors)})

def run_test(test,shard):
    fn=globals().get(f'test{test}')
    if not fn: raise SystemExit(f'unsupported test {test}')
    if not 0<=shard<N: raise SystemExit('shard must be 0..19')
    fn(shard)

def merge_simple_entries(test, key):
    model=load_model(); parts=[gzread(result_path(test,i)) for i in range(N)]
    entries=[]
    for p in parts: entries.extend(p.get(key,[]))
    return model,parts,entries

def merge(test):
    model=load_model(); manifest=jread(WORK/'prepared-manifest.json')
    if test in {4,5,11}:
        _,parts,entries=merge_simple_entries(test,'entries')
        entries.sort(key=lambda e:(-e.get('confidence',0),-e.get('families',0),e['meaning']))
        controls=[p.get('control') for p in parts if p.get('control')]
        out={'version':4,'test_id':test,'status':'complete','shards':20,
             'grid':{'cells':1074,'all_rectangles_mirrored':True},
             'summary':{'entries':len(entries),'shard_outputs':[len(p.get('entries',[])) for p in parts],
                        'shards_real_better_than_control':sum(bool(c.get('real_better')) for c in controls)},
             'entries':entries,'execution':manifest['execution']}
    elif test==13:
        parts=[gzread(result_path(13,i)) for i in range(N)]
        rp=sum(p['pairs'] for p in parts); real=[p['real_mean_distance'] for p in parts if p['real_mean_distance'] is not None]
        wrong=[p['wrong_mean_distance'] for p in parts if p['wrong_mean_distance'] is not None]
        ev=Counter()
        for p in parts:
            for k,n in p['events']: ev[tuple(k)]+=n
        out={'version':4,'test_id':13,'status':'complete','shards':20,'grid':{'cells':1074,'all_rectangles_mirrored':True},
             'summary':{'historical_pairs':rp,'mean_real_distance':statistics.mean(real) if real else None,
                        'mean_wrong_distance':statistics.mean(wrong) if wrong else None,
                        'shards_real_better':sum(p['real_better'] for p in parts)},
             'event_counts':[[list(k),n] for k,n in ev.most_common()], 'execution':manifest['execution']}
    elif test in {6,7,8}:
        k={6:'languages',7:'families',8:'families'}[test];_,parts,entries=merge_simple_entries(test,k)
        sortkey=(lambda e:(-e['similarity'],-e['shared_meanings'],e['code'])) if test==6 else (lambda e:(-e.get('advantage',e.get('reverse_gain',0)),e['family']))
        entries.sort(key=sortkey)
        out={'version':4,'test_id':test,'status':'complete','shards':20,
             'summary':{'records':len(entries),'shard_outputs':[len(p.get(k,[])) for p in parts]},
             k:entries,'execution':manifest['execution']}
    elif test==9:
        parts=[gzread(result_path(9,i)) for i in range(N)];pairs=[]
        for p in parts:pairs.extend(p['candidate_pairs'])
        pairs.sort(key=lambda x:(-x['score'],x['left']['code'],x['right']['code']))
        out={'version':4,'test_id':9,'status':'complete','shards':20,
             'summary':{'candidate_pairs':len(pairs),'shard_outputs':[len(p['candidate_pairs']) for p in parts]},
             'best_pair':pairs[0] if pairs else None,'top_pairs':pairs[:50],'execution':manifest['execution']}
    elif test in {10,12}:
        parts=[gzread(result_path(test,i)) for i in range(N)]
        if test==10:
            n=sum(p['meanings'] for p in parts);real=[p['real_parent_distance'] for p in parts if p['real_parent_distance'] is not None];wrong=[p['wrong_anchor_distance'] for p in parts if p['wrong_anchor_distance'] is not None]
            out={'version':4,'test_id':10,'status':'complete','shards':20,
                 'summary':{'meanings':n,'mean_real_parent_distance':statistics.mean(real) if real else None,
                            'mean_wrong_anchor_distance':statistics.mean(wrong) if wrong else None,
                            'shards_real_better':sum(p['real_better'] for p in parts)},'execution':manifest['execution']}
        else:
            n=sum(p['heldout_cases'] for p in parts)
            def av(k):return statistics.mean([p[k] for p in parts if p[k] is not None]) if any(p[k] is not None for p in parts) else None
            out={'version':4,'test_id':12,'status':'complete','shards':20,
                 'summary':{'heldout_cases':n,'correct_anchor_distance':av('correct_anchor_distance'),
                            'no_anchor_distance':av('no_anchor_distance'),'wrong_anchor_distance':av('wrong_anchor_distance')},
                 'execution':manifest['execution']}
    elif test==14:
        parts=[gzread(result_path(14,i)) for i in range(N)];real=Counter();ctrl=Counter();contexts=Counter()
        for p in parts:
            for k,n in p['real_rules']:real[tuple(k)]+=n
            for k,n in p['control_rules']:ctrl[tuple(k)]+=n
            for k,n in p['contexts']:contexts[tuple(k)]+=n
        rules=[]
        for k,n in real.items():
            c=ctrl[k];typ,fr,to=k
            lift=(n+1)/(c+1)
            if typ!='identity':
                rule={'type':typ,'from':fr,'to':to,'support':n,'control_support':c,'lift':lift}
                if typ=='substitute' and fr in model['params'] and to in model['params']:
                    gf=model['params'][fr]['grid'];gt=model['params'][to]['grid']
                    rule['grid_delta']={'dx':gt['x']-gf['x'],'dy':gt['y']-gf['y'],
                                        'same_coordinate':gf['all_left']==gt['all_left']}
                rules.append(rule)
        rules.sort(key=lambda r:(-r['support'],-r['lift'],r['type'],str(r['from']),str(r['to'])))
        out={'version':4,'test_id':14,'status':'complete','shards':20,
             'summary':{'rules_observed':len(rules),'supported_rules':sum(r['support']>=20 and r['lift']>=1.2 for r in rules)},
             'rules':rules,'context_counts':[[list(k),n] for k,n in contexts.most_common(1000)],
             'transformative_circle_operator':None,
             'transformative_circle_boundary':'No circle operator is inferred because the lexical/historical evidence does not directly observe a traversal through the manuscript circle.',
             'execution':manifest['execution']}
    elif test==15:
        parts=[gzread(result_path(15,i)) for i in range(N)];entries=[]
        for p in parts:entries.extend(p['entries'])
        def weighted(k):
            vals=[(p[k],p['cases']) for p in parts if p[k] is not None and p['cases']]
            return sum(v*n for v,n in vals)/sum(n for _,n in vals) if vals else None
        b=weighted('baseline_distance');a=weighted('augmented_distance');s=weighted('shuffled_rule_distance')
        selected='augmented' if a is not None and b is not None and a<b and (s is None or a<s) else 'baseline'
        out={'version':4,'test_id':15,'status':'complete','shards':20,'selected_system':selected,
             'summary':{'cases':len(entries),'baseline_distance':b,'augmented_distance':a,'shuffled_rule_distance':s,
                        'selected_system':selected},'entries':entries,'execution':manifest['execution']}
    elif test==16:
        parts=[gzread(result_path(16,i)) for i in range(N)];entries=[];errors=[]
        for p in parts:entries.extend(p['entries']);errors.extend(p['errors'])
        entries.sort(key=lambda e:e['meaning'])
        out={'version':4,'test_id':16,'status':'complete' if not errors else 'complete-with-consistency-errors','shards':20,
             'summary':{'final_entries':len(entries),'consistency_errors':len(errors),'shard_outputs':[len(p['entries']) for p in parts]},
             'final_phoneme_inventory':jread(T1)['original_phoneme_inventory'],
             'entries':entries,'errors':errors,'execution':manifest['execution'],
             'evidence_boundary':'Candidate reconstruction under the exact-v4 computational model; not proof of a literal single prehistoric world language.'}
        jwrite(ROOT/'data/man-grid-original-language-final-exact-v4.json',out)
    else:
        raise SystemExit(f'no merge for test {test}')
    jwrite(out_path(test),out)
    print(json.dumps(out.get('summary',{}),ensure_ascii=False,indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('prepare')
    r=sp.add_parser('run');r.add_argument('--test',type=int,required=True);r.add_argument('--shard',type=int,required=True)
    m=sp.add_parser('merge');m.add_argument('--test',type=int,required=True)
    a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='run':run_test(a.test,a.shard)
    else:merge(a.test)

if __name__=='__main__':
    main()
