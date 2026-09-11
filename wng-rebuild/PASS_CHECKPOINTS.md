# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Replicator Grav adaptation validated on branch

## Public implementation state

Public mod `main` remains:

**`45e62cd7f5ea18d2cf3f57df8b25beda1aabe1ad` — native WNG backstories.**

The Grav implementation is branch-only at this checkpoint.

## Active branch

**`rebuild/replicator-grav-adaptation-20260912`**

Validated clean branch HEAD:

**`82f22acb64b11ebf812dd8b0004ab423be8c0800` — `rebuild: wire Def-tunable Replicator Grav maneuver`**

The branch is three commits ahead of public because it contains the source edit, temporary validator commit and final validated Def/validator-removal commit. Comparison against public shows only two intended files changed:
- `Source/WNG/Replicators/ReplicatorAdaptationEffects.cs`;
- `Defs/ThingDefs/Races_Replicator.xml`.

## What this pass implemented

- learned `ReplicatorAdaptation.Grav` now has a real gameplay effect instead of state/overlay only;
- effect is a short-range gravitic reposition using RimWorld's native `JumpUtility.DoJump` / `PawnFlyer` same-pawn movement transaction;
- no passive MoveSpeed bonus, teleport, sustained flight or pawn recreation;
- Def-tunable first-build values are `gravRange=7`, `gravMinDistance=3`, `gravCooldownTicks=360`, `gravLandingRadius=2`;
- target validation uses native `JumpUtility.ValidJumpTarget`, range/minimum-distance bounds and line of sight, so the maneuver does not phase through sealed structures;
- active WNG containment blocks both launch from the origin and landing in the destination;
- EMP suppression disables Grav use;
- player-faction Grav-adapted block Replicators expose an explicit `Grav reposition` target command;
- autonomous hostile Grav-adapted blocks may use the maneuver tactically toward a visible hostile target, with cooldown and short retry delay rather than per-tick spam;
- autonomous use remains behind existing `ReplicatorCombatPermission.CanAttack` and does not replace specialist jobs;
- existing Grav learned state, overlay and hierarchy/save inheritance are untouched;
- `nextGravTick` is save-persistent.

## Validation

GitHub Actions run:

**`34609531708` — SUCCESS**

Passed:
- Release C# build;
- all Def/Patch XML parsing;
- native JumpUtility/PawnFlyer source path present;
- EMP + containment boundaries present;
- controlled target command present;
- autonomous tactical path present;
- save-persistent Grav cooldown present;
- Def tuning present;
- validation explicitly rejects implementing Grav as a source-level generic MoveSpeed effect.

The workflow removed its temporary validator before branch HEAD `82f22ac...`.

This is **source/Def validation, not live RimWorld validation**.

## Exact next pass

**Promotion-only pass:**
1. recheck public `main` is still `45e62cd...`;
2. promote the clean validated Grav tree to public `main` as one clean commit without validator history;
3. verify public diff contains only the two intended files;
4. update `CURRENT_PUBLIC_STATE.md` and this checkpoint to the exact promoted SHA;
5. only then begin the separate AntiShield reconciliation pass.

---

# PRIOR CHECKPOINT — Replicator Grav adaptation reconciliation

The plan/history/lore/native-mechanics decision is preserved here: Grav means a short native gravitic reposition maneuver, not generic speed, teleport, permanent flight or telekinesis. Stargate canon supports learned gravitic field control as the basis, while the pawn-scale maneuver is explicitly a WNG gameplay extrapolation.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
