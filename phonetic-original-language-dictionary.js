(()=>{
'use strict';
const PHONE={A1:'i',A2:'a',A3:'u',A4:'ɑ',B1:'m',B2:'n',B3:'ŋ',B4:'r',C1:'f',C2:'s',C3:'x',C4:'h',D1:'p',D2:'t',D3:'k',D4:'ʔ'};
const WORDS=[
 {meaning:'water',path:['B1','A3','D2','B2'],ipa:'mutn',display:'mutn',basis:'cross-family medoid path',forms:['PIE *wódr̥','Proto-Semitic *māy-','Proto-Austronesian *daNum','Proto-Uralic *wete','Proto-Dravidian *nīr']},
 {meaning:'mother',path:['A1','B2','A2'],ipa:'ina',display:'ina',basis:'cross-family medoid path',forms:['PIE *méh₂tēr','Proto-Semitic *ʔimm-','Proto-Austronesian *ina','Proto-Uralic *emä','Proto-Dravidian *taḷḷay']},
 {meaning:'fire',path:['D2','A1','B3','A2','B1'],ipa:'tiŋam',display:'tiŋam',basis:'cross-family medoid path',forms:['PIE *péh₂wr̥','Proto-Semitic *ʔiš-','Proto-Austronesian *Sapuy','Proto-Uralic *tule','Proto-Dravidian *tiyam']},
 {meaning:'star',path:['D2','A2','C2','D2','A2'],ipa:'tasta',display:'tasta',basis:'cross-family medoid path',forms:['PIE *h₂stḗr','Proto-Semitic *kabkab-','Proto-Austronesian *bituqən','Proto-Uralic/Finno-Volgaic *täštä','Proto-Dravidian *miHn']}
];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const style=document.createElement('style');style.textContent=`
#originalLanguageDictionary{margin-top:18px}.oldict-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.oldict-card{background:#0d1119;border:1px solid var(--line);border-radius:12px;padding:14px}.oldict-word{font:700 1.55rem Georgia,serif;color:var(--cyan)}.oldict-meaning{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:.72rem}.oldict-path{font-family:ui-monospace,monospace;font-size:.85rem;margin:8px 0}.oldict-actions{display:flex;gap:8px;flex-wrap:wrap}.oldict-compare{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}.oldict-compare>div{border:1px solid var(--line);border-radius:10px;padding:12px;background:#0d1119}.oldict-num{font:700 1.35rem Georgia,serif;color:var(--cyan)}.oldict-table{width:100%;border-collapse:collapse}.oldict-table th,.oldict-table td{padding:8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.oldict-badge{display:inline-block;padding:3px 7px;border:1px solid var(--line);border-radius:999px;font-size:.72rem;color:var(--muted);margin:2px}.oldict-warning{border-left:3px solid #d4a72c;padding:10px 12px;background:#16130a;border-radius:6px}.oldict-ok{color:#8bd49c}.oldict-low{color:#e0b36b}@media(max-width:800px){.oldict-grid,.oldict-compare{grid-template-columns:1fr}}
`;document.head.appendChild(style);

function wait(){const host=document.querySelector('#protoBody');if(!host){setTimeout(wait,120);return;}Promise.all([
 fetch('data/phonetic-proto-reconstruction.json?v=20260910-dict1',{cache:'no-store'}).then(r=>r.json()),
 fetch('data/phonetic-extended-operator-classes.json?v=20260910-dict1',{cache:'no-store'}).then(r=>r.json())
]).then(([root,ext])=>build(host,root,ext)).catch(()=>build(host,null,null));}

function gates(path){const out=[];for(let i=0;i<path.length-1;i++)out.push(path[i]+'→'+path[i+1]);return out;}
function build(host,root,ext){if(document.querySelector('#originalLanguageDictionary'))return;
 const top=new Set((root?.refined_roots?.family_balanced?.top_gates||root?.latent_root?.top_gates||[]).map(g=>g.gate));
 let allG=[];WORDS.forEach(w=>allG.push(...gates(w.path)));const hit=allG.filter(g=>top.has(g)).length;const hitRate=allG.length?hit/allG.length:0;
 const cells=new Set(WORDS.flatMap(w=>w.path));const rootEff=root?.latent_root?.effective_gates;
 const p=ext?.summary||{};
 const sec=document.createElement('section');sec.id='originalLanguageDictionary';sec.className='protoCard';sec.innerHTML=`
 <h3>Candidate Original Language — reconstructed dictionary</h3>
 <p>This section turns the lexical tests into an actual reconstruction. For each meaning currently supported by the five-family comparison corpus, the candidate ancestral path is rendered through the same 16-state phonetic bridge already used by the page. The spoken form is therefore a <b>model reconstruction</b>, not a claim that we possess a recording or historically attested spelling.</p>
 <div class="oldict-warning"><b>Current dictionary size: ${WORDS.length} evidence-backed entries.</b> The cross-family source corpus presently contains only water, mother, fire and star. I have not invented unsupported extra vocabulary to make the dictionary look larger.</div>
 <div class="oldict-compare">
  <div><div class="oldict-num">${WORDS.length}</div><b>reconstructed lexical entries</b><br><span class="small">all concepts currently present in the cross-family proto-form test</span></div>
  <div><div class="oldict-num">${cells.size}/16</div><b>bridge states used</b><br><span class="small">dictionary coverage of the existing original-language phonetic state space</span></div>
  <div><div class="oldict-num">${Math.round(hitRate*100)}%</div><b>top-root gate overlap</b><br><span class="small">dictionary transitions that are also among the latent root's strongest recorded gates</span></div>
 </div>
 <div class="oldict-grid">${WORDS.map((w,i)=>card(w,i,top)).join('')}</div>
 <h4 style="margin-top:18px">Dictionary ↔ original-language phonetics comparison</h4>
 <table class="oldict-table"><thead><tr><th>Word</th><th>Bridge path</th><th>Strong-root gate matches</th><th>Interpretation</th></tr></thead><tbody>${WORDS.map(w=>{
   const gs=gates(w.path), hs=gs.filter(g=>top.has(g)); const q=gs.length?hs.length/gs.length:0;return `<tr><td><b>/${esc(w.display)}/</b><br>${esc(w.meaning)}</td><td>${w.path.join(' → ')}</td><td>${hs.length}/${gs.length}${hs.length?`<br><span class="small">${hs.map(esc).join(', ')}</span>`:''}</td><td class="${q>=.5?'oldict-ok':'oldict-low'}">${q>=.5?'strong local agreement':'partial/local agreement'} with the broad latent-root motif</td></tr>`}).join('')}</tbody></table>
 <p class="small">The older phonetic reconstruction on this page is a population-level 256-gate distribution across hundreds of languages; this dictionary is lexical and concept-specific. Agreement means a reconstructed word travels through transitions that are common in that broad root. Disagreement is not automatically failure: a real vocabulary cannot consist only of the most frequent transitions.</p>
 <details><summary>How these four words were formed</summary><p>The word paths are the cross-family medoid paths already computed from five independently reconstructed family-level forms. The new lexical-operator experiment then showed that metathesis/acrophonic/clipping-resegmentation classes generalize better than the earlier global mirror operators: held-out score <b>${Number(p.heldout_operator_bank_score||0).toFixed(3)}</b> versus shuffled <b>${Number(p.permutation_mean||0).toFixed(3)}</b>, p=${Number(p.p_ge_observed||0).toFixed(4)}. The displayed pronunciation maps each bridge state to the same representative phone used by the page's original playable root: A1=i, A2=a, A3=u, B1=m, B2=n, B3=ŋ, C2=s, D2=t, etc.</p><p><b>Important:</b> these are candidate latent proto-forms under this experimental model. They are not established Proto-World reconstructions.</p></details>
 `;
 const sound=document.querySelector('#protoSound');(sound||host).insertAdjacentElement('afterend',sec);
 sec.querySelectorAll('[data-play]').forEach(b=>b.onclick=()=>play(WORDS[+b.dataset.play].path,1));
 sec.querySelectorAll('[data-slow]').forEach(b=>b.onclick=()=>play(WORDS[+b.dataset.slow].path,1.65));
}
function card(w,i,top){const gs=gates(w.path),hs=gs.filter(g=>top.has(g));return `<article class="oldict-card"><div class="oldict-meaning">${esc(w.meaning)}</div><div class="oldict-word">/${esc(w.display)}/</div><div class="oldict-path">${w.path.join(' → ')}</div><div class="oldict-actions"><button class="btn" data-play="${i}">▶ Hear word</button><button class="btn" data-slow="${i}">▶ Slow</button></div><p class="small">Representative phones: /${w.path.map(c=>PHONE[c]).join(' ')}/ · ${esc(w.basis)}</p><details><summary>Evidence trail</summary>${w.forms.map(x=>`<span class="oldict-badge">${esc(x)}</span>`).join('')}<p class="small">Strong-root gate hits: ${hs.length}/${gs.length}${hs.length?' · '+hs.join(', '):''}</p></details></article>`;}

let active=[];function stop(){for(const x of active.splice(0)){try{x.close?.();x.stop?.()}catch(_){}}}
function play(seq,tempo){stop();const AC=window.AudioContext||window.webkitAudioContext;if(!AC){alert('Web Audio is not available in this browser.');return}const ctx=new AC();active.push(ctx);let t=ctx.currentTime+.05;for(const c of seq)t+=synth(ctx,c,t,.22*tempo);setTimeout(()=>{try{ctx.close()}catch(_){}},Math.ceil((t-ctx.currentTime+1)*1000));}
function env(ctx,t,d,l=.1){const g=ctx.createGain();g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(l,t+.015);g.gain.exponentialRampToValueAtTime(.0001,t+d);return g;}
function noise(ctx){const b=ctx.createBuffer(1,Math.floor(ctx.sampleRate*.24),ctx.sampleRate),a=b.getChannelData(0);for(let i=0;i<a.length;i++)a[i]=Math.random()*2-1;return b;}
function synth(ctx,c,t,d){if(c[0]==='A'){const fs={A1:[300,2300],A2:[800,1700],A3:[350,900],A4:[750,1100]}[c];const out=env(ctx,t,d,.08);out.connect(ctx.destination);for(const f of fs){const o=ctx.createOscillator(),bp=ctx.createBiquadFilter();o.type='sawtooth';o.frequency.value=120;bp.type='bandpass';bp.frequency.value=f;bp.Q.value=7;o.connect(bp);bp.connect(out);o.start(t);o.stop(t+d)}return d+.03}
 if(c[0]==='B'){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=env(ctx,t,d,.07);o.type='sawtooth';o.frequency.value=({B1:120,B2:145,B3:110,B4:165}[c]||130);lp.type='lowpass';lp.frequency.value=c==='B4'?1800:900;o.connect(lp);lp.connect(g);g.connect(ctx.destination);o.start(t);o.stop(t+d);return d+.03}
 if(c[0]==='C'){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=env(ctx,t,d,.07);s.buffer=noise(ctx);bp.type='bandpass';bp.frequency.value=({C1:1100,C2:5200,C3:1800,C4:900}[c]||2500);bp.Q.value=2.4;s.connect(bp);bp.connect(g);g.connect(ctx.destination);s.start(t);s.stop(t+d);return d+.03}
 const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=noise(ctx);bp.type='bandpass';bp.frequency.value=({D1:700,D2:2500,D3:1300,D4:500}[c]||1200);bp.Q.value=1.2;g.gain.setValueAtTime(.11,t);g.gain.exponentialRampToValueAtTime(.0001,t+.055);s.connect(bp);bp.connect(g);g.connect(ctx.destination);s.start(t);s.stop(t+.06);return .13;}
wait();
})();