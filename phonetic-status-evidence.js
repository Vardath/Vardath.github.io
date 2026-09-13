(()=>{
'use strict';
const GREEN='goodtxt', ORANGE='warntxt';
function tooltip(text){const s=document.createElement('span');s.textContent=' ?';s.title=text;s.setAttribute('aria-label',text);s.style.cursor='help';s.style.color='var(--cyan,#5ce1e6)';s.style.fontWeight='700';return s}
function addRow(tbody,statement,status,tip,kind='green'){const tr=document.createElement('tr'),a=document.createElement('td'),b=document.createElement('td');a.textContent=statement;if(tip)a.appendChild(tooltip(tip));b.textContent=status;b.className=kind==='orange'?ORANGE:GREEN;tr.append(a,b);tbody.appendChild(tr)}
function addSemanticNav(){const nav=document.querySelector('.hero .nav');if(!nav||nav.querySelector('a[href="#word-semantics"]'))return;const a=document.createElement('a');a.href='#word-semantics';a.textContent='Sound → meaning';const limits=nav.querySelector('a[href="#status"]');if(limits)nav.insertBefore(a,limits);else nav.appendChild(a)}
function addSemanticSection(statusSection){if(document.getElementById('word-semantics'))return;const s=document.createElement('section');s.className='section wrap';s.id='word-semantics';s.innerHTML=`
  <div class="eyebrow">New word-level falsification test · PHOIBLE + NorthEuraLex</div>
  <h2>Sound sequence → word identity → meaning</h2>
  <p class="lead">The earlier bridge work showed that individual sounds can be compressed into increasingly fine phonetic grids. This test asks the next question: when those sound states are placed in their real word order, does the resulting pronunciation retain enough information to recover an independently defined word meaning?</p>

  <div class="notice"><b>Critical separation:</b> meanings were <em>not</em> assigned to cells and were never used to build the phonetic grids. PHOIBLE supplied the phonetic geometry. NorthEuraLex supplied the independent concept labels only after each pronunciation had been encoded. The test therefore asks whether pronunciation carries information about concept identity; it does not build meaning into the map.</div>

  <div class="stats" style="margin:20px 0">
    <span><b>106</b>languages</span>
    <span><b>1,016</b>concepts</span>
    <span><b>92,678</b>canonical word forms</span>
    <span><b>20</b>populated shards</span>
  </div>

  <div class="experiment">
    <div class="panel">
      <h3>How the test worked</h3>
      <p>For every target-language pronunciation, the system ranked its true NorthEuraLex concept against <b>15 deterministic wrong concepts</b>. The phonetic representation was tested at every square resolution from <b>3×3 through 23×23</b>.</p>
      <p>Three controls were run beside it: a shuffled/pseudo-positive meaning null, a same-capacity random segment→cell code, and exact raw segment-identity edit distance.</p>
      <p class="small">The first 3×3→21×21 range was treated as the candidate progression. 22×22 and 23×23 were continuation checks, so a late boundary improvement could not be mistaken for a preregistered optimum.</p>
    </div>
    <div class="panel">
      <h3>Two increasingly difficult questions</h3>
      <p><b>Within-family:</b> can a pronunciation recover the same concept in another related language? This measures lexical transmission where cognacy and inherited sound change are expected to matter.</p>
      <p><b>Family-blocked:</b> remove the target language's entire family, then compare against three reference languages from three different families. This asks whether any useful sound↔concept signal survives ordinary close genealogical relatedness.</p>
    </div>
  </div>

  <h3 style="margin-top:28px">Result 1 — word-level concept information is real</h3>
  <p>Within language families the effect is strong. The best candidate grid was <b>14×14</b>: the true meaning ranked first <b>31.28%</b> of the time, versus a <b>4.60%</b> label-null baseline. The real result beat the label null in <b>20/20 shards</b> for both top-1 accuracy and pairwise AUC (one-sided sign <i>p</i> ≈ 9.54×10<sup>−7</sup>).</p>
  <p>That means the bridge is not restricted to isolated phonemes. Ordered phonetic states can preserve enough structure for an entire word form to carry recoverable lexical identity.</p>

  <div class="stats" style="margin:20px 0">
    <span><b>31.28%</b>within-family top-1</span>
    <span><b>4.60%</b>within-family null</span>
    <span><b>8.95%</b>family-blocked top-1</span>
    <span><b>6.11%</b>family-blocked null</span>
  </div>

  <h3>Result 2 — a smaller signal survives family blocking</h3>
  <p>When the target language's whole family was excluded, accuracy fell sharply—as it should—but did not fall to chance. The strongest candidate result occurred at <b>20×20</b>: <b>8.95%</b> top-1 versus <b>6.11%</b> for the meaning null, with pairwise AUC <b>0.5545</b>. Both semantic criteria again won in <b>20/20 shards</b>.</p>
  <p>This is evidence for a <em>small residual relationship between pronunciation and independently labelled concept identity across unrelated language families</em>. It is not yet evidence that sounds inherently generate meanings. Deep inheritance, borrowing/contact, phonotactic structure, iconic or sound-symbolic effects, and corpus structure are all still possible contributors.</p>

  <h3>Result 3 — the phonetic geometry contributes</h3>
  <p>The real articulatory grid was compared with a random segment→cell assignment of exactly the same capacity. Within families, at the 14×14 peak, the real grid reached <b>31.28%</b> while random cells reached <b>27.01%</b>, with the real geometry winning <b>20/20 shards</b>.</p>
  <p>In the family-blocked test, the 20×20 real grid reached <b>8.95%</b> versus <b>8.40%</b> for random cells, winning <b>15/20 shards</b> (<i>p</i> ≈ 0.0207). Exact raw IPA identity reached <b>8.10%</b> there, so the articulatory geometry generalized slightly better than literal phone identity in this particular cross-family task.</p>

  <h3>Result 4 — meaning does <em>not</em> progressively appear as the squares get larger</h3>
  <p>This is the important negative result. The semantic signal is already present at <b>3×3</b> and then stays broadly flat. Within-family top-1 is 29.87% at 3×3, 31.26% at 4×4, 31.26% at 5×5, 31.14% at 9×9, 31.28% at 14×14 and 31.08% at 21×21.</p>
  <p>The preregistered monotonic-progression test failed: within-family resolution/accuracy ρ ≈ <b>0.066</b> with only 9/20 positive shards (<i>p</i> ≈ 0.748); family-blocked ρ ≈ <b>0.174</b> with 13/20 positive shards (<i>p</i> ≈ 0.132).</p>

  <table class="compare" style="margin-top:18px">
    <tr><th>Grid</th><th>Within-family top-1</th><th>Family-blocked top-1</th></tr>
    <tr><td>3×3</td><td>29.87%</td><td>8.80%</td></tr>
    <tr><td>4×4</td><td>31.26%</td><td>8.74%</td></tr>
    <tr><td>5×5</td><td>31.26%</td><td>8.80%</td></tr>
    <tr><td>9×9</td><td>31.14%</td><td>8.83%</td></tr>
    <tr><td>14×14</td><td><b>31.28%</b></td><td>8.90%</td></tr>
    <tr><td>20×20</td><td>30.98%</td><td><b>8.95%</b></td></tr>
    <tr><td>21×21</td><td>31.08%</td><td>8.89%</td></tr>
    <tr><td>23×23 boundary check</td><td>31.00%</td><td>8.89%</td></tr>
  </table>

  <div class="verdict" style="margin-top:22px"><b>Interpretation:</b> the accumulating evidence now points to two different operations. Increasing square size refines <em>phonetic resolution</em>; it does not progressively manufacture lexical meaning. The major semantic transition appears when phonetic states become an <em>ordered sequence</em>: <span class="node">sound states</span><span class="arrowmini">→</span><span class="node">word form</span><span class="arrowmini">→</span><span class="node">recoverable concept identity</span>.</div>

  <div class="notice"><b>What this establishes:</b> pronunciation contains statistically reproducible information useful for recovering word/concept identity, strongly within families and weakly across family boundaries, and the articulatory geometry contributes beyond a random code. <b>What it does not establish:</b> that meanings are generated by the grids, that every concept has an intrinsic universal sound, or that larger grids monotonically create semantic detail.</div>

  <p class="small">Pinned evidence: PHOIBLE commit <code>5c477f1934f57b3c1a16168fadc08e83dbc03362</code>; NorthEuraLex commit <code>e9a8119f25cf6078299132d8c4e7db338d46ff23</code>. <a href="data/sound-word-semantics-v1-summary.json">Open the preserved result summary →</a></p>`;
  statusSection.parentNode.insertBefore(s,statusSection)}
function upgrade(){const section=document.querySelector('#status');if(!section)return false;const table=section.querySelector('table.compare');if(!table)return false;const tbody=table.tBodies[0]||table;
  addSemanticNav();addSemanticSection(section);
  [...table.rows].forEach(row=>{const txt=(row.cells?.[0]?.textContent||'').trim(),cell=row.cells?.[1];if(!cell)return;
    if(txt.startsWith('The present rules assign non-prosodic segments to sixteen coarse bridge cells.')){cell.className=GREEN;cell.textContent='Implemented + benchmarked';cell.title='The classifier has been exercised across the completed benchmark. This validates the implementation, not global optimality.'}
    if(txt.startsWith('The 16-cell compression is globally optimal.')){cell.className=ORANGE;cell.textContent='Not established';cell.title='3×3 has higher coverage while 5×5 has lower feature and round-trip loss. 4×4 is a useful trade-off, not proven globally optimal.'}
    if(txt.startsWith('WikiPron lexical transitions equal continuous connected-speech articulation.')){cell.className=ORANGE;cell.textContent='No — separate speech validation remains';cell.title='The aligned-speech comparison did not meet the preset agreement thresholds. WikiPron is lexical pronunciation evidence, not a substitute for connected speech.'}
    if(txt.startsWith('The magic-square/powers-of-3 ordering has a phonetic relationship beyond chance.')){row.cells[0].firstChild.nodeValue='Canonical magic-square phonetic-coordinate layouts show a relationship with phonetic geometry beyond random mappings.';cell.className=GREEN;cell.textContent='Supported under current tests';cell.title='Coordinate benchmark, frozen hold-out, magic-variant comparisons, property-ablation tests and the 4×4 antipode test all support a non-random relationship. This is not a claim of universality or global optimality.'}
  });
  if(document.getElementById('evidence-status-divider'))return true;
  const d=document.createElement('tr');d.id='evidence-status-divider';const h=document.createElement('th');h.colSpan=2;h.textContent='Empirical findings from the completed analyses';h.style.paddingTop='24px';h.style.color='var(--cyan,#5ce1e6)';d.appendChild(h);tbody.appendChild(d);
  addRow(tbody,'Phonetic-coordinate numbering performs better than alphabet/symbol-order numbering for the current magic-square experiment.','Supported in benchmark','The alphabet/symbol-order benchmark was strongly negative, while the frozen phonetic-coordinate formulation was positive on the canonical set and stronger on the held-out dataset set.');
  addRow(tbody,'Spatial phonetic locality is the strongest measured contributor to the positive 3–4–5 result.','Supported by ablation','Separating locality, adjacency and powers-of-3 spacing showed locality carrying the clearest aggregate positive signal.');
  addRow(tbody,'The powers-of-3 exponent-spacing overlay is the mechanism behind the positive phonetic effect.','Not supported','The dedicated ablation made the powers-of-3 component negative overall. It remains an exploratory numerical overlay, not the supported mechanism.', 'orange');
  addRow(tbody,'The 4×4 Dürer complement relation behaves like an articulatory antipode better than random pairing.','Supported under current feature test','After inverting standardized PHOIBLE cell-feature vectors, the Dürer numerical complement was the nearest predicted opposite for 6/16 cells, top-three for 11/16; empirical random-matching p≈0.0036 for exact hits and ≈0.000115 for rank.');
  addRow(tbody,'The 5×5 Siamese arrangement is unusually phonetic among tested valid 5×5 magic-square variants.','Supported in specificity test','The canonical Siamese layout outperformed the median valid magic variant across most held-out languages, especially for consonant and place/manner structure. It is not globally optimal because trained non-magic layouts can do better.');
  addRow(tbody,'Magic sums alone, complement geometry alone, V/C placement alone, or place/manner compactness alone fully explains the effect.','No — interaction required','Single-property destruction tests failed to recover the canonical effect. In 5×5, magic + complement recovered most of it, with place/manner structure recovering still more.', 'orange');
  addRow(tbody,'Languages in the same Glottolog family are more bridge-similar on average than languages in different families.','Supported in benchmark','Observed mean stable-gate Jaccard: 0.5051 for same-family pairs versus 0.3731 for cross-family pairs; uplift +0.132.');
  addRow(tbody,'Among different-family languages, present-day geographic distance is negatively associated with bridge similarity.','Supported in benchmark','Cross-family log-distance correlation is -0.1578. Geography is a proxy for possible contact, not proof of contact.');
  addRow(tbody,'Bridge compatibility can be strongly directional rather than symmetric.','Observed in benchmark','Directional direct-support measures differ substantially for some language pairs.');
  addRow(tbody,'Known historical sound changes can involve transformations as large as those allowed by the word-level pilot.','Calibration established','Positive controls include independently attested eight/eight-family and octo/ogdo developments. This calibrates tolerance; it does not establish proposed cross-family etymologies.');
  addRow(tbody,'Ordered pronunciation contains reproducible information useful for recovering independently labelled lexical concept identity.','Supported in 20-shard word test','Across 106 languages and 1,016 concepts, the true concept beat the meaning-label null at every tested resolution. Within-family evidence was strong; a smaller signal survived full target-family blocking.');
  addRow(tbody,'The real articulatory grid contributes word-level predictive information beyond an equally sized random segment-to-cell code.','Supported; strongest within families','At the 14×14 within-family peak the real grid scored 31.28% top-1 versus 27.01% for random cells, winning 20/20 shards. Cross-family geometry support was smaller and resolution-dependent.');
  addRow(tbody,'Lexical meaning emerges monotonically as square resolution grows from 3×3 upward.','Not supported','Semantic recovery was already present at 3×3 and remained broadly flat. The preregistered resolution-versus-accuracy progression test failed in both within-family and family-blocked conditions.', 'orange');
  addRow(tbody,'The phonetic grids generate or uniquely determine universal word meanings.','Not established','The test shows recoverable concept information in pronunciation. Cognacy, deep inheritance, borrowing/contact, phonotactics, sound symbolism and dataset structure remain possible contributors, especially to the small cross-family residual.', 'orange');
  const note=document.createElement('div');note.className='notice';note.style.marginTop='22px';note.innerHTML='<b>What remains orange:</b> global optimality of 16 cells, equivalence between WikiPron lexical sequences and continuous connected speech, powers-of-3 as the causal phonetic mechanism, monotonic creation of meaning by successively larger grids, any claim that the grids themselves generate universal meanings, and any claim that one isolated structural property fully explains the square effect. These are deliberately kept separate from the findings that have now passed their dedicated tests.';table.insertAdjacentElement('afterend',note);return true}
if(!upgrade()){const o=new MutationObserver(()=>{if(upgrade())o.disconnect()});o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>o.disconnect(),10000)}
})();