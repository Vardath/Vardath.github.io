# WNG rebuild — corrections and process history

Author/final design authority: **Vardath**.

This file records explicit corrections that override older assistant assumptions, stale process rules and historical source behavior.

# NEWEST PROCESS CORRECTION — 2026-09-12

## No checkpoints or pass logs; rely on the plan

Vardath explicitly corrected the continuation process:

- stop relying on checkpoints;
- remove checkpoint files;
- remove the rebuild pass log;
- do not recreate checkpoint/pass-log machinery;
- rely on the **master plan and active append/correction material** to determine what WNG is supposed to contain;
- use actual current public WNG source only to determine what has already been implemented;
- do not let a stale “next pass”, validation note, pass number, branch diary or short handoff choose the next feature.

The active authority order is now:

**newest Vardath instruction -> MASTER_PLAN + active append(s) + CORRECTIONS_LOG -> relevant recovered history -> actual public source for implementation truth.**

`CURRENT_PUBLIC_STATE.md`, reconciliation documents, feature maps and repository contracts are supporting reference/state evidence only. They do not outrank the plan and do not choose work.

# CORE PROCESS CORRECTIONS

## No known-good state

There are **no known-good historical WNG builds**. Old code/builds/branches are reference evidence only.

## Rebuild rather than patching accumulated damage

The active reset/rebuild instruction was to reconstruct WNG cleanly from the plan rather than preserving accumulated mistakes merely because code already existed.

This does not mean repeatedly rewriting current working foundations. Current public source must be checked first; existing required implementation that already satisfies the plan should be preserved and refined rather than replaced without reason.

## Preserve approved Replicator graphics and intended behavior

Approved block Replicator graphics are preserved through the reset. Intended Replicator behavior must remain/reconstruct cleanly. Do not regenerate replacement art unless Vardath explicitly asks.

## Vardath is the author/design authority

Assistant implementation choices are proposals/technical decisions, not permanent doctrine.

## Nothing is set in stone

Timers, races/xenotypes, castes, PawnKinds, sounds, art, recipes, resources, balance, quests, progression, UI, processes and whole systems can be revised by Vardath.

Older words such as “locked”, “canonical”, “protected” or “must remain stable” mean only current first-build intent unless Vardath explicitly declares something immutable.

## No buried design doctrine

Do not scatter author-tunable timing/cost/cap/frequency/balance values as buried magic constants. Prefer Defs/settings/centralized configuration where practical.

Technical constants are fine when they are implementation details rather than design locks.

## No anti-regression/release-check bureaucracy

Do not recreate the old design-locking audit/release-check framework. Use only proportionate compile/XML/reference/live checks needed to establish function.

Static validation does not decide design acceptance and does not equal live gameplay validation.

## Public repo is current implementation authority

Active code: public `Vardath/Wraith-Nanite-Gravtech-1.6`.

Private/old repositories are reference evidence only unless Vardath explicitly changes that instruction.

Never infer public implementation from a private branch, historical commit, discussion or assistant statement.

## Do not waste chat turns reconstructing settled history

The broad WNG history recovery was done once and consolidated into `CANONICAL_RECOVERY_LEDGER.md`.

Do not reread weeks of raw chat by default. Retrieve raw history only for a genuine unresolved plan/history conflict, current-source contradiction or explicit Vardath request. Resolve it once and write the correction back into durable plan/history material.

## Do not omit features

Every feature/branch/faction/caste/xenotype/PawnKind/Replicator form/adaptation path/quest/event/integration/craft/gravship part/resource/art/sound/UI flow/behavior recorded in the current plan must remain implemented, explicitly unfinished, planned-only/deferred or explicitly changed/rejected by Vardath.

Never silently simplify something away because it is inconvenient or difficult.

## Follow the plan before code

Do not write a partial remembered implementation and then use the plan afterwards to discover omissions.

Working order:

**plan + corrections -> relevant recovered history -> Stargate lore/function -> current public source/assets -> native/optional-mod mechanics -> full feature map -> implement -> verify -> reconcile against plan.**

# GAMEPLAY / DESIGN CORRECTIONS

## Wraith feeding request popup

The request popup is **not** triggered by normal Wraith Drain Life or ordinary feeding.

It appears only when a Wraith **faction** is strategically hungry enough to request feeding subjects/access. Refusal/non-acceptance/unresolved hunger increases attack/raid pressure according to faction behavior.

This is faction strategy, not a normal pawn ability and not automatically a generic quest.

## Mature Hive vs strategic hunger

Mature-Hive feeding stock is local Hive ecology. It does not trigger the strategic feeding-request popup.

Mature-Hive neutralization retaliation is another separate system.

Therefore keep four distinct systems:
- ordinary Drain Life;
- strategic faction hunger/request pressure;
- mature-Hive local feeding ecology;
- mature-Hive retaliation.

## Wraith castes

Hunter, Warrior, Commander, Keeper, Queen and related roles are caste/PawnKind layers under the Wraith identity, not separate races.

## Backstories

Backstories are biography/history, not race/xenotype/caste identity.

## Replicator hierarchy and adaptation branches

The block Replicator design is more than a reduced main combat ladder.

Required physical size ladder:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass** upward through recombination.

Genuine destruction breaks downward:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**.

Base Drone is irreducible.

Split-born children currently have an approximately one-hour / 2,500-tick recombination lockout so destroying a large form does not make it instantly rebuild itself. This is tunable.

Required specialist/adaptation ecology includes:
- Controller;
- Repairer;
- Burrower;
- Artillery/Siege support;
- Ranged;
- Armor;
- Power;
- Grav;
- Shield;
- AntiShield/countermeasure development.

Do not silently omit any of these merely because an old scaffold did.

## Replicator graphics are completeness evidence

Approved retained graphics include Drone, Hunter, Bulwark, Titan, Siege Mass, Controller, Repairer, Burrower and Artillery plus Armor/Ranged/Power/Grav/Shield overlays and Replicator Matter/Core Fragment resources.

The graphics roster itself is evidence of planned forms and must be accounted for.

## Replicator split behavior

Large combined forms must break down into smaller existing forms on genuine destruction rather than simply disappearing.

Intentional upward recombination consumption must not accidentally trigger death splitting. Matter/state/adaptation/control should survive appropriate transformations.

## Human-form Replicators

Human-form Replicators/Asurans are nanite humanoids using Human-pawn systems and their own xenotype/genes/PawnKinds. They are distinct from block Replicator custom forms.

## Mixed raids

Human-form + block Replicator compositions can be intentional. Block recombination rules do not prohibit mixed raid composition.

## Replicator Queen

Current first-build Queen design includes:
- one exact female human-form Replicator Queen;
- current age target 13;
- real cryosleep/cryptosleep chamber;
- immediate player recruitment on release/spawn;
- hostile Asuran/Lattice physical capture attempts;
- later recovery/capture attempts only on a player map where the exact Queen is physically present;
- capture commits only after a hostile carrier physically exits with that exact pawn;
- before exit she remains recoverable/player-owned;
- captured-Queen consequences give the Lattice genuine sovereign block-Replicator access in appropriate threats, not an arbitrary +1 outbreak modifier.

Queen innate authority, Sovereign Neural Lattice authority and Temporary Asuran intrusion are separate control identities.

## Queen pacing

The old day-84 vault schedule was rejected. Major WNG content must be reachable in shorter campaigns.

Do not replace day 84 with another buried magic number. Pacing remains tunable and should not dump every event at once.

## Wraith Grav Engine

Use the intended **Wraith Grav Engine**. Do not restore obsolete Wraith Gravcore semantics where the engine is intended.

## Wraith appearance

Wraith hair should be strongly pale/white/colorless rather than ordinary random human colors. Long straight Wraith-appropriate hair is preferred where feasible.

## Wraith Drain Life

Current first-build full-feed target:
- one coherent Drain Life/Wither ability;
- victim biological age increases substantially (current target +50 years);
- Wraith biological age decreases (current target -5 years) but not below adulthood/current target 18;
- victim gets temporary Life Drained state;
- Wraith gets temporary Fed Recently state;
- duplicated/overwritten genes must not permanently lose their granted ability gizmos.

Exact numeric tuning remains editable.

## Wraith living-tech bootstrap

Living Forge/workshop and Wraith Grav Engine progression should support corpse use as well as a living host where the current plan requires that route, so progression/testing is not dependent on keeping a living victim available.

## Art generation

Do not generate new images merely because graphics are being audited. Only generate/replace art when Vardath explicitly asks for image/art creation.

# 2026-09-10 RESET CONTEXT

Vardath ordered the public 1.6 mod restarted cleanly, preserving approved Replicator graphics and intended behavior and rebuilding everything else according to accumulated requirements.

That reset is historical context, not current implementation state. Current public source has advanced substantially beyond it.

The reset does not authorize deleting later required/current features. Always compare actual public source against the plan before changing a subsystem.
