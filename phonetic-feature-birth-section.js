// Human-facing explanation of the completed 20-fold phonetic feature-birth test.
// Presentation only: reads frozen result JSON and does not alter any classifier/test maths.
(()=>{
'use strict';
if(window.__VARDATH_FEATURE_BIRTH_SECTION__)return;
window.__VARDATH_FEATURE_BIRTH_SECTION__=true;
const DATA='data/phonetic-feature-birth-v1-summary.json';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
const labels={
 short:'short duration',long:'long duration',delayedRelease:'delayed release',approximant:'approximant',tap:'tap',trill:'trill',nasal:'nasal',lateral:'lateral',round:'rounding',labiodental:'labiodental',anterior:'anteriority',distributed:'distributed articulation',strident:'strident',tense:'tenseness',retractedTongueRoot:'retracted tongue root',advancedTongueRoot:'advanced tongue root',periodicGlottalSource:'periodic glottal source',epilaryngealSource:'epilaryngeal source',spreadGlottis:'spread glottis',constrictedGlottis:'constricted glottis',fortis:'fortis',raisedLarynxEjective:'raised-larynx / ejective',loweredLarynxImplosive:'lowered-larynx / implosive',click:'click'
};
const phase={
 3:'Broad source, tongue-root and laryngeal organisation',
 4:'Major manner distinctions',
 5:'Release timing and finer articulation',
 6:'Glottal constriction',
 8:'Duration refinement',
 11:'Lip detail',
 12:'Nasal refinement',
 15:'Implosive / lowered-larynx detail',
 18:'Tension and epilaryngeal detail',
 21:'Spread-glottis detail'
};
function styles(){
 if(document.getElementById('featureBirthStyles'))return;
 const s=document.createElement('style');s.id='featureBirthStyles';s.textContent=`
 #feature-birth .fb-intro{padding:19px;border:1px solid #355066;border-radius:15px;background:linear-gradient(180deg,#111925,#0d131d);margin:17px 0}
 #feature-birth .fb-defs{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:17px 0}#feature-birth .fb-def{padding:14px;border:1px solid #30384d;border-radius:12px;background:#10151e}#feature-birth .fb-def b{display:block;color:#5ce1e6;margin-bottom:5px}
 #feature-birth .fb-ladder{display:grid;grid-template-columns:repeat(19,minmax(105px,1fr));gap:8px;overflow-x:auto;padding:8px 1px 17px;scrollbar-width:thin}
 #feature-birth .fb-step{min-height:155px;padding:10px;border:1px solid #30384d;border-radius:11px;background:linear-gradient(180deg,#171c29,#10141d);position:relative}#feature-birth .fb-step.active{border-color:#4d6579}#feature-birth .fb-step strong{display:block;font-size:1rem;color:#eef1f8}#feature-birth .fb-step .phase{display:block;color:#5ce1e6;font-size:.72rem;line-height:1.25;margin:4px 0 8px}#feature-birth .fb-chip{display:inline-block;border:1px solid #3a4358;background:#0d121a;border-radius:999px;padding:3px 6px;margin:2px 2px 0 0;font-size:.69rem;color:#cbd3e5}#feature-birth .fb-none{font-size:.72rem;color:#778098;margin-top:9px}
 #feature-birth .fb-arc{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}#feature-birth .fb-arc>div{padding:14px;border:1px solid #30384d;border-radius:12px;background:#10141d}#feature-birth .fb-arc b{display:block;color:#5ce1e6;margin-bottom:5px}
 #feature-birth .fb-tablewrap{overflow:auto;border:1px solid #30384d;border-radius:12px;margin:15px 0}#feature-birth table{width:100%;border-collapse:collapse;min-width:760px}#feature-birth th,#feature-birth td{padding:9px 10px;border-bottom:1px solid #293044;text-align:left;font-size:.85rem}#feature-birth th{background:#10151e;color:#aab1c5;position:sticky;top:0}#feature-birth td.num{text-align:right;font-family:Consolas,monospace}#feature-birth tr:last-child td{border-bottom:0}
 #feature-birth .fb-strength{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:16px 0}#feature-birth .fb-card{border:1px solid #30384d;border-radius:12px;padding:14px;background:#10141d}#feature-birth .fb-card h4{margin:0 0 8px}#feature-birth .fb-barrow{display:grid;grid-template-columns:150px 1fr 70px;gap:8px;align-items:center;margin:7px 0;font-size:.8rem}#feature-birth .fb-bar{height:10px;border-radius:999px;background:#171e2a;overflow:hidden;border:1px solid #2c3448}#feature-birth .fb-fill{height:100%;background:#5ce1e6}#feature-birth .fb-warn{border-left:4px solid #ffd37a;padding:14px 16px;background:#18150e;border-radius:8px;margin:18px 0}#feature-birth .fb-good{border-left:4px solid #80e7a8;padding:14px 16px;background:#0f1716;border-radius:8px;margin:18px 0}
 @media(max-width:820px){#feature-birth .fb-defs,#feature-birth .fb-strength,#feature-birth .fb-arc{grid-template-columns:1fr}#feature-birth .fb-barrow{grid-template-columns:120px 1fr 58px}}
 `;document.head.appendChild(s);
}
function bars(items){
 const mx=Math.max(...items.map(x=>x[1]),.001);
 return items.map(([name,val])=>`<div class="fb-barrow"><span>${esc(labels[name]||name)}</span><div class="fb-bar"><div class="fb-fill" style="width:${Math.max(2,100*val/mx)}%"></div></div><span>${Number(val).toFixed(4)}</span></div>`).join('');
}
function addStatusRows(){
 const table=document.querySelector('#status table.compare');if(!table)return false;const body=table.tBodies[0]||table;if(document.getElementById('feature-birth-status-row'))return true;
 const add=(id,a,b,cls,title)=>{const tr=document.createElement('tr');tr.id=id;const x=document.createElement('td'),y=document.createElement('td');x.textContent=a;y.textContent=b;y.className=cls;y.title=title;tr.append(x,y);body.appendChild(tr)};
 add('feature-birth-status-row','Successive square resolutions reveal reproducible held-out phonetic distinctions at different scales.','Supported in 20-fold feature-birth test','goodtxt','All 24 target features were withheld from grid construction. Most acquire significant predictive information at one or more successive resolutions versus coordinate-shuffled controls.');
 add('feature-birth-history-row','A feature “born” at a grid means the feature historically or biologically originated at that stage.','No — not established','warntxt','Birth is an operational codec term: first or strongest resolvability in this square hierarchy. It is not a claim about the chronological invention of human speech features.');
 return true;
}
function render(d){
 if(document.getElementById('feature-birth'))return true;const anchor=document.getElementById('square-sequence');if(!anchor)return false;styles();
 const peaks=d.feature_births_by_peak_resolution||{};
 const ladder=Array.from({length:19},(_,i)=>i+3).map(n=>{const fs=peaks[String(n)]||[];return `<div class="fb-step ${fs.length?'active':''}"><strong>${n}×${n}</strong>${phase[n]?`<span class="phase">${esc(phase[n])}</span>`:''}${fs.length?fs.map(f=>`<span class="fb-chip">${esc(labels[f]||f)}</span>`).join(''):`<div class="fb-none">No tested feature has its strongest birth here.</div>`}</div>`}).join('');
 const rows=Object.entries(d.features||{}).map(([f,x])=>({f,...x})).sort((a,b)=>(a.peak??99)-(b.peak??99)||String(a.f).localeCompare(String(b.f)));
 const table=rows.map(x=>`<tr><td>${esc(labels[x.f]||x.f)}</td><td>${x.onset??'—'}</td><td>${x.peak??'—'}</td><td class="num">${x.peak_adjusted_gain==null?'—':Number(x.peak_adjusted_gain).toFixed(5)}</td><td class="num">${x.peak_fold_wins==null?'—':x.peak_fold_wins+'/20'}</td><td class="num">${x.peak_sign_p==null?'—':Number(x.peak_sign_p).toPrecision(3)}</td></tr>`).join('');
 const strongest=rows.filter(x=>x.peak_adjusted_gain!=null).sort((a,b)=>b.peak_adjusted_gain-a.peak_adjusted_gain).slice(0,8).map(x=>[x.f,x.peak_adjusted_gain]);
 const cat=Object.entries(d.category_peaks||{}).map(([k,x])=>[k,x.peak_adjusted_gain]).sort((a,b)=>b[1]-a[1]);
 const sec=document.createElement('section');sec.className='section wrap';sec.id='feature-birth';sec.innerHTML=`
 <div class="eyebrow">20-fold follow-up · feature birth test</div>
 <h2>What phonetic information is born at each successive grid?</h2>
 <p class="lead">Once the 3×3→21×21 ladder was shown to behave like a real coarse-to-fine phonetic hierarchy, the next question was whether different resolutions reveal <em>different kinds</em> of phonetic information. We tested that directly instead of assigning meanings to the grids by hand.</p>
 <div class="fb-intro"><h3 style="margin-top:0">What “born” means here</h3><p>A feature is said to be <b>born at a resolution</b> when that grid makes the feature newly predictable from phonetic position, beyond the previous grid and beyond a coordinate-shuffled control. It means the codec can first or most strongly <b>resolve</b> that distinction there. It does <b>not</b> mean human speech historically invented that feature at that stage.</p></div>
 <div class="fb-defs"><div class="fb-def"><b>Onset</b>The first grid at which a held-out feature passes the preregistered support rule: positive real gain, positive null-adjusted gain, at least 15/20 fold wins and one-sided p&lt;0.05.</div><div class="fb-def"><b>Peak birth</b>The supported transition where that feature gains the most new predictive information. The timeline below uses peak birth because it best answers “what does this grid add most strongly?”</div></div>
 <h3>The empirical feature ladder</h3><div class="fb-ladder">${ladder}</div>
 <div class="fb-arc"><div><b>3×3 · broad foundations</b>Anteriority, tongue-root organisation, periodic glottal source, fortisness and clicks are already strongly separated at the coarsest tested candidate layer.</div><div><b>4×4–5×5 · manner and release</b>Approximant, tap, lateral, strident, shortness, delayed release, trill and distributed articulation receive their strongest gains here.</div><div><b>6×6–12×12 · specialised refinement</b>Glottal constriction, length, rounding, labiodental detail and nasal structure become most strongly resolved in this middle-fine region.</div><div><b>15×15–21×21 · rare/subtle laryngeal detail</b>Implosive/lowered-larynx, tenseness, epilaryngeal source and spread-glottis distinctions peak late in the sequence.</div></div>
 <div class="fb-good"><b>Important result:</b> the grids do not all perform the same phonetic job. The 3–4–5 sequence has a concrete empirical interpretation: 3×3 carries broad source/root organisation, 4×4 adds major manner structure, and 5×5 adds finer release and articulatory structure. Later grids continue into increasingly specialised detail.</div>
 <div class="fb-strength"><div class="fb-card"><h4>Strongest individual feature births</h4>${bars(strongest)}</div><div class="fb-card"><h4>Category-level peak gains</h4>${bars(cat)}</div></div>
 <h3>Every tested feature</h3><p class="small">All target features below were excluded from construction of the grid coordinates. “—” means the feature never passed the preregistered birth criterion between 3×3 and 21×21.</p><div class="fb-tablewrap"><table><thead><tr><th>Held-out feature</th><th>First onset</th><th>Peak grid</th><th>Null-adjusted gain</th><th>Fold wins</th><th>Sign p</th></tr></thead><tbody>${table}</tbody></table></div>
 <h3>What happens at 9×9?</h3><p>The 9×9 layer is a real refinement step, but <b>none of the 24 withheld features has its strongest birth at 9×9</b>. Several distinctions continue gaining information through that region, but the current evidence does not make 81 cells a unique culmination. This independently agrees with the earlier sequence test, which also found that refinement continues beyond 9×9.</p>
 <h3>Does refinement stop at 21×21?</h3><p>No. The test restricted feature-birth assignments to 3×3–21×21, but 22×22 and 23×23 were run as continuation controls. Overall held-out prediction error falls from <b>${Number(d.overall_mae['2x2']).toFixed(5)}</b> at 2×2 to <b>${Number(d.overall_mae['21x21']).toFixed(5)}</b> at 21×21 and <b>${Number(d.overall_mae['23x23_boundary']).toFixed(5)}</b> at the 23×23 boundary check. The shuffled-coordinate null stays nearly flat around 0.196–0.199.</p>
 <div class="fb-warn"><b>Research boundary:</b> these results support a multiresolution phonetic codec in which different scales resolve different feature families. They do not establish a chronological evolution of the human vocal tract, a biological mutation sequence, a unique ancient grid system, or a privileged endpoint at 9×9 or 21×21.</div>
 <details class="panel"><summary><b>How the test avoided circularity</b></summary><p>The 3,065 research segments were divided into 20 deterministic held-out folds. For each fold, cell means were learned from the other 19 folds and used to predict the untouched segments. Only 11 broad place/manner features defined the two-dimensional grid. The 24 features listed above were withheld from projection and placement. A deterministic coordinate-shuffled null kept the same phonetic records but broke their relationship to articulatory position. A feature birth had to beat that null and replicate across folds.</p><p>The permanent result is <code>data/phonetic-feature-birth-v1-summary.json</code>; the executable test is <code>tools/test_phonetic_feature_birth_v1.py</code>.</p></details>`;
 anchor.insertAdjacentElement('afterend',sec);
 const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#feature-birth"]')){const a=document.createElement('a');a.href='#feature-birth';a.textContent='Feature births';const sq=nav.querySelector('a[href="#square-sequence"]');if(sq)sq.insertAdjacentElement('afterend',a);else nav.appendChild(a)}
 addStatusRows();return true;
}
function boot(){fetch(DATA,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}).then(d=>{if(render(d))return;const o=new MutationObserver(()=>{if(render(d))o.disconnect()});o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>o.disconnect(),12000)}).catch(e=>console.error('Feature-birth section failed',e));}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();