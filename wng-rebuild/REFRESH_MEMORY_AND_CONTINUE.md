# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable plan/continuity copy: `Vardath/Vardath.github.io/wng-rebuild/`.
- Do not depend on or write to the private WNG repository unless Vardath explicitly re-authorizes it later.

## Mandatory read order

1. Read `STANDING_RULES.md` first.
2. Read `PLAN_EXECUTION_PROTOCOL.md` second and follow it before writing code.
3. Read `CORRECTIONS_LOG.md`.
4. Read `MASTER_PLAN.md` for the active subsystem and adjacent dependencies.
5. Read active subsystem notes, including `REPLICATOR_HIERARCHY.md` and `REPLICATOR_QUEEN.md` when relevant.
6. Read `NEXT_GPT_PRIMER.md` for the latest handoff snapshot, then verify that snapshot against the current public repository head before trusting it.
7. Fetch current public 1.6 `main` before editing. Do not assume the last chat head is still current.

## Mandatory implementation method

Do **not** start coding from remembered requirements or a previous assistant summary.

For every subsystem:

**read -> reconcile -> inventory -> map relationships -> implement -> account for every known item -> then move on.**

Before implementation, inventory the subsystem using all relevant evidence:
- standing rules;
- correction log;
- master plan;
- subsystem notes;
- retained graphics/assets/audio;
- current public Defs/source;
- faction/PawnKind/xenotype/race references;
- research/recipes/resources;
- quests/incidents/integrations;
- relevant historical code only as reference evidence.

Every known feature must end the pass as:
- implemented;
- explicitly unfinished with its dependency recorded; or
- explicitly changed/rejected by Vardath.

There is no acceptable fourth state where a feature simply disappears because it was forgotten.

Before leaving a subsystem, reconcile it against the full inventory again. Do not move on merely because the most obvious feature works.

## Development philosophy — critical correction

The plan is the **default first-build implementation authority**, not immutable canon.

Follow it rigorously while constructing the first complete mod. Do not improvise features away because another approach is easier. If Vardath changes the design, update the continuity documents and follow the new instruction.

At the same time, **nothing is set in stone**. Timers, races/xenotypes/castes/PawnKinds, sounds, art, recipes, resources, balance, quests, progression, UI, processes, systems and the entire mod can be changed later by Vardath.

Do not hard-code author-tunable design choices merely because a number or structure was previously discussed. Prefer data/Defs/settings/configuration or clearly centralized tunable values where practical. Low-level technical constants may still exist where they are implementation details rather than design locks.

Do not create anti-regression tests whose purpose is to freeze the design. Do not recreate release-gate/checklist bureaucracy around an unfinished mod. Minimal compile/load/reference sanity is acceptable only when it materially helps implementation.

## Current clean-reset rule

As of 2026-09-10, public 1.6 has been reset and is being rebuilt from scratch again.

Keep:
- approved Replicator graphics;
- intended block Replicator behavior, reconstructed cleanly where necessary.

Do not carry forward:
- accumulated design-lock audits;
- anti-regression enforcement machinery;
- release-acceptance bureaucracy;
- obsolete hard-coded story schedules;
- code merely because a previous assistant called it green or known-good.

## Critical conceptual rules

- Wraith are one Wraith identity/xenotype with **castes** represented by PawnKinds/roles such as Hunter, Warrior, Commander, Keeper and Queen. Castes are not separate races merely because they have different behavior.
- Backstories are biography/history only. **Backstories are not races or castes.**
- Ordinary Wraith Drain Life/feeding does **not** create a feeding-request popup.
- Strategic Wraith faction hunger is a separate system. A popup/request appears only when a Wraith faction genuinely becomes strategically hungry and requests feeding access/subjects. Refusal/non-acceptance increases attack/raid pressure.
- Mature-Hive local feeding stock and Hive retaliation are separate from strategic hunger/request UI.
- Block Replicators are mechanical custom forms; human-form Replicators/Asurans are nanite humanoids and belong to a separate identity layer.
- The Replicator system includes the complete physical ladder **Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass** upward and **Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base** downward on genuine destruction.
- Split-born Replicators use the current first-build approximately one-hour recombination delay so destroying a large form does not immediately recreate it. This is gameplay behavior and remains tunable.
- The Replicator system also includes specialist/adaptation branches. **Shield Replicators/shield adaptation and anti-shield development must not be omitted**, nor may Controller, Repairer, Burrower, Artillery, ranged/armor/power/grav adaptations or other recorded branches disappear from the rebuild.
- Retained Replicator graphics are part of the subsystem inventory and must be reconciled against Defs/behavior before the Replicator foundation is called complete.
- Mixed block + human-form Replicator raid composition is intentional where appropriate even though block recombination itself is block-machine behavior.
- Queen release from the cryosleep chamber recruits her to the player **immediately on spawning**.
- Asurans/Lattice try to capture the Queen during that quest and may later launch occasional capture raids only against a player home map where she is physically present.
- Queen capture is only real when a carrier physically exits the map with her; downing/pickup alone is not loss.
- If the Asurans capture her, they gain real sovereign access to block Replicators in appropriate future threats, not a fake `+1 outbreak` modifier.
- Obsolete Wraith `Gravcore` must not replace the intended functional **Wraith Grav Engine**.
- CatCraft owns Stargate networking when installed; WNG integrates optionally rather than replacing it.
- Do not generate/replace art unless Vardath asks for image/art generation or a specific art rebuild task requires it.

## Immediate restart sequence

1. Preserve/carry approved Replicator PNG assets into the fresh 1.6 tree.
2. Reconstruct the **complete** block Replicator foundation: Defs, PawnKinds, physical hierarchy, specialist/adaptation branches including Shield, faction, split/recombine, matter economy, assimilation, regeneration, EMP/control behavior, containment, swarm AI, player-safety behavior and Child's Toy/player branch. Do not call the foundation complete while a known branch is missing.
3. Verify actual behavior/compile as needed without creating design-lock tests.
4. Rebuild Wraith identity/castes/factions and Life Force/feeding.
5. Rebuild strategic hunger separately from ordinary feeding.
6. Rebuild Wraith captivity/Hive/living-tech systems.
7. Rebuild human-form Replicators/Asurans, Queen, Neural Interface and infiltration.
8. Rebuild quests/discovery with author-tunable pacing rather than a fixed day-84 style schedule.
9. Rebuild craft, Stargate integrations and both gravship families.
10. Add/review professional art/audio and tune the entire mod from live testing.

Do not stop after refreshing this material when Vardath asked to continue. Continue the implementation from the first unfinished item after reconciling the subsystem completely.
