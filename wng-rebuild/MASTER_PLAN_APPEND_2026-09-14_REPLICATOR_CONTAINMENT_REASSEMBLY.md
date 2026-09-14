# WNG MASTER PLAN APPEND — REPLICATOR CONTAINMENT + LOOSE-BLOCK REASSEMBLY

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE WNGv1 IMPLEMENTATION DECISION

Active implementation remains:

`/mnt/data/WNGv1/Wraith-Nanite-Gravtech`

Older local/public/private WNG implementations remain evidence only.

## Loose Replicator Block hazard

Current first-build contract:

- `WNG_ReplicatorMatter` represents physical loose Replicator Blocks, not a hidden stored-matter currency and not an output of ordinary environmental assimilation.
- A stack requires at least **10 Blocks** to self-assemble a Drone.
- Self-assembly requires **30,000 exposed / non-contained ticks**.
- When assembly commits, exactly **10 physical Blocks are consumed** for one real hostile `WNG_ReplicatorDrone`.
- Drone placement happens before Block consumption. Placement/cap/pre-commit failure leaves the Blocks intact.
- The existing hostile block-population cap also applies to loose-Block self-assembly.
- Exposure age is save-persistent.
- Splitting a stack preserves its exposure age on both pieces.
- Merging stacks preserves the oldest exposure age so mature Blocks cannot be made dormant again by mixing them with fresh Blocks.
- Containment pauses exposure; it does not reset the accumulated exposure age.

The clean WNGv1 implementation makes reassembly deterministic once the current threshold is met and a valid Drone can be placed. The historical post-dormancy random-chance formula is evidence of an older implementation, not a current requirement.

## Powered containment

Powered containment is a real physical countermeasure. In the current WNGv1 block foundation an active containment field suppresses the hostile Replicator growth behaviors that already exist:

- loose-Block reassembly;
- autonomous environmental assimilation/reproduction;
- physical hierarchy recombination.

Containment does not destroy Replicators. Loss of projector power ends suppression from the field immediately; the systems query current `CompPowerTrader.PowerOn` state rather than relying on a cached enabled flag.

This scope does **not** automatically wire containment into future Queen, controller/domain, specialist or authority systems merely because the old implementation did. Those systems must make their own explicit containment decision when they are rebuilt, guided by the feature-map principle that containment should meaningfully suppress appropriate hostile Replicator behavior.

## Projector implementation boundary

The old containment-projector code/art/research is archaeology only. The clean WNGv1 projector is being rebuilt from the physical behavior contract.

The current first functional implementation uses historical radius/power/material values (8.5-cell radius, 1200 W, historical build cost) as provisional tuning evidence.

Until the WNG research/progression chain is rebuilt, the clean functional scaffold may use a temporary vanilla research/category gate and a verified vanilla presentation graphic. Those placeholders are **not final WNG progression/art decisions** and must not be mistaken for approval to copy old non-retained containment artwork.

## Validation requirements

Record separately:

- XML/static/reference validation;
- C# compile status;
- live powered/unpowered containment behavior;
- live 30,000-tick pause/resume behavior;
- stack split/merge + save/reload exposure state;
- 10-Block consumption transaction;
- hostile population-cap behavior;
- assimilation/recombination suppression inside field;
- loss-of-power behavior.

A static audit is not runtime proof.
