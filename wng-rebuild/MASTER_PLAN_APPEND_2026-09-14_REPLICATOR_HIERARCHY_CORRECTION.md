# WNG MASTER PLAN APPEND — REPLICATOR HIERARCHY CORRECTION

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE CORRECTION FOR WNGv1

This append resolves an ambiguity between older Replicator hierarchy experiments and the later consolidated WNG design.

The active implementation remains:

`/mnt/data/WNGv1/Wraith-Nanite-Gravtech`

Older local/public/private implementations remain evidence only.

## Physical hierarchy

Current intended ladder:

**Drone -> Hunter -> Bulwark -> Titan -> Siege Mass**

Current intended upward recombination is **two compatible units at every rung**:

- 2 Drones -> 1 Hunter
- 2 Hunters -> 1 Bulwark
- 2 Bulwarks -> 1 Titan
- 2 Titans -> 1 Siege Mass

Current intended genuine-destruction breakup is:

- Siege Mass -> 2 Titans
- Titan -> 2 Bulwarks
- Bulwark -> 2 Hunters
- Hunter -> 2 Drones
- Drone is irreducible

Intentional upward recombination consumes the real source units through a non-death path such as `DestroyMode.Vanish`; it must never trigger death splitting or death salvage.

Split-born children have a current first-build recombination lockout of **2,500 ticks**. This is gameplay tuning and should remain Def-driven/tunable.

## Why this correction exists

Historical evidence includes an earlier compiled hierarchy that used 3 Drones -> Hunter and 3 Hunters -> Bulwark, and a later Siege Mass experiment that made Siege formation a separate mature-swarm event. Those states are useful evidence that the mechanics could compile and that the general split/recombine idea was viable, but their ratios/architecture were later superseded.

The cumulative WNG continuity record explicitly states that old 3-unit counts must not be copied merely because they existed, and that the later controlling design is two compatible units combining upward unless Vardath changes it again.

Therefore WNGv1 must not restore the 3/3/2 hierarchy or the 48-population Controller-gated Siege formation as the ordinary physical ladder.

## Conservation rule

A destroyed higher form should not simultaneously produce complete lower-form children **and** extra loose Replicator Blocks unless a later explicit design decision adds a balanced salvage rule. The current clean implementation should avoid duplicating matter. Physical loose Blocks are guaranteed at the irreducible Drone destruction boundary; higher forms primarily preserve their constituent matter by splitting into lower forms.

## Tuning evidence

Historical September 12 values that already corresponded to the later two-unit ladder may be reused as provisional first-build balance/visual tuning evidence (body size, draw size, speed, armor, melee power, combatPower). They are not immutable canon and may be changed after live testing.

## Validation requirement

For the hierarchy slice record separately:

- XML/static/reference validation;
- C# compile status;
- live recombination test at every rung;
- live genuine-destruction split at every rung;
- proof that `Vanish` recombination does not emit split/death salvage;
- save/reload during assembly cooldown/lockout;
- faction retention and child placement;
- performance under a large hostile swarm.
