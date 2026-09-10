# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable plan/continuity copy: `Vardath/Vardath.github.io/wng-rebuild/`.
- Do not depend on or write to the private WNG repository unless Vardath explicitly re-authorizes it later.

## How to continue

1. Read `CORRECTIONS_LOG.md` first. It records user corrections that override older implementation assumptions.
2. Read `MASTER_PLAN.md` completely enough to understand the subsystem being rebuilt and adjacent dependencies.
3. Read `REPLICATOR_QUEEN.md` when Queen/Asuran work is involved.
4. Fetch current public 1.6 `main` before editing. Do not assume the last chat head is still current.
5. Continue implementation, not merely a summary.
6. Do not ask Vardath to repeat a requirement already recorded here.
7. Historical code/builds are reference material only. There are no known-good historical states.
8. If current code conflicts with the plan or a newer explicit Vardath instruction, correct it forward or rebuild it.
9. If Vardath changes the plan, append/update these website continuity documents; do not erase the accumulated history of corrections.

## Development philosophy — critical correction

The plan is a **working first-build target**, not immutable canon.

Do not hard-code design choices merely because a number or structure was once discussed. Prefer data/Defs/settings/configuration or clearly centralized tunable values where practical. A low-level implementation may still contain constants when technically appropriate, but story timing, balance, population, progression and author-tunable behavior must not be scattered as buried magic numbers.

Do not create anti-regression tests whose purpose is to force the design to remain exactly as previously implemented. Do not create release gates/checklists that impede rebuilding an unfinished mod. Minimal compile/load/reference sanity is acceptable when it materially helps implementation.

Vardath may later change:
- timers/cooldowns/event timing;
- races/xenotypes/castes/PawnKinds;
- sounds/audio counts;
- art/icons/textures;
- recipes/resources/balance;
- factions/raid composition;
- quests/progression;
- UI;
- mechanics/processes/systems;
- compatibility approach;
- any other part of the mod or the whole mod.

Build the complete mod according to current intent first; tune/redesign after real testing.

## Current clean-reset rule

As of 2026-09-10, rebuild public 1.6 from scratch again.

Keep:
- approved Replicator graphics;
- intended block Replicator behavior, especially splitting/recombination/material/adaptation/swarm concepts, but reconstruct it cleanly if copying old code risks importing mistakes.

Do not carry forward:
- the accumulated design-lock audits;
- anti-regression enforcement machinery;
- release-acceptance bureaucracy;
- obsolete hard-coded story schedules;
- code simply because a previous assistant called it green/known-good.

## Critical conceptual rules

- Wraith are one Wraith identity/xenotype with **castes** represented by PawnKinds/roles such as Hunter, Warrior, Commander, Keeper and Queen. Castes are not separate races merely because they have different behavior.
- Backstories are biography/history only. **Backstories are not races or castes.**
- Ordinary Wraith Drain Life/feeding does **not** create a feeding-request popup.
- Strategic Wraith faction hunger is a separate system. A popup/request appears only when a Wraith faction genuinely becomes strategically hungry and requests feeding access/subjects. Refusal/non-acceptance increases attack/raid pressure.
- Mature-Hive local feeding stock and Hive retaliation are separate from strategic hunger/request UI.
- Block Replicators are mechanical custom forms; human-form Replicators/Asurans are nanite humanoids and belong to a separate identity layer.
- Mixed block + human-form Replicator raid composition is intentional where appropriate even though block recombination itself is block-machine behavior.
- Queen release from the cryosleep chamber recruits her to the player **immediately on spawning**.
- Asurans/Lattice try to capture the Queen during that quest and may later launch occasional capture raids only against a player home map where she is physically present.
- Queen capture is only real when a carrier physically exits the map with her; downing/pickup alone is not loss.
- If the Asurans capture her, they gain real sovereign access to block Replicators in appropriate future threats, not a fake `+1 outbreak` modifier.
- Obsolete Wraith “Gravcore” must not replace the intended functional **Wraith Grav Engine**.
- CatCraft owns Stargate networking when installed; WNG integrates optionally rather than replacing it.
- Do not generate/replace art unless Vardath asks for image/art generation or a specific art rebuild task requires it.

## Immediate restart sequence

1. Preserve/carry approved Replicator PNG assets into the fresh 1.6 tree.
2. Reconstruct the minimum block Replicator foundation: defs, PawnKinds, faction, split/recombine, matter economy, adaptation, EMP/control behavior and swarm AI.
3. Verify the Replicator hierarchy works in code/compile before building unrelated systems on top.
4. Rebuild Wraith identity/castes/factions and Life Force/feeding.
5. Rebuild strategic hunger separately from ordinary feeding.
6. Rebuild Wraith captivity/Hive/living-tech systems.
7. Rebuild human-form Replicators/Asurans, Queen, Neural Interface and infiltration.
8. Rebuild quests/discovery with author-tunable pacing rather than a fixed day-84 style schedule.
9. Rebuild craft, Stargate integrations and both gravship families.
10. Add/review professional art/audio and tune the entire mod from live testing.
