# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is reference evidence only.

---

# PAUSE CHECKPOINT — 2026-09-12 — Asuran evidence reconciliation in progress

## Public state

Public mod `main` remains **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**.

No Asuran/Ancient progression code has been changed. No implementation branch has been created for this next slice.

The immediately previous completed public progression bridges are:
- `9f45ebf18caacde671f015cdd1a25217eebb6838` — Replicator encounter/evidence/research bridge;
- `d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — Wraith Hive Heart evidence/research bridge.

## Current task when work resumes

Continue **reconciliation only** for one first-tier **Asuran fabrication evidence -> `WNG_AsuranFabrication`** bridge.

Do **not** yet implement anything and do not combine this with Ancient shuttle engineering or Asuran gravships.

## Findings already established in this interrupted pass

Current `WNG_AsuranFabrication` remains a bypass candidate because its ordinary route is still vanilla-tech-first rather than evidence-first.

Evidence/acquisition candidates examined so far:

- **`WNG_NaniteSludge`** exists as the manufactured Asuran engineering/fuel medium, but it is produced through the Asuran workshop/research chain. It is therefore not acceptable as the first pre-research evidence gate unless another genuine pre-research acquisition path already exists and is verified. Do not create circular progression.
- **Asuran human-form pawns** (`WNG_AsuranOperative`, Technician, Commander, Infiltrator) genuinely exist before Asuran fabrication research through hostile/covert/recovery systems. They are real evidence of nanite fabrication, but no clean native physical-analysis route has yet been selected. Do not invent a pawn-dissection/corpse-drop mechanic merely for convenience without reconciling it first.
- **`WNG_AsuranRecoveryJumper`** genuinely appears in Queen-recovery operations and is a physical Asuran-operated Puddle Jumper, but it mixes Asuran and Ancient shuttle technology. It is therefore a poor first gate for `WNG_AsuranFabrication` because it would collapse fabrication and later Ancient shuttle progression into one evidence object.
- Covert visitor/revealed-infiltrator mechanics expose the exact same Asuran synthetic pawn and do not currently yield a separate physical research object.

No evidence object has yet been approved.

## Exact resume point

On resume, continue examining **existing physical Asuran/Quiet-Lattice/hostile-Lattice structures or items that can genuinely be encountered before `WNG_AsuranFabrication`**.

Priority order:
1. hostile Asuran Lattice encounter structures/items;
2. Quiet Lattice settlement/interaction structures/items;
3. existing Queen-recovery Asuran mission hardware **excluding** the recovery Jumper unless a fabrication-only subcomponent already exists;
4. existing recoverable synthetic components/resources already spawned independently of research.

For each candidate, prove:
- it exists in current public source;
- it is actually obtainable or preservable before `WNG_AsuranFabrication`;
- using it does not create a research/acquisition cycle;
- it represents Asuran nanite fabrication specifically, not Ancient shuttle engineering;
- native Odyssey analysis is mechanically coherent for its Thing type;
- no new timed discovery site is necessary unless all existing evidence routes fail.

Once one exact object is selected, checkpoint that decision **before** creating a branch or editing code.

---

# PREVIOUS COMPLETED CHECKPOINT — Wraith Hive Heart evidence bridge

Public mod `main`: **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da`**.

Validated run **`34616521496` — SUCCESS**. Public diff from `9f45ebf18...` is exactly:
- `Defs/ThingDefs/Wraith_HiveHeart.xml`;
- `Defs/ResearchProjectDefs/Research_WraithBootstrap.xml`.

Public behavior:
- preserved `WNG_WraithHiveHeart` is native in-place analyzable evidence (`analysisID=160912002`);
- 2-hour colonist analysis, no mechanitor, no destruction, `canStudyInPlace=true`;
- `WNG_WraithLivingTechnology` keeps `Fabrication` and additionally requires analyzed Hive Heart;
- Mature-Hive population tuning and all unrelated Wraith mechanics are unchanged.

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
