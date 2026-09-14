# WNG MASTER PLAN APPEND — CLEAN RESTART / WNGv1

Date: **2026-09-14**  
Author/final design authority: **Vardath**

## STATUS — ACTIVE, CONTROLLING RESTART DIRECTIVE

This append records a new implementation reset ordered by Vardath after repeated reconstruction drift and repeated reintroduction of previously identified mistakes.

The active implementation is now a **new clean local rebuild** called **WNGv1**. `WNGv1` is only the workspace/build-generation name. All in-mod Def naming remains `WNG_...`, and the mod identity remains **Wraith & Nanite Gravtech** with package ID `vardath.wraithnanitegravtech` unless Vardath explicitly changes it later.

## Exact active local implementation path

The ONLY active implementation tree for this restart is:

`/mnt/data/WNGv1/Wraith-Nanite-Gravtech`

The handoff/control files for this rebuild live at:

- `/mnt/data/WNGv1/ACTIVE_BUILD.md`
- `/mnt/data/WNGv1/HANDOFF.md`
- `/mnt/data/WNGv1/DECISION_LOG.md`
- `/mnt/data/WNGv1/BUILD_STATE.md`
- `/mnt/data/WNGv1/FILE_MANIFEST.md`

A future GPT must read these files before editing implementation files. If another WNG tree exists anywhere else, it is NOT the active build unless Vardath explicitly says otherwise.

## What older WNG material is now for

All earlier local rebuilds, old checkpoints, public/private WNG repositories, historical source, recovered files and archived local trees are **evidence/archaeology only**.

They may be consulted to answer questions such as:

- What gameplay behavior was intended?
- What systems appeared to work or partially work?
- What art or retained assets were approved?
- What exact mistake caused a live or static failure?
- What useful API technique had already been discovered?
- What balance/timing/naming was previously tried?

They are NOT implementation authority. Do not copy an old subsystem wholesale merely because it exists. Do not reconstruct line-for-line. Do not treat a historical or current checkpoint as a known-good base.

The local evidence trees now have the same evidentiary role as the private repository: useful history, not the active implementation.

The public repository is likewise historical/reference material only and must never select the next implementation or override current requirements.

## Why this restart was ordered

The rebuild repeatedly drifted into reproducing old architecture too literally and then rediscovered old problems. The clearest recent example was shuttle boarding:

- WNG craft already used native Odyssey `Building_PassengerShuttle`, `CompShuttle`, `CompTransporter`, `CompLaunchable` and `CompRefuelable`;
- custom WNG `TransportShipDef`s omitted native `playerShuttle=true`;
- vanilla therefore did not initialize player boarding allowances and produced `Enter shuttle (Not allowed)`;
- previous work had treated the symptom as something to disable/work around rather than fixing the native contract.

The lesson is broader: when RimWorld/Odyssey already provides the required gameplay system, WNG should satisfy the native contract before inventing replacement machinery.

Another recent warning was the temptation to replace a custom subsystem merely because a vanilla component looked similar. Similarity alone is not proof of a defect. A current implementation should only be changed when a specific defect, incompatibility or unnecessary duplication has been demonstrated.

## Rebuild philosophy

The target is a **close functional approximation of Vardath's intended WNG**, not a forensic reproduction of any previous build.

For every subsystem:

1. Start from the current design requirement/lore/gameplay intent.
2. Check RimWorld 1.6 + Odyssey native systems first.
3. Use native systems directly where they already provide the required behavior.
4. Add the smallest WNG-specific code required for behavior RimWorld does not provide.
5. Consult old/private/local evidence to recover intent and known traps, not to choose architecture by default.
6. Preserve exact pawn/Thing identity whenever story/gameplay depends on the real object.
7. Prefer Def-driven/tunable configuration over scattered magic constants.
8. Do not silently disable a vanilla mechanic because the WNG Def/API contract is wrong; fix WNG to meet the native contract.
9. Do not refactor or replace a working custom mechanic solely because a vanilla analogue exists. First demonstrate the actual defect or duplication.
10. Separate static validation, compilation and live RimWorld testing. Never call a static pass runtime proof.

## Decision-record requirement

Every nontrivial architectural decision must be recorded in `/mnt/data/WNGv1/DECISION_LOG.md` with:

- subsystem/feature;
- intended player-visible behavior;
- evidence consulted;
- relevant native RimWorld/Odyssey capability;
- chosen implementation;
- alternatives rejected;
- **why** the choice was made;
- known risks/unknowns;
- validation performed;
- whether compile/runtime proof exists.

This is mandatory continuity material. The purpose is to let the next GPT reconstruct the reasoning, not merely see the final code.

## Handoff requirement

Every handoff must explicitly name:

- active build root: `/mnt/data/WNGv1/Wraith-Nanite-Gravtech`;
- exact current subsystem and next action;
- files created/modified in this rebuild;
- files copied as approved retained assets versus newly authored files;
- old/reference trees consulted;
- decisions made and their rationale;
- validation already performed and what remains unproven;
- known issues/open questions;
- checkpoint/archive path if one exists.

The handoff must never say only “continue WNG.” It must make it difficult for the next GPT to accidentally continue `/mnt/data/WNG-current/...` or a repository checkout.

## Old evidence preservation

Do NOT delete the previous WNG trees/checkpoints. They are needed to understand what was intended and what failed.

Important existing evidence includes, among other material:

- `/mnt/data/WNG-current/Wraith-Nanite-Gravtech`
- `/mnt/data/WNG-current/WNG-CHECKPOINT-20260914-HOSTILE-HATAK.zip`
- `/mnt/data/WNG-current/WNG-CHECKPOINT-20260914-VANILLA-SHUTTLES.zip`
- `/mnt/data/WNG-recovered/`
- private WNG repository history
- public WNG repository history
- website WNG recovery/master-plan files.

None of these is the active implementation after this directive.

## Retained assets

The master plan already permits the approved block Replicator graphics/adaptation/resource art to be carried forward. Those may be copied deliberately into WNGv1 as retained assets, with the copy recorded in `FILE_MANIFEST.md` and `DECISION_LOG.md`.

Do not bulk-copy source/Defs simply because their art is retained.

## Initial rebuild order

Begin again from the master plan's foundation, with the clean implementation tree:

1. establish minimal valid mod identity/scaffold;
2. recover only approved retained Replicator art;
3. rebuild the block Replicator foundation from current requirements and native 1.6 contracts;
4. validate each small slice before adding the next behavior;
5. continue through the master plan and active append/correction material in dependency order.

Do not jump directly to late systems merely because they existed in the previous local build.

## Shuttle rule carried forward

For player-usable craft, normal boarding/loading/fuel/launch/world travel must use the vanilla Odyssey shuttle stack wherever possible. A healthy eligible pawn receiving disabled `Enter shuttle (Not allowed)` because WNG failed to satisfy native Def/comp requirements is a WNG bug, not a feature.

This rule does not forbid WNG-specific mission behavior around a craft; it forbids replacing ordinary player shuttle functionality when Odyssey already supplies it.

## Validation rule

For each subsystem, record separately:

- XML/Def/reference/static validation;
- C# compilation against real RimWorld/Unity assemblies;
- live RimWorld load/startup test;
- live feature test;
- save/reload test where persistent state matters.

A green static audit is not equivalent to a compiling or working mod.

## Supersession note

Any older continuity text that tells a future GPT to continue one of the `/mnt/data/WNG-current/...` checkpoints as the implementation is superseded by this append and by Vardath's explicit 2026-09-14 clean-restart instruction.

Those checkpoints remain evidence only.