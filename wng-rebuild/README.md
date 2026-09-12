# WNG RimWorld 1.6 rebuild continuity

Author/final design authority: **Vardath**.

Active implementation repository: `Vardath/Wraith-Nanite-Gravtech-1.6`.

This directory stores the durable WNG plan, corrections, recovered history and descriptive current-state material.

# Plan-first rule

**Do not use checkpoint files, pass logs, pass numbers or stale short handoffs to decide what to build. They were removed on 2026-09-12 by explicit Vardath instruction and must not be recreated.**

The authority order is:

1. newest explicit Vardath instruction;
2. `MASTER_PLAN.md` + active master-plan append files + `CORRECTIONS_LOG.md`;
3. `STANDING_RULES.md` and the mandatory implementation protocol/checklist;
4. `CANONICAL_RECOVERY_LEDGER.md` for recovered historical/design context;
5. actual current public WNG `main` for implementation truth — what already exists;
6. reconciliation/current-state/feature-map/contract documents as supporting reference only where they agree with the plan and current source.

**The plan defines the target. Public source defines the present implementation.**

There are no known-good historical WNG builds. Old/private repositories and branches are reference evidence only.

## Recovery order for “refresh memory and continue”

1. Load PAIN if needed.
2. Read `STANDING_RULES.md`.
3. Read `MASTER_PLAN.md` completely.
4. Read every active `MASTER_PLAN_APPEND_*` file completely.
5. Read `CORRECTIONS_LOG.md` completely.
6. Read `CANONICAL_RECOVERY_LEDGER.md` completely so recovered requirements/history are not lost.
7. Read `WNG_IMPLEMENTATION_CHECKLIST.md` and `PLAN_EXECUTION_PROTOCOL.md`.
8. Read the relevant feature map/contract for the plan section being implemented.
9. Fetch actual current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and inspect newer commits/files before deciding what is missing.
10. Reconcile current implementation against the plan and continue the next genuinely unfinished plan requirement.

Do not reread weeks of raw chat by default. Retrieve raw WNG history only for a real unresolved conflict/gap, a repo-vs-plan contradiction, or an explicit Vardath request.

## Non-negotiable process rules

- WNG is a Stargate mod: lore/function first.
- Do not code from memory and consult the plan afterwards.
- Do not silently omit features.
- Do not remove an existing required feature because an older note says rebuild/correct/refine.
- Current public source must be inspected before deciding something is absent.
- Preserve approved block Replicator graphics and intended behavior.
- Keep Wraith ordinary feeding, strategic hunger, mature-Hive ecology and retaliation separate.
- Keep Queen, Neural-Lattice and Temporary-Asuran controller identities separate.
- Use native RimWorld/DLC systems when they faithfully fit.
- Respect CatCraft/ONAC/RimGate ownership boundaries and verified Def/package IDs.
- Do not invent convenience fallbacks such as arbitrary Goa'uld ship fuel.
- Do not generate replacement art unless Vardath explicitly asks.
- Do not rebuild design-locking audit/release bureaucracy.
- Static validation is not live-game validation.

## Continuity after changes

Update the master plan/corrections/current-state description only when needed to keep them truthful. Do not create checkpoint files, numbered pass diaries or rebuild pass logs.

The intended workflow is simple: **plan -> inspect current source -> implement unfinished plan requirement -> verify -> reconcile against plan -> continue.**
