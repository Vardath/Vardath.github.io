# WNG rebuild — standing rules

Author/design authority: **Vardath**.

These rules apply at the start of every WNG continuation and throughout the rebuild. Read them before interpreting old code, old plans, old audits or prior assistant summaries.

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
12. **Do not depend on the private WNG repository for current work.** Use the public `Vardath/Wraith-Nanite-Gravtech-1.6` repository and the durable continuity copy under `Vardath/Vardath.github.io/wng-rebuild/` unless Vardath explicitly changes this.
13. **Do not generate replacement art unless Vardath asks for image/art generation or a specific art task requires it.** Existing approved Replicator graphics are to be preserved through the current reset.
14. **Continue the build after refreshing memory.** Do not stop after summarizing context when the user asked to continue.

## Completeness rule for the current reset

Before leaving a subsystem and moving to another one, compare it against the entire current plan/history for that subsystem and make sure no known branch has been silently dropped. If part of the subsystem cannot yet be completed because another dependency is missing, record it explicitly in the plan/continuity notes and return to it when the dependency exists.

For Replicators specifically, this means the fresh rebuild must account for more than the main Drone -> Hunter -> Bulwark -> Titan -> Siege Mass combat ladder. It must also preserve/reconstruct the specialist/adaptation branches described in the plan/history, including Controller, Repairer, Burrower, Artillery/Siege support, ranged adaptation, armor adaptation, power adaptation, grav adaptation, **shield adaptation / shield Replicators and their anti-shield development**, matter economy, EMP behavior, containment, swarm coordination, player behavior, Child's Toy branch, human-form interactions and later sovereign/Asuran interactions. None of those may be silently omitted just because the first scaffold does not implement them yet.
