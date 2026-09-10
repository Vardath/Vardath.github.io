(()=>{
'use strict';
const DATA='data/original-language-nearest-current.json';
const fmt=x=>(x*100).toFixed(2)+'%';
let tries=0;
function fixLayout(dict){
  dict.style.gridColumn='1 / -1';
  dict.style.width='100%';
  dict.style.minWidth='0';
  const parent=dict.parentElement;
  if(parent&&getComputedStyle(parent).display.includes('grid')) dict.style.gridColumn='1 / -1';
}
async function render(){
  if(document.getElementById('nearest-current-language')) return;
  const dict=document.getElementById('originalLanguageDictionary');
  if(!dict){ if(tries++<300) setTimeout(render,100); return; }
  fixLayout(dict);
  try{
    const r=await fetch(DATA+'?v=20260910-nearest3',{cache:'no-store'}); if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json(), rows=(d.ranking||[]).slice(0,10); if(!rows.length) return;
    const winner=rows[0], box=document.createElement('div'); box.id='nearest-current-language'; box.className='oldict-method'; box.style.cssText='margin:16px 0 18px;border:3px solid var(--cyan);background:#101923;scroll-margin-top:18px';
    box.innerHTML=`<div class="oldict-kicker">RESULT · 20-SHARD CURRENT-LANGUAGE COMPARISON</div><h3 style="font-size:1.9rem;margin:.2em 0">Closest current-day language: <span style="color:var(--cyan)">${winner.name}</span></h3><p><b>${fmt(winner.mean_score)}</b> mean model similarity · median rank <b>#${winner.median_rank}</b> · <b>${winner.top1_shards}/${d.shards}</b> shard wins · top five in <b>${winner.top5_shards}/${d.shards}</b>.</p><p class="small">The completed ${Number(d.dictionary_entries).toLocaleString()}-entry reconstruction was divided into ${d.shards} independent 600-word shards and compared with the canonical attested-language profiles in the same 256 directed A1–D4 gate space. Occitan won 16 shards; Spanish won the other four.</p><div style="overflow-x:auto"><table class="compare"><thead><tr><th>#</th><th>Language</th><th>Family</th><th>Similarity</th><th>Mean rank</th><th>Wins</th><th>Top 5</th></tr></thead><tbody>${rows.map((x,i)=>`<tr><td><b>${i+1}</b></td><td>${x.name}</td><td>${x.family||'Unclassified'}</td><td>${fmt(x.mean_score)}</td><td>${Number(x.mean_rank).toFixed(2)}</td><td>${x.top1_shards}/${d.shards}</td><td>${x.top5_shards}/${d.shards}</td></tr>`).join('')}</tbody></table></div><div class="oldict-warning"><b>Interpretation:</b> this is phonetic / bridge-gate similarity, not a claim that Occitan is ${fmt(winner.mean_score)} genetically descended from the reconstruction. The stability result is that Occitan ranked first in 16/20 independent shards and top-five in all 20.</div><p class="small">Metrics: cosine similarity, Jensen–Shannon divergence and top-32 gate overlap. <a href="${DATA}">Full machine-readable result</a> · <a href="https://github.com/Vardath/Vardath.github.io/actions/runs/34440026051">GitHub Actions run #34440026051</a></p>`;
    const head=dict.querySelector('.oldict-head');
    if(head&&head.nextSibling) dict.insertBefore(box,head.nextSibling); else dict.prepend(box);
    const nav=document.querySelector('.nav'); if(nav&&!nav.querySelector('a[href="#nearest-current-language"]')){const a=document.createElement('a');a.href='#nearest-current-language';a.textContent='Closest language result';nav.appendChild(a);}
    if(location.hash==='#nearest-current-language') setTimeout(()=>box.scrollIntoView({block:'start'}),50);
  }catch(e){console.warn('Nearest-current-language results unavailable',e);}
}
render();
})();
