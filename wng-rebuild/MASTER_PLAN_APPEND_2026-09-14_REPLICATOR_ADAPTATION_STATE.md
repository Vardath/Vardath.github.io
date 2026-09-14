# WNG MASTER PLAN APPEND — REPLICATOR ADAPTATION STATE / ACQUISITION

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE WNGv1 IMPLEMENTATION DECISION

Active implementation remains `/mnt/data/WNGv1/Wraith-Nanite-Gravtech`.

## Separation of concerns

Learned adaptation knowledge is a separate persistent layer from:
- physical hierarchy;
- loose-block matter/reassembly;
- controller/domain authority;
- EMP timing;
- specialist bodies;
- adaptation gameplay effects.

Do not restore the old bundled Replicator state object that mixed StoredMatter, adaptation, controller identity and a custom EMP clock. WNGv1 adaptation stores only learned flags and evidence counters.

## Required branches

Current learned branches remain:
- Material;
- Armor;
- Ranged;
- Power;
- Shield;
- Grav;
- AntiShield.

Learned flags and relevant evidence counters are save-persistent and must survive hierarchy transformations.

## Evidence acquisition — native/concrete signals, not DefName guessing

The clean rebuild rejects old acquisition heuristics based on strings such as `gun`, `shield`, `grav`, `thruster`, `shuttle`, etc. where a real RimWorld/Odyssey property or component exists.

Current WNGv1 evidence rules:
- **Material** — every successfully committed real environmental assimilation;
- **Armor** — assimilated apparel with concrete ArmorRating Sharp/Blunt/Heat evidence above the minimal threshold;
- **Ranged** — a real ranged weapon (`ThingDef.IsRangedWeapon`) or a building with an actual turret gun Def;
- **Power** — real `CompPowerTrader` or `CompPowerBattery` evidence;
- **Shield** — real native `CompShield` or `CompProjectileInterceptor` evidence;
- **Grav** — real Odyssey `Building_GravEngine`, `CompGravshipFacility`, or `CompShuttle` evidence.

Third-party adaptation integration must only be added for verified concrete APIs/Defs, not guessed names.

## AntiShield evidence

AntiShield must require repeated meaningful shield evidence rather than unlocking from the first shield target.

Current first-build threshold is **2 real shield-evidence assimilation events**, stored as a save-persistent counter and exposed as Def-driven tuning. This matches the intended repeated-evidence rule and approximates the old later behavior where AntiShield appeared after Shield had already been learned and another shield target was encountered.

## Swarm sharing

When an autonomous block successfully commits assimilation, learned evidence is shared to valid same-faction block Replicators on the same map. EMP-disrupted source or recipients cannot transmit/receive through this WNG learning path.

Current WNGv1 has not rebuilt exact controller domains yet, so sharing is faction-scoped. When domain/controller state exists, tighten this existing sharing compatibility by exact domain; do not create a second adaptation framework.

## Transaction ordering

Evidence is detected before target destruction but applied only **after** the assimilation transaction is committed. A post-commit adaptation-sharing exception must never roll back already-placed offspring after the real target has been consumed.

Offspring staged by the committed assimilation are already real same-faction blocks and receive the successful evidence through the normal sharing pass.

## Hierarchy continuity

Upward recombination merges adaptation flags across donors. Shared shield-evidence history uses the **maximum** donor evidence count, not the sum, because donors may know the same shared encounter and summing would fabricate additional evidence.

Genuine downward split copies the parent's learned state/evidence to each child.

## Effects are a separate next layer

This append defines knowledge/acquisition/continuity only. Armor mitigation, learned ranged attack, Power regeneration effects, adaptive Shield, Grav behavior and AntiShield interaction must be implemented and audited separately so acquisition correctness is not mixed with combat-effect correctness.

## Validation boundary

Static/API validation may verify concrete evidence signals, Scribe state, EMP sharing suppression and hierarchy continuity. Compilation and live RimWorld evidence acquisition/save/reload remain separate required tests.