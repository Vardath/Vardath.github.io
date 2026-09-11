# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Replicator evidence-analysis bridge validated on clean branch

## Public state

Public mod `main` remains **`ff4f8dcb7b8ba17760a48a54f616466642189b0c`**.

## Validated branch

Branch: **`rebuild/replicator-evidence-analysis-20260912`**  
Clean HEAD: **`9f45ebf18caacde671f015cdd1a25217eebb6838`**  
Clean tree: **`1adc84839a890d31e3e53f4aa9e941d3d9d7d97c`**

Diff from public is exactly two files:
- `Defs/ThingDefs/Things_Replicator.xml`;
- `Defs/ResearchProjectDefs/Research_Replicator.xml`.

## Implemented bridge

- `WNG_ReplicatorMatter` retains its existing dangerous reassembly component and exact tuning;
- it now also uses native Odyssey `CompProperties_CompAnalyzableUnlockResearch`;
- stable WNG analysis ID: `160912001`;
- analysis takes 1.5 hours, requires a colonist/research bench, does not require a mechanitor and does not consume the blocks;
- `WNG_ReplicatorStudy` still requires `Machining` and now additionally requires analyzed `WNG_ReplicatorMatter` through native `requiredAnalyzed`;
- no core-fragment gate, new incident, site, Quest, GameComponent or fixed-day schedule was added;
- no other progression family changed.

Result: **Replicator encounter -> recovered blocks -> analysis -> Replicator Study -> containment/gestation/reconstruction.**

## Validation

Run **`34615590179` — SUCCESS**:
- Release C# build passed;
- all Def/Patch XML parsed;
- analysis comp/ID/interaction invariants passed;
- `requiredAnalyzed` target passed;
- existing Replicator Matter reassembly tuning was verified unchanged.

### Consequence-Mirror correction during cleanup

The validation workflow itself succeeded, but its cleanup step used `git add -A`, which accidentally committed generated `Assemblies/` and `Source/WNG/obj/` output to the temporary branch history. That head was immediately rejected as unclean and was never eligible for promotion.

Rather than manually trusting a large delete set or rerunning the same workflow, the branch was reconstructed from the exact public base tree plus the two already-validated XML blobs. Branch compare now proves the clean head contains only the intended two files. Future validation cleanup must use explicit paths or reconstruct a clean tree; do not use `git add -A` after builds.

This remains source/Def validation, not live RimWorld validation.

## Exact next short pass

**Promotion only**:
1. recheck public `main` remains `ff4f8dcb...`;
2. promote clean tree `1adc8483...` as one commit;
3. verify public diff is exactly two XML files;
4. update current-state continuity;
5. stop that pass.

Then reconcile **one** next evidence bridge, not the whole remaining progression system at once.

---

# PUBLIC MILESTONES

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — infiltration conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native energy-shield AntiShield integration.
- `e1a080c938...` — bounded Wraith Growth Chamber.
- `ff4f8dcb7b...` — paused two-stage strategic Wraith feeding-request UI.

Broad live RimWorld validation remains outstanding.
