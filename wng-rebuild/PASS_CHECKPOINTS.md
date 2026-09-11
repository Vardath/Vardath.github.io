# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — First discovery/progression bridge reconciled

## Public state

Public mod `main` remains **`ff4f8dcb7b8ba17760a48a54f616466642189b0c`**.

No progression source was changed in this reconciliation pass.

## Audit result

Current public already has real encounter/discovery content including the Replicator Queen vault, Mature Wraith Hives, exact Wraith holding/rescue sites, Wraith Dart activity, Asuran covert presence and captured-Queen threats. The first missing progression layer is the bridge from encountered alien evidence into research.

Examples of current bypasses:
- `WNG_ReplicatorStudy` requires only `Machining`;
- `WNG_WraithLivingTechnology` requires only `Fabrication`;
- `WNG_ShuttleEngineering` requires only `Fabrication`;
- `WNG_AsuranFabrication` requires only `Fabrication`.

This skips the retained chain `mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery`.

## First small bridge

Implement **Replicator evidence analysis only**.

Existing Replicator combat already yields `WNG_ReplicatorMatter` reliably. `WNG_ReplicatorStudy` already describes studying recovered Replicator blocks. RimWorld/Odyssey 1.6 provides the native `CompAnalyzableUnlockResearch`, `ResearchProjectDef.requiredAnalyzed` and save-persistent `AnalysisManager` path, and WNG already requires Odyssey.

Exact first implementation:
- add a native analyzable comp to `WNG_ReplicatorMatter`;
- require one successful analysis;
- analysis does not consume the blocks and does not alter their existing reassembly behavior;
- keep `Machining` as the ordinary prerequisite for `WNG_ReplicatorStudy`;
- additionally require analyzed `WNG_ReplicatorMatter` through `requiredAnalyzed`;
- do not use the rarer `WNG_ReplicatorCoreFragment` for this first-tier gate;
- add no new incident, Quest, site, custom GameComponent or fixed-day gate;
- change no Wraith, Asuran, Ancient, Goa'uld or Queen progression in this pass.

Resulting chain: **Replicator encounter -> recover blocks -> analyze blocks -> Replicator Study -> later containment/gestation/reconstruction.**

## Exact next short pass

Implement and validate only:
- `Defs/ThingDefs/Things_Replicator.xml`;
- `Defs/ResearchProjectDefs/Research_Replicator.xml`.

Validation: Release build, all Def/Patch XML, stable WNG-specific analysis ID, native analyze interaction fields, exact `requiredAnalyzed` target, unchanged existing Replicator Matter reassembly tuning, and no unrelated file changes. Checkpoint the branch before promotion.

After promotion, stop that pass and reconcile the next single evidence bridge rather than batching multiple progression families together.

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
