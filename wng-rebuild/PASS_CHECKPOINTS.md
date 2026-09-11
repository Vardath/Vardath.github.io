# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Wraith Hive Heart evidence bridge promoted to public

## Public state

Public mod `main` is now **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**.

Promoted validated tree: **`a97e879e5fc73ba4012d7281997e6398c3334dc0`** with parent `9f45ebf18...`.

Public diff is exactly:
- `Defs/ThingDefs/Wraith_HiveHeart.xml`;
- `Defs/ResearchProjectDefs/Research_WraithBootstrap.xml`.

## Public behavior now

- every generated Mature Hive still requires its exact Hive Heart and all existing population behavior/tuning is unchanged;
- a preserved `WNG_WraithHiveHeart` is now native Odyssey analyzable evidence using analysis ID `160912002`;
- analysis takes 2 hours, is colonist-only, requires no mechanitor, does not destroy the Heart and uses `canStudyInPlace=true`;
- `WNG_WraithLivingTechnology` still requires `Fabrication` and now also requires analyzed `WNG_WraithHiveHeart`;
- no new site, Quest, timed gate or progression component was added;
- no Wraith shuttle, gravship, Growth Chamber power, hunger, feeding or retaliation mechanics changed.

Result: **Mature Hive discovery -> neutralize/preserve Hive Heart -> in-place analysis -> Wraith Living Technology -> reconstruction/growth.**

## Validation

Run **`34616521496` — SUCCESS**: Release build, all Def/Patch XML, unique analysis ID, in-place analysis, exact `requiredAnalyzed` target and unchanged Mature-Hive population invariants passed.

Corrected cleanup used explicit paths only; public compare confirms exactly two intended XML files. This remains source/Def validation, not live RimWorld validation.

## Exact next short pass

Stop this pass here. The next progression pass must begin with **reconciliation of one Asuran/Ancient evidence-to-research bridge only**, before any implementation. Do not combine Asuran fabrication, shuttle engineering and later gravship progression into one batch.

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
- `d38ce6f321...` — Wraith Hive Heart evidence-analysis progression bridge.

Broad live RimWorld validation remains outstanding.
