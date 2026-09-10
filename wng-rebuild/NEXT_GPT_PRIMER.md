# WNG rebuild — primer for the next GPT

Snapshot date: **2026-09-10**  
Author/design authority: **Vardath**

This is a handoff snapshot, not a substitute for the plan. **Verify the current public repository head before editing.**

## Mandatory first action

Do not begin coding from this primer alone.

Read in this order:
1. `wng-rebuild/STANDING_RULES.md`
2. `wng-rebuild/PLAN_EXECUTION_PROTOCOL.md`
3. `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`
4. `wng-rebuild/CORRECTIONS_LOG.md`
5. relevant sections of `wng-rebuild/MASTER_PLAN.md`
6. `wng-rebuild/REPLICATOR_HIERARCHY.md`
7. `wng-rebuild/REPLICATOR_QUEEN.md` when working on Queen/Asuran systems
8. current public `Vardath/Wraith-Nanite-Gravtech-1.6` tree

Then perform the mandatory subsystem reconciliation before writing code.

## Current repository arrangement

Current implementation repository:
- public `Vardath/Wraith-Nanite-Gravtech-1.6`

Durable requirements/continuity repository:
- public `Vardath/Vardath.github.io/wng-rebuild/`

Do **not** depend on or write to the private WNG repository unless Vardath explicitly re-authorizes it. Private credits are currently not to be consumed for this rebuild.

## Current reset state

The public 1.6 mod was deliberately wiped and restarted on 2026-09-10.

Reset commit:
- `0386f33665b08f9c4f82cbcec23d844bc68ea3af` — `reset: restart WNG from Replicator foundation only`

Latest verified public `main` at the time of this primer:
- `84b9c08991cabd26e950d640fb9c4a350613e760` — `rebuild: restore full Replicator size hierarchy`

Always fetch `main` again because it may have advanced after this primer.

The fresh tree intentionally does **not** contain the old Wraith/Asuran/Queen implementation, old audit suite, old release gates or old design-lock machinery. Git history still exists for reference, but there is no known-good old state.

## What was deliberately preserved

Approved block Replicator graphics and resource graphics were retained.

The retained Replicator graphic inventory includes:
- Drone/base Replicator;
- Hunter;
- Bulwark;
- Titan;
- Siege Mass;
- Controller;
- Repairer;
- Burrower;
- Artillery;
- adaptation overlays for Armor, Ranged, Power, Grav and Shield;
- Replicator Matter and Core Fragment resource graphics.

**Treat this asset inventory as completeness evidence.** Do not rebuild a shorter Def/behavior roster from memory while these assets show that additional planned forms/branches exist.

## Current Replicator implementation — partial, not complete

The current fresh source includes a reconstructed foundation around:
- Replicator state;
- assimilation;
- matter/resource handling;
- EMP suppression;
- regeneration;
- physical hierarchy;
- Replicator ThinkTree/faction/basic Defs;
- specialist Def placeholders for Repairer, Burrower and Artillery;
- Controller Def;
- approved graphics.

This subsystem is **not complete**.

### Physical size hierarchy currently implemented

Upward recombination:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Downward breakup on genuine destruction:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**

Current first-build breakup count is generally two children per higher form. Upward combine counts vary by tier and are stored in Def/component data.

Intentional upward recombination consumption is distinguished from genuine destruction so consumed source bodies do not trigger unwanted death splitting.

Split-born children receive the current first-build recombination lockout of about **one in-game hour / historically 2,500 ticks**, configured in Def data. The reason is gameplay: destroying a Siege Mass or Titan must not produce smaller forms that instantly rebuild the same large threat and make it feel immortal.

The current design values are tunable. Do not turn them into anti-regression doctrine.

### Important current gap discovered during reset

The first fresh scaffold initially omitted the Titan -> Siege Mass upward path. Vardath corrected this. Commit `84b9c089...` added it. This is a concrete example of why the mandatory reconciliation protocol now exists.

## Replicator work that is still explicitly unfinished

Do **not** move to Wraith merely because the main size ladder now exists.

Before the block Replicator foundation is considered accounted for, reconcile and implement/track all of the following:

- Controller actual coordination behavior;
- Repairer actual repair/support behavior;
- Burrower actual breach/infiltration behavior;
- Artillery actual ranged/siege support behavior;
- full adaptation system earned from actual assimilation;
- Ranged adaptation gameplay effect;
- Armor adaptation gameplay effect;
- Power adaptation gameplay effect;
- Grav adaptation gameplay effect;
- **Shield adaptation / Shield Replicator behavior**;
- **learned anti-shield/countermeasure development** after suitable shield encounters;
- adaptation visuals using retained overlays;
- state/adaptation/material transfer through split and recombination;
- Replicator Matter dangerous salvage/reassembly behavior;
- assimilation target priorities and matter economy;
- bounded growth/population behavior;
- EMP behavior across forms/adaptations;
- containment awareness/behavior;
- swarm coordination/AI;
- player-owned Replicator safety/control behavior so they do not eat the player's colony;
- Child's Toy/player Replicator branch;
- any additional Replicator feature found by full plan/history/asset reconciliation;
- later dependent human-form/Asuran/Queen sovereign interactions must remain tracked even if implemented in the later human-form layer.

If another planned feature is discovered, add it to the inventory; do not silently omit it because it was absent from this primer.

## Required working method from this point

For the active Replicator subsystem, do this **before the next code change**:

1. Re-read the complete Replicator-related plan/corrections/subsystem notes.
2. Inventory every retained Replicator asset and every current Replicator Def/source file.
3. Compare that inventory against all planned Replicator roles, forms, mechanics and branches.
4. Build a complete feature/relationship map.
5. Mark current status for every item: implemented / unfinished with dependency / changed by Vardath.
6. Only then implement the next coherent slice.
7. Reconcile again before moving to the next slice or subsystem.

Do not use the previous bad workflow of writing from memory first and waiting for Vardath to point out what was forgotten.

## Process rules that must not regress

- Vardath is the author and final design authority.
- Follow the current plan rigorously for the first complete build.
- Nothing is permanently set in stone; Vardath may redesign any part later.
- Do not omit features.
- Do not bury author-tunable design/balance choices as scattered magic numbers or immutable constants.
- Prefer Defs/settings/centralized configuration where practical for tunable behavior.
- Do not recreate anti-regression or release-check bureaucracy. Use only minimal checks necessary to establish that code/Defs function.
- Historical source is reference evidence only, not a code authority.
- Do not call any old checkpoint known-good.
- Do not use private-repository credits for this rebuild.
- Do not generate new art unless Vardath explicitly asks for image/art generation or a specific art task requires it.
- Do not ask Vardath to repeat requirements already recorded in the continuity set.
- Continue implementation when told to continue; do not stop after a context summary.

## Major later-plan reminders

These are not the immediate coding target while the block Replicator foundation is incomplete, but must not be forgotten later:

- Wraith are one identity/xenotype with caste PawnKinds such as Hunter, Warrior, Commander, Keeper and Queen; backstories are biography, not races/castes.
- Ordinary Wraith Drain Life never opens the strategic feeding-request popup.
- Strategic Wraith faction hunger is separate and drives genuine feeding requests and escalating attack pressure when unresolved/refused.
- Mature-Hive feeding ecology and mature-Hive retaliation are separate from strategic hunger.
- Wraith Living Forge / Grav Engine biological progression should support the intended living-host and corpse paths where retained.
- Use **Wraith Grav Engine**, not obsolete Gravcore substitution.
- Human-form Replicators/Asurans are nanite humanoids, distinct from block Replicator custom forms.
- Mixed block + human-form raid composition can be intentional.
- Queen is currently designed as one exact age-13 female human-form Replicator in a real cryosleep chamber.
- Queen becomes player-recruited immediately upon release/spawn.
- Four hostile Asuran/Lattice recovery operatives attempt to capture her during the vault encounter under the current design.
- Capture is committed only when a hostile carrier physically exits the map with the exact Queen.
- If she remains on a player home map, Asurans may later make occasional capture raids against the home map where she is physically present.
- If captured, the Lattice gains genuine sovereign use of block Replicators in appropriate threats, not a fake `+1 outbreak` bonus.
- Old day-84 discovery pacing was rejected. Major WNG content must be reachable in short campaigns and story/event pacing must remain tunable rather than buried in code.
- CatCraft Stargates! integration is optional; CatCraft owns gate networking, WNG owns WNG incidents/craft/objectives.
- Wraith Dart culling currently intends two real culling/abduction passes, but counts remain editable by Vardath.
- Both Wraith and Asuran/Precursor Odyssey gravship families remain planned and must be functionally distinct.
- Professional art/audio remains part of the full mod, but approved Replicator graphics are currently preserved and should not be casually replaced.

## Verification status at this handoff

The fresh-reset public repository does not currently use the old release/audit workflow, by design. Do not infer that `84b9c089...` is compile-verified merely because older pre-reset commits once had green CI.

When continuing, use a minimal compile/load/reference check when needed to establish that the fresh implementation actually works. Do not turn that check into a new design-lock framework.
