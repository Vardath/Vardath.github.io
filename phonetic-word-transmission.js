(() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = n => `${(Number(n)*100).toFixed(1)}%`;
  async function run(){
    const res = await fetch('data/word-transmission-pilot.json?v=20260905-word1', {cache:'no-store'});
    const d = await res.json();
    const section = document.createElement('section');
    section.className='section wrap'; section.id='wordTransmission';
    const controls = d.positive_controls.map(x=>`<tr><td><b>${esc(x.from)}</b> → <b>${esc(x.to)}</b></td><td>${pct(x.phonetic)}</td><td>${pct(x.semantic)}</td><td>${esc(x.status)}</td><td>${esc(x.note)}</td></tr>`).join('');
    const candidates = d.candidates.map(x=>`<div class="panel" style="margin-top:12px"><h3>${esc(x.from)} → ${esc(x.to)}</h3><div class="stats"><span title="Broad phonetic similarity under the pilot weighted sound-change cost model. This is not an etymology probability."><b>${pct(x.phonetic)}</b>phonetic ?</span><span title="Similarity on the transparent pilot semantic graph. Meanings such as cause, efficacy, authority and divine agency are adjacent but not treated as identical."><b>${pct(x.semantic)}</b>semantic ?</span><span title="60% phonetic + 40% semantic. Used only to rank pilot candidates against the fixed controls."><b>${pct(x.combined)}</b>combined ?</span></div><p><b>${esc(x.verdict)}</b></p><p class="small">${esc(x.note)}</p></div>`).join('');
    const axis = d.semantic_axis.map((x,i)=>`<span class="node" title="${esc(x.meaning)}">${esc(x.term)}<br><small>${esc(x.position)}</small></span>${i<d.semantic_axis.length-1?'<span class="arrowmini">→</span>':''}`).join('');
    section.innerHTML=`<h2>Word-level transmission calibration</h2>
      <p class="lead">This test asks whether a proposed word connection behaves like known historical sound change after meaning is considered. Known lineages are fixed first as positive controls; the Yoruba–Germanic candidates are scored afterwards.</p>
      <div class="notice"><b>Important:</b> a high score means “mechanically worth investigating,” not “same root proved.” Short words generate accidental matches easily, and this pilot does not yet search every world-language lexicon.</div>
      <div class="panel"><h3>Confirmed calibration paths</h3><p class="small">These establish the scale. The experiment has to accommodate genuine transformations such as <b>oktō → ógdoos</b> and <b>*ahtō → eahta → eight</b> before testing speculative pairs.</p><div style="overflow:auto"><table class="compare"><thead><tr><th>Path</th><th title="Broad weighted phonetic similarity">Phonetic ?</th><th title="Semantic continuity score">Meaning ?</th><th>Status</th><th>Why included</th></tr></thead><tbody>${controls}</tbody></table></div></div>
      <div class="panel" style="margin-top:16px"><h3>The meaning axis being tested</h3><p class="small">Tooltips show the assigned meaning. The chain is deliberately narrow: cause → efficacy → authority → divine agency. “Ark” and the numeral-eight family are kept separate unless evidence links them.</p><div class="corebox">${axis}</div></div>
      <h3 style="margin-top:24px">Yoruba àṣẹ candidate results</h3>${candidates}
      <div class="panel" style="margin-top:18px"><h3>Current conclusion</h3><p>${esc(d.conclusion)}</p><details><summary>Method and limitations</summary><p class="small"><b>Phonetics:</b> ${esc(d.method.phonetic_score)}</p><p class="small"><b>Semantics:</b> ${esc(d.method.semantic_score)}</p><p class="small"><b>Calibration:</b> ${esc(d.method.calibration)}</p><p class="small"><b>Warning:</b> ${esc(d.method.warning)}</p></details></div>`;
    const anchor = document.getElementById('wordTransmission');
    if(!anchor){
      const target = document.getElementById('transmission') || document.getElementById('magic') || document.querySelector('main');
      if(target && target.parentNode && target !== document.querySelector('main')) target.parentNode.insertBefore(section, target.nextSibling); else document.querySelector('main')?.appendChild(section);
    }
    const nav=document.querySelector('.nav'); if(nav && !nav.querySelector('a[href="#wordTransmission"]')){const a=document.createElement('a');a.href='#wordTransmission';a.textContent='Word test';nav.appendChild(a);}
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>run().catch(console.error)); else run().catch(console.error);
})();
