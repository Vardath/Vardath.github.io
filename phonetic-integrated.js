const INTEGRATED_CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4'];
let BENCH=null;
const gi=id=>document.getElementById(id);
function ie(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]))}
function featureWords(p){return FEATURE_NAMES.filter(f=>fnum(p[f])>.25)}

// Canonical IPA reference recordings hosted by Wikimedia Commons.
// These are reference articulations, not claims about a particular language's allophonic realization.
const IPA_AUDIO_FILES={
  'p':'Voiceless bilabial plosive.ogg','b':'Voiced bilabial plosive.ogg','t':'Voiceless alveolar plosive.ogg','d':'Voiced alveolar plosive.ogg','k':'Voiceless velar plosive.ogg','g':'Voiced velar plosive.ogg','ɡ':'Voiced velar plosive.ogg',
  'm':'Bilabial nasal.ogg','n':'Alveolar nasal.ogg','ŋ':'Velar nasal.ogg','ɲ':'Palatal nasal.ogg',
  'f':'Voiceless labiodental fricative.ogg','v':'Voiced labiodental fricative.ogg','θ':'Voiceless dental fricative.ogg','ð':'Voiced dental fricative.ogg','s':'Voiceless alveolar sibilant.ogg','z':'Voiced alveolar sibilant.ogg','ʃ':'Voiceless postalveolar fricative.ogg','ʒ':'Voiced postalveolar fricative.ogg','x':'Voiceless velar fricative.ogg','ɣ':'Voiced velar fricative.ogg','h':'Voiceless glottal fricative.ogg',
  'l':'Alveolar lateral approximant.ogg','r':'Alveolar trill.ogg','ɹ':'Alveolar approximant.ogg','j':'Palatal approximant.ogg','w':'Voiced labio-velar approximant.ogg','ʔ':'Glottal stop.ogg',
  'i':'Close front unrounded vowel.ogg','y':'Close front rounded vowel.ogg','ɨ':'Close central unrounded vowel.ogg','ʉ':'Close central rounded vowel.ogg','ɯ':'Close back unrounded vowel.ogg','u':'Close back rounded vowel.ogg','ɪ':'Near-close near-front unrounded vowel.ogg','ʊ':'Near-close near-back rounded vowel.ogg',
  'e':'Close-mid front unrounded vowel.ogg','ø':'Close-mid front rounded vowel.ogg','ɘ':'Close-mid central unrounded vowel.ogg','ɵ':'Close-mid central rounded vowel.ogg','ɤ':'Close-mid back unrounded vowel.ogg','o':'Close-mid back rounded vowel.ogg','ə':'Mid-central vowel.ogg',
  'ɛ':'Open-mid front unrounded vowel.ogg','œ':'Open-mid front rounded vowel.ogg','ɜ':'Open-mid central unrounded vowel.ogg','ɞ':'Open-mid central rounded vowel.ogg','ʌ':'Open-mid back unrounded vowel.ogg','ɔ':'Open-mid back rounded vowel.ogg',
  'æ':'Near-open front unrounded vowel.ogg','ɐ':'Near-open central vowel.ogg','a':'Open front unrounded vowel.ogg','ɶ':'Open front rounded vowel.ogg','ɑ':'Open back unrounded vowel.ogg','ɒ':'Open back rounded vowel.ogg'
};
function audioReferenceFor(segment){
  const raw=String(segment||'').normalize('NFD');
  if(IPA_AUDIO_FILES[raw])return {symbol:raw,file:IPA_AUDIO_FILES[raw],exact:true};
  const stripped=raw.replace(/[\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\uFE20-\uFE2Fːˑʰʷʲˠˤʼ̥̬̩̯̚͜͡]/gu,'');
  const chars=Array.from(stripped);
  if(chars.length===1&&IPA_AUDIO_FILES[chars[0]])return {symbol:chars[0],file:IPA_AUDIO_FILES[chars[0]],exact:false};
  return null;
}
function commonsAudioUrl(file){return 'https://commons.wikimedia.org/wiki/Special:Redirect/file/'+encodeURIComponent(file)}
window.playIpaReference=function(symbol,button){
  const ref=audioReferenceFor(symbol);if(!ref)return;
  if(window.__ipaAudio){try{window.__ipaAudio.pause()}catch(_){}}
  const a=new Audio(commonsAudioUrl(ref.file));window.__ipaAudio=a;
  const old=button?.textContent;if(button)button.textContent='▶ playing';
  const reset=()=>{if(button)button.textContent=old||'🔊 hear'};
  a.addEventListener('ended',reset,{once:true});a.addEventListener('error',()=>{if(button){button.textContent='audio unavailable';button.disabled=true}},{once:true});
  a.play().catch(()=>{if(button){button.textContent='tap again';setTimeout(reset,1800)}});
};
function audioButton(segment){
  const ref=audioReferenceFor(segment);if(!ref)return '';
  const label=ref.exact?'hear':'reference /'+ref.symbol+'/';
  return `<button type="button" onclick="playIpaReference('${ie(String(segment).replace(/'/g,'&#39;'))}',this)" title="Wikimedia Commons IPA reference recording${ref.exact?'':' — base sound only'}" style="margin-left:7px;border:1px solid #3d455d;background:#0d1320;color:#eef1f8;border-radius:999px;padding:5px 9px;cursor:pointer;font-size:.76rem">🔊 ${ie(label)}</button>`;
}

function renderSoundCorrespondence(){
  if(!state?.loaded)return;
  const srcInv=gi('sourceInventory')?.value,tgtInv=gi('targetInventory')?.value;
  if(!srcInv||!tgtInv)return;
  const src=(state.inventorySegments.get(srcInv)||[]).map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY');
  const tgtIds=state.inventorySegments.get(tgtInv)||[];
  const sLang=state.languages.get(gi('sourceLanguage').value),tLang=state.languages.get(gi('targetLanguage').value);
  gi('corrTitle').textContent=`${sLang?.Name||'Source'} → ${tLang?.Name||'Target'}`;
  const rows=src.map(p=>{
    const r=nearest(p,tgtIds,false).ranked[0]; if(!r)return '';
    const q=r.p,sc=classify(p),tc=classify(q),shared=featureWords(p).filter(x=>featureWords(q).includes(x));
    const dif=r.parts.slice(0,6).map(x=>x[0]);
    let why=`Both sounds share ${shared.slice(0,6).join(', ')||'few strongly positive features'}. `;
    why+=sc===tc?`They occupy the same coarse bridge cell (${sc}), so their broad articulatory state agrees. `:`They occupy different bridge cells (${sc} → ${tc}), so this is a cross-cell fallback. `;
    if(dif.length)why+=`The largest remaining PHOIBLE differences are ${dif.join(', ')}.`;
    const kind=p.Name===q.Name?'exact IPA':(sc===tc?'same-cell':'fallback');
    return `<div class="corrrow"><div class="corrsound">/${ie(p.Name)}/${audioButton(p.Name)} <span>→</span> /${ie(q.Name)}/${audioButton(q.Name)}</div><div class="corrmeta"><span class="pill">${ie(sc)}</span><span class="pill">${ie(tc)}</span><span class="pill">distance ${r.distance.toFixed(4)}</span><span class="pill ${kind==='exact IPA'?'good':''}">${kind}</span></div><details><summary>Why this maps this way</summary><p>${ie(why)}</p><p class="small">🔊 Audio buttons use canonical IPA reference recordings from Wikimedia Commons. They demonstrate the reference articulation, not every accent or allophone of the selected language.</p></details></div>`;
  }).join('');
  gi('correspondenceGrid').innerHTML=rows||'<p class="small">No comparable non-prosodic sounds in these inventories.</p>';
}
function renderBenchmark(){
  if(!BENCH)return;
  const c=BENCH.counts,core=BENCH.core_thresholds['0.8']||[],strict=BENCH.core_thresholds['1.0']||[];
  gi('benchStatus').className='status ok';
  gi('benchStatus').innerHTML=`Complete benchmark · ${c.datasets_completed}/${c.wikipron_datasets_indexed} WikiPron datasets · ${c.canonical_languages} canonical languages · ${c.pairwise_comparisons.toLocaleString()} pairwise comparisons · ${c.datasets_failed} failures`;
  gi('benchStats').innerHTML=`<span><b>${c.canonical_languages}</b>languages</span><span><b>${core.length}</b>80% core gates</span><span><b>${strict.length}</b>100% strict core</span><span><b>${c.families_ge_3_languages}</b>families ≥3 languages</span>`;
  gi('benchCore').innerHTML=core.map(g=>`<span class="pill">${ie(g)}</span>`).join(' ')||'<span class="small">none</span>';
  let html='<div></div>'+INTEGRATED_CELLS.map(x=>`<div class="bmhead">${x}</div>`).join('');
  const by=new Map(BENCH.gate_prevalence.map(x=>[x.index,x]));
  for(let i=0;i<16;i++){html+=`<div class="bmhead">${INTEGRATED_CELLS[i]}</div>`;for(let j=0;j<16;j++){const g=by.get(i*16+j),p=g?.prevalence||0;html+=`<div class="bmcell" title="${ie(g?.gate||'')} · ${(p*100).toFixed(1)}% languages · power ratio 3^${g?.power_exponent_delta??0}" style="background:rgba(92,225,230,${(.06+.86*p).toFixed(3)})">${(p*100).toFixed(0)}%</div>`}};
  gi('benchmarkMatrix').innerHTML=html;
  const top=[...BENCH.power_delta_profile].sort((a,b)=>b.language_prevalence-a.language_prevalence||b.mass-a.mass).slice(0,12);
  gi('powerProfile').innerHTML=top.map(x=>`<div class="metric"><b>3^${x.delta}</b><span>${(x.language_prevalence*100).toFixed(1)}% of languages</span></div>`).join('');
}
async function loadBenchmark(){
  try{const r=await fetch('data/phonetic-benchmark-summary.json?v=2',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);BENCH=await r.json();renderBenchmark()}catch(e){gi('benchStatus').className='status error';gi('benchStatus').textContent='Benchmark results unavailable: '+e.message}
}
function wireIntegrated(){
  ['sourceLanguage','targetLanguage','sourceInventory','targetInventory'].forEach(id=>gi(id)?.addEventListener('change',()=>setTimeout(renderSoundCorrespondence,0)));
  const timer=setInterval(()=>{if(typeof state!=='undefined'&&state.loaded){clearInterval(timer);renderSoundCorrespondence()}},250);
  loadBenchmark();
}
document.addEventListener('DOMContentLoaded',wireIntegrated);
