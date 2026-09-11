# WNG rebuild — mandatory plan execution protocol

Author/design authority: **Vardath**.

This protocol is part of the WNG rebuild plan. The one-time broad conversation/history reconstruction now lives in `CANONICAL_RECOVERY_LEDGER.md`. The protocol's job is to keep future implementation aligned with that recovered history and current public state without making Vardath reconstruct it again.

# ⛔ FIRST GATE: RECOVER STATE, THEN STARGATE LORE, THEN CODE

Before every implementation pass:

1. read `STANDING_RULES.md`;
2. read `CANONICAL_RECOVERY_LEDGER.md` completely;
3. fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and compare it to the ledger's recorded HEAD/state;
4. read `WNG_IMPLEMENTATION_CHECKLIST.md`;
5. read the active subsystem contract/plan documents;
6. establish the actual Stargate identity/function of the thing being implemented;
7. only then write code.

Raw historical chat is **not** a default step anymore. Retrieve it only for a genuine ledger gap/conflict, repo-vs-ledger contradiction, or explicit Vardath request. Resolve the issue once and write the resolution back into the ledger.

## Core rule

**Do not code a subsystem from memory. Reconcile the whole affected slice first.**

The current plan/ledger is the default first-build specification. Newer explicit Vardath instructions override it and must be written back into continuity before handoff.

## Required procedure before every subsystem implementation

### 1. Recover the current design and implementation state

Use:
- `STANDING_RULES.md`;
- `CANONICAL_RECOVERY_LEDGER.md`;
- current public `main` and recent commits;
- `WNG_IMPLEMENTATION_CHECKLIST.md`;
- relevant master-plan append/active subsystem contract(s);
- retained assets and supplied external-mod source evidence where relevant.

Do not depend on the private WNG repository for current work.

### 2. Pass the Stargate identity/function gate

For each feature, establish:
- what it is in Stargate;
- what it actually does;
- who uses/owns it;
- its scale, limitations and interactions;
- what visual/audio/behavioral cues make it recognisable;
- how Vardath has chosen to represent it in WNG.

Do not implement generic sci-fi first and retrofit lore afterwards.

### 3. Inventory the affected slice completely

Before writing code, make an explicit working inventory of every known related element, including where relevant:
- current ledger requirements;
- newest Vardath corrections;
- current public Defs/source and recent commits;
- retained graphics/icons/textures/audio;
- faction/PawnKind/xenotype/race identity;
- recipes/resources/research;
- quests/incidents/sites;
- integrations and exact external Def/package IDs;
- save-state/exact-pawn requirements;
- native RimWorld/Odyssey/Biotech mechanics;
- historical WNG evidence only when needed for a known gap.

Assets are evidence. A retained/approved form or overlay must be accounted for rather than omitted because code memory is shorter.

### 4. Build the relationship map before implementation

For every inventory item identify:
- Stargate identity/function;
- identity layer: race/xenotype/caste/PawnKind/faction/backstory;
- physical hierarchy/transformations where relevant;
- economy/resource flow;
- state/save-load requirements;
- event trigger and completion transaction;
- native-game ownership vs WNG custom behavior;
- optional-mod ownership and absent-mod behavior;
- art/audio/UI requirements that the mechanics must leave room for.

Do not start coding until the map is coherent and still recognisably Stargate.

### 5. Preserve author-tunable design

Prefer Defs/settings/centralized configuration for author-facing values such as:
- story/event timing;
- cooldowns and population caps;
- raid/request frequency;
- resource costs/yields;
- combat/stat tuning;
- progression thresholds.

Technical constants may remain in code when they are genuinely implementation details.

Do not create tests whose purpose is to freeze a balance/design choice.

### 6. Implement the whole accounted slice

Implementation may be staged, but every known item must finish the pass as:
- **implemented**;
- **unfinished — dependency explicitly recorded**; or
- **changed/rejected by Vardath**.

There is no forgotten/silently removed state.

Do not represent an unfinished mechanic as finished with flavor text, a marker gene, empty comp or decorative-only substitute.

Do not invent a fallback resource/faction/technology merely because it is easier. In particular, do not repeat the rejected invented Goa'uld uranium/chemfuel fallback.

### 7. Verify function proportionately

Use checks needed for the current slice, such as:
- C# compile;
- XML/Def/reference sanity;
- code inspection for exact transaction/state behavior;
- real RimWorld testing/log review when available/required.

Static green does not outrank actual `Player.log`, RimDoctor, screenshots or live behavior.

Do not rebuild the old audit/release-gate bureaucracy.

### 8. Reconcile before moving on

Before leaving the slice:
- compare implementation against the full inventory and checklist;
- re-check Stargate function/identity for drift;
- inspect current public state for accidental removal/regression;
- record every unfinished dependency;
- update any Vardath correction/supersession;
- update `CANONICAL_RECOVERY_LEDGER.md`.

Only then move to the next subsystem.

## Mandatory working order

**CANONICAL LEDGER -> STARGATE LORE -> CURRENT PUBLIC STATE -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE LEDGER/HANDOFF**

The ledger update is part of completing the pass, not optional paperwork. It is what makes the next recovery smooth.
