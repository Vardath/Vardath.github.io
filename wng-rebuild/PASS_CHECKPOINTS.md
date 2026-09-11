# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — AntiShield promoted to public

## Public state

Public mod `main` is now:

**`b5cde48e3cbcb2d608edabc78758e5fe9e4aec39` — `rebuild: integrate Replicator AntiShield with native energy shields`**

Promotion used clean validated tree `37fecb7e3f137ff92ab5f2255105cb7c214a5471` with parent `12590e8...`. Temporary validation/script history did not enter public `main`.

Public diff is exactly:
- `Defs/ThingDefs/Projectiles_Replicator.xml` — added;
- `Source/WNG/Replicators/ReplicatorAdaptiveProjectile.cs` — added;
- `Source/WNG/Replicators/ReplicatorAdaptationEffects.cs` — modified.

## Public behavior now

- adaptive Replicator ranged fire is a real native projectile rather than direct damage;
- native walls/cover and `CompProjectileInterceptor` / `CompGravshipShieldGenerator` shields participate normally;
- AntiShield after repeated shield evidence increases native energy-shield depletion using the existing Def-tunable multiplier;
- ordinary unshielded body impact remains normal adaptive-ranged damage, not a generic AntiShield body-damage bonus;
- existing block-Replicator adaptive-shield countermeasure behavior is preserved;
- Wraith living-hull regeneration is explicitly excluded because it is not an energy shield;
- no Harmony interception patch was introduced.

## Validation

Corrected run **`34610731875` — SUCCESS**:
- Release build passed;
- all Def/Patch XML parsed;
- native projectile/shield/body-damage invariants passed;
- temp validator and helper removed before promoted tree.

Earlier run `34610597370` was only a malformed temporary-workflow failure before any job/source validation and is not a code failure.

This remains **source/Def validation, not live RimWorld validation**.

`CURRENT_PUBLIC_STATE.md` now records exact public HEAD `b5cde48...` and removes broader native AntiShield integration from missing-required debt.

## Exact next pass

**Wraith Growth Chamber reconciliation only.**

1. recover exact plan/chat-history requirement and historical file evidence;
2. inspect current public Wraith Hive infrastructure/source/Defs/assets;
3. Stargate lore gate on Wraith cloning/growth facilities;
4. define the exact distinct gameplay role relative to Hive Heart, Feeding Niche, Hibernation Pod and Dormancy Vault;
5. preserve separation between ordinary feeding, strategic faction hunger, mature-Hive local ecology and retaliation;
6. checkpoint the decision before any Growth Chamber code.

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

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
