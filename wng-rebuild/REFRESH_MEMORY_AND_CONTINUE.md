# WNG — refresh memory and continue

Read this before touching WNG after any context reset.

Author/final design authority: **Vardath**.

# NO CHECKPOINTS / NO PASS LOGS

Checkpoint files and the rebuild pass log were removed on 2026-09-12 by explicit Vardath instruction.

Do **not** recreate them. Do **not** recover project direction from old checkpoint/pass-log prose, pass numbers, stale validation notes or a short “next step” sentence.

# ACTIVE AUTHORITY ORDER

1. Newest explicit Vardath instruction.
2. `STANDING_RULES.md`.
3. `MASTER_PLAN.md` + active `MASTER_PLAN_APPEND_*` files + `CORRECTIONS_LOG.md`.
4. `CANONICAL_RECOVERY_LEDGER.md` for recovered historical/design context and superseded-decision evidence.
5. Actual current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` for implementation truth: what currently exists in code/Defs/assets.
6. `PUBLIC_RECONCILIATION_2026-09-11.md`, `CURRENT_PUBLIC_STATE.md`, feature maps and repository contracts only as supporting reference where they still agree with the plan and current public source.

**The plan decides what WNG must become. Current public source decides what has already been built.**

There are no known-good historical WNG builds. Private/old source is reference evidence only.

# RECOVERY PROCEDURE

When told “refresh memory and continue”:

1. Load PAIN if it is not already loaded.
2. Read `STANDING_RULES.md`.
3. Read `MASTER_PLAN.md` completely.
4. Read all active master-plan append files completely.
5. Read `CORRECTIONS_LOG.md` completely.
6. Read `CANONICAL_RECOVERY_LEDGER.md` completely so recovered requirements/history are not lost.
7. Read `WNG_IMPLEMENTATION_CHECKLIST.md` and `PLAN_EXECUTION_PROTOCOL.md`.
8. Read the relevant feature map/contract for the plan section being worked on.
9. Fetch actual current public WNG `main` and inspect newer commits/files before deciding what is absent.
10. Compare current implementation against the plan, choose the next genuinely unfinished plan requirement, implement it, verify it, and reconcile back against the plan.

Do not make Vardath repeat decisions already preserved in the plan/history. Raw chat retrieval is only for a genuine unresolved conflict/gap, current-source contradiction, or explicit Vardath request.

# CORE BUILD RULES

- WNG is a Stargate mod. Establish Stargate identity/function before code.
- Never silently omit a planned feature.
- Never delete an existing required feature merely because an older note says rebuild/correct/refine.
- Preserve approved block Replicator graphics and intended block behavior.
- Block Replicator hierarchy remains Drone -> Hunter -> Bulwark -> Titan -> Siege Mass with real destruction breakup downward.
- Replicator specialists/adaptations remain required and tracked.
- Ordinary Wraith Drain Life, strategic faction hunger, mature-Hive local ecology and mature-Hive retaliation are separate systems.
- Wraith castes are PawnKind/role layers under one Wraith identity, not separate races.
- Human-form Replicators/Asurans are distinct from block Replicators.
- Queen sovereignty, Sovereign Neural Lattice authority and Temporary Asuran intrusion are distinct control layers.
- Use Wraith Grav Engine, not obsolete Wraith Gravcore semantics.
- CatCraft owns Stargate network/dial/iris/receive mechanics.
- Do not invent Goa'uld ship fuel/resource fallbacks.
- Do not generate replacement art unless Vardath explicitly asks.
- Planned Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty content stays planned-only until Vardath advances it.

# CURRENT-SOURCE RULE

Never claim a feature exists because it was discussed, historically implemented, prepared on a branch or described in a continuity document. Verify current public `main`.

Likewise, never rebuild a feature merely because an old continuity note says it was unfinished. Inspect current source first.

# CONTINUITY AFTER WORK

Keep the plan/corrections/current-state description truthful when a meaningful implementation changes them. Do not create checkpoint files, pass logs or numbered pass diaries.

The objective is simple: Vardath should be able to say **“refresh memory and continue”** and implementation resumes from the plan and actual public source without reconstruction or checkpoint archaeology.
