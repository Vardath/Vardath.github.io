# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

# ⛔ FULL WNG CHAT HISTORY FIRST — DO NOT TOUCH MOD CODE BEFORE THIS

Before any implementation pass, retrieve and reconcile **all accessible relevant WNG prior conversations** for the subsystem being touched and any adjacent systems that could be affected.

- Handoff summaries, memory summaries, repo notes and old assistant recaps are **not substitutes** for the underlying prior WNG chats when those chats are accessible.
- If Vardath says **read/check/review chat history**, retrieval is mandatory before code changes.
- Use multiple focused retrieval passes across the WNG timeline/subsystems when necessary; do not skim one recent chat and assume continuity is complete.
- Reconcile conflicts chronologically: **newest explicit Vardath instruction wins**.
- Older instructions remain useful historical evidence, but must not reactivate superseded repo authority, architecture or design.
- Do not ask Vardath to repeat information that exists in accessible WNG chat history.
- If literal full transcripts are not technically available, do not falsely claim every literal line is loaded. Retrieve all accessible WNG history and identify any genuine retrieval limitation **before** modifying code.

This requirement was explicitly stated by Vardath before the 2026-09-10 reset and is now a standing gate again because summaries alone repeatedly caused continuity errors.

# ⛔ STARGATE LORE SECOND — DO NOT CODE BEFORE THIS

After the chat-history reconstruction, read and answer `WNG_IMPLEMENTATION_CHECKLIST.md`.

The required questions are:
- **What is this in Stargate?**
- **What does it actually do in Stargate?**
- **What has Vardath said about it across retrieved chat history?**
- **What does current public WNG already do?**
- **What had historical WNG attempted before, and what failed?**
- **What native RimWorld/Odyssey/Biotech mechanics already provide the required function?**
- **What do optional Stargate integrations own?**
- **What is the best faithful implementation now?**

Do not write a generic sci-fi approximation and check Stargate lore afterwards.

An older note saying `next`, `unfinished`, `reconcile`, `correct` or `rebuild` does not prove a feature is absent from current public `main`. Verify current state and recent implementation history first. **Rebuild/correct/refine does not mean remove.**

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable plan/continuity copy: `Vardath/Vardath.github.io/wng-rebuild/`.
- Do not depend on or write to the private WNG repository unless Vardath explicitly re-authorizes it later. Older chats that made the private repo authoritative are superseded historical instructions.

## Mandatory read/retrieval order

1. **Retrieve all accessible relevant WNG chat history first.**
2. Read `STANDING_RULES.md`.
3. Read `WNG_IMPLEMENTATION_CHECKLIST.md` — mandatory chat-history + Stargate-lore gate before any code.
4. Read `PLAN_EXECUTION_PROTOCOL.md` and follow it before writing code.
5. Read `CORRECTIONS_LOG.md`.
6. Read `MASTER_PLAN.md` for the active subsystem and adjacent dependencies.
7. Read active subsystem notes, including `REPLICATOR_HIERARCHY.md` and `REPLICATOR_QUEEN.md` when relevant.
8. Read `NEXT_GPT_PRIMER.md` only as a handoff snapshot, then verify it against retrieved chat history and current public repository state before trusting it.
9. Fetch current public 1.6 `main` and inspect relevant recent commits before editing. Do not assume the last chat head or an old next-step note is still current.

## Mandatory implementation method

Do **not** start coding from remembered requirements or a previous assistant summary.

For every subsystem:

**FULL ACCESSIBLE WNG CHAT HISTORY -> STARGATE LORE -> VARDATH/CHAT CHRONOLOGY -> CURRENT PUBLIC STATE -> HISTORICAL EVIDENCE -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> HANDOFF**

Before implementation, inventory the subsystem using all relevant evidence:
- retrieved WNG chat history;
- Stargate canon/lore and actual function;
- standing rules;
- correction log;
- master plan;
- subsystem notes;
- retained graphics/assets/audio;
- current public Defs/source and recent implementation history;
- faction/PawnKind/xenotype/race references;
- research/recipes/resources;
- quests/incidents/integrations;
- native RimWorld/Odyssey/Biotech mechanics;
- relevant historical WNG code only as reference evidence.

Every known feature must end the pass as:
- implemented;
- explicitly unfinished with its dependency recorded; or
- explicitly changed/rejected by Vardath.

There is no acceptable fourth state where a feature simply disappears because it was forgotten, assumed absent from stale prose, or removed while being "rebuilt".

Before leaving a subsystem, reconcile it against the full inventory and the implementation checklist again. Do not move on merely because the most obvious feature works.

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
- Asurans/Lattice try to capture the Queen during that quest and may later launch occasional capture raids against **any player map where she is physically present**.
- Queen capture is only real when a carrier physically exits the map with her; downing/pickup alone is not loss.
- If the Asurans capture her, they gain real sovereign access to block Replicators in appropriate future threats, not a fake `+1 outbreak` modifier.
- Obsolete Wraith `Gravcore` must not replace the intended functional **Wraith Grav Engine**.
- CatCraft owns Stargate networking when installed; WNG integrates optionally rather than replacing it.
- Do not generate/replace art unless Vardath asks for image/art generation or a specific art rebuild task requires it.

## Immediate restart sequence

The numbered restart sequence below is historical planning context, **not authoritative current implementation state**. Before acting on any item, reconcile it against retrieved chat history, current public `main`, recent commits and the checklist.

1. Preserve/carry approved Replicator PNG assets into the fresh 1.6 tree.
2. Reconstruct the **complete** block Replicator foundation: Defs, PawnKinds, physical hierarchy, specialist/adaptation branches including Shield, faction, split/recombine, matter economy, assimilation, regeneration, EMP/control behavior, containment, swarm AI, player-safety behavior and Child's Toy/player branch. Do not call the foundation complete while a known branch is missing.
3. Verify actual behavior/compile as needed without creating design-lock tests.
4. Rebuild Wraith identity/castes/factions and Life Force/feeding.
5. Rebuild strategic hunger separately from ordinary feeding.
6. Rebuild Wraith captivity/Hive/living-tech systems.
7. Rebuild human-form Replicators/Asurans, Queen, Neural Interface and infiltration.
8. Rebuild quests/discovery with author-tunable pacing rather than a fixed day-84 style schedule.
9. Rebuild craft, Stargate integrations and gravship families.
10. Add/review professional art/audio and tune the entire mod from live testing.

Do not stop after refreshing this material when Vardath asked to continue. Continue implementation only after identifying the **actual first unfinished item from retrieved chat history plus current public state**, not merely the first item that an older document calls unfinished.
