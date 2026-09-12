# WNG rebuild — standing rules

Author/design authority: **Vardath**.

These rules govern every WNG continuation. They supersede older checkpoint/pass-log procedures.

# 0. AUTHORITY ORDER — PLAN FIRST, NO CHECKPOINTS

The active authority order is:

1. **Newest explicit Vardath instruction.**
2. **`MASTER_PLAN.md` + active master-plan append(s) + `CORRECTIONS_LOG.md`.** These define what WNG is supposed to be and what must be built.
3. **`CANONICAL_RECOVERY_LEDGER.md`** only as recovered history/design evidence and for superseded-decision context.
4. **Current public `Vardath/Wraith-Nanite-Gravtech-1.6` source/Defs/assets** as implementation truth for what already exists right now.
5. `PUBLIC_RECONCILIATION_2026-09-11.md`, `CURRENT_PUBLIC_STATE.md`, feature maps, old contracts and historical/private work as supporting state/reference evidence only where still consistent with the plan and current public source.

**There are no WNG checkpoint files and there is no WNG pass-log authority. Do not recreate them. Do not decide the next task from an old checkpoint, pass number, short handoff, stale “next” sentence or validation note.**

The plan decides what remains required. Current public source decides what has already been implemented. The next implementation work is the next genuinely unfinished requirement in the plan after checking actual public source.

# 1. CURRENT REPOSITORY AUTHORITY

- Active implementation repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable design/continuity repository: public `Vardath/Vardath.github.io/wng-rebuild/`.
- Private/old WNG repositories and branches are **reference evidence only** unless Vardath explicitly says otherwise.
- There are **no known-good historical WNG builds**.
- Never infer that discussed, prepared, private, branch-only or historical work exists in the current mod. Verify public `main`.

# 2. FOLLOW THE PLAN, DO NOT IMPROVISE A DIFFERENT MOD

- The plan is the default first-build specification.
- Do not simplify away a required feature because it is difficult, inconvenient or secondary.
- Every planned feature must end up implemented, explicitly still unfinished, explicitly deferred/planned-only, or explicitly changed/rejected by Vardath.
- `rebuild`, `correct`, `refine`, `reconcile`, `unfinished` and `next` never mean delete a required existing feature.
- Vardath can change any part of the plan. Newer instructions override older wording and should be written back into the plan/corrections when appropriate.

# 3. WNG IS A STARGATE MOD

Before implementing a subsystem:

1. establish what it is in Stargate;
2. establish what it actually does, who uses it, its scale and limitations;
3. read the relevant plan section and active append/contract;
4. inspect current public source to see what already exists;
5. inspect native RimWorld 1.6/DLC mechanics and verified optional-mod ownership;
6. implement the smallest faithful WNG layer needed.

Do not create generic sci-fi substitutes and retrofit Stargate names afterwards.

# 4. DO NOT OMIT FEATURES OR IDENTITY LAYERS

Race/xenotype, caste/PawnKind, faction role and biography/backstory are separate concepts.

Important examples:
- Wraith are one Wraith identity/xenotype with caste/PawnKind roles such as Hunter, Warrior, Commander, Keeper and Queen.
- Human-form Replicators/Asurans are nanite humanoids, distinct from block Replicators.
- Block Replicator size hierarchy, specialists, adaptations and controller authority are separate layers.

For Replicators, the required physical hierarchy remains:

**Drone -> Hunter -> Bulwark -> Titan -> Siege Mass** upward through recombination, and genuine destruction breaks downward through the same ladder.

The specialist/adaptation ecology must remain accounted for, including Controller, Repairer, Burrower, Artillery, Armor, Ranged, Power, Grav, Shield and AntiShield/countermeasure development.

Approved block Replicator graphics remain preserved. Do not generate replacement art unless Vardath explicitly asks for it.

# 5. KEEP DISTINCT GAMEPLAY SYSTEMS DISTINCT

Do not merge systems merely because they share a theme.

Especially:
- ordinary Wraith Drain Life/feeding;
- strategic Wraith faction hunger/request pressure;
- mature-Hive local feeding ecology;
- mature-Hive neutralization/retaliation;

are separate systems.

Likewise Queen sovereignty, Sovereign Neural Lattice authority and Temporary Asuran intrusion are distinct control identities.

# 6. PRESERVE EXACT IDENTITY AND SAVE/LOAD STATE WHERE IT MATTERS

Do not replace exact pawns with proxy recreations when story or control continuity depends on identity.

Stateful systems include, where relevant:
- Replicator split/recombine/adaptation/control state;
- exact Queen identity/capture/sovereignty;
- temporary controller override/restoration;
- Neural Interface copies;
- exact Wraith abductees/captives/rescue;
- strategic faction hunger/request state;
- shuttle/ring/gravship cargo and transport state;
- living-tech incubation;
- mature-Hive population/retaliation.

At-most-once transactions must remain at-most-once through reload.

# 7. USE NATIVE RIMWORLD/DLC SYSTEMS WHEN THEY FIT

Prefer native RimWorld 1.6, Biotech, Odyssey, Royalty, Ideology and Anomaly systems when they faithfully perform the intended function.

Do not replace correct native boarding, transport, gravship, power, fuel, faction, gene, surgery, containment, research-analysis or save/load behavior with unnecessary parallel systems.

For optional Stargate mods, verify exact package/Def identities from source and respect ownership boundaries. CatCraft owns its Stargate network/dial/iris/receive behavior. ONAC/RimGate own their Goa'uld/Tok'ra/Jaffa systems. Do not guess external Def names.

# 8. NO INVENTED FALLBACKS TO SOLVE IMPLEMENTATION INCONVENIENCE

Do not invent resources, fuels, factions or replacement mechanics merely because integration is difficult.

In particular:
- use **Wraith Grav Engine**, not obsolete Wraith Gravcore semantics;
- do not invent uranium/chemfuel or another arbitrary standalone Goa'uld ship fallback;
- Puddle Jumper final power/fuel design must be deliberate rather than convenience-driven;
- hostile Ha'tak takeoff must not be faked through deletion/proxy replacement if Odyssey ownership prevents a real implementation.

# 9. AUTHOR-TUNABLE DESIGN STAYS TUNABLE

Do not bury story timing, cooldowns, raid/request frequency, population caps, resource costs, combat tuning or progression thresholds as scattered immutable doctrine.

Use Defs/settings/centralized configuration where practical. Technical constants are fine when they are genuinely implementation details.

# 10. NO DESIGN-LOCKING AUDIT BUREAUCRACY

Do not rebuild the old anti-regression/release-check machinery.

Use only proportionate checks needed to establish function:
- compile/build when needed;
- XML/Def/reference sanity;
- direct code/API inspection;
- real RimWorld testing, save/load testing, screenshots, `Player.log` and RimDoctor where applicable.

Static green does not equal live gameplay validation.

# 11. WORKING ORDER FOR EVERY IMPLEMENTATION SLICE

**PLAN + CORRECTIONS -> RELEVANT RECOVERED HISTORY -> STARGATE LORE/FUNCTION -> CURRENT PUBLIC SOURCE/ASSETS -> NATIVE/OPTIONAL-MOD MECHANICS -> COMPLETE FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE AGAINST THE PLAN**

Do not write code from memory and then consult the plan afterwards.

# 12. CONTINUITY WITHOUT CHECKPOINTS

After meaningful work, update the durable **plan/corrections/current-state description only when needed to keep them truthful**. Do not create checkpoint files, pass logs, numbered-pass ledgers or branch-status diaries.

A state document may describe what public source contains, but it never outranks the plan and never chooses the next feature by itself.

# 13. CONTINUE WHEN ASKED TO CONTINUE

When Vardath says “refresh memory and continue”, recover the plan and current source and continue implementation. Do not stop at a summary and do not make Vardath reconstruct decisions already preserved in the plan/history.
