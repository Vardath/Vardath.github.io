# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith Hive Heart evidence bridge validated on branch

## Public state

Public mod `main` remains **`9f45ebf18caacde671f015cdd1a25217eebb6838` — Replicator evidence-analysis bridge**.

## Validated branch

Branch: **`rebuild/wraith-heart-analysis-20260912`**  
Clean HEAD: **`58ef90ca9a7a6018dd7f6a2523fa7e46202084ce`**  
Clean tree: **`a97e879e5fc73ba4012d7281997e6398c3334dc0`**

Diff from public is exactly:
- `Defs/ThingDefs/Wraith_HiveHeart.xml`;
- `Defs/ResearchProjectDefs/Research_WraithBootstrap.xml`.

## Implemented bridge

- `WNG_WraithHiveHeart` keeps its existing Mature-Hive population component and exact tuning (`dormantWakeRadius=18`, `activeLossesBeforeDormantWake=2`);
- it additionally uses native Odyssey `CompProperties_CompAnalyzableUnlockResearch`;
- stable analysis ID: `160912002`, distinct from Replicator analysis `160912001`;
- analysis takes 2 hours, is colonist-only, requires no mechanitor, does not destroy the Heart and uses `canStudyInPlace=true` so the 3x3 building is studied where it stands;
- `WNG_WraithLivingTechnology` still requires `Fabrication` and now additionally requires analyzed `WNG_WraithHiveHeart` through native `requiredAnalyzed`;
- no Wraith shuttle, gravship, Growth Chamber power, strategic hunger, feeding or retaliation system changed.

Result: **Mature Hive discovery -> neutralize/preserve Hive Heart -> in-place analysis -> Wraith Living Technology -> reconstruction/growth.**

## Validation

Run **`34616521496` — SUCCESS**:
- Release C# build passed;
- all Def/Patch XML parsed;
- unique analysis-ID invariants passed;
- `canStudyInPlace=true` and colonist-only analysis passed;
- exact `requiredAnalyzed` target passed;
- existing Mature-Hive population tuning verified unchanged.

The corrected cleanup used explicit `git rm` paths only. Branch compare confirms no generated `Assemblies/`, `obj/`, validator or workflow files remain in the intended diff.

This remains source/Def validation, not live RimWorld validation.

## Exact next short pass

**Promotion only**:
1. recheck public `main` remains `9f45ebf18...`;
2. promote clean tree `a97e879e...` as one public commit;
3. verify public diff is exactly the two intended XML files;
4. update current-state continuity;
5. stop the pass before reconciling another progression family.

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
- `ff4f8dcb7b...` — paused strategic Wraith feeding-request UI.
- `9f45ebf18c...` — Replicator evidence-analysis progression bridge.

Broad live RimWorld validation remains outstanding.
