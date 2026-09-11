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
<p class="lead">The historical test says that language change is <b>not just random noise</b>. Across real older→younger word pairs, some changes repeat often enough that the model can learn them from other words and then partly run them backwards on words it has never seen before.</p>
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

<hr style="border:0;border-top:1px solid var(--line);margin:34px 0 22px">
<h3 id="historicalTransformationRules">The transformation rules we recovered</h3>
<p class="lead">We then widened the historical scan to the complete Wiktextract corpus and learned context-sensitive changes for every ancestor→descendant route with enough inherited word evidence. The scan found <b>719,153 usable inherited pairs</b> across <b>4,220 raw routes</b>; <b>1,176 routes</b> had enough evidence for held-out testing, and <b>411 routes</b> passed the strict reversible-rule criterion.</p>
<div class="pc-grid">
  <div class="pc-card"><div class="pc-kicker">What a rule is</div><h3>source + context → outcome</h3><p>A rule is not “k always becomes h”. It is more like <b>D3 → C4 when it occurs between particular neighbouring cells</b>. The model learns substitutions, deletions and insertions conditioned on the cells immediately to the left and right.</p></div>
  <div class="pc-card"><div class="pc-kicker">Strongest tendency</div><h3>Word edges erode heavily</h3><p>Among rules from the successful routes there were <b>1,164 deletion-rule entries</b>, <b>797 substitutions</b> and <b>432 insertions</b>. Their accumulated training support was about <b>60,625 deletion</b>, <b>23,261 substitution</b> and <b>14,878 insertion</b> observations.</p></div>
  <div class="pc-card"><div class="pc-kicker">Important boundary</div><h3>There is no single global substitution cipher</h3><p>Across all 1,176 routes at once, learned reverse rules did <b>not</b> improve the average: 0.78346 learned versus 0.79492 raw, and they were below the shuffled-rule control overall. The useful signal is <b>branch- and context-dependent</b>, which is why the reconstruction test now running uses the verified rules as weighted historical evidence rather than one universal hard-coded table.</p></div>
</div>
<div style="overflow-x:auto;margin:18px 0">
<table class="compare" style="min-width:900px">
<thead><tr><th>Recurring Man-grid rule</th><th>Context</th><th>Successful routes</th><th>Total support</th><th>Mean confidence</th></tr></thead>
<tbody>
<tr><td>C2 (s/z/š-like) → ∅</td><td>after A3 (u-like), word end</td><td>64</td><td>4,775</td><td>84.0%</td></tr>
<tr><td>C2 (s/z/š-like) → ∅</td><td>after A1 (i-like), word end</td><td>38</td><td>1,468</td><td>77.1%</td></tr>
<tr><td>A1 (i-like) → ∅</td><td>after B2 (n/r/l-like), word end</td><td>34</td><td>1,464</td><td>81.0%</td></tr>
<tr><td>B1 (m-like) → ∅</td><td>after A3 (u-like), word end</td><td>32</td><td>1,983</td><td>79.4%</td></tr>
<tr><td>A1 (i-like) → ∅</td><td>after D2 (t/d-like), word end</td><td>28</td><td>1,497</td><td>79.1%</td></tr>
<tr><td>∅ → B2 (n/r/l-like)</td><td>after A3 (u-like), word end</td><td>24</td><td>1,133</td><td>94.4%</td></tr>
<tr><td>A2 (a-like) → ∅</td><td>after D2 (t/d-like), word end</td><td>23</td><td>1,240</td><td>77.8%</td></tr>
<tr><td>∅ → D3 (k/g-like)</td><td>after B3 (ŋ/j-like), word end</td><td>23</td><td>1,102</td><td>89.1%</td></tr>
<tr><td>C4 (h-like) → ∅</td><td>word start before B2 (n/r/l-like)</td><td>23</td><td>908</td><td>89.9%</td></tr>
<tr><td>A2 (a-like) → ∅</td><td>after B2 (n/r/l-like), word end</td><td>22</td><td>7,664</td><td>75.5%</td></tr>
<tr><td>D3 (k/g-like) → ∅</td><td>after A2 (a-like), word end</td><td>22</td><td>2,128</td><td>81.3%</td></tr>
<tr><td>C2 (s/z/š-like) → ∅</td><td>after A2 (a-like), word end</td><td>18</td><td>5,043</td><td>70.3%</td></tr>
<tr><td>C4 (h-like) → ∅</td><td>word start before A1 (i-like)</td><td>18</td><td>724</td><td>79.9%</td></tr>
<tr><td>D3 (k/g-like) → ∅</td><td>after A3 (u-like), word end</td><td>18</td><td>343</td><td>87.3%</td></tr>
<tr><td>B3 (ŋ/j-like) → ∅</td><td>between A1 (i-like) and A2 (a-like)</td><td>17</td><td>2,106</td><td>77.6%</td></tr>
<tr><td>B2 (n/r/l-like) → ∅</td><td>after A2 (a-like), word end</td><td>17</td><td>1,245</td><td>71.1%</td></tr>
<tr><td>A3 (u-like) → ∅</td><td>between D2 (t/d-like) and C2 (s/z/š-like)</td><td>17</td><td>1,220</td><td>70.6%</td></tr>
<tr><td>A3 (u-like) → B2 (n/r/l-like)</td><td>after A1 (i-like), word end</td><td>17</td><td>881</td><td>89.6%</td></tr>
<tr><td>D3 (k/g-like) → ∅</td><td>word start before A2 (a-like)</td><td>17</td><td>730</td><td>74.8%</td></tr>
<tr><td>B3 (ŋ/j-like) → B2 (n/r/l-like)</td><td>after A2 (a-like), word end</td><td>15</td><td>622</td><td>82.6%</td></tr>
<tr><td>D1 (p/b-like) → C1 (f/v-like)</td><td>word start before A2 (a-like)</td><td>15</td><td>299</td><td>88.1%</td></tr>
<tr><td>C4 (h-like) → ∅</td><td>between A1 (i-like) and D2 (t/d-like)</td><td>14</td><td>350</td><td>83.8%</td></tr>
<tr><td>D3 (k/g-like) → C2 (s/z/š-like)</td><td>word start before A3 (u-like)</td><td>13</td><td>535</td><td>84.7%</td></tr>
<tr><td>A1 (i-like) → ∅</td><td>between D2 (t/d-like) and C2 (s/z/š-like)</td><td>13</td><td>372</td><td>83.6%</td></tr>
<tr><td>A2 (a-like) → ∅</td><td>between D2 (t/d-like) and C2 (s/z/š-like)</td><td>12</td><td>1,016</td><td>78.0%</td></tr>
</tbody>
</table>
</div>
<p class="small"><b>How to read the table:</b> A1–D4 are broad Man-grid phonetic regions, not exact phonemes. For example, D3 contains k/g-like material and C1 contains f/v-like material. Therefore D1→C1 is evidence for a repeated movement between those regions, not a claim that every historical /p/ literally became /f/ in every language.</p>
<div class="pc-tests">
  <div class="pc-test pc-good"><b>Examples of familiar-looking historical movements</b>The recovered set includes stop→fricative movements such as D1→C1, velar weakening/fronting such as D3→C4 or D3→C2 in particular environments, nasal-place movement such as B3→B2, vowel epenthesis, and extensive final-segment loss.</div>
  <div class="pc-test pc-warn"><b>Rules are probabilities, not commands</b>A rule only enters the displayed set after meeting fixed support/confidence thresholds. Even then it should be used as weighted evidence. Different branches can preserve a cell, delete it, insert around it, or send it to a different region depending on context.</div>
</div>
<div class="notice"><b>Current working model:</b> languages appear to drift through a shared space of possible Man-grid transformations, but each branch follows its own context-sensitive mixture of them. The geometry may be shared; the historical path through that geometry is branch-specific.</div>
<p class="small">Full machine-readable all-language ruleset and every tested route: <a href="data/all-language-historical-transformation-rules.json">all-language-historical-transformation-rules.json</a>. This is the source now being used by the rule-augmented 20-shard reconstruction/validation experiment.</p>
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
