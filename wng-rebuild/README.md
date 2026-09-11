# WNG RimWorld 1.6 rebuild handoff

This directory is the durable continuity/handoff record for rebuilding **Wraith & Nanite Gravtech (WNG)**.

Author and design authority: **Vardath**.

Active mod repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

The one-time broad chat/history reconstruction was consolidated on **2026-09-11** into `CANONICAL_RECOVERY_LEDGER.md`.

A later contradiction was then found: the canonical ledger's implementation snapshot was 45 public commits behind current `main`, while later checkpoint prose still overstated several subsystems as complete. The completed public-vs-plan/private audit is therefore preserved separately in:

**`PUBLIC_RECONCILIATION_2026-09-11.md`**

That reconciliation must be read before using any old implementation-status/"next" statement.

## Read in this order when told “refresh memory and continue”

1. `wng-rebuild/STANDING_RULES.md`
2. **`wng-rebuild/CANONICAL_RECOVERY_LEDGER.md` — recovered project history/design.**
3. **`wng-rebuild/PUBLIC_RECONCILIATION_2026-09-11.md` — authoritative completed public-vs-plan/private reconciliation.**
4. **`wng-rebuild/CURRENT_PUBLIC_STATE.md` — mutable current implementation state.**
5. **`wng-rebuild/WNG_IMPLEMENTATION_CHECKLIST.md` — mandatory Stargate/current-state implementation gate.**
6. `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`
7. `wng-rebuild/PLAN_EXECUTION_PROTOCOL.md`
8. Relevant current master-plan append/active subsystem contract(s) for the actual next slice.
9. `wng-rebuild/CORRECTIONS_LOG.md` and `wng-rebuild/MASTER_PLAN.md` when deeper design chronology is needed.
10. `wng-rebuild/NEXT_GPT_PRIMER.md` only as a short pointer; it never outranks current public source/reconciliation/live state.
11. Fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`, compare it with the maintained HEAD/state, inspect any new commits, and continue only the genuinely unfinished slice.

### Hard public-state rule

**Current public source is implementation truth.**

Do not claim a feature exists merely because:
- it was discussed in chat;
- an assistant said it was completed;
- a checkpoint says it was completed;
- code exists on the old/private repository;
- a private commit/branch was prepared;
- a historical build once had something similar.

Historical/private work is requirement/reference evidence only unless an equivalent real implementation is present on current public `main`.

### Raw-chat retrieval rule

Do **not** reread weeks of WNG chat by default after the one-time reconstruction/reconciliation. Retrieve older raw WNG chat only when:
- the canonical history or public reconciliation flags a genuine unresolved gap/conflict;
- current repo evidence conflicts with the maintained state; or
- Vardath explicitly asks for raw-history review.

When a conflict is resolved, update durable continuity so it does not need to be solved again.

## Mandatory working method

Do not code from memory and then check the plan afterwards.

For every pass:

**CANONICAL HISTORY -> PUBLIC RECONCILIATION -> CURRENT PUBLIC STATE -> STARGATE LORE -> CURRENT REPO -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE HANDOFF**

The plan is the default specification for the first complete build. Every known planned feature must be implemented, explicitly tracked as unfinished/dependency-recorded, explicitly planned-only/deferred, or explicitly changed/rejected by Vardath. Silent omission is not acceptable.

**An older “next step”, “unfinished”, “reconcile”, “correct” or “rebuild” note does not prove a current feature is absent. Verify current public `main` first. Rebuild/correct/refine does not mean remove.**

## Reset instruction — 2026-09-10

The public 1.6 mod was deliberately restarted from a clean fresh-rebuild tree.

The fresh rebuild preserved approved **block Replicator graphics** and reconstructed intended Replicator behavior cleanly. Historical implementations are reference evidence only; there is no known-good old state.

The current public repository has advanced substantially beyond the reset. **Do not interpret the reset instruction or the canonical ledger's original implementation snapshot as the current inventory.** Use the public reconciliation + current live state + actual public `main`.

Do not create design-locking anti-regression machinery. Do not build release-check bureaucracy around an unfinished mod. Use only the practical sanity/compile/load/live checks needed to establish function.

Nothing in the mod is immutable merely because it appears in this continuity set. Timers, races/xenotypes, castes, sounds, art, processes, systems, balance, quests, factions, progression and whole subsystems can all be changed later by Vardath. Newer explicit Vardath instructions must be written back into durable continuity before handoff.
