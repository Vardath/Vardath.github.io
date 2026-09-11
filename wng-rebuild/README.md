# WNG RimWorld 1.6 rebuild handoff

This directory is the durable continuity/handoff record for rebuilding **Wraith & Nanite Gravtech (WNG)**.

Author and design authority: **Vardath**.

Active mod repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

The one-time broad chat/history reconstruction was consolidated on **2026-09-11** into `CANONICAL_RECOVERY_LEDGER.md`. Future sessions should recover from that ledger plus current public `main`, not force Vardath to repeat the project and not reread weeks of raw chat unless a real unresolved conflict/gap requires it.

## Read in this order when told “refresh memory and continue”

1. `wng-rebuild/STANDING_RULES.md`
2. **`wng-rebuild/CANONICAL_RECOVERY_LEDGER.md` — canonical recovered history + current-state ledger.**
3. **`wng-rebuild/WNG_IMPLEMENTATION_CHECKLIST.md` — mandatory Stargate/current-state implementation gate.**
4. `wng-rebuild/REFRESH_MEMORY_AND_CONTINUE.md`
5. `wng-rebuild/PLAN_EXECUTION_PROTOCOL.md`
6. Relevant current master-plan append/active subsystem contract(s) for the actual next slice.
7. `wng-rebuild/CORRECTIONS_LOG.md` and `wng-rebuild/MASTER_PLAN.md` when deeper design chronology is needed.
8. `wng-rebuild/NEXT_GPT_PRIMER.md` only as a short current pointer/snapshot; it never outranks the canonical ledger or current `main`.
9. Fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`, compare it with the ledger's recorded HEAD/state, and continue the genuinely unfinished slice.

### Raw-chat retrieval rule

Do **not** reread weeks of WNG chat by default after the one-time reconstruction. Retrieve older raw WNG chat only when:
- `CANONICAL_RECOVERY_LEDGER.md` flags a genuine unresolved historical gap/conflict;
- current repo evidence conflicts with the ledger; or
- Vardath explicitly asks for raw-history review.

When a conflict is resolved, update the ledger so it does not need to be solved again.

## Mandatory working method

Do not code from memory and then check the plan afterwards.

For every pass:

**CANONICAL LEDGER -> STARGATE LORE -> CURRENT PUBLIC STATE -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE LEDGER/HANDOFF**

The plan is the default specification for the first complete build. Every known planned feature must be implemented, explicitly tracked as unfinished with its dependency recorded, or explicitly changed/rejected by Vardath. Silent omission is not acceptable.

**An older “next step”, “unfinished”, “reconcile”, “correct” or “rebuild” note does not prove a current feature is absent. Verify current public `main` first. Rebuild/correct/refine does not mean remove.**

## Reset instruction — 2026-09-10

The public 1.6 mod was deliberately restarted from a clean fresh-rebuild tree.

The fresh rebuild preserved approved **block Replicator graphics** and reconstructed intended Replicator behavior cleanly. Historical implementations are reference evidence only; there is no known-good old state.

The current public repository has advanced substantially beyond the reset. **Do not interpret this old reset instruction as the current implementation inventory.** Use `CANONICAL_RECOVERY_LEDGER.md` plus current public `main` for present state.

Do not create design-locking anti-regression machinery. Do not build release-check bureaucracy around an unfinished mod. Use only the practical sanity/compile/load/live checks needed to establish function.

Nothing in the mod is immutable merely because it appears in this continuity set. Timers, races/xenotypes, castes, sounds, art, processes, systems, balance, quests, factions, progression and whole subsystems can all be changed later by Vardath. Newer explicit Vardath instructions must be written back into the canonical ledger before handoff.
