import * as B from './phonetic-345-magic-core.mjs';

export * from './phonetic-345-magic-core.mjs';
export const VERSION_V2='20260906-345magic-full348-v3';

function makeTokenizer(alphabet,meta){
  const locale=B.localeFor(meta),idx=new Map(alphabet.map((x,i)=>[x,i])),multi=alphabet.filter(x=>[...x].length>1).sort((a,b)=>b.length-a.length);
  return word=>{
    const text=B.lowerLocale(String(word||'').normalize('NFC'),locale);
    if(!multi.length)return B.segmentGraphemes(text,locale);
    const out=[];let i=0;
    while(i<text.length){let hit=null;for(const t of multi){if(text.startsWith(t,i)){hit=t;break;}}
      if(hit){out.push(hit);i+=hit.length;continue}
      const cp=String.fromCodePoint(text.codePointAt(i));if(/\p{L}/u.test(cp))out.push(cp);i+=cp.length;
    }
    return out;
  };
}

// Sparse transition storage is essential for large ordered symbol inventories such as Han.
// The previous N×N dense matrix was safe for alphabets but could exhaust browser memory.
function pairCounts(words,alphabet,meta){
  const idx=new Map(alphabet.map((x,i)=>[x,i])),N=alphabet.length,out=new Map(),tokenize=makeTokenizer(alphabet,meta);
  let transitions=0,unknown=0;
  for(const w of words){
    const toks=tokenize(w);let prev=null;
    for(const raw of toks){const t=B.resolveAlphabetToken(raw,alphabet),cur=t&&idx.has(t)?idx.get(t):null;if(cur===null){unknown++;prev=null;continue}if(prev!==null){const k=prev*N+cur;out.set(k,(out.get(k)||0)+1);transitions++}prev=cur}
  }
  return{pairs:out,N,transitions,unknown};
}

function orthFromPairs(pairData,rankOverride,n,mode='magic',magic=B.MAGIC,magicCellOverride=null){
  const states=n*n,out=new Float64Array(states*states),N=pairData.N,rank=rankOverride||Array.from({length:N},(_,i)=>i);
  const cellOfValue=magicCellOverride||((v)=>mode==='magic'?B.valueToCell(n,v,magic):B.sequentialValueToCell(n,v));
  for(const [key,w] of pairData.pairs){
    const a=Math.floor(key/N),b=key-a*N,va=B.ordinalBucket(rank[a],N,n),vb=B.ordinalBucket(rank[b],N,n),ca=cellOfValue(va),cb=cellOfValue(vb);
    if(ca>=0&&cb>=0)out[ca*states+cb]+=w;
  }
  return out;
}

function permValueCell(_n,perm){return v=>perm[v-1]}

export function analyzeLayerFast({pairData,phoneMatrix,n,permutations=120,seed='',magic=B.MAGIC}){
  const seq=orthFromPairs(pairData,null,n,'sequential',magic),mag=orthFromPairs(pairData,null,n,'magic',magic);
  const simSeq=B.cosine(B.normalizeMatrix(seq),B.normalizeMatrix(phoneMatrix)),simMagic=B.cosine(B.normalizeMatrix(mag),B.normalizeMatrix(phoneMatrix)),gain=simMagic-simSeq;
  const rng=B.rngFor(`${VERSION_V2}:${seed}:n${n}`),states=n*n,magicNull=[],orderNull=[],localityNull=[],observedLocality=B.phoneticMagicCost(phoneMatrix,n,magic);
  for(let k=0;k<permutations;k++){
    const valuePerm=B.shuffled(states,rng),q=orthFromPairs(pairData,null,n,'magic',magic,permValueCell(n,valuePerm));
    magicNull.push(B.cosine(B.normalizeMatrix(q),B.normalizeMatrix(phoneMatrix)));
    const rankPerm=B.shuffled(pairData.N,rng),qo=orthFromPairs(pairData,rankPerm,n,'magic',magic);
    orderNull.push(B.cosine(B.normalizeMatrix(qo),B.normalizeMatrix(phoneMatrix)));
    const cellPerm=B.shuffled(states,rng);localityNull.push(B.phoneticMagicCost(phoneMatrix,n,magic,cellPerm));
  }
  const magicZ=B.zHigher(simMagic,magicNull),orderZ=B.zHigher(simMagic,orderNull),localityZ=B.zLower(observedLocality,localityNull),layerZ=(magicZ+orderZ+localityZ)/Math.sqrt(3);
  return{n,simSequential:simSeq,simMagic,magicGain:gain,magicZ,magicP:B.pFromHigher(simMagic,magicNull),alphabetOrderZ:orderZ,alphabetOrderP:B.pFromHigher(simMagic,orderNull),phoneticMagicCost:observedLocality,phoneticLocalityZ:localityZ,phoneticLocalityP:B.pFromLower(observedLocality,localityNull),layerZ,permutations};
}

export async function analyzeLanguageFast(meta,{params,fetchImpl=fetch,alphabetPresets={},permutations=120,maxWords=3000,magic=B.MAGIC}={}){
  const r=await fetchImpl(B.WP_BASE+meta.file);if(!r.ok)throw new Error(`${meta.file}: ${r.status}`);
  const raw=await r.text(),lines=B.sampleLinesDeterministic(raw,maxWords,meta.file),words=B.wordsFromLines(lines),preset=alphabetPresets[meta.iso]||null,a=B.deriveAlphabet(words,meta,preset);
  if(a.order.length<3)throw new Error('fewer than 3 ordered symbols');
  const pairs=pairCounts(words,a.order,meta),layers={};if(!pairs.transitions)throw new Error('no usable ordered-symbol transitions');
  for(const n of [3,4,5]){const ph=B.buildPhoneTransitions(lines,params,n);layers[n]=analyzeLayerFast({pairData:pairs,phoneMatrix:ph.matrix,n,permutations,seed:meta.iso,magic});layers[n].phoneCoverage=ph.mapped/(ph.mapped+ph.unknown||1);layers[n].phoneTransitions=ph.transitions}
  const z345=(layers[3].layerZ+2*layers[4].layerZ+layers[5].layerZ)/Math.sqrt(6),simMid=(layers[3].simMagic+layers[5].simMagic)/2,bridgeResidual=Math.abs(layers[4].simMagic-simMid),coherence=Math.max(0,1-Math.min(1,bridgeResidual/.20)),allPositive=[3,4,5].every(n=>layers[n].magicGain>0),fourPositive=layers[4].magicGain>0;
  let strength='none/anti-fit';if(z345>=2.58&&fourPositive&&coherence>=.5)strength='strong';else if(z345>=1.645&&fourPositive)strength='moderate';else if(z345>0)strength='weak';
  return{iso:meta.iso,name:meta.name,family:meta.family||'Unclassified',macroarea:meta.macroarea||'',script:meta.script||'',file:meta.file,alphabet:a.order,alphabetSize:a.order.length,alphabetSource:a.source,alphabetConfidence:a.confidence,wordSample:lines.length,alphabetTransitions:pairs.transitions,layers,z345,bridgeResidual,bridgeCoherence:coherence,allLayersPositive:allPositive,strength,power4:{description:'Dürer cell value n corresponds to 3^(n−1); locality uses absolute exponent-step distance.',meanExponentStep:layers[4].phoneticMagicCost,z:layers[4].phoneticLocalityZ,p:layers[4].phoneticLocalityP}};
}

export async function runExperimentFast({metas,topologyData=null,params=null,fetchImpl=fetch,alphabetPresets={},permutations=120,maxWords=3000,onProgress=null,concurrency=4,magic=B.MAGIC}={}){
  params=params||await B.loadPhoibleParameters(fetchImpl);const queue=[...metas],results=[],failures=[];let done=0;
  async function worker(){while(queue.length){const meta=queue.shift();try{results.push(await analyzeLanguageFast(meta,{params,fetchImpl,alphabetPresets,permutations,maxWords,magic}))}catch(e){failures.push({iso:meta.iso,name:meta.name,error:String(e?.message||e)})}done++;onProgress?.({done,total:metas.length,meta,results:results.length,failures:failures.length})}}
  await Promise.all(Array.from({length:Math.max(1,Math.min(concurrency,metas.length))},worker));results.sort((a,b)=>b.z345-a.z345);
  const groups={families:B.groupResults(results,B.familyMapping(results),'Glottolog family'),scripts:B.groupResults(results,B.scriptMapping(results),'Writing system'),topology:topologyData?B.groupResults(results,B.topologyMapping(topologyData),'Phonetic topology group'):[]},globalZ=results.length?results.reduce((s,x)=>s+x.z345,0)/Math.sqrt(results.length):0;
  return{version:VERSION_V2,pins:B.PINS,magicSquares:{3:B.MAGIC[3],4:B.MAGIC[4],5:B.MAGIC[5]},method:{coverage:'All canonical benchmark languages are attempted. Alphabetic scripts use curated intended order where available and otherwise an explicitly labelled inferred order. Non-alphabetic scripts are retained as labelled symbol-order sensitivity proxies rather than excluded.',mapping:'Ordered symbols receive ordinal numbers, normalized to 1..9, 1..16 and 1..25, then placed in the cell carrying that value in the corresponding magic square. Row-major sequential placement is the control.',phonetics:'The same WikiPron entries are independently projected through the PHOIBLE-derived 3×3, 4×4 and 5×5 phonetic space.',controls:'Each layer compares magic placement with sequential placement, random magic-cell assignment, shuffled symbol/alphabet order, and randomized phonetic magic locality.',powersOf3:'Magic value n maps to 3^(n−1). Locality uses exponent-step distance, exactly log₃ distance between powers.',combined:'Layer z combines magic mapping, intended symbol order, and phonetic magic locality. The combined 3–4–5 z weights the 4×4 bridge twice. Group q-values use Benjamini–Hochberg correction.'},settings:{permutations,maxWords,concurrency},counts:{languagesRequested:metas.length,languagesTested:results.length,failures:failures.length},global:{z:globalZ,p:1-B.normalCdf(globalZ)},languages:results,groups,failures};
}
