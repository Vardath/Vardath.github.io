(()=>{
'use strict';
if(window.__VARDATH_TEST8_PLAIN_RESULTS__)return;
window.__VARDATH_TEST8_PLAIN_RESULTS__=true;

function addStyles(){
  if(document.getElementById('test8PlainResultsStyles'))return;
  const s=document.createElement('style');
  s.id='test8PlainResultsStyles';
  s.textContent=`
#test8PlainResults{min-width:0}
#test8PlainResults .t8-kicker{color:var(--cyan);font-size:.76rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700}
#test8PlainResults .t8-summary{border-left:4px solid var(--good);padding:15px 18px;background:#0f1716;border-radius:8px;margin:18px 0;font-size:1.03rem}
#test8PlainResults .t8-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0}
#test8PlainResults .t8-stat,#test8PlainResults .t8-panel{border:1px solid var(--line);border-radius:12px;padding:14px;background:linear-gradient(180deg,var(--panel2),var(--panel))}
#test8PlainResults .t8-num{display:block;color:var(--cyan);font:700 1.45rem Georgia,serif;line-height:1.1;margin-bottom:4px}
#test8PlainResults .t8-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:18px 0}
#test8PlainResults .t8-panel h3{margin-top:0}
#test8PlainResults .t8-panel p:last-child{margin-bottom:0}
#test8PlainResults .t8-warning{border-left:4px solid var(--warn);padding:14px 16px;background:#18150e;border-radius:8px;margin:18px 0}
#test8PlainResults .t8-equation{font-family:Consolas,monospace;color:var(--cyan);font-size:1.05rem}
#test8PlainResults details{border:1px solid var(--line);border-radius:10px;padding:11px 13px;background:#0d1119;margin-top:14px}
#test8PlainResults summary{cursor:pointer;color:var(--cyan);font-weight:700}
@media(max-width:850px){#test8PlainResults .t8-stats{grid-template-columns:repeat(2,minmax(0,1fr))}#test8PlainResults .t8-grid{grid-template-columns:1fr}}
@media(max-width:480px){#test8PlainResults .t8-stats{grid-template-columns:1fr}}
`;
  document.head.appendChild(s);
}

function build(anchor){
  if(document.getElementById('test8PlainResults'))return;
  addStyles();
  const sec=document.createElement('section');
  sec.id='test8PlainResults';
  sec.className='section wrap';
  sec.innerHTML=`
    <div class="t8-kicker">Corrected research · Test 8 complete · 20/20 shards</div>
    <h2>Test 8 — Do separate language families point back toward the same thing?</h2>
    <p class="lead">This test asked a very simple question. If we split the language families into independent groups, make each group reconstruct a word on its own through the mirrored Man Grid, and then compare the answers, do those independent answers move toward the same place for the same meaning?</p>

    <div class="t8-summary"><b>Plain-English result: yes, more often than the control.</b> Independent groups of language families tended to reconstruct the same meaning closer together than they reconstructed unrelated meanings. The effect appeared in every one of the 20 shards, but it was not universal: roughly 28% of meanings did not beat the control.</div>

    <div class="t8-stats">
      <div class="t8-stat"><span class="t8-num">12,000</span><b>meanings tested</b><div class="small">The full corrected Test 5 dictionary was used.</div></div>
      <div class="t8-stat"><span class="t8-num">138</span><b>classified families seen</b><div class="small">A broad cross-family test rather than a single-family comparison.</div></div>
      <div class="t8-stat"><span class="t8-num">71.8%</span><b>meanings beat control</b><div class="small">8,611 of 12,000 same-meaning reconstructions were closer than their wrong-meaning control.</div></div>
      <div class="t8-stat"><span class="t8-num">20 / 20</span><b>shards agreed</b><div class="small">Every independent shard showed the same overall direction.</div></div>
    </div>

    <div class="t8-grid">
      <div class="t8-panel">
        <h3>What we actually did</h3>
        <p>For each meaning, the available language families were split into independent panels. Each panel chose its own best reconstructed form using the exact ten-layer mirrored-Man-Grid distance. The panels did not get to copy one another's answer.</p>
        <p>We then measured how far apart the independent same-meaning reconstructions landed. As a control, we compared them with reconstructions for deliberately different meanings.</p>
      </div>
      <div class="t8-panel">
        <h3>What the main numbers mean</h3>
        <p class="t8-equation">same meaning: 0.246 &nbsp; vs &nbsp; wrong meaning: 0.319</p>
        <p>Lower distance means closer together on the Grid. The independent same-meaning reconstructions were therefore about <b>22.8% closer</b> than the wrong-meaning control on this measure.</p>
        <p>The paired effect size was <b>dz = 0.645</b>, which means the difference was substantial enough to be visible across the complete test rather than coming from only a handful of words.</p>
      </div>
    </div>

    <div class="t8-panel">
      <h3>Why this is more useful than simply finding one “closest language”</h3>
      <p>This test did not nominate Georgian, Esperanto, Indo-European, or any other modern language as the answer. Instead, different families were allowed to work independently. Their reconstructions still tended to meet in the same meaning-specific region of the Man Grid.</p>
      <p>The independent panel reconstructions also sat an average distance of <b>0.147</b> from the complete corrected Test 5 reconstruction. In plain terms, when part of the family evidence was separated away, it usually rebuilt something recognisably close to the full reconstruction.</p>
    </div>

    <div class="t8-warning"><b>What this does not prove:</b> it does not prove that one literal prehistoric world language existed, identify a homeland, establish a date, or prove a specific family tree. Modern borrowing and international vocabulary can strengthen some individual words. The important result here is the aggregate pattern across all 12,000 meanings, together with the wrong-meaning control and 20-shard agreement.</div>

    <div class="t8-panel">
      <h3>Method boundary</h3>
      <p>This corrected Test 8 used the exact 1,074-cell mirrored Man Grid as the scoring geometry. It did <b>not</b> use the old PHOIBLE feature-distance score for the test, did <b>not</b> reuse Test 4, did <b>not</b> use a learned historical transformation rule, and did <b>not</b> force a modern language to be the attractor. No phonological rule was invented for the central circle.</p>
    </div>

    <details><summary>Exact result summary</summary><p class="small">Mean same-meaning attractor distance: 0.24625516. Mean wrong-meaning control distance: 0.31899521. Mean convergence advantage: 0.07274005. Relative convergence advantage: 0.22802866. Paired effect dz: 0.64517209. Meanings beating control: 8,611 / 12,000. Mean panel-attractor distance to the corrected Test 5 root: 0.14691516. Shards agreeing with the overall direction: 20 / 20. Source run: 34675070199. Full machine-readable result: <a href="data/man-grid-test-08-exact-v4.json">data/man-grid-test-08-exact-v4.json</a>.</p></details>
  `;
  anchor.insertAdjacentElement('afterend',sec);
  const nav=document.querySelector('.nav');
  if(nav&&!nav.querySelector('a[href="#test8PlainResults"]')){
    const a=document.createElement('a');
    a.href='#test8PlainResults';
    a.textContent='Test 8 results';
    nav.appendChild(a);
  }
}

function waitForAnchor(attempt=0){
  const anchor=document.getElementById('test5MirrorDictionary');
  if(anchor){build(anchor);return;}
  if(attempt<320)setTimeout(()=>waitForAnchor(attempt+1),125);
  else console.error('Test 8 plain-English results: Test 5 dictionary anchor did not appear.');
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>waitForAnchor(),{once:true});
else waitForAnchor();
})();
