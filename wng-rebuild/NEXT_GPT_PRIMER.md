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
8. `wng-rebuild/REPLICATOR_FEATURE_MAP.md`
9. `wng-rebuild/REPLICATOR_FOUNDATION_CHECKPOINT_2026-09-10.md`
10. current public `Vardath/Wraith-Nanite-Gravtech-1.6` tree

Then perform the mandatory subsystem reconciliation before writing code.

## Current repository arrangement

Current implementation repository:
- public `Vardath/Wraith-Nanite-Gravtech-1.6`

Durable requirements/continuity repository:
- public `Vardath/Vardath.github.io/wng-rebuild/`

Do **not** depend on or write to the private WNG repository unless Vardath explicitly re-authorizes it. Private credits are not to be consumed for this rebuild.

## Current reset state

The public 1.6 mod was deliberately wiped and restarted on 2026-09-10.

Reset commit:
- `0386f33665b08f9c4f82cbcec23d844bc68ea3af` — `reset: restart WNG from Replicator foundation only`

Latest implementation cleanup head at this snapshot:
- `94705ee8894b6659920178e19ea0ebe21555c7be` — temporary verification workflow removed after the tactical Burrower refinement passed compilation/XML checks.

Always fetch `main` again because it may have advanced after this primer.

The fresh tree intentionally does **not** contain the old Wraith/Asuran/Queen implementation, old audit suite, old release gates or old design-lock machinery. Git history remains reference material only; there is no known-good old state.

## Preserved asset inventory

Approved block Replicator graphics and resource graphics remain retained.

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

Treat this asset inventory as completeness evidence. Do not rebuild a shorter Def/behavior roster from memory.

## Block Replicator foundation — current implemented state

Physical hierarchy:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass**

Genuine-destruction breakup:

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base**

Intentional upward recombination is separated from genuine destruction so consumed bodies do not trigger death splitting.

Split-born children receive the current first-build approximately **one in-game hour / 2,500-tick recombination lockout**. This exists specifically so destroying a Titan or Siege Mass does not immediately recreate the same large threat and make combat effectively impossible/immortal. The exact timer remains tunable.

Current fresh implementation now includes:
- cumulative learned adaptation state rather than single-value overwrite state;
- adaptation/state inheritance through split and recombination;
- stored matter conservation through recombination and genuine-death splitting;
- technology-prioritized assimilation;
- matter-budget offspring production;
- Def-tunable population ceiling for autonomous growth and dormant-matter reassembly;
- dangerous Replicator Matter reassembly;
- Replicator Core Fragment resource;
- regeneration with EMP suppression;
- Power adaptation improving regeneration;
- Armor adaptation damage reduction;
- Shield adaptation with rechargeable defensive pool;
- Ranged adaptation with learned ranged fire;
- repeated shield evidence before AntiShield knowledge unlocks;
- retained Armor/Ranged/Power/Grav/Shield overlay rendering;
- Controller coordination behavior;
- Repairer support behavior;
- Burrower breach behavior with tactical priority for WNG containment projectors, doors/gates/bulkheads, walls and barricades before generic hostile structures;
- Artillery ranged support behavior;
- autonomous Replicator faction roster containing Drone, Hunter, Bulwark, Controller, Repairer, Burrower, Artillery, Titan and Siege Mass;
- powered Replicator containment projector that blocks hostile assimilation/recombination and freezes dangerous Matter reassembly while powered;
- player-owned safety preventing autonomous hostile-style assimilation/recombination;
- Child's Toy as a player-owned mech branch that physically transforms into an ordinary hostile Replicator Drone after a tunable feral/uncontrolled period.

## Current verification status

The fresh block Replicator implementation was verified with temporary public GitHub Actions checks and the temporary workflow was then deleted.

Latest completed verification before cleanup:
- RimWorld 1.6 C# assembly build: **SUCCESS**
- Def XML syntax parse: **SUCCESS**

Do not recreate a permanent release-lock/audit framework. Use only temporary/minimal checks when needed to establish that newly written code and Defs function.

## Explicitly unfinished block-related dependencies

These are tracked and must not be forgotten:

- **Grav adaptation gameplay effect:** learned state and retained overlay exist, but the actual mobility/grav effect must bind to WNG's real later gravtech implementation. Do not invent an unrelated placeholder buff.
- **Full anti-shield interaction:** evidence/learning state exists, but countermeasure behavior against later concrete shield systems remains dependent on those systems existing.
- **Queen sovereign control domain:** the exact Queen must later provide genuine sovereign access/control over block Replicators.
- **Asuran sovereign consequence:** only physical successful Queen capture grants later Asuran/Lattice sovereign block-Replicator access.
- **Mixed human-form + block raids:** remain a later human-form/Asuran-layer integration.
- **Broader deliberate player sovereign control commands:** block safety exists now; richer intentional control belongs with the later sovereign/control layer.

If full reconciliation discovers another block feature, add it rather than silently omitting it.

## Major later-plan reminders

- Wraith are one identity/xenotype with caste PawnKinds such as Hunter, Warrior, Commander, Keeper and Queen; backstories are biography, not races/castes.
- Ordinary Wraith Drain Life never opens the strategic feeding-request popup.
- Strategic Wraith faction hunger is separate and drives genuine feeding requests and escalating attack pressure when unresolved/refused.
- Mature-Hive feeding ecology and mature-Hive retaliation are separate from strategic hunger.
- Use **Wraith Grav Engine**, not obsolete Gravcore substitution.
- Human-form Replicators/Asurans are nanite humanoids, distinct from block Replicator custom forms.
- Mixed block + human-form raid composition can be intentional.
- Queen is one exact female human-form Replicator, age 13 in the current first-build design, held in a real cryosleep chamber.
- Queen becomes player-recruited immediately upon release/spawn.
- Asuran/Lattice recovery operatives try to capture her during the vault encounter.
- Capture is committed only when a hostile carrier physically exits the map with the exact Queen.
- While she remains player-owned, Asurans may later make occasional capture raids against **any player map where she is physically present**; this is not restricted to home maps.
- If captured, the Lattice gains genuine sovereign use of block Replicators in appropriate threats, not a fake `+1 outbreak` bonus.
- Old day-84 discovery pacing was rejected. Major WNG content must be reachable in short campaigns and story/event pacing must remain tunable rather than buried in code.
- CatCraft Stargates! integration is optional; CatCraft owns gate networking, WNG owns WNG incidents/craft/objectives.
- Both Wraith and Asuran/Precursor Odyssey gravship families remain planned and must be functionally distinct.
- Professional art/audio remains part of the full mod, but approved Replicator graphics are currently preserved and should not be casually replaced.

## Process rules that must not regress

- Vardath is the author and final design authority.
- Follow the current plan rigorously for the first complete build.
- Nothing is permanently set in stone; Vardath may redesign any part later.
- Do not omit features.
- Do not bury author-tunable design/balance choices as scattered magic numbers or immutable constants.
- Prefer Defs/settings/centralized configuration where practical for tunable behavior.
- Historical source is reference evidence only, not a code authority.
- Do not call any old checkpoint known-good.
- Do not use private-repository credits for this rebuild.
- Do not generate new art unless Vardath explicitly asks for it.
- Do not ask Vardath to repeat requirements already recorded in the continuity set.
- Continue implementation when told to continue; do not stop after a context summary.
