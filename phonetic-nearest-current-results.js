(()=>{
'use strict';
const DATA='data/original-language-nearest-current.json';
const fmt=x=>(x*100).toFixed(2)+'%';
async function render(){
  try{
    const r=await fetch(DATA+'?v=20260910-nearest1',{cache:'no-store'}); if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json(), rows=(d.ranking||[]).slice(0,10); if(!rows.length) return;
    const winner=rows[0];
    const sec=document.createElement('section'); sec.className='section wrap'; sec.id='nearest-current-language';
    sec.innerHTML=`
      <h2>Closest current-day language to the reconstructed original language</h2>
      <p class="lead">We tested the completed ${Number(d.dictionary_entries||12000).toLocaleString()}-entry reconstructed candidate language against the canonical attested-language phonetic profiles. The reconstruction was split into ${d.shards||20} independent shards so the result had to remain stable across different portions of the dictionary rather than winning only as one aggregate.</p>
      <div class="panel" style="margin:18px 0">
        <div class="eyebrow">20-shard result</div>
        <h3 style="font-size:2rem;margin:.2em 0">${winner.name}</h3>
        <p><b>${fmt(winner.mean_score)}</b> mean model similarity · median rank <b>#${winner.median_rank}</b> · won <b>${winner.top1_shards}/${d.shards}</b> shards · top five in <b>${winner.top5_shards}/${d.shards}</b>.</p>
        <p class="small">This is a phonetic / 4×4 directed-gate similarity result. It does not mean ${winner.name} is ${fmt(winner.mean_score)} genetically descended from the reconstruction, nor does it establish historical identity.</p>
      </div>
      <div style="overflow-x:auto"><table class="compare"><thead><tr><th>Rank</th><th>Language</th><th>Family</th><th>Mean similarity</th><th>Mean shard rank</th><th>Shard wins</th><th>Top 5</th></tr></thead><tbody>${rows.map((x,i)=>`<tr><td><b>${i+1}</b></td><td>${x.name}</td><td>${x.family||'Unclassified'}</td><td>${fmt(x.mean_score)}</td><td>${Number(x.mean_rank).toFixed(2)}</td><td>${x.top1_shards}/${d.shards}</td><td>${x.top5_shards}/${d.shards}</td></tr>`).join('')}</tbody></table></div>
      <div class="notice"><b>What stands out:</b> Occitan won 16 of 20 independent shards; Spanish won the remaining four. Occitan never fell outside the top five. A Romance cluster occupies much of the top ranking, while Indonesian and Turkish also place highly, showing the metric is not restricted to one language family.</div>
      <p class="small"><b>Test:</b> each shard builds the reconstruction's 256 directed A1–D4 gate distribution and compares it with the attested canonical language profiles using cosine similarity, Jensen–Shannon divergence and top-32 gate overlap. The final ordering rewards both similarity and stability across all 20 shards. Full machine-readable result: <a href="${DATA}">original-language-nearest-current.json</a>. <a href="https://github.com/Vardath/Vardath.github.io/actions/runs/34440026051">GitHub Actions run #34440026051</a>.</p>`;
    const dict=document.getElementById('originalLanguageDictionary');
    const anchor=dict?.closest('section')||document.querySelector('#status')||document.querySelector('main')?.lastElementChild;
    if(anchor?.parentNode) anchor.parentNode.insertBefore(sec,anchor); else document.querySelector('main')?.appendChild(sec);
  }catch(e){ console.warn('Nearest-current-language results unavailable',e); }
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',render,{once:true}); else render();
})();
