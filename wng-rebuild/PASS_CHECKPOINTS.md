# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — AntiShield reconciliation complete

## Public implementation state

Public mod `main` remains:

**`12590e8ea88ce208a640fe2475de1843a7e227af` — physical Replicator Grav adaptation.**

No AntiShield implementation code was changed in this reconciliation pass.

## Recovered plan/history boundary

The recovered plan/history requires:
- shield adaptation / Shield Replicators remain a real learned branch;
- AntiShield is **later learned countermeasure development**, not the same flag as learning Shield;
- repeated shield/barrier evidence is required before AntiShield unlocks;
- learned adaptation state survives hierarchy/swarm transactions;
- EMP remains a meaningful counter;
- broader non-Replicator shield interaction was explicitly deferred until concrete shield systems existed.

Current public source confirms:
- `antiShieldEvidenceRequired` is Def-tunable and currently 3;
- assimilating a Def whose identity contains `shield` or `barrier` learns Shield, increments persistent `shieldEvidence`, and unlocks AntiShield only at the evidence threshold;
- evidence/state copy, merge and save/load correctly;
- current AntiShield gameplay only multiplies adaptive ranged damage against another block Replicator's WNG adaptive shield.

## Concrete current technical defect

Current Replicator adaptive ranged fire in `CompReplicatorAdaptationEffects` calls `target.TakeDamage(...)` directly.

That means RimWorld's normal projectile flight/interception path never runs, so native energy shields such as `CompProjectileInterceptor` / `CompGravshipShieldGenerator` cannot intercept the shot at all. The missing cross-system AntiShield behavior therefore cannot be repaired correctly by merely adding more direct damage multipliers.

## Stargate lore boundary

Lore supports Replicators learning and reproducing capabilities/countermeasures from advanced technology they study and consume, including ship defensive technology. This supports WNG's repeated-shield-evidence countermeasure progression.

Do **not** implement AntiShield as:
- the Ancient anti-Replicator gun/disruptor (ARG);
- a generic anti-Replicator energy wave;
- a shield-deleting aura;
- immunity to all shields;
- generic bonus damage against ordinary unshielded targets.

AntiShield here is specifically **learned modulation/countermeasure behavior against energy-shield technology**.

## Concrete native shield systems confirmed

Current RimWorld/Odyssey exposes:
- `CompProjectileInterceptor`;
- `CompGravshipShieldGenerator : CompProjectileInterceptor`;
- `ThingRequestGroup.ProjectileInterceptor` used by native projectile flight;
- `CheckIntercept(Projectile, lastExactPos, newExactPos)` which consumes shield hit points using the projectile's `DamageAmount`;
- public `Active`, `currentHitPoints`, `HitPointsMax`, radius/ground/air interception configuration.

Current WNG concrete true-energy-shield target:
- `WNG_AsuranShieldEmitter` uses native `CompGravshipShieldGenerator` with a real projectile-interceptor shield pool.

Explicit non-target:
- Wraith gravship living-hull regeneration is biological repair, **not** an energy shield and must never be affected by AntiShield.

## Exact implementation decision

**Convert the learned Replicator adaptive ranged attack from direct `TakeDamage` into a real WNG projectile using RimWorld's normal `Projectile` / `Bullet` flight path.**

This makes normal shield behavior correct first:
- a non-AntiShield Replicator adaptive shot is intercepted normally by native projectile shields;
- a shot that reaches an unshielded pawn applies the existing adaptive ranged body damage/armor penetration;
- ordinary collision, cover and projectile-interceptor behavior become native rather than bypassed.

**AntiShield effect:** if the exact launcher has learned `ReplicatorAdaptation.AntiShield`, its adaptive projectile presents increased effective `DamageAmount` **to native projectile interceptors**, using the existing Def-tunable `antiShieldDamageMultiplier` as the first-build shield-drain multiplier.

Body-hit boundary:
- AntiShield must not simply increase normal body damage after a native shield has been bypassed/depleted;
- the custom projectile should distinguish shield-interception damage from ordinary impact damage;
- current WNG Replicator adaptive-shield behavior must remain at least functionally equivalent to today's countermeasure behavior rather than accidentally losing the existing Replicator-vs-Replicator interaction.

A technically compatible native path exists because:
- `Projectile.DamageAmount` is virtual and is what `CompProjectileInterceptor.CheckIntercept` reads when reducing shield HP;
- shield interception then calls projectile `Impact(..., blockedByShield: true)` and ends the projectile;
- `Bullet.Impact` is virtual, so a WNG bullet subclass can report amplified shield-drain damage during flight/interception while using normal configured body damage on a genuine non-shield impact.

## Required implementation boundaries

Next implementation pass must:
1. create one real WNG adaptive projectile Def/class rather than direct damage;
2. launch it from the exact Replicator pawn toward the exact hostile target using native projectile launch semantics;
3. keep current ranged range/cooldown/base damage/armor penetration Def-tunable;
4. make native `CompProjectileInterceptor` shields intercept normal adaptive shots naturally;
5. when launcher has AntiShield, multiply shield HP depletion using Def-tunable `antiShieldDamageMultiplier`;
6. preserve normal body damage instead of multiplying all post-shield damage;
7. preserve the existing WNG adaptive-shield countermeasure behavior for block Replicator shields;
8. respect existing EMP and `ReplicatorCombatPermission` gates;
9. do not affect Wraith living-hull regeneration;
10. do not add Harmony patches if a native projectile subclass is sufficient;
11. source/Def validate and checkpoint branch before promotion.

## Explicit future dependency boundary

This pass covers current native projectile-interceptor shields. Optional third-party shield systems that do not derive from / participate in RimWorld's native projectile-interceptor path remain separate integration dependencies and must not be guessed or patched blindly.

## Exact next pass

**Implement native adaptive projectile + AntiShield shield-drain integration only** on a fresh public-repo branch from `12590e8...`. Do not move into Wraith Growth Chamber or another subsystem until this implementation is validated, checkpointed, and promoted/closed.

---

# PRIOR PUBLIC MILESTONE — Replicator Grav adaptation

Public milestone: **`12590e8ea88ce208a640fe2475de1843a7e227af`**.  
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
