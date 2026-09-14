# WNG MASTER PLAN APPEND — REPLICATOR ASSIMILATION CORRECTION FOR WNGv1

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE CORRECTION

This append carries the newer 2026-09-13 user correction about block-Replicator assimilation into the clean WNGv1 rebuild. It overrides any WNGv1 handoff/build-state wording that says ordinary environmental assimilation should produce loose `WNG_ReplicatorMatter` / Replicator Blocks.

## Controlling behavior

- Block Replicators eat/assimilate real environmental matter and technology directly.
- Ordinary environmental assimilation does **not** convert the consumed target into loose `WNG_ReplicatorMatter` / Replicator Blocks.
- There is **no hidden stored-matter bank** used later by offspring.
- The current intended ordinary-assimilation transaction creates **two Drone offspring** directly from the consumed environmental target.
- The transaction is target-safe: offspring must be successfully staged/placed first; only then may the environmental target be consumed.
- If the two-offspring transaction cannot complete because of population cap, placement failure, reservation loss or another pre-commit failure, staged offspring must be rolled back and the environmental target must remain unconsumed.
- The job giver must check target eligibility and reservation before starting so multiple Replicators do not repeatedly race the same target.
- `WNG_ReplicatorMatter` / Replicator Blocks and Core Fragments are excluded from ordinary environmental assimilation to prevent self-feeding loops.
- Loose Replicator Blocks remain a separate physical salvage/hazard system. Established behavior is that genuine body destruction may shed Blocks, and loose Blocks may later self-assemble/reassemble by consuming the Blocks themselves.
- Current established loose-block reassembly cost is **10 Blocks -> 1 Drone**, subject to the separately implemented dormancy/containment rules.

## Why this correction matters

During the WNGv1 clean restart, the initial handoff accidentally proposed implementing "assimilation-to-matter first" as a way to separate accounting from reproduction. Re-reading the cumulative WNG memory exposed that this contradicted Stephen's newer explicit 2026-09-13 correction. The incorrect WNGv1 plan was caught before any assimilation code was written.

This is a continuity lesson: a clean rebuild changes implementation architecture, but it does **not** erase newer explicit gameplay decisions. Historical/local material is evidence only, but a clearly recorded newer user correction remains a design requirement unless Vardath changes it again.

## WNGv1 implementation order correction

For the first block-Replicator behavior slice:

1. validate the autonomous hostile Drone foundation;
2. implement ordinary environmental assimilation and its two-Drone reproduction as **one atomic transaction** because they are one gameplay operation;
3. do not produce loose Blocks from that operation;
4. keep loose-block reassembly, hierarchy recombination, destruction splitting, adaptation, containment and player-control work as separate later slices;
5. validate reservation behavior, cap behavior, placement rollback and target-preservation failure paths before proceeding.

## Validation boundary

Static validation is not live proof. Compilation and live RimWorld tests remain separate gates.