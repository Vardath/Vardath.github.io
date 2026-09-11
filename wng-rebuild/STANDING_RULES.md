# WNG rebuild — standing rules

Author/design authority: **Vardath**.

These rules apply at the start of every WNG continuation and throughout the rebuild. Read them before interpreting old code, old plans, old audits or prior assistant summaries.

0. **⛔ FULL WNG CHAT HISTORY + STARGATE LORE FIRST — mandatory before every pass.** Before touching WNG code, retrieve and reconcile all accessible relevant prior WNG conversations for the subsystem and adjacent affected systems. Handoff summaries, memory summaries, repo notes and prior assistant recaps are not substitutes for the underlying chat history when it is accessible. If Vardath says read/check/review chat history, retrieval is mandatory. Reconcile contradictions chronologically: **newest explicit Vardath instruction wins**. Then read and answer `WNG_IMPLEMENTATION_CHECKLIST.md`: establish what this is in Stargate, what it actually does there, what Vardath said about it in chat/history, what current public WNG already does, what historical WNG attempted, what vanilla RimWorld/Odyssey already provides, and only then decide the best faithful implementation. Do not code a generic sci-fi substitute and check lore/history afterwards. If literal full transcripts are not technically available, do not pretend they are; retrieve all accessible history in multiple focused passes before code is changed.
1. **Do not omit any feature.** If a feature, subsystem, branch, faction, caste, race/xenotype, PawnKind, Replicator form, adaptation path, quest, event, integration, craft, gravship part, resource, art family, sound family, UI flow or behavior exists in the current plan/history, it must either be implemented in the rebuild or remain explicitly tracked as unfinished. Never silently simplify it away because it looks secondary, difficult, redundant or inconvenient.
2. **Vardath is the mod author and final design authority.** Assistant implementation choices are proposals, not permanent doctrine.
3. **There are no known-good historical builds.** Old code/builds are reference material only.
4. **Rebuild cleanly rather than preserving accumulated mistakes.** Keep only explicitly preserved assets/behavior and reconstruct the rest from the current plan.
5. **Nothing is set in stone.** Timers, races/xenotypes, castes, PawnKinds, sounds, art, recipes, resources, balance, quests, progression, UI, processes, systems and the whole mod may be changed later if Vardath dislikes the result.
6. **Do not hard-code author-tunable design choices as buried magic numbers or immutable doctrine.** Prefer Defs, settings, centralized configuration or clearly editable data where practical. Technical/internal constants are fine when they are implementation details rather than design locks.
7. **Do not build anti-regression or release-check bureaucracy.** Use only the minimum compile/load/reference sanity needed to implement a functioning mod. Tests must not freeze design choices.
8. **Do not confuse identity layers.** Race/xenotype, caste/PawnKind, faction role and backstory/biography are separate concepts.
9. **Do not merge separate gameplay systems merely because they are thematically related.** In particular, ordinary Wraith feeding, strategic Wraith faction hunger, mature-Hive feeding ecology and mature-Hive retaliation are distinct systems.
10. **Do not substitute a reduced approximation for a planned feature without recording that it is incomplete.** A marker gene is not a finished mechanic; flavor text is not a finished infiltration system; a faction flip is not necessarily a complete sovereign-control system; a bare site is not a complete quest environment.
11. **Do not erase corrections.** Append/update the website continuity documents when Vardath corrects the design or process so later refreshes can see how the plan evolved.
12. **Do not depend on the private WNG repository for current work.** Use the public `Vardath/Wraith-Nanite-Gravtech-1.6` repository and the durable continuity copy under `Vardath/Vardath.github.io/wng-rebuild/` unless Vardath explicitly changes this. Older chat instructions that made the private repo authoritative are historical evidence only and are superseded by the current public-repo instruction.
13. **Do not generate replacement art unless Vardath asks for image/art generation or a specific art task requires it.** Existing approved Replicator graphics are to be preserved through the current reset.
14. **Continue the build after refreshing memory.** Do not stop after summarizing context when the user asked to continue.
15. **Follow the plan rigorously before writing code.** Do not implement a subsystem from partial memory, a previous assistant summary, or whichever files happen to be open. Before changing a subsystem, perform the complete reconciliation procedure in `PLAN_EXECUTION_PROTOCOL.md`. Build an explicit feature inventory from the standing rules, corrections log, master plan, active subsystem notes, retained assets/graphics, current public source/Defs, relevant retrieved chat history, and relevant historical/reference evidence. Only then implement. Every known item in that inventory must end the pass as implemented, intentionally deferred with a recorded dependency, or explicitly rejected/changed by Vardath. Never let an item disappear because it was forgotten.
16. **The plan is the default implementation authority for the first complete build.** Do not improvise away from it merely because another implementation seems easier. If implementation reality requires a departure, record the issue and make the smallest practical adjustment consistent with Vardath's instructions; if the design itself needs changing, Vardath decides.
17. **Current public state beats stale “next step” prose.** Before treating anything as absent, unfinished or safe to rebuild, inspect current public `main` and recent implementation history. An older note saying “next”, “unfinished”, “reconcile”, “correct” or “rebuild” is not proof the feature is absent. **Rebuild/correct/refine does not mean remove. A named required feature remains required unless Vardath explicitly removes it.**

## Mandatory pre-implementation rule

For every subsystem, the order is:

**FULL ACCESSIBLE WNG CHAT HISTORY -> STARGATE LORE -> VARDATH/CHAT CHRONOLOGY -> CURRENT PUBLIC STATE -> HISTORICAL EVIDENCE -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> HANDOFF**

The detailed gate is `WNG_IMPLEMENTATION_CHECKLIST.md` and must be answered before code is written.

Do not reverse that order. In particular, do not start writing code and then use the plan, chat history or Stargate lore afterwards to discover what was forgotten or what the feature was actually supposed to do.

The explicit procedure is in `PLAN_EXECUTION_PROTOCOL.md` and is part of the rebuild plan.

## Completeness rule for the current reset

Before leaving a subsystem and moving to another one, compare it against the entire current plan/history for that subsystem and make sure no known branch has been silently dropped. If part of the subsystem cannot yet be completed because another dependency is missing, record it explicitly in the plan/continuity notes and return to it when the dependency exists.

For Replicators specifically, this means the fresh rebuild must account for more than the main Drone -> Hunter -> Bulwark -> Titan -> Siege Mass combat ladder. It must also preserve/reconstruct the specialist/adaptation branches described in the plan/history, including Controller, Repairer, Burrower, Artillery/Siege support, ranged adaptation, armor adaptation, power adaptation, grav adaptation, **shield adaptation / shield Replicators and their anti-shield development**, matter economy, EMP behavior, containment, swarm coordination, player behavior, Child's Toy branch, human-form interactions and later sovereign/Asuran interactions. None of those may be silently omitted just because the first scaffold does not implement them yet.
