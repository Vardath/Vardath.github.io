(()=>{
'use strict';
const GREEN='goodtxt', ORANGE='warntxt', RED='badtxt';
function ensureRed(){if(document.getElementById('validation-status-style'))return;const s=document.createElement('style');s.id='validation-status-style';s.textContent='.badtxt{color:var(--bad,#ff9292)} .validation-detail{font-size:.8rem;color:var(--muted,#aab1c5);display:block;margin-top:3px}';document.head.appendChild(s);}
function findRow(table,start){return [...table.rows].find(r=>(r.cells?.[0]?.textContent||'').trim().startsWith(start));}
function fmt(x,n=3){return Number.isFinite(+x)?(+x).toFixed(n):'—';}
async function apply(){
 const sec=document.getElementById('status'); const table=sec?.querySelector('table.compare'); if(!table)return false;
 ensureRed();
 let d;try{const r=await fetch('data/phonetic-validation-results.json?v=20260905-validation1',{cache:'no-store'});if(!r.ok)return false;d=await r.json();}catch(_){return false;}
 const a=d.tests?.sixteen_cell_optimality,b=d.tests?.lexical_vs_speech,c=d.tests?.magic_powers3;
 const r16=findRow(table,'The 16-cell compression is globally optimal.');
 if(r16&&a){r16.cells[1].className=ORANGE;r16.cells[1].innerHTML='Tested — trade-off, not established<span class="validation-detail">3×3 coverage '+fmt(a.results?.['3']?.coverage*100,1)+'% · 4×4 '+fmt(a.results?.['4']?.coverage*100,1)+'% · 5×5 '+fmt(a.results?.['5']?.coverage*100,1)+'%</span>';r16.cells[0].title=a.conclusion||'';}
 const rs=findRow(table,'WikiPron lexical transitions equal continuous connected-speech articulation.');
 if(rs&&b){rs.cells[1].className=RED;rs.cells[1].innerHTML='Tested — current speech control failed<span class="validation-detail">Pearson '+fmt(b.metrics?.pearson_gate_frequency)+' · cosine '+fmt(b.metrics?.cosine_gate_frequency)+' · JSD '+fmt(b.metrics?.jensen_shannon_divergence)+'</span>';rs.cells[0].title=b.conclusion||'';}
 const rm=findRow(table,'The magic-square/powers-of-3 ordering has a phonetic relationship beyond chance.');
 if(rm&&c){rm.cells[1].className=RED;rm.cells[1].innerHTML='Tested — not beyond chance in current controls<span class="validation-detail">path p='+fmt(c.centroid_path?.one_sided_p,4)+' · gate-order p='+fmt(c.gate_prevalence?.one_sided_p,4)+'</span>';rm.cells[0].title=c.conclusion||'';}
 const old=[...sec.querySelectorAll('.notice')].find(x=>x.textContent.includes('Why some rows remain orange'));
 if(old)old.innerHTML='<b>Controlled validation completed:</b> the 4×4 remains a useful middle-resolution trade-off but is not established as globally optimal. The current English aligned-speech comparison did not validate lexical transitions as equivalent to connected speech. The Dürer/powers-of-3 ordering did not beat the controlled chance tests. Negative results are retained because the experiment is allowed to fail.';
 return true;
}
function boot(){apply().then(ok=>{if(ok)return;const o=new MutationObserver(()=>apply().then(x=>{if(x)o.disconnect();}));o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>o.disconnect(),12000);});}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot):boot();
})();
