# WNG rebuild — mandatory plan execution protocol

Author/design authority: **Vardath**.

This protocol is part of the WNG rebuild plan. It exists because prior implementation repeatedly started from partial recollection and only discovered omitted features after Vardath had to correct them. That process is not acceptable for this rebuild.

# ⛔ FIRST GATE: STARGATE LORE BEFORE CODE

**WNG is a Stargate mod. `WNG_IMPLEMENTATION_CHECKLIST.md` must be answered before every implementation pass.**

Before code, establish:
- what this is in Stargate;
- what it actually does in Stargate, including capabilities, limitations, scale, users and relationships;
- what Vardath has said about it in chat/history;
- what current public WNG `main` already does;
- what historical WNG attempted and what failed;
- what native RimWorld/Odyssey/Biotech already provides;
- what optional Stargate integrations own;
- and only then how to implement it faithfully and cleanly.

Do not write a generic sci-fi approximation and check Stargate lore afterwards.

An older note saying `next`, `unfinished`, `reconcile`, `correct` or `rebuild` does not prove a feature is absent from current `main`. Verify the current public state first. **Rebuild/correct/refine does not mean remove.**

## Core rule

**Do not code a subsystem from memory. Reconcile the whole subsystem first.**

The plan is not a loose suggestion to glance at after implementation. It is the default first-build specification. Newer explicit Vardath instructions override older plan text, and all values/systems remain editable later, but the current plan must be followed rigorously while building the first complete version.

## Required procedure before every subsystem implementation

### 0. Pass the mandatory implementation checklist
Read and answer `WNG_IMPLEMENTATION_CHECKLIST.md` first.

Required order:

**STARGATE LORE -> VARDATH/CHAT -> CURRENT PUBLIC STATE -> HISTORICAL EVIDENCE -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> HANDOFF**

Do not proceed to implementation while an applicable checklist gate is unanswered.

### 1. Read the governing material
Read, in order:
- `STANDING_RULES.md`;
- `WNG_IMPLEMENTATION_CHECKLIST.md`;
- `CORRECTIONS_LOG.md`;
- `MASTER_PLAN.md` sections relevant to the subsystem and adjacent dependencies;
- any active subsystem document, such as `REPLICATOR_HIERARCHY.md` or `REPLICATOR_QUEEN.md`;
- the current public 1.6 repository state and relevant recent commits.

Do not depend on the private WNG repository for current work.

### 2. Inventory the subsystem completely
Before writing code, make an explicit working inventory of every known element belonging to the subsystem. Sources must include, where relevant:
- Stargate canon/lore and the feature's real function;
- current plan requirements;
- Vardath chat/history and corrections;
- existing public Defs/source and recent implementation history;
- retained graphics/icons/textures;
- retained audio if present;
- faction/PawnKind/xenotype/race references;
- recipes/resources/research;
- quests/incidents/sites;
- integrations;
- save-state requirements;
- native RimWorld/Odyssey/Biotech mechanics;
- relevant historical WNG source only as reference evidence.

Assets are evidence. If an approved graphic exists for a form such as Shield adaptation, Artillery, Repairer, Burrower, Controller, Titan or Siege Mass, it must be reconciled against the feature inventory instead of ignored because the remembered code list was shorter.

### 3. Build the feature map before implementation
For each inventory item, record its intended relationship to the rest of the subsystem. Examples:
- Stargate identity/function: what canon role is being represented and what must remain recognisable;
- identity: race/xenotype/caste/PawnKind/faction/backstory;
- physical hierarchy: what combines into what and what breaks down into what;
- specialist branch: how a specialist appears and what it actually does;
- adaptation: what evidence unlocks it, what gameplay effect it has, what visual representation exists;
- economy: what resource is consumed/produced and how state survives transitions;
- event: what triggers it, what real pawn/item/site state changes, how it ends;
- integration: who owns which mechanics and what happens when the optional mod is absent;
- vanilla mapping: what native game mechanic should remain authoritative and what WNG genuinely needs to add.

Do not start coding until this map is internally coherent and still recognisably Stargate.

### 4. Distinguish first-build defaults from implementation invariants
Author-tunable values must remain easy to change. Prefer Defs, settings or centralized configuration where practical for:
- story/event timing;
- cooldowns that affect balance;
- population counts;
- raid/event frequency;
- resource costs/yields;
- combat/stat tuning;
- progression thresholds.

Technical constants may remain in code when they are genuinely implementation details rather than author-facing design locks.

Do not create anti-regression tests that freeze a current balance value or design choice.

### 5. Implement the whole accounted slice
Implementation may be staged, but the stage must be explicit. For every feature-map item, end the pass with one of three statuses:
- **implemented**;
- **unfinished — dependency recorded**;
- **changed/rejected by Vardath**.

There is no fourth status called `forgotten`, `silently removed`, or `assumed absent from an old note`.

Do not represent an unfinished feature as complete through flavor text, placeholder Defs, marker genes or empty comps.

Do not invent a generic fallback, duplicate resource, new faction, substitute technology or altered canon role merely because it is easier to implement. Any necessary abstraction must remain consistent with Stargate lore and Vardath's instructions.

### 6. Verify function, not doctrine
Use only checks necessary to establish that the current implementation is usable, such as:
- C# compile;
- XML/Def load/reference sanity when needed;
- direct code inspection for transaction correctness;
- later live RimWorld testing/log review.

Verification must also include a design sanity question: **does this still behave like the Stargate thing it is supposed to represent?**

Do not rebuild the prior anti-regression/release-gate framework. A test must not become the authority over Vardath's design.

### 7. Reconcile again before moving on
Before leaving the subsystem:
- compare the implemented state against `WNG_IMPLEMENTATION_CHECKLIST.md` and the feature inventory;
- re-check Stargate lore/function for any abstraction that drifted during implementation;
- inspect current public state so the handoff records what actually exists now;
- inspect retained assets again for unaccounted forms/content;
- inspect plan/corrections for missed branches;
- record any unfinished dependency;
- update continuity documentation if Vardath corrected the design/process.

Only after this reconciliation should work move to another subsystem.

## Current Replicator application

The fresh public reset is currently in the **block Replicator foundation** and must remain there until the full planned foundation is accounted for.

Physical hierarchy currently intended:

**Drone/base -> Hunter -> Bulwark -> Titan -> Siege Mass** through upward recombination.

**Siege Mass -> Titan -> Bulwark -> Hunter -> Drone/base** through genuine destruction breakup.

Split-born children have a current first-build recombination delay of roughly one in-game hour (historically 2,500 ticks) so killing a large form does not result in immediate recreation of that same large form. The delay is gameplay behavior and remains tunable.

The Replicator foundation also includes, and must not omit:
- Controller;
- Repairer;
- Burrower;
- Artillery/Siege support;
- Ranged adaptation;
- Armor adaptation;
- Power adaptation;
- Grav adaptation;
- Shield adaptation / Shield Replicators;
- learned anti-shield/countermeasure development;
- matter economy and dangerous Replicator Matter;
- assimilation;
- regeneration;
- EMP suppression;
- containment behavior;
- swarm coordination/AI;
- player-owned safety/control behavior;
- Child's Toy/player branch;
- state inheritance through split/recombine where appropriate;
- later human-form/Asuran/Queen sovereign interactions as dependent branches.

Do not move to Wraith implementation while known block-Replicator foundation features are still silently absent. If a dependent later feature cannot yet be completed, mark the dependency explicitly and continue completing everything that can be done in the current layer.
