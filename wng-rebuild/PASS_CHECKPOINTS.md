# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Replicator evidence-analysis bridge promoted to public

## Public state

Public mod `main` is now **`9f45ebf18caacde671f015cdd1a25217eebb6838` — `rebuild: add Replicator evidence-analysis bridge`**.

Promoted clean tree: **`1adc84839a890d31e3e53f4aa9e941d3d9d7d97c`**.

Public diff from `ff4f8dcb...` is exactly:
- `Defs/ThingDefs/Things_Replicator.xml`;
- `Defs/ResearchProjectDefs/Research_Replicator.xml`.

No generated `Assemblies/` or `Source/WNG/obj/` output entered public `main`.

## Public behavior now

- recovered `WNG_ReplicatorMatter` remains dangerous self-reassembling Replicator material with its previous tuning unchanged;
- it is additionally native Odyssey analyzable evidence using stable analysis ID `160912001`;
- one 1.5-hour colonist/research-bench analysis is required and does not consume the blocks;
- `WNG_ReplicatorStudy` still requires `Machining` and now additionally requires analyzed `WNG_ReplicatorMatter`;
- no new incident, site, Quest, fixed-day gate or custom progression component was added;
- rarer `WNG_ReplicatorCoreFragment` remains deeper evidence/material rather than the first-tier gate.

Result: **Replicator encounter -> recovered blocks -> analysis -> Replicator Study -> later containment/gestation/reconstruction.**

## Validation / process correction

Run **`34615590179` — SUCCESS**: Release build, all Def/Patch XML and evidence-bridge invariants passed.

The temporary workflow later staged generated build outputs because cleanup used `git add -A`. That dirty head was rejected before promotion. The clean tree was reconstructed from the exact public base plus the two validated XML blobs and compared before promotion. Future post-build cleanup must use explicit paths or clean-tree reconstruction; never `git add -A`.

This remains source/Def validation, not live RimWorld validation.

## Exact next short pass

**Wraith evidence-to-research reconciliation only.**

Identify one physical Wraith evidence object that is genuinely obtainable before `WNG_WraithLivingTechnology`, preferably from existing Mature Hive/Dart/living-tech encounters. Confirm acquisition order and native analysis suitability, checkpoint the exact bridge, then stop the reconciliation pass before implementation.

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
