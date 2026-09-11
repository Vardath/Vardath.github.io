# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Replicator Grav adaptation promoted to public

## Public implementation state

Public mod `main` is now:

**`12590e8ea88ce208a640fe2475de1843a7e227af` — `rebuild: add Replicator Grav reposition adaptation`**

Promotion used the validated clean branch tree `1353c93224ddb116512d998f71afff4b75bd2948` with parent `45e62cd...`. Temporary validation-workflow history did not enter public `main`.

Public diff contains only:
- `Source/WNG/Replicators/ReplicatorAdaptationEffects.cs`;
- `Defs/ThingDefs/Races_Replicator.xml`.

## What is now public

- learned Grav evidence now produces real physical mobility rather than state/overlay only;
- native `JumpUtility.DoJump` / `PawnFlyer` exact-pawn reposition transaction;
- Def-tunable range/min-distance/cooldown/landing radius;
- no generic MoveSpeed buff, teleport, permanent flight, phasing or pawn recreation;
- native walkable/LOS/range validation;
- EMP and WNG containment suppression at origin/destination;
- explicit player Grav target command;
- bounded autonomous hostile tactical reposition under normal combat-permission rules;
- save-persistent cooldown;
- existing learned state/overlay/hierarchy inheritance preserved.

## Validation

GitHub Actions run **`34609531708` — SUCCESS** before promotion:
- Release C# build passed;
- all Def/Patch XML parsed;
- Grav source/Def invariants passed;
- temporary validator removed before the promoted tree.

This remains **source/Def validation, not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` is updated to exact public HEAD `12590e8...` and removes richer Grav behavior from missing-required debt.

## Exact next pass

**AntiShield reconciliation only.**

1. recover plan/history meaning and learning boundary;
2. inspect current Replicator AntiShield evidence/state and Replicator-shield effect;
3. inspect native `CompProjectileInterceptor` / `CompGravshipShieldGenerator` and current WNG shield Defs;
4. perform Stargate lore gate and explicitly separate this from ARG anti-Replicator disruption;
5. decide concrete shield interactions that current public APIs can support;
6. explicitly exclude Wraith living-hull regeneration because it is not an energy shield;
7. checkpoint the decision before implementation.

---

# PRIOR CHECKPOINT — Grav branch validation

Validated branch milestone: **`82f22acb64b11ebf812dd8b0004ab423be8c0800`**.  
Validation run: **`34609531708` — SUCCESS**.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
