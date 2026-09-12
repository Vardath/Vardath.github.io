# WNG rebuild — mandatory plan execution protocol

Author/design authority: **Vardath**.

This protocol governs implementation order. Checkpoint files and pass logs were removed on 2026-09-12 by explicit Vardath instruction and must not be recreated.

# CORE RULE

**Do not code a subsystem from memory. Read the plan first, inspect actual current public source second, then implement only the genuinely unfinished plan requirement.**

The master plan and active append files define the target. Current public source defines what already exists.

# AUTHORITY ORDER

1. Newest explicit Vardath instruction.
2. `MASTER_PLAN.md` + relevant `MASTER_PLAN_APPEND_*` files + `CORRECTIONS_LOG.md`.
3. `STANDING_RULES.md` and `WNG_IMPLEMENTATION_CHECKLIST.md`.
4. `CANONICAL_RECOVERY_LEDGER.md` for recovered historical/design context.
5. Actual current public `Vardath/Wraith-Nanite-Gravtech-1.6` source/Defs/assets for implementation truth.
6. Reconciliation/current-state/feature-map/contract documents as supporting reference only where consistent with the plan and current source.

Private/old WNG is reference evidence only. There are no known-good historical builds.

# REQUIRED PROCEDURE

## 1. Read the plan slice completely

Before touching a subsystem:
- read the relevant master-plan section;
- read every active append that affects it;
- read corrections that supersede older wording;
- identify every required feature/branch, not just the easiest or most visible one.

Do not let a short handoff or stale “next” sentence replace the plan.

## 2. Establish Stargate identity and function

For every planned feature establish:
- what it is in Stargate;
- what it actually does;
- who uses/owns it;
- scale, limitations and interactions;
- visual/audio/behavioral identity;
- Vardath's intended WNG representation.

Do not implement generic sci-fi first and retrofit lore afterwards.

## 3. Inspect current public implementation

Fetch actual current public `main` and inspect affected source/Defs/assets/recent commits.

Determine:
- what already exists;
- what is complete vs partial;
- what the plan still requires;
- what existing behavior must be preserved;
- what current dependencies and integrations already rely on it.

Never rebuild a feature merely because old notes/private code say it was unfinished. Never claim it exists merely because old notes/private code say it was completed.

## 4. Build a complete relationship map

Account for, where relevant:
- race/xenotype/caste/PawnKind/faction/backstory layers;
- hierarchy and transformations;
- controller domains/authority;
- resources/economy;
- research/acquisition/progression;
- incidents/sites/quests;
- exact-pawn/save-load transaction state;
- native RimWorld/DLC ownership;
- CatCraft/ONAC/RimGate ownership and exact verified IDs;
- retained assets;
- art/audio/UI requirements;
- author-tunable values.

No planned item may silently disappear.

## 5. Reuse native RimWorld/DLC behavior where faithful

Prefer native mechanics for boarding, transport, gravships, power, fuel, genes, surgery, factions, containment, research analysis, world travel, save/load and similar systems when they correctly express the plan.

Add WNG custom logic only for Stargate-specific behavior that native systems do not provide.

Do not create unnecessary parallel systems or hijack optional-mod ownership.

## 6. Preserve tunability

Prefer Defs/settings/centralized configuration for author-facing timing, costs, caps, frequencies, cooldowns, combat values and progression thresholds.

Do not create tests or constants whose purpose is to freeze design choices.

## 7. Implement the whole accounted slice

Implementation may be staged, but every planned item in the affected slice must remain one of:
- implemented;
- explicitly unfinished/dependency-recorded;
- planned-only/deferred;
- changed/rejected by Vardath.

There is no forgotten/silently removed state.

Do not use flavor text, marker genes, empty comps or decorative objects as substitutes for required mechanics.

Do not invent arbitrary fallback resources, factions, fuels or technologies for convenience.

## 8. Verify proportionately

Use only practical verification needed for the slice:
- compile/build;
- XML/Def/reference checks;
- API/state/transaction inspection;
- real RimWorld/save-load/log testing where required and available.

Static green is not live-game proof. Actual `Player.log`, RimDoctor, screenshots and observed gameplay outrank static assumptions.

Do not rebuild the old audit/release bureaucracy.

## 9. Reconcile back against the plan

Before moving on:
- reread the affected plan slice;
- confirm all planned branches remain accounted for;
- confirm no existing required feature was accidentally removed;
- record genuine unfinished dependencies where useful;
- write new Vardath corrections back into durable plan/corrections material;
- keep current-state description truthful if public implementation materially changed.

Do not create checkpoint files, pass logs, pass-number ledgers or branch-status diaries.

# MANDATORY WORKING ORDER

**NEWEST VARDATH INSTRUCTION -> MASTER PLAN + ACTIVE APPENDS + CORRECTIONS -> RELEVANT RECOVERED HISTORY -> STARGATE LORE/FUNCTION -> CURRENT PUBLIC SOURCE/ASSETS -> NATIVE/OPTIONAL-MOD MECHANICS -> COMPLETE FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE AGAINST PLAN**

The objective is that “refresh memory and continue” means: recover the plan, inspect actual public source, and keep building—without checkpoint archaeology.
