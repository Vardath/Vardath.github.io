#!/usr/bin/env python3
import csv,json,math,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LANG=ROOT/'data/phonetic-benchmark-languages.csv'
PAIR=ROOT/'data/phonetic-benchmark-pairs.csv'
OUTJ=ROOT/'data/phonetic-group-comparison.json'
OUTM=ROOT/'data/phonetic-group-comparison.md'
GLOTTO='https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv'
TOPK=4

def read_csv(p):
    with open(p,encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def pairkey(a,b):return '|'.join(sorted((a,b)))

def load():
    langs=[r for r in read_csv(LANG) if r.get('canonical','').lower()=='true']
    wanted={r['iso'] for r in langs}
    pairs=[]
    for p in read_csv(PAIR):
        if p['iso_a'] in wanted and p['iso_b'] in wanted:
            q=dict(p)
            for k in ('jaccard','cosine','jsd_bits','a_to_b_direct_mass','b_to_a_direct_mass'):
                q[k]=float(q[k])
            pairs.append(q)
    return langs,pairs

def neighbours(langs,pairs):
    pm={pairkey(p['iso_a'],p['iso_b']):p for p in pairs}
    out={}
    for l in langs:
        iso=l['iso']; arr=[]
        for x in langs:
            if x['iso']==iso:continue
            p=pm.get(pairkey(iso,x['iso']))
            if p:arr.append((x['iso'],p['jaccard']))
        out[iso]=sorted(arr,key=lambda z:(-z[1],z[0]))
    return out,pm

def derive_groups(langs,pairs):
    ns,pm=neighbours(langs,pairs)
    chosen={iso:{x for x,_ in arr[:TOPK]} for iso,arr in ns.items()}
    edges=[]
    for p in pairs:
        a,b=p['iso_a'],p['iso_b']; aa=b in chosen[a]; bb=a in chosen[b]
        if (aa and bb) or ((aa or bb) and p['jaccard']>=.55): edges.append(p)
    adj={l['iso']:[] for l in langs}
    for p in edges:
        a,b,w=p['iso_a'],p['iso_b'],p['jaccard'];adj[a].append((b,w));adj[b].append((a,w))
    lab={l['iso']:l['iso'] for l in langs}
    for _ in range(30):
        changed=0
        for iso in sorted(lab):
            score=defaultdict(float)
            for n,w in adj[iso]:score[lab[n]]+=w
            if not score:continue
            best=sorted(score.items(),key=lambda z:(-z[1],z[0]))[0][0]
            if best!=lab[iso]:lab[iso]=best;changed+=1
        if not changed:break
    for _ in range(3):
        cnt=Counter(lab.values())
        for iso in sorted(lab):
            g=lab[iso]
            if cnt[g]>=3:continue
            score=defaultdict(float)
            for n,w in adj[iso]:
                ng=lab[n]
                if ng!=g:score[ng]+=w
            if score:lab[iso]=max(score,key=score.get)
    gm=defaultdict(list)
    for iso,g in lab.items():gm[g].append(iso)
    groups=sorted(gm.values(),key=lambda x:(-len(x),x[0]))
    groupof={iso:i+1 for i,g in enumerate(groups) for iso in g}
    return groups,groupof,edges,pm

def glottolog_map():
    req=urllib.request.Request(GLOTTO,headers={'User-Agent':'Vardath-phonetic-group-audit/1.0'})
    rows=list(csv.DictReader(line.decode('utf-8') for line in urllib.request.urlopen(req,timeout=120)))
    famnames={r['ID']:r['Name'] for r in rows if r.get('Level')=='family'}
    out={}
    for r in rows:
        iso=(r.get('ISO639P3code') or '').strip()
        if iso and r.get('Level')=='language':
            fid=(r.get('Family_ID') or '').strip(); out[iso]={'family_id':fid or r['ID'],'family':famnames.get(fid,'Isolate' if not fid else fid),'glottocode':r.get('Glottocode') or r['ID'],'lat':r.get('Latitude'),'lon':r.get('Longitude')}
    return out

def pair_metrics(groupof,known):
    tp=fp=fn=tn=0; keys=sorted(set(groupof)&set(known))
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            sg=groupof[a]==groupof[b]; sk=known[a]==known[b]
            if sg and sk:tp+=1
            elif sg and not sk:fp+=1
            elif not sg and sk:fn+=1
            else:tn+=1
    prec=tp/(tp+fp) if tp+fp else 0; rec=tp/(tp+fn) if tp+fn else 0
    return {'n':len(keys),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'precision':prec,'recall':rec,'f1':2*prec*rec/(prec+rec) if prec+rec else 0}

def main():
    langs,pairs=load(); groups,groupof,edges,pm=derive_groups(langs,pairs); by={r['iso']:r for r in langs}; gl=glottolog_map()
    known={iso:x['family_id'] for iso,x in gl.items() if iso in by}
    group_rows=[]; weighted=0
    for i,g in enumerate(groups,1):
        fam=Counter(gl[x]['family'] if x in gl else by[x].get('family','Unknown') for x in g)
        topfam,topn=fam.most_common(1)[0]; purity=topn/len(g);weighted+=topn
        group_rows.append({'group':i,'size':len(g),'purity':purity,'dominant_family':topfam,'dominant_n':topn,'families':fam.most_common(),'members':[{'iso':x,'name':by[x]['name'],'family':gl.get(x,{}).get('family',by[x].get('family','Unknown'))} for x in sorted(g)]})
    same=[];cross=[]
    for p in pairs:
        a,b=p['iso_a'],p['iso_b']; fa=gl.get(a,{}).get('family_id');fb=gl.get(b,{}).get('family_id')
        if fa and fb and fa==fb:same.append(p['jaccard'])
        elif fa and fb:cross.append(p['jaccard'])
    cross_edges=[]
    for p in sorted(pairs,key=lambda x:-x['jaccard']):
        a,b=p['iso_a'],p['iso_b']; ga,gb=gl.get(a),gl.get(b)
        if ga and gb and ga['family_id']!=gb['family_id']:
            cross_edges.append({'a':a,'a_name':by[a]['name'],'a_family':ga['family'],'b':b,'b_name':by[b]['name'],'b_family':gb['family'],'jaccard':p['jaccard']})
            if len(cross_edges)>=25:break
    result={'method':{'site_top_k':TOPK,'grouping':'same label-propagation logic as phonetic-language-atlas.js','known_reference':'Glottolog CLDF master, matched by ISO 639-3'},'counts':{'languages':len(langs),'groups':len(groups),'glottolog_matched':len(set(by)&set(gl))},'summary':{'weighted_cluster_purity':weighted/len(langs),'mean_same_family_jaccard':sum(same)/len(same) if same else None,'mean_cross_family_jaccard':sum(cross)/len(cross) if cross else None,'same_family_pairs':len(same),'cross_family_pairs':len(cross),'pairwise':pair_metrics(groupof,known)},'groups':group_rows,'strongest_cross_family_pairs':cross_edges}
    OUTJ.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    s=result['summary']; lines=['# Phonetic site groups vs Glottolog genealogy','',f"Languages: {len(langs)} | site groups: {len(groups)} | Glottolog matched: {result['counts']['glottolog_matched']}",f"Weighted cluster purity: {s['weighted_cluster_purity']:.3f}",f"Mean same-family Jaccard: {s['mean_same_family_jaccard']:.3f}",f"Mean cross-family Jaccard: {s['mean_cross_family_jaccard']:.3f}",f"Pairwise precision/recall/F1: {s['pairwise']['precision']:.3f} / {s['pairwise']['recall']:.3f} / {s['pairwise']['f1']:.3f}",'']
    for g in group_rows:
        lines += [f"## Group {g['group']} — {g['size']} languages",f"Dominant known family: **{g['dominant_family']}** ({g['dominant_n']}/{g['size']}, purity {g['purity']:.1%})",'Families: '+', '.join(f'{a} {n}' for a,n in g['families'][:8]),'Members: '+', '.join(f"{m['name']} [{m['family']}]" for m in g['members']),'']
    lines += ['## Strongest cross-family bridge similarities','']+[f"- {x['a_name']} ({x['a_family']}) ↔ {x['b_name']} ({x['b_family']}): {x['jaccard']:.3f}" for x in cross_edges]
    OUTM.write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
