# WNG RimWorld 1.6 rebuild handoff

This directory is the independent continuity/handoff record for rebuilding **Wraith & Nanite Gravtech (WNG)** from scratch.

Author and design authority: **Vardath**.

Active mod repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

This website repository is being used as the durable requirements/continuity copy because private-repository work is currently unavailable/undesired. Do not require access to the private WNG repository to continue the rebuild.

## Read in this order when told “refresh memory and continue”

1. `wng-rebuild/STANDING_RULES.md`
2. `wng-rebuild/PLAN_EXECUTION_PROTOCOL.md`
3. `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`
4. `wng-rebuild/CORRECTIONS_LOG.md`
5. `wng-rebuild/MASTER_PLAN.md`
6. Active subsystem notes such as `wng-rebuild/REPLICATOR_HIERARCHY.md` and `wng-rebuild/REPLICATOR_QUEEN.md`.
7. `wng-rebuild/NEXT_GPT_PRIMER.md` for the latest handoff snapshot, then verify it against current public `main`.
8. Inspect the current public `Vardath/Wraith-Nanite-Gravtech-1.6` tree and continue the next unfinished subsystem.

## Mandatory working method

Do not code from memory and then check the plan afterwards.

For each subsystem use:

**read -> reconcile -> inventory -> map relationships -> implement -> account for every known item -> then move on.**

The plan is the default specification for the first complete build. Every known planned feature must be implemented, explicitly tracked as unfinished with its dependency recorded, or explicitly changed/rejected by Vardath. Silent omission is not acceptable.

## Reset instruction — 2026-09-10

The 1.6 mod has been restarted again from a clean tree.

Preserve only the approved **block Replicator graphics** and the useful Replicator behavioral design; behavior may be freshly reconstructed rather than blindly copied. Everything else is to be rebuilt from the current plan.

There is no “known-good” old mod state. Historical implementations may be used as design reference only.

**Do not omit any planned feature.** If a feature is not yet implementable, keep it explicitly tracked as unfinished rather than silently simplifying it away.

Do not create design-locking anti-regression machinery. Do not build release-check bureaucracy around an unfinished mod. Use only the minimum sanity/compile/load checks actually needed to know that the implementation works.

Nothing in the mod is immutable merely because it appears in this plan. Timers, races/xenotypes, castes, sounds, art, processes, systems, balance, quests, factions, progression and whole subsystems can all be changed later by Vardath. The plan records the intended first complete build, not permanent law.
