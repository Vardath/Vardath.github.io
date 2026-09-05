// Shared engine for the Vardath ordered-alphabet 3×3 → 4×4 → 5×5 magic-square experiment.
// The browser UI and the reproducible batch runner import this same file.

export const VERSION = '20260905-345magic-v1';
export const PINS = {
  wikipron: 'd282e848a211ea31cfd730f0ced8bc8cdab9e83d',
  phoible: '5c477f1934f57b3c1a16168fadc08e83dbc03362'
};
export const WP_BASE = `https://raw.githubusercontent.com/CUNY-CL/wikipron/${PINS.wikipron}/data/scrape/tsv/`;
export const PH_BASE = `https://raw.githubusercontent.com/cldf-datasets/phoible/${PINS.phoible}/cldf/`;

// Standard choices for the experiment. 3×3 = Lo Shu, 4×4 = Dürer 1514,
// 5×5 = the standard normal Siamese square. The UI exposes these values.
export const MAGIC = {
  3: [8,1,6, 3,5,7, 4,9,2],
  4: [16,2,3,13, 5,11,10,8, 9,7,6,12, 4,14,15,1],
  5: [17,24,1,8,15, 23,5,7,14,16, 4,6,13,20,22, 10,12,19,21,3, 11,18,25,2,9]
};
export const MAGIC_NAMES = {3:'Lo Shu 3×3',4:'Dürer 4×4 (1514)',5:'Siamese 5×5'};

export function parseCSV(text){
  const rows=[]; let row=[], field='', q=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(q){ if(c==='"'){ if(text[i+1]==='"'){field+='"';i++;} else q=false; } else field+=c; continue; }
    if(c==='"'){q=true;continue;} if(c===','){row.push(field);field='';continue;}
    if(c==='\n'){row.push(field);rows.push(row);row=[];field='';continue;} if(c!=='\r')field+=c;
  }
  if(field.length||row.length){row.push(field);rows.push(row);} const header=rows.shift()||[];
  return rows.filter(r=>r.some(x=>x!=='')).map(r=>Object.fromEntries(header.map((h,i)=>[h,r[i]??''])));
}
export function fnum(v){
  if(v===undefined||v===null||v===''||v==='N'||v==='0')return 0;
  let n=0,c=0; for(const x of String(v).split(',')){if(x==='+'){n++;c++;}else if(x==='-'){n--;c++;}}
  return c?n/c:0;
}
export function isPlus(v){return fnum(v)>.25;}
export function classify(p){
  if(!p)return null; const sc=(p.SegmentClass||'').toLowerCase();
  if(sc==='tone'||isPlus(p.tone))return null;
  if(sc==='vowel'||(isPlus(p.syllabic)&&!isPlus(p.consonantal))){
    const vert=fnum(p.high)-fnum(p.low), horiz=fnum(p.front)-fnum(p.back);
    if(vert>=0)return horiz>=0?'A1':'A3'; return horiz>=0?'A2':'A4';
  }
  const row=isPlus(p.sonorant)?'B':isPlus(p.continuant)?'C':'D';
  const places=[['1',fnum(p.labial)],['2',fnum(p.coronal)],['3',fnum(p.dorsal)]].sort((a,b)=>b[1]-a[1]);
  return row+(places[0][1]>.25?places[0][0]:'4');
}
export function latentPoint(p){
  const c=classify(p); if(!c)return null; const ri='ABCD'.indexOf(c[0]), ci=Number(c[1])-1; let dx=0,dy=0;
  if(c[0]==='A'){
    dx=Math.max(-1,Math.min(1,(fnum(p.back)-fnum(p.front))/2));
    dy=Math.max(-1,Math.min(1,(fnum(p.low)-fnum(p.high))/2));
  }else{
    const lab=fnum(p.labial),cor=fnum(p.coronal),dor=fnum(p.dorsal);
    dx=Math.max(-1,Math.min(1,(dor-lab+.35*(dor-cor))/2));
    dy=Math.max(-1,Math.min(1,(fnum(p.continuant)-fnum(p.sonorant)+.35*fnum(p.delayedRelease))/2));
  }
  return {x:(ci+.5+.42*dx)/4,y:(ri+.5+.42*dy)/4};
}
export function cellN(p,n){
  const pt=latentPoint(p); if(!pt)return null;
  const col=Math.min(n-1,Math.floor(Math.max(0,Math.min(.999999,pt.x))*n));
  const row=Math.min(n-1,Math.floor(Math.max(0,Math.min(.999999,pt.y))*n));
  return row*n+col;
}
export function normalizePhone(s){return String(s||'').trim().replace(/^\/+|\/+$/g,'').replace(/^\ufeff/,'');}
export function phoneParam(phone,params){
  const n=normalizePhone(phone); let p=params.get(n); if(p)return p;
  const base=n.replace(/[ˈˌ.‿#]/g,''); if(base!==n)p=params.get(base); return p||null;
}
export async function loadPhoibleParameters(fetchImpl=fetch){
  const r=await fetchImpl(PH_BASE+'parameters.csv'); if(!r.ok)throw new Error(`PHOIBLE parameters ${r.status}`);
  const rows=parseCSV(await r.text()); const m=new Map(); for(const p of rows){const name=(p.Name||'').trim(); if(name)m.set(name,p);} return m;
}
export function hash32(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
export function rngFor(seed){let a=hash32(seed)||1;return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
export function shuffled(n,rng){const a=Array.from({length:n},(_,i)=>i);for(let i=n-1;i>0;i--){const j=Math.floor(rng()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
export function mean(a){return a.length?a.reduce((x,y)=>x+y,0)/a.length:0;}
export function sd(a,mu=mean(a)){return a.length?Math.sqrt(a.reduce((s,x)=>s+(x-mu)**2,0)/a.length):0;}
export function normalCdf(z){return .5*(1+erf(z/Math.SQRT2));}
export function erf(x){
  const sign=x<0?-1:1; x=Math.abs(x); const a1=.254829592,a2=-.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=.3275911;
  const t=1/(1+p*x), y=1-(((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-x*x); return sign*y;
}
export function cosine(a,b){let aa=0,bb=0,dot=0;for(let i=0;i<a.length;i++){aa+=a[i]*a[i];bb+=b[i]*b[i];dot+=a[i]*b[i];}return aa&&bb?dot/Math.sqrt(aa*bb):0;}
export function normalizeMatrix(a){const t=a.reduce((x,y)=>x+y,0)||1;return a.map(x=>x/t);}
export function lowerLocale(s,locale='und'){try{return String(s||'').toLocaleLowerCase(locale==='und'?undefined:locale);}catch{return String(s||'').toLowerCase();}}
export function segmentGraphemes(s,locale='und'){
  const text=lowerLocale(String(s||'').normalize('NFC'),locale);
  if(typeof Intl!=='undefined'&&Intl.Segmenter){
    const seg=new Intl.Segmenter(locale,{granularity:'grapheme'}); return [...seg.segment(text)].map(x=>x.segment).filter(x=>/\p{L}/u.test(x));
  }
  return [...text].filter(x=>/\p{L}/u.test(x));
}
export function tokenizeWithAlphabet(word,alphabet,locale='und'){
  const text=lowerLocale(String(word||'').normalize('NFC'),locale);
  if(!alphabet?.length)return segmentGraphemes(text,locale);
  const tokens=[...alphabet].sort((a,b)=>b.length-a.length); const out=[]; let i=0;
  while(i<text.length){let hit=null;for(const t of tokens){if(text.startsWith(t,i)){hit=t;break;}}
    if(hit){out.push(hit);i+=hit.length;continue;} const cp=String.fromCodePoint(text.codePointAt(i)); if(/\p{L}/u.test(cp))out.push(cp); i+=cp.length;
  }
  return out;
}
export function localeFor(meta){return (meta.locale||meta.iso||'und').replace('_','-');}
export function deriveAlphabet(words,meta,explicit=null){
  const locale=localeFor(meta); const raw=Array.isArray(explicit)?explicit:explicit?.symbols;
  if(raw?.length){const order=raw.map(x=>lowerLocale(x.normalize('NFC'),locale));return{order,source:explicit?.source||'explicit preset',confidence:'explicit'};}
  const seen=new Set(); for(const w of words)for(const g of segmentGraphemes(w,locale))seen.add(g);
  let coll;try{coll=new Intl.Collator(locale,{usage:'sort',sensitivity:'variant'});}catch{coll=new Intl.Collator('und',{usage:'sort'});}
  const order=[...seen].sort(coll.compare); return{order,source:`Intl locale collation (${locale})`,confidence:'inferred'};
}
export function ordinalBucket(rank,total,n){
  const states=n*n; if(total<=1)return 1; return Math.min(states,1+Math.floor(rank*states/total));
}
export function valueToCell(n,value,magic=MAGIC){return magic[n].indexOf(value);}
export function sequentialValueToCell(_n,value){return value-1;}
export function resolveAlphabetToken(token,alphabet){
  if(alphabet.includes(token))return token;
  const td=token.normalize('NFD'),base=[...td][0]; let best=null,bestMarks=-1; const tmarks=[...td].slice(1);
  for(const a of alphabet){const ad=a.normalize('NFD'),ap=[...ad];if(ap[0]!==base)continue;const marks=ap.slice(1);let ok=true;for(const m of marks){if(!tmarks.includes(m)){ok=false;break;}}if(ok&&marks.length>bestMarks){best=a;bestMarks=marks.length;}}
  return best;
}
export function buildOrthTransitions(words,alphabet,meta,n,mode='magic',magic=MAGIC,letterRankOverride=null,magicCellOverride=null){
  const states=n*n, out=new Float64Array(states*states), rank=new Map();
  alphabet.forEach((g,i)=>rank.set(g,letterRankOverride?letterRankOverride[i]:i));
  const locale=localeFor(meta), cellOfValue=magicCellOverride||((v)=>mode==='magic'?valueToCell(n,v,magic):sequentialValueToCell(n,v));
  let transitions=0,unknown=0;
  for(const w of words){const toks=tokenizeWithAlphabet(w,alphabet,locale);let prev=null;
    for(const raw of toks){const t=resolveAlphabetToken(raw,alphabet);if(!t||!rank.has(t)){unknown++;prev=null;continue;}const b=ordinalBucket(rank.get(t),alphabet.length,n),cur=cellOfValue(b);if(cur<0){prev=null;continue;}if(prev!==null){out[prev*states+cur]++;transitions++;}prev=cur;}
  }
  return {matrix:out,transitions,unknown};
}
export function buildPhoneTransitions(lines,params,n){
  const states=n*n,out=new Float64Array(states*states);let mapped=0,unknown=0,transitions=0;
  for(const line of lines){const tab=line.indexOf('\t');if(tab<0)continue;let prev=null;for(const ph of line.slice(tab+1).trim().split(/\s+/)){
    const p=phoneParam(ph,params),cur=p?cellN(p,n):null;if(cur===null){unknown++;prev=null;continue;}mapped++;if(prev!==null){out[prev*states+cur]++;transitions++;}prev=cur;
  }}
  return {matrix:out,mapped,unknown,transitions};
}
export function phoneticMagicCost(matrix,n,magic=MAGIC,cellPermutation=null){
  const states=n*n,total=matrix.reduce((x,y)=>x+y,0)||1;let s=0;
  const posToValue=cellPermutation?cellPermutation.map(i=>magic[n][i]):magic[n];
  for(let a=0;a<states;a++)for(let b=0;b<states;b++){const w=matrix[a*states+b];if(w)s+=w*Math.abs((posToValue[b]-1)-(posToValue[a]-1))/(states-1);}
  return s/total;
}
export function permToValueCell(n,perm,magic=MAGIC){
  if(perm)return v=>perm[v-1]; const inv=new Array(n*n);magic[n].forEach((v,i)=>inv[v-1]=i);return v=>inv[v-1];
}
export function pFromHigher(observed,nulls){return(1+nulls.filter(x=>x>=observed).length)/(nulls.length+1);}
export function pFromLower(observed,nulls){return(1+nulls.filter(x=>x<=observed).length)/(nulls.length+1);}
export function zHigher(observed,nulls){const m=mean(nulls),s=sd(nulls,m)||1e-12;return(observed-m)/s;}
export function zLower(observed,nulls){const m=mean(nulls),s=sd(nulls,m)||1e-12;return(m-observed)/s;}
export function analyzeLayer({words,alphabet,meta,phoneMatrix,n,permutations=120,seed='',magic=MAGIC}){
  const seq=buildOrthTransitions(words,alphabet,meta,n,'sequential',magic).matrix;
  const mag=buildOrthTransitions(words,alphabet,meta,n,'magic',magic).matrix;
  const simSeq=cosine(normalizeMatrix(seq),normalizeMatrix(phoneMatrix));
  const simMagic=cosine(normalizeMatrix(mag),normalizeMatrix(phoneMatrix));
  const gain=simMagic-simSeq;
  const rng=rngFor(`${VERSION}:${seed}:n${n}`),states=n*n,magicNull=[],orderNull=[],localityNull=[];
  const observedLocality=phoneticMagicCost(phoneMatrix,n,magic);
  for(let k=0;k<permutations;k++){
    const valuePerm=shuffled(states,rng);
    const q=buildOrthTransitions(words,alphabet,meta,n,'magic',magic,null,permToValueCell(n,valuePerm,magic)).matrix;
    magicNull.push(cosine(normalizeMatrix(q),normalizeMatrix(phoneMatrix)));
    const rankPerm=shuffled(alphabet.length,rng);
    const qo=buildOrthTransitions(words,alphabet,meta,n,'magic',magic,rankPerm).matrix;
    orderNull.push(cosine(normalizeMatrix(qo),normalizeMatrix(phoneMatrix)));
    const cellPerm=shuffled(states,rng);
    localityNull.push(phoneticMagicCost(phoneMatrix,n,magic,cellPerm));
  }
  const magicZ=zHigher(simMagic,magicNull),orderZ=zHigher(simMagic,orderNull),localityZ=zLower(observedLocality,localityNull);
  const layerZ=(magicZ+orderZ+localityZ)/Math.sqrt(3);
  return {n,simSequential:simSeq,simMagic,magicGain:gain,magicZ,magicP:pFromHigher(simMagic,magicNull),alphabetOrderZ:orderZ,alphabetOrderP:pFromHigher(simMagic,orderNull),phoneticMagicCost:observedLocality,phoneticLocalityZ:localityZ,phoneticLocalityP:pFromLower(observedLocality,localityNull),layerZ,permutations};
}
export function sampleLinesDeterministic(text,maxLines,seed=''){
  const lines=text.split(/\r?\n/).filter(x=>x.includes('\t')); if(lines.length<=maxLines)return lines;
  const rng=rngFor(`${VERSION}:sample:${seed}`),sample=[];let seen=0;
  for(const line of lines){seen++;if(sample.length<maxLines)sample.push(line);else{const j=Math.floor(rng()*seen);if(j<maxLines)sample[j]=line;}}
  return sample;
}
export function wordsFromLines(lines){return lines.map(x=>x.slice(0,x.indexOf('\t'))).filter(Boolean);}
export async function analyzeLanguage(meta,{params,fetchImpl=fetch,alphabetPresets={},permutations=120,maxWords=3000,magic=MAGIC}={}){
  const r=await fetchImpl(WP_BASE+meta.file);if(!r.ok)throw new Error(`${meta.file}: ${r.status}`);const text=await r.text();
  const lines=sampleLinesDeterministic(text,maxWords,meta.file),words=wordsFromLines(lines),preset=alphabetPresets[meta.iso]||null;
  const a=deriveAlphabet(words,meta,preset);if(a.order.length<3)throw new Error('fewer than 3 ordered symbols');
  const layers={};for(const n of [3,4,5]){const ph=buildPhoneTransitions(lines,params,n);layers[n]=analyzeLayer({words,alphabet:a.order,meta,phoneMatrix:ph.matrix,n,permutations,seed:meta.iso,magic});layers[n].phoneCoverage=ph.mapped/(ph.mapped+ph.unknown||1);layers[n].phoneTransitions=ph.transitions;}
  const z345=(layers[3].layerZ+2*layers[4].layerZ+layers[5].layerZ)/Math.sqrt(6);
  const simMid=(layers[3].simMagic+layers[5].simMagic)/2,bridgeResidual=Math.abs(layers[4].simMagic-simMid),coherence=Math.max(0,1-Math.min(1,bridgeResidual/.20));
  const allPositive=[3,4,5].every(n=>layers[n].magicGain>0),fourPositive=layers[4].magicGain>0;
  let strength='none/anti-fit'; if(z345>=2.58&&fourPositive&&coherence>=.5)strength='strong';else if(z345>=1.645&&fourPositive)strength='moderate';else if(z345>0)strength='weak';
  return {iso:meta.iso,name:meta.name,family:meta.family||'Unclassified',macroarea:meta.macroarea||'',script:meta.script||'',file:meta.file,alphabet:a.order,alphabetSize:a.order.length,alphabetSource:a.source,alphabetConfidence:a.confidence,wordSample:lines.length,layers,z345,bridgeResidual,bridgeCoherence:coherence,allLayersPositive:allPositive,strength,power4:{description:'Dürer cell value n corresponds to 3^(n−1); locality uses absolute exponent-step distance.',meanExponentStep:layers[4].phoneticMagicCost,z:layers[4].phoneticLocalityZ,p:layers[4].phoneticLocalityP}};
}
export function bh(rows,pKey='p',qKey='q'){
  const m=rows.length;if(!m)return rows;const order=[...rows.keys()].sort((a,b)=>rows[a][pKey]-rows[b][pKey]);let prev=1;
  for(let rank=m;rank>=1;rank--){const i=order[rank-1],v=Math.min(prev,rows[i][pKey]*m/rank);rows[i][qKey]=v;prev=v;}return rows;
}
export function groupResults(languages,mapping,type){
  const byIso=new Map(languages.map(x=>[x.iso,x])),out=[];
  for(const [name,isos] of Object.entries(mapping)){const xs=isos.map(i=>byIso.get(i)).filter(Boolean);if(xs.length<3)continue;
    const z=xs.reduce((s,x)=>s+x.z345,0)/Math.sqrt(xs.length),p=1-normalCdf(z);
    out.push({group:name,type,languages:xs.length,z,p,meanZ:mean(xs.map(x=>x.z345)),mean3:mean(xs.map(x=>x.layers[3].magicGain)),mean4:mean(xs.map(x=>x.layers[4].magicGain)),mean5:mean(xs.map(x=>x.layers[5].magicGain)),meanOrderZ:mean(xs.map(x=>x.layers[4].alphabetOrderZ)),meanLocalityZ:mean(xs.map(x=>x.layers[4].phoneticLocalityZ)),meanCoherence:mean(xs.map(x=>x.bridgeCoherence)),members:xs.map(x=>x.name).sort(),strongMembers:xs.filter(x=>x.strength==='strong').length,moderateMembers:xs.filter(x=>['strong','moderate'].includes(x.strength)).length});
  }
  bh(out,'p','q');for(const g of out){g.strength=g.q<.01&&g.z>0?'strong':g.q<.05&&g.z>0?'moderate':g.z>0?'weak':'none/anti-fit';}return out.sort((a,b)=>b.z-a.z);
}
export function familyMapping(languages){const m={};for(const x of languages)(m[x.family]??=[]).push(x.iso);return m;}
export function scriptMapping(languages){const m={};for(const x of languages)(m[x.script||'Unknown script']??=[]).push(x.iso);return m;}
export function topologyMapping(groupData){const m={};for(const g of groupData?.groups||[])m[`Topology group ${g.group}`]=(g.members||[]).map(x=>x.iso);return m;}
export async function runExperiment({metas,topologyData=null,params=null,fetchImpl=fetch,alphabetPresets={},permutations=120,maxWords=3000,onProgress=null,concurrency=3,magic=MAGIC}={}){
  params=params||await loadPhoibleParameters(fetchImpl);const queue=[...metas],results=[],failures=[];let done=0;
  async function worker(){while(queue.length){const meta=queue.shift();try{results.push(await analyzeLanguage(meta,{params,fetchImpl,alphabetPresets,permutations,maxWords,magic}));}catch(e){failures.push({iso:meta.iso,name:meta.name,error:String(e?.message||e)});}done++;onProgress?.({done,total:metas.length,meta,results:results.length,failures:failures.length});}}
  await Promise.all(Array.from({length:Math.max(1,Math.min(concurrency,metas.length))},worker));results.sort((a,b)=>b.z345-a.z345);
  const groups={families:groupResults(results,familyMapping(results),'Glottolog family'),scripts:groupResults(results,scriptMapping(results),'Writing system'),topology:topologyData?groupResults(results,topologyMapping(topologyData),'Phonetic topology group'):[]};
  const globalZ=results.length?results.reduce((s,x)=>s+x.z345,0)/Math.sqrt(results.length):0;
  return {version:VERSION,pins:PINS,magicSquares:{3:MAGIC[3],4:MAGIC[4],5:MAGIC[5]},method:{alphabet:'Explicit preset where supplied; otherwise locale-aware collation of observed grapheme symbols. Multi-character symbols are supported by explicit presets.',mapping:'Alphabet symbols receive ordinal numbers in intended order. Each rank is normalized to 1..9, 1..16 and 1..25. The experimental mapping places each ordinal bucket in the cell carrying that number in the 3×3, 4×4 or 5×5 magic square. Sequential row-major placement is the control.',phonetics:'The same WikiPron entries are projected through the PHOIBLE-derived 3×3, 4×4 and 5×5 phonetic space.',controls:'For every language and layer: compare magic placement with sequential placement; randomize magic-square cell assignment; randomize alphabet order; and randomize magic values for phonetic-locality cost.',powersOf3:'On 4×4, Dürer value n maps to exponent n−1 in 3^(n−1); exponent-step locality is tested against randomized cell assignments.',combined:'Per-layer standardized signals combine magic-vs-random mapping, real-vs-shuffled alphabet order, and phonetic magic locality. 3–4–5 z weights the 4×4 bridge twice. Group q-values use Benjamini–Hochberg correction and are exploratory.'},settings:{permutations,maxWords,concurrency},counts:{languagesRequested:metas.length,languagesTested:results.length,failures:failures.length},global:{z:globalZ,p:1-normalCdf(globalZ)},languages:results,groups,failures};
}
