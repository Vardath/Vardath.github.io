# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — AntiShield native-projectile integration validated on branch

## Public state

Public mod `main` remains:

**`12590e8ea88ce208a640fe2475de1843a7e227af` — physical Replicator Grav adaptation.**

AntiShield work is branch-only at this checkpoint.

## Active branch

**`rebuild/replicator-antishield-20260912`**

Validated clean branch HEAD:

**`625ab2254ed5e4a8d88985822836554c6750f657` — `rebuild: route Replicator adaptive fire through native shields`**

Clean compare against public contains exactly three intended files:
- `Defs/ThingDefs/Projectiles_Replicator.xml` — added;
- `Source/WNG/Replicators/ReplicatorAdaptiveProjectile.cs` — added;
- `Source/WNG/Replicators/ReplicatorAdaptationEffects.cs` — modified.

Temporary workflow/script helpers are absent from the clean branch tree.

## What this pass implements

- learned Replicator adaptive ranged fire no longer calls direct `target.TakeDamage`; it launches a real native projectile;
- new `WNG_ReplicatorAdaptiveBolt` uses current RimWorld 1.6 `BaseBullet`/`Bullet` projectile machinery;
- native walls/cover/projectile interception now participate instead of being bypassed;
- native `CompProjectileInterceptor` / `CompGravshipShieldGenerator` energy shields can intercept ordinary adaptive shots normally;
- launcher-side existing Def-tunable ranged body damage and armor penetration remain the source values for real body impacts;
- when the exact launcher has learned `ReplicatorAdaptation.AntiShield`, the projectile reports the existing Def-tunable `antiShieldDamageMultiplier`-amplified `DamageAmount` to native shield interception;
- genuine ordinary unshielded body impacts are explicitly resolved at normal configured body damage, so AntiShield is not a generic body-damage multiplier;
- current block-Replicator adaptive-shield countermeasure behavior is preserved: an AntiShield shot hitting a WNG adaptive-shield Replicator still presents amplified damage to that WNG shield transaction;
- current EMP and `ReplicatorCombatPermission` gates remain before adaptive fire;
- no Harmony patch was introduced;
- no interaction with `CompWraithHullRegenerator` exists, preserving the rule that Wraith living-hull regeneration is biological repair, not an AntiShield target.

## Validation

First workflow attempt `34610597370` failed before creating a job because the temporary workflow wrapper was malformed. No source patch from that failed run was committed/promoted.

Corrected validation run:

**`34610731875` — SUCCESS**

Passed:
- patch application;
- Release C# build;
- all Def/Patch XML parsing;
- native projectile launch invariants;
- no remaining direct adaptive `TakeDamage` path;
- custom AntiShield projectile/shield-vs-body distinction;
- projectile Def/class wiring;
- explicit absence of Wraith living-hull AntiShield coupling;
- temporary validation workflow and patch script removed by clean branch HEAD.

This is **source/Def validation, not live RimWorld validation**.

## Exact next pass

**Promotion-only pass:**
1. recheck public `main` is still `12590e8...`;
2. promote clean tree from branch HEAD `625ab225...` as one public commit without temp history;
3. verify public diff is exactly the three intended files;
4. update `CURRENT_PUBLIC_STATE.md` and this checkpoint to the promoted SHA;
5. close AntiShield as implemented foundation / live-test-needed;
6. only then reconcile the next required subsystem, currently Wraith Growth Chamber unless newer Vardath instruction changes priority.

---

# PREVIOUS RECONCILIATION DECISION

AntiShield is learned shield-countermeasure modulation after repeated shield evidence. It is not ARG anti-Replicator disruption, not a shield-deleting aura, not generic shield immunity, and not generic bonus body damage. Current native projectile-interceptor shields are the concrete supported target; third-party non-native shield systems remain future explicit integrations.

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
