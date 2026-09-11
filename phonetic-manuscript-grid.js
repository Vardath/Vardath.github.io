(()=>{
'use strict';
const style=document.createElement('style');
style.textContent=`
.manugrid{margin-top:30px}.manugrid .mg-grid{display:grid;grid-template-columns:minmax(0,1fr) 112px minmax(0,1fr);gap:14px;align-items:stretch;margin:18px 0}.manugrid .mg-side{display:grid;gap:8px}.manugrid .mg-layer{border:1px solid var(--line);border-radius:12px;background:linear-gradient(180deg,#171b27,#0e1119);padding:10px;min-height:74px;position:relative;overflow:hidden}.manugrid .mg-layer:before{content:'';position:absolute;inset:8px;background:repeating-linear-gradient(90deg,transparent 0 17px,#2b3347 18px 19px),repeating-linear-gradient(0deg,transparent 0 14px,#2b3347 15px 16px);opacity:.72;pointer-events:none}.manugrid .mg-layer>*{position:relative;z-index:1}.manugrid .mg-layer b{color:var(--cyan)}.manugrid .mg-fold{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px}.manugrid .mg-axis{width:2px;flex:1;min-height:32px;background:#46516d}.manugrid .mg-hub{width:92px;height:92px;border:2px solid #596783;border-radius:50%;display:grid;place-items:center;text-align:center;background:radial-gradient(circle,#273149 0 32%,#171d2b 33% 57%,#0b0f17 58%);box-shadow:0 0 0 7px #0b0f17,0 0 0 8px #333c52;color:var(--cyan);font-weight:800;font-size:.78rem;padding:8px}.manugrid .mg-arrow{font-size:1.25rem;color:var(--cyan)}.manugrid .mg-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}.manugrid .mg-card{border:1px solid var(--line);border-radius:12px;background:#111622;padding:13px}.manugrid .mg-card b{display:block;color:var(--cyan);margin-bottom:5px}.manugrid .mg-flow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:stretch;margin:16px 0}.manugrid .mg-step{border:1px solid var(--line);border-radius:10px;padding:10px;background:#0f1420;text-align:center;font-size:.82rem}.manugrid .mg-step strong{display:block;color:var(--cyan);margin-bottom:4px}.manugrid .mg-note{border-left:3px solid var(--warn);padding:10px 12px;background:#17131a;border-radius:8px;margin-top:14px}.manugrid .mg-status{border:1px solid #3d455d;border-radius:12px;padding:13px;background:#0c1018;margin-top:14px}.manugrid .mg-status b{color:var(--cyan)}
@media(max-width:820px){.manugrid .mg-grid{grid-template-columns:1fr}.manugrid .mg-fold{flex-direction:row;min-height:104px}.manugrid .mg-axis{height:2px;width:auto;min-width:28px;min-height:0}.manugrid .mg-cards{grid-template-columns:1fr}.manugrid .mg-flow{grid-template-columns:1fr}}
`;
document.head.appendChild(style);

const section=document.createElement('section');
section.className='section wrap manugrid';
section.id='manuscript-grid';
section.innerHTML=`
<h2>The Man Grid — layered mirror / fold model</h2>
<p class="lead">The manuscript figure is being treated as a <b>layered coordinate system built around a central vertical fold</b>. It is <b>not a magic square</b>, and it is <b>not a 16×16 matrix</b>. The earlier 16-state/256-gate display was a computational proxy and is retired as a representation of the manuscript itself.</p>
<div class="notice"><b>Working interpretation:</b> the left and right fields are paired faces of one system. A word is placed as a path through one side/layer, folded across the centreline, and read on the corresponding position of the opposite side or another aligned layer. The layers can be overlaid and transformed in a way analogous to how we used stacked magic-square layers, but there is no claim that these manuscript grids are magic squares or obey magic-sum rules.</div>

<div class="mg-grid" aria-label="Schematic of the layered Man Grid fold model">
  <div class="mg-side">
    <div class="mg-layer"><b>Upper left layer</b><br><span class="small">source-side coordinates / one resolution of the lattice</span></div>
    <div class="mg-layer" style="min-height:122px"><b>Torso left layers</b><br><span class="small">multiple dense, superimposed coordinate fields</span></div>
    <div class="mg-layer" style="min-height:150px"><b>Lower left layers</b><br><span class="small">expanded lower-body lattice / continuation of the source field</span></div>
  </div>
  <div class="mg-fold">
    <div class="mg-axis"></div>
    <div class="mg-arrow">⇄</div>
    <div class="mg-hub">CENTRAL<br>FOLD /<br>TRANSFER</div>
    <div class="mg-arrow">⇄</div>
    <div class="mg-axis"></div>
  </div>
  <div class="mg-side">
    <div class="mg-layer"><b>Upper right layer</b><br><span class="small">mirror partner of the upper-left coordinates</span></div>
    <div class="mg-layer" style="min-height:122px"><b>Torso right layers</b><br><span class="small">paired mirror fields sharing the same centreline</span></div>
    <div class="mg-layer" style="min-height:150px"><b>Lower right layers</b><br><span class="small">folded / target-side coordinates</span></div>
  </div>
</div>

<div class="mg-cards">
  <div class="mg-card"><b>1. The centreline is the fold</b>The body is not decoration in the model. The vertical middle axis is the stable reference used to pair left and right coordinates.</div>
  <div class="mg-card"><b>2. The grids are layered</b>The visible lattices are not one uniform square. Upper, torso and lower regions contain overlapping scales/resolutions that can be aligned, overlaid and read as different layers.</div>
  <div class="mg-card"><b>3. Words are paths, not single cells</b>A pronunciation is treated as an ordered path through positions on a chosen layer. Folding that path produces a second path to compare with the same meaning in another language.</div>
</div>

<h3>How a language test now uses the real Man Grid</h3>
<div class="mg-flow">
  <div class="mg-step"><strong>Source word</strong>take an IPA/sound sequence for one meaning</div>
  <div class="mg-step"><strong>Place on a layer</strong>map the sound sequence to the selected manuscript-derived coordinates</div>
  <div class="mg-step"><strong>Fold</strong>reflect positions across the actual central axis, preserving the layer geometry</div>
  <div class="mg-step"><strong>Change layer if defined</strong>use only alignments genuinely produced by the manuscript layers</div>
  <div class="mg-step"><strong>Compare target</strong>measure whether the folded path matches the same-meaning word better than direct and wrong-meaning controls</div>
</div>

<div class="mg-note"><b>Critical correction:</b> old results labelled “Mirror-Man” were produced with earlier proxy operators (4×4/16-state reflections, reversals and related transforms). Those results remain useful as historical comparison data, but they are <b>not evidence from the reconstructed manuscript Man Grid itself</b>. They must be rerun through the real layered fold model before being described as Man-Grid results.</div>

<div class="mg-status"><b>Current reconstruction status:</b> the manuscript geometry is now treated as the primary object. The next implementation step is to transcribe the visible layer boundaries and mirror-paired coordinates directly from the image, derive the permitted folds from that geometry, and rerun the complete test suite using only those derived operations. No 16×16 substitute is to be used for those reruns.</div>

<p class="small">Research boundary: the layered/fold interpretation is our working reconstruction of the supplied manuscript image. Until the historical labels and exact original purpose are independently identified, the linguistic use of those coordinates remains experimental.</p>`;

const old=document.querySelector('#manuscript-grid');if(old)old.remove();
const mirror=document.querySelector('#mirror-lab');
if(mirror?.parentNode)mirror.parentNode.insertBefore(section,mirror);else(document.querySelector('main')||document.body).appendChild(section);
const nav=document.querySelector('.nav');
if(nav&&!nav.querySelector('a[href="#manuscript-grid"]')){const a=document.createElement('a');a.href='#manuscript-grid';a.textContent='Man Grid';nav.appendChild(a)}
else if(nav){const a=nav.querySelector('a[href="#manuscript-grid"]');if(a)a.textContent='Man Grid'}
})();
