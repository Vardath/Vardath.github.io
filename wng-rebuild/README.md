# WNG RimWorld 1.6 rebuild handoff

This directory is the independent continuity/handoff record for rebuilding **Wraith & Nanite Gravtech (WNG)** from scratch.

Author and design authority: **Vardath**.

Active mod repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

This website repository is being used as the durable requirements/continuity copy because private-repository work is currently unavailable/undesired. Do not require access to the private WNG repository to continue the rebuild.

## Read in this order when told “refresh memory and continue”

1. `wng-rebuild/STANDING_RULES.md`
2. `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`
3. `wng-rebuild/CORRECTIONS_LOG.md`
4. `wng-rebuild/MASTER_PLAN.md`
5. `wng-rebuild/REPLICATOR_QUEEN.md` when working on the Queen/Asuran branch.
6. Inspect the current public `Vardath/Wraith-Nanite-Gravtech-1.6` tree and continue the next unfinished subsystem.

## Reset instruction — 2026-09-10

The 1.6 mod is being restarted again from a clean tree.

Preserve only the approved **block Replicator graphics** and the useful Replicator behavioral design; behavior may be freshly reconstructed rather than blindly copied. Everything else is to be rebuilt from the current plan.

There is no “known-good” old mod state. Historical implementations may be used as design reference only.

**Do not omit any planned feature.** If a feature is not yet implementable, keep it explicitly tracked as unfinished rather than silently simplifying it away.

Do not create design-locking anti-regression machinery. Do not build release-check bureaucracy around an unfinished mod. Use only the minimum sanity/compile/load checks actually needed to know that the implementation works.

Nothing in the mod is immutable merely because it appears in this plan. Timers, races/xenotypes, castes, sounds, art, processes, systems, balance, quests, factions, progression and whole subsystems can all be changed later by Vardath. The plan records the intended first complete build, not permanent law.
