// Transmission/contact hypothesis presentation layer. Additive only.
(function(){
  const $=id=>document.getElementById(id);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct=x=>x==null?'—':(100*Number(x)).toFixed(1)+'%';
  const num=x=>x==null?'—':Number(x).toFixed(3);

  function css(){
    if($('pttStyle'))return;const st=document.createElement('style');st.id='pttStyle';st.textContent=`
      .ptt-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.ptt-card{border:1px solid #30374c;border-radius:14px;background:linear-gradient(180deg,#181c2a,#121520);padding:16px}.ptt-card b.big{display:block;font-size:1.65rem;color:#5ce1e6}.ptt-help{display:inline-grid;place-items:center;width:18px;height:18px;border:1px solid #5ce1e6;border-radius:50%;color:#5ce1e6;font-size:.72rem;cursor:help;margin-left:4px}.ptt-badge{display:inline-block;border:1px solid #46506b;border-radius:999px;padding:4px 8px;font-size:.74rem;background:#10151f}.ptt-band{display:grid;grid-template-columns:1.6fr .6fr .7fr;gap:8px;padding:9px 0;border-bottom:1px solid #2c3346}.ptt-table{width:100%;border-collapse:collapse}.ptt-table th,.ptt-table td{padding:9px;border-bottom:1px solid #2d3549;text-align:left;font-size:.84rem}.ptt-table th{color:#aab1c5;font-size:.72rem;text-transform:uppercase}.ptt-good{color:#80e7a8}.ptt-warn{color:#ffd37a}.ptt-callout{border-left:4px solid #5ce1e6;background:#0e151d;border-radius:9px;padding:15px 17px;margin:14px 0}.ptt-method{color:#aab1c5;font-size:.86rem}.ptt-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}.ptt-metric{border:1px solid #30374c;border-radius:12px;padding:12px;background:#10151f}.ptt-metric b{display:block;color:#5ce1e6;font-size:1.25rem}@media(max-width:900px){.ptt-grid,.ptt-metrics{grid-template-columns:1fr 1fr}}@media(max-width:600px){.ptt-grid,.ptt-metrics{grid-template-columns:1fr}}
    `;document.head.appendChild(st);
  }

  function install(){
    if($('transmissionTest'))return;css();
    const sec=document.createElement('section');sec.className='section wrap';sec.id='transmissionTest';sec.innerHTML=`
      <h2>Language transmission test</h2>
      <p class="lead">Can phonetic similarity track language contact and cultural transmission even when languages are not close genealogical relatives? This section tests that idea against two independent controls: <b>Glottolog genealogy</b> and <b>geographic distance</b>.</p>
      <div class="notice"><b>Important boundary:</b> this experiment studies language history, not race. Languages can spread, shift and converge without population replacement. Geography is a proxy for contact opportunity, not proof that two communities historically interacted.</div>
      <div id="pttStatus" class="status">Loading transmission analysis…</div>
      <div id="pttEvidence" class="ptt-grid"></div>
      <div id="pttMetrics" class="ptt-metrics"></div>
      <div class="magiclayout" style="margin-top:18px"><div class="panel"><h3>Does proximity matter for unrelated languages? <span class="ptt-help" title="Only cross-family pairs are used here. If nearby unrelated languages are more bridge-similar than far-apart unrelated languages, that is consistent with areal/contact convergence, though it does not prove direct historical contact.">?</span></h3><div id="pttBands"></div></div><div class="panel"><h3>Current conclusion <span class="ptt-help" title="The conclusion is generated from the measured benchmark, Glottolog family assignments, and Glottolog coordinates. It is intentionally cautious: correlation can identify a pattern but cannot prove a particular migration or contact event.">?</span></h3><div id="pttConclusion" class="ptt-callout"></div><div id="pttMethod" class="ptt-method"></div></div></div>
      <h3 style="margin-top:26px">Strongest unexplained cross-family similarities</h3>
      <p class="small">These are languages that remain more bridge-similar than a simple model using only genealogy and present-day geographic distance predicts. They are <b>leads for historical research</b>, not claims of hidden ancestry or proven contact.</p>
      <div class="panel" style="overflow:auto"><table class="ptt-table"><thead><tr><th>Language A</th><th>Language B</th><th>Known families</th><th>Distance</th><th>Bridge similarity</th><th>Excess similarity <span class="ptt-help" title="Residual = observed bridge similarity minus the similarity predicted by a simple model using same-family status and log geographic distance. Positive values mean the pair is more similar than those two controls predict.">?</span></th></tr></thead><tbody id="pttPairs"></tbody></table></div>
      <details class="panel" style="margin-top:16px"><summary><b>What exactly is being tested?</b></summary><p><b>Test 1 — inherited signal:</b> are languages in the same accepted Glottolog family more similar in the bridge?</p><p><b>Test 2 — contact-opportunity signal:</b> among languages in different families, are geographically nearby languages more similar than distant ones?</p><p><b>Test 3 — unexplained residuals:</b> after accounting for family and modern geographic distance, which pairs still look unusually similar?</p><p>The third category is where the proposed cultural-transmission idea becomes interesting. It could reflect historical contact, language shift, shared phonological pressures, dataset effects, or 4×4 compression collisions. Each candidate needs independent historical evidence before any contact claim is made.</p></details>`;
    const anchor=$('languageAtlas')||$('magic')||$('status');if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(sec,anchor);else document.querySelector('main')?.appendChild(sec);
    const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#transmissionTest"]')){const a=document.createElement('a');a.href='#transmissionTest';a.textContent='Transmission test';nav.appendChild(a);}
    load();
  }

  async function load(){
    try{
      const r=await fetch('data/phonetic-transmission-analysis.json?v=20260905-transmission1',{cache:'no-store'});if(!r.ok)throw new Error(r.status+' analysis file');const d=await r.json();render(d);
      $('pttStatus').className='status ok';$('pttStatus').innerHTML=`Tested <b>${Number(d.pair_count_with_coordinates).toLocaleString()}</b> language pairs with coordinates across <b>${d.glottolog_matched}</b> Glottolog-matched benchmark languages.`;
    }catch(e){$('pttStatus').className='status error';$('pttStatus').textContent='Transmission analysis is not available yet: '+e.message;}
  }

  function render(d){
    $('pttEvidence').innerHTML=(d.evidence||[]).map(x=>`<div class="ptt-card"><span class="ptt-badge ${x.result==='supported'||x.result==='present'?'ptt-good':'ptt-warn'}">${esc(x.result)}</span><h3>${esc(x.test)} <span class="ptt-help" title="${esc(x.explanation)}">?</span></h3><b class="big">${x.metric==null?'—':num(x.metric)}</b><p class="small">${esc(x.explanation)}</p></div>`).join('');
    const m=d.metrics||{};
    $('pttMetrics').innerHTML=`<div class="ptt-metric"><b>${pct(m.same_family_mean_jaccard)}</b>same-family mean</div><div class="ptt-metric"><b>${pct(m.cross_family_mean_jaccard)}</b>cross-family mean</div><div class="ptt-metric"><b>${num(m.cross_family_log_distance_correlation)}</b>distance correlation <span class="ptt-help" title="Pearson correlation between bridge similarity and log geographic distance for cross-family pairs. Negative means similarity tends to decrease as distance increases.">?</span></div><div class="ptt-metric"><b>${pct(m.near_vs_far_cross_family_uplift)}</b>near-vs-far uplift <span class="ptt-help" title="Mean bridge-similarity advantage of unrelated pairs within 500 km compared with unrelated pairs more than 5,000 km apart.">?</span></div>`;
    $('pttBands').innerHTML=(d.distance_bands||[]).map(x=>`<div class="ptt-band"><span>${esc(x.label)}</span><span>${Number(x.n).toLocaleString()} pairs</span><b>${pct(x.mean_jaccard)}</b></div>`).join('');
    $('pttConclusion').textContent=d.conclusion||'';
    $('pttMethod').innerHTML=(d.method_notes||[]).map(x=>'• '+esc(x)).join('<br>');
    $('pttPairs').innerHTML=(d.top_unexplained_cross_family_pairs||[]).slice(0,20).map(x=>`<tr><td><b>${esc(x.name_a)}</b></td><td><b>${esc(x.name_b)}</b></td><td>${esc(x.family_a)} ↔ ${esc(x.family_b)}</td><td>${Math.round(x.distance_km).toLocaleString()} km</td><td>${pct(x.jaccard)}</td><td class="${x.residual>0?'ptt-good':''}">${x.residual>0?'+':''}${num(x.residual)}</td></tr>`).join('');
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install();
})();
