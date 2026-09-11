# WNG — MANDATORY IMPLEMENTATION CHECKLIST

Author/design authority: **Vardath**.

# ⛔ STOP — CANONICAL HISTORY + PUBLIC RECONCILIATION + STARGATE LORE FIRST

**DO NOT WRITE, CHANGE, DELETE, REBUILD OR REINTERPRET WNG CODE UNTIL THE RECOVERY, RECONCILIATION AND LORE GATES BELOW HAVE BEEN COMPLETED.**

This checklist applies to **every pass, implementation, addition, correction, rebuild, integration, balance pass, art/audio pass and subsystem review**.

## RECOVERY GATE — USE THE ONE-TIME RECONSTRUCTION AND COMPLETED PUBLIC AUDIT

The broad WNG chat/history reconstruction was completed on 2026-09-11 and consolidated into `CANONICAL_RECOVERY_LEDGER.md`.

A later public-vs-plan/private reconciliation established that the ledger's original implementation snapshot was 45 public commits behind and that later checkpoint prose still omitted genuine unfinished branches. That completed audit is `PUBLIC_RECONCILIATION_2026-09-11.md`.

Before touching the mod:

- read `STANDING_RULES.md`;
- read `CANONICAL_RECOVERY_LEDGER.md` completely for recovered history/design;
- read `PUBLIC_RECONCILIATION_2026-09-11.md` completely;
- read `CURRENT_PUBLIC_STATE.md` completely;
- fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and verify the maintained HEAD/state against reality;
- inspect every newer real commit/file before deciding what exists;
- read the active subsystem contract/plan documents needed for this pass;
- **do not force Vardath to repeat old decisions**;
- **do not reread weeks of raw WNG chat by default**;
- retrieve older raw chat only if the canonical history/reconciliation marks an unresolved conflict/gap, current repo evidence conflicts with maintained continuity, or Vardath explicitly asks for raw-history review;
- when a historical conflict is resolved, update durable continuity so the same archaeology is not needed again.

**Hard rule: current public source is implementation truth.** Discussion, an assistant statement, a checkpoint, a private branch, a prepared private commit or a historical build does not make a feature current unless an equivalent real implementation exists on public `main`.

---

# ⛔ STARGATE LORE FIRST

**WNG IS A STARGATE MOD. DO NOT WRITE OR CHANGE CODE UNTIL THIS SECTION HAS BEEN ANSWERED.**

The most important question is not "what code is easiest?" It is:

> **What is this in Stargate, what does it actually do there, what has Vardath decided, what does current WNG already do, what does native RimWorld provide, and what is the best faithful implementation now?**

A generic sci-fi approximation is not acceptable merely because it compiles.

---

## A. STARGATE LORE GATE — ANSWER FIRST

Before implementation, establish from relevant Stargate canon/lore:

- **Is this actually Stargate?** Identify the exact species, faction, technology, craft, ship, weapon, structure, ability, event or concept being represented.
- **What is it called in Stargate?** Do not invent or restore obsolete WNG terminology when canon/current design has a better identity.
- **What does it actually do in Stargate?** Record its real purpose, capabilities, limitations and operating behavior.
- **Who uses it and why?** Identify the faction/species/caste/role that owns or operates it.
- **How does it interact with other Stargate systems?** For example: Stargates, transport rings, shields, culling beams, naquadah, Wraith feeding, Replicators, Ancient technology, Jaffa/Goa'uld command structure, etc.
- **What scale is it?** Do not turn a capital ship into a shuttle, a strategic system into a pawn ability, or a pawn ability into faction strategy without a deliberate gameplay abstraction.
- **What are the important visual/audio/behavioral cues?** These matter when later implementing graphics, sounds, effects, animations or UI.
- **Are there canon variations or era differences?** If sources conflict, reconcile them against Vardath's current design rather than silently choosing whichever version is easiest.

**If the implementation does not still feel recognisably Stargate after this mapping, stop and redesign it before coding.**

---

## B. VARDATH / HISTORY / RECONCILIATION / PLAN GATE

Before implementation, answer:

- **What does `CANONICAL_RECOVERY_LEDGER.md` say about the recovered design/history?**
- **What does `PUBLIC_RECONCILIATION_2026-09-11.md` classify as actually implemented, partial, missing required, changed/rejected, planned-only or live-test-needed?**
- **What does `CURRENT_PUBLIC_STATE.md` say now?**
- **What are Vardath's newest instructions in the current conversation?** Newer explicit Vardath instructions override older continuity and must then be written back.
- **What do `STANDING_RULES.md`, `CORRECTIONS_LOG.md`, `MASTER_PLAN.md` and active subsystem notes say?**
- **Is there a flagged unresolved historical conflict/gap?** If yes, retrieve only the relevant raw WNG history, resolve it chronologically, and update durable continuity.
- **Is this feature required, optional, intentionally deferred/planned-only, or explicitly changed/rejected?**
- **What parts are author-tunable?** Do not bury balance/design choices in hard-coded doctrine.

Do not ask Vardath to repeat an answer already preserved in the continuity set.

---

## C. CURRENT PUBLIC WNG STATE GATE

Before interpreting an old checklist or "next step" note, inspect current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main`.

Answer:

- **Does the current HEAD match the maintained live state?** If not, inspect what changed and update continuity before relying on prior implementation-state prose.
- **Does this feature already exist on current public `main`?**
- **What does it currently do in Defs/source/assets/research/integrations?**
- **What recent commits changed it?** Trace the actual implementation timeline when state is unclear.
- **Is the current implementation complete, partial, provisional, placeholder, broken, deliberately changed/rejected, planned-only, or merely awaiting refinement/live testing?**
- **What related systems already depend on it?**
- **What current art/audio/assets belong to it?** Assets are part of the feature inventory.

### Critical state rule

**An older note saying "next", "unfinished", "reconcile", "correct" or "rebuild" is NOT proof that the feature is absent.**

Verify current `main` first.

**"Rebuild/correct/refine" does not mean "remove". A named required feature remains required unless Vardath explicitly removes it.**

Likewise, an older/private implementation is not evidence that work landed publicly. Use it only after current public absence/partiality is proven.

---

## D. HISTORICAL / PRIVATE WNG REFERENCE GATE

Historical WNG has **no known-good state**, but it still contains useful evidence.

Use historical/private source/commits only when needed to answer:

- **What had WNG attempted before?**
- **What behavior/design was Vardath trying to achieve?**
- **What failed, regressed or caused problems?**
- **What names/assets/relationships are useful evidence?**
- **What architecture must NOT be copied because it was broken or obsolete?**

Historical/private source informs the design; it does not override the reconciliation, newer Vardath instructions, Stargate lore or current public implementation.

If public already has a valid equivalent foundation — for example native current shuttle mechanics, current Replicator hierarchy, current Queen/Neural-Lattice controller architecture or current Wraith/Asuran gravship mechanics — do **not** overwrite it merely because a similar older branch exists.

---

## E. RIMWORLD / DLC / OPTIONAL-MOD GATE

Before inventing custom code, determine what the game already provides.

Ask:

- **What native RimWorld 1.6/DLC system already performs this function?**
- **Can WNG use or extend native behavior instead of replacing it?**
- **What exact Def/class/component contracts does vanilla use?**
- **What must remain native for save/load, UI, AI, boarding, launch, gravship, power, fuel, faction, containment, ideology, anomaly or gene behavior?**
- **Which part genuinely requires WNG custom logic?**

For optional Stargate mods, establish ownership before coding:

- **Who owns the mechanic?** CatCraft, ONAC, RimGate, WNG or vanilla RimWorld?
- **What happens when the optional mod is absent?** WNG must remain valid where the current plan says it is standalone.
- **Are exact package IDs and Def names verified from supplied/source mod files?** Never guess an external Def identity.
- **Are we duplicating something the integration mod already provides?** Do not create competing factions/resources/systems without an explicit reason.

Current special warning: Ha'tak/Al'kesh standalone ship resources are **not** solved merely because Goa'uld transport rings have a standalone architect route. Do not invent uranium/chemfuel or another Goa'uld ship fallback.

---

## F. BEST-IMPLEMENTATION GATE

Only after A-E are answered, decide implementation.

Ask:

- **How can this be represented in RimWorld while preserving its Stargate identity and actual purpose?**
- **What is the smallest custom layer needed on top of native systems?**
- **How does it connect to the rest of WNG rather than existing as an isolated gimmick?**
- **What resources, research, factions, PawnKinds, genes, abilities, incidents, quests, ships, buildings, UI, art and audio does it touch?**
- **What state must survive save/load and transformations?**
- **What can be implemented now and what genuinely depends on later work?**
- **Am I inventing a fallback, resource, mechanic, faction, name or behavior that Vardath never requested and Stargate does not support?** If yes, stop unless it is technically necessary and clearly consistent with the plan.

Every known feature/item must finish the pass as one of:

- **IMPLEMENTED FOUNDATION / implemented**;
- **PARTIAL — unfinished dependencies explicitly recorded**;
- **MISSING REQUIRED — retained in the debt inventory**;
- **CHANGED / REJECTED by Vardath/current design**;
- **PLANNED ONLY / DEFERRED**;
- **LIVE-TEST NEEDED** where source exists but real play has not established behavior.

There is no status called "forgotten", "silently removed" or "I thought the private commit landed".

---

## G. PRE-COMMIT / PRE-HANDOFF CHECK

Before committing or moving on, answer **YES** to every applicable item:

- [ ] **HISTORY:** I read the canonical recovery ledger.
- [ ] **RECONCILIATION:** I read `PUBLIC_RECONCILIATION_2026-09-11.md` and did not use stale/private completion claims as public truth.
- [ ] **LIVE STATE:** I read `CURRENT_PUBLIC_STATE.md` and fetched current public `main`.
- [ ] **HEAD:** If public `main` advanced, I inspected the actual newer commits/files before coding.
- [ ] **STARGATE:** I verified what this is in Stargate canon/lore.
- [ ] **FUNCTION:** I verified what it actually does in Stargate, not just its name.
- [ ] **IDENTITY:** The implementation still reads/plays as Stargate rather than generic sci-fi.
- [ ] **VARDATH:** I applied the newest explicit Vardath instructions and did not ask for decisions already preserved in continuity.
- [ ] **PLAN:** I checked current standing rules, master plan and active subsystem contracts.
- [ ] **RAW HISTORY ONLY IF NEEDED:** If a genuine continuity gap/conflict existed, I retrieved relevant raw history, resolved it and updated continuity. Otherwise I did not waste the handoff rereading weeks of chat.
- [ ] **PRIVATE IS REFERENCE:** I did not equate old/private code or a prepared private commit with current public implementation.
- [ ] **PRESERVATION:** I did not remove/replace an existing required current feature merely because historical code also exists.
- [ ] **NATIVE GAME:** I checked vanilla RimWorld/DLC mechanics and reused them where appropriate.
- [ ] **INTEGRATIONS:** I respected ownership boundaries and verified optional external Def/package identities from source where relevant.
- [ ] **NO INVENTED SUBSTITUTE:** I did not invent an unsupported generic replacement/fallback because it was easier.
- [ ] **COMPLETE INVENTORY:** Every known related feature is implemented, partial/dependency-recorded, missing-required/tracked, changed/rejected, planned-only/deferred, or live-test-needed.
- [ ] **VERIFY FUNCTION:** I used only the necessary compile/XML/reference/live-game/log checks needed to establish function and did not call static validation live validation.
- [ ] **CONTINUITY UPDATED:** I updated current state/reconciliation with the real new public HEAD and actual feature statuses before handoff.

If any applicable box is **NO**, the pass is not ready to move on.

---

## Mandatory working order

For every WNG subsystem or feature:

**CANONICAL HISTORY -> PUBLIC RECONCILIATION -> CURRENT PUBLIC STATE -> STARGATE LORE -> CURRENT REPO -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE LIVE STATE/HANDOFF**

Do not reverse this order by writing code first and discovering intended history, current public reality or Stargate behavior afterwards.
