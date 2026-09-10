(()=>{
'use strict';
const $=q=>document.querySelector(q);
function build(){
  if($('#historicalDriftConclusions'))return true;
  const host=$('#whatWeLearned');
  if(!host)return false;
  const block=document.createElement('div');
  block.id='historicalDriftConclusions';
  block.innerHTML=`
<hr style="border:0;border-top:1px solid var(--line);margin:28px 0 22px">
<h3>Historical language drift — what the new test means in plain English</h3>
<p class="lead">The new historical test says that language change is <b>not just random noise</b>. Across real older→younger word pairs, some of the changes repeat often enough that the model can learn them from other words and then partly run them backwards on words it has never seen before.</p>
<div class="pc-grid">
  <div class="pc-card"><div class="pc-kicker">Main result</div><h3>Part of language drift can be reversed</h3><p>We tested <b>21,745 historical word pairs</b>. The model learned sound-grid changes on 19 of 20 folds, then tried to reconstruct the older form on the unseen 20th fold. It improved average similarity from <b>0.92232 to 0.92444</b>. That numerical gain is small because the historical pairs were already very similar, but it was consistently above zero across the resampling test.</p></div>
  <div class="pc-card"><div class="pc-kicker">Control</div><h3>The direction is real, not just a similar sound inventory</h3><p>When the historical ancestry was deliberately shuffled so that words were paired with the wrong older forms, the learned mapping scored much worse. The real-history reverse mapping beat that shuffled control by about <b>0.05855</b>. Meaning-matched historical forms also beat wrong-meaning forms by about <b>0.23227</b>.</p></div>
  <div class="pc-card"><div class="pc-kicker">Occitan branch</div><h3>Going backwards moved Occitan toward the reconstructed root</h3><p>On the Occitan-side historical chain, the older forms were closer to the current reconstructed root than the younger forms: <b>0.63312 vs 0.62439</b> using direct grid similarity, and <b>0.72159 vs 0.69987</b> when the allowed Man-grid transformations were used. In plain English: the Occitan line shows the direction we would expect if later language drift moved it away from an older state.</p></div>
  <div class="pc-card"><div class="pc-kicker">Malayic branch</div><h3>The same simple rootward pattern did not appear everywhere</h3><p>The Malayic branch still showed learnable, reversible historical change, but its older forms were <b>not</b> generally closer to our present reconstructed root. That means we should not force every branch into one simple “older = closer to this root” ladder. The present root may be approximate, and different branches can preserve and change different parts of the older structure.</p></div>
  <div class="pc-card"><div class="pc-kicker">What this supports</div><h3>Modern languages contain recoverable traces of earlier states</h3><p>The useful conclusion is that descendant languages retain enough regular structure for part of their historical movement to be learned and reversed. That gives us a defensible way to work backwards through successive language stages instead of treating a modern language as an unchanged copy of its ancestor.</p></div>
  <div class="pc-card"><div class="pc-kicker">What it does not prove</div><h3>It does not yet identify one ultimate original language</h3><p>This test establishes recoverable historical drift inside the Man-grid encoding. It does <b>not</b> by itself prove where the first language was spoken, when an ultimate split occurred, or that every branch must converge on the current reconstructed root. Those are separate questions that now can be tested with the reverse-drift method.</p></div>
</div>
<div class="pc-tests">
  <div class="pc-test pc-good"><b>9. Historical reverse-drift test</b>Used 20 deterministic folds. For each historical route, the model learned descendant→ancestor gate correspondences from 19 folds and was tested only on the withheld fold. Both the Occitan and Malayic branches showed cross-validated reversible drift.</div>
  <div class="pc-test pc-good"><b>Positive historical routes</b>The strongest independently positive routes were Latin → Modern Occitan, Latin → Old Occitan, Proto-Malayo-Polynesian → Indonesian, and Proto-Malayo-Polynesian → Malay.</div>
</div>
<div class="notice"><b>Plain-English conclusion:</b> languages really do drift after they split, but some of that drift follows repeatable patterns rather than disappearing into noise. We can now learn part of those patterns from historical evidence and use them to move modern forms back toward earlier states. The Occitan evidence moves toward the current reconstructed root when taken backward; the Malayic evidence confirms reversible drift but warns that the deeper common state is not yet solved by simply picking the oldest available form.</div>
<p class="small">Full reproducible result: <a href="data/historical-drift-20-shards.json">historical-drift-20-shards.json</a>. The historical-word layer is based on explicit older/ancestor forms in the source data; it is a coarse 4×4 structural test rather than a full scholarly reconstruction of historical pronunciation.</p>
`;
  host.appendChild(block);
  return true;
}
if(!build()){
  const o=new MutationObserver(()=>{if(build())o.disconnect()});
  o.observe(document.documentElement,{childList:true,subtree:true});
  setTimeout(()=>o.disconnect(),15000);
}
})();
