(()=>{
'use strict';
if(window.__VARDATH_MAN_GRID_REBUILD_V2__)return;
window.__VARDATH_MAN_GRID_REBUILD_V2__=true;
const PLAN='data/man-grid-rebuild-plan-v2.json?v=20260911-pass1';
const RESULTS={
  1:'data/man-grid-original-phonetics-v2.json?v=20260911-pass1',
  2:'data/man-grid-phonetic-locality-v2.json?v=20260911-pass1',
  3:'data/man-grid-sibling-split-v2.json?v=20260911-pass1'
};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
async function get(url){try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)return null;return await r.json();}catch{return null;}}
function css(){if(document.getElementById('mgr2styles'))return;const s=document.createElement('style');s.id='mgr2styles';s.textContent=`
#man-grid-rebuild-v2 .mgr2-correction{border:2px solid var(--bad);background:#241215;padding:18px;border-radius:12px;margin:18px 0}#man-grid-rebuild-v2 .mgr2-correction b{color:var(--bad)}
#man-grid-rebuild-v2 .mgr2-tests{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px}#man-grid-rebuild-v2 .mgr2-test{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:13px;padding:15px}#man-grid-rebuild-v2 .mgr2-test.running{border-color:#6b5c2a}#man-grid-rebuild-v2 .mgr2-test.done{border-color:#315749}#man-grid-rebuild-v2 .mgr2-test h3{margin:0 0 7px;font-size:1.05rem}#man-grid-rebuild-v2 .mgr2-meta{color:var(--cyan);font:12px/1.35 Consolas,monospace;margin-bottom:7px}#man-grid-rebuild-v2 .mgr2-result{margin-top:10px;padding-top:10px;border-top:1px solid var(--line);font-size:.9rem}#man-grid-rebuild-v2 .mgr2-phonemes{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}#man-grid-rebuild-v2 .mgr2-phonemes span{font-family:Georgia,serif;font-size:1.15rem;padding:4px 8px;border:1px solid var(--line);border-radius:8px;background:#0d1018}@media(max-width:800px){#man-grid-rebuild-v2 .mgr2-tests{grid-template-columns:1fr}}
`;document.head.appendChild(s);}
function resultHTML(id,r){if(!r)return `<div class="mgr2-result"><span class="warntxt">Pass queued/running — result file not published yet.</span></div>`;
 if(id===1){const p=r.original_phoneme_inventory||r.candidate_inventory||[];const shown=p.slice(0,80).map(x=>`<span title="${esc(x.root_cell||x.cell||'')}">${esc(x.ipa||x.segment||x.sound||'?')}</span>`).join('');return `<div class="mgr2-result"><b>Result published.</b> ${esc(r.summary?.families??r.families??'')} families · ${esc(r.summary?.candidate_phonemes??p.length)} reconstructed candidate sounds${shown?`<div class="mgr2-phonemes">${shown}</div>`:''}</div>`;}
 const v=r.verdict||r.summary||{};return `<div class="mgr2-result"><b>Result published.</b><pre style="white-space:pre-wrap;margin:8px 0 0;color:var(--muted);font-size:.78rem">${esc(JSON.stringify(v,null,2).slice(0,2600))}</pre></div>`;}
async function init(){css();const plan=await get(PLAN);if(!plan)return;let section=document.getElementById('man-grid-rebuild-v2');if(section)section.remove();section=document.createElement('section');section.id='man-grid-rebuild-v2';section.className='section wrap';
 const results=await Promise.all([get(RESULTS[1]),get(RESULTS[2]),get(RESULTS[3])]);const by={1:results[0],2:results[1],3:results[2]};
 const cards=plan.tests.map(t=>{const r=by[t.id]||null;const live=t.can_run_now;return `<article class="mgr2-test ${r?'done':(live?'running':'')}"><div class="mgr2-meta">TEST ${t.id} · ${esc(t.shards)} SHARDS · ${r?'RESULT PUBLISHED':(live?'PASS 1 / RUN NOW':'DEPENDENT')}</div><h3>${esc(t.name)}</h3><p class="small">${esc(t.purpose)}</p><div class="small"><b>Dependency:</b> ${esc(t.dependency)}</div>${t.id<=3?resultHTML(t.id,r):''}</article>`}).join('');
 section.innerHTML=`<div class="eyebrow">Exact Man Grid rebuild · V2</div><h2>Original phonetics and original-language reconstruction — corrected sequence</h2><p class="lead">The earlier research is retained below/elsewhere as a record. This appended V2 series rebuilds the phonetics and language from the exact computerized Man Grid before repeating the downstream tests.</p><div class="mgr2-correction"><b>Correction — ChatGPT implementation error:</b> ${esc(plan.correction)}</div><div class="notice"><b>Working hypothesis being tested, not assumed:</b> ${esc(plan.exact_grid.hypothesis)}</div><div class="mgr2-tests">${cards}</div>`;
 const grid=document.getElementById('manuscript-grid');if(grid?.parentNode)grid.parentNode.insertBefore(section,grid.nextSibling);else(document.querySelector('main')||document.body).appendChild(section);
 const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#man-grid-rebuild-v2"]')){const a=document.createElement('a');a.href='#man-grid-rebuild-v2';a.textContent='Exact-grid rebuild';nav.appendChild(a);}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,80),{once:true});else setTimeout(init,80);
})();
