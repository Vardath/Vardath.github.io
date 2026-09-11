# WNG — refresh memory and continue

Read this before touching the WNG 1.6 repository after any context reset.

# ⛔ THE RECOVERY WORK HAS ALREADY BEEN DONE

The broad WNG conversation/history reconstruction was completed on **2026-09-11** and consolidated into:

**`CANONICAL_RECOVERY_LEDGER.md`**

The current implementation state is maintained separately in:

**`CURRENT_PUBLIC_STATE.md`**

The ledger preserves settled history. The current-state file exists specifically so the ledger's original repository snapshot cannot be mistaken for live implementation state after the mod advances.

Do not make Vardath reconstruct the project again. Do not reread weeks of raw chat by default. Recover from the canonical ledger, the live-state file and the actual current public repository.

Retrieve older raw WNG chat only when:
- the canonical ledger explicitly flags an unresolved historical conflict/gap;
- current public repo evidence conflicts with the ledger/state file; or
- Vardath explicitly asks for raw-history review.

When a raw-history issue is resolved, update continuity so it never has to be solved again.

## Identity and authority

- Mod: **Wraith & Nanite Gravtech (WNG)** for RimWorld 1.6.
- Author/final design authority: **Vardath**.
- Active code repository: public `Vardath/Wraith-Nanite-Gravtech-1.6`.
- Durable continuity: `Vardath/Vardath.github.io/wng-rebuild/`.
- Private/old WNG repositories/builds are historical/reference evidence only unless Vardath explicitly re-authorizes them.
- There are **no known-good historical WNG builds**.

## Mandatory recovery order

1. Read `STANDING_RULES.md`.
2. Read **all of `CANONICAL_RECOVERY_LEDGER.md`**.
3. Read **all of `CURRENT_PUBLIC_STATE.md`**.
4. Read `WNG_IMPLEMENTATION_CHECKLIST.md`.
5. Fetch current public mod `main` and compare its HEAD/state to `CURRENT_PUBLIC_STATE.md`.
6. If `main` advanced, inspect the actual commits/files before relying on old state and update `CURRENT_PUBLIC_STATE.md`.
7. Read only the active subsystem contract/master-plan append(s) needed for the genuine next slice.
8. Read `PLAN_EXECUTION_PROTOCOL.md` and implement through the checklist.
9. After the batch, update `CURRENT_PUBLIC_STATE.md` before handoff.

`NEXT_GPT_PRIMER.md` is only a short pointer. It never outranks the ledger, current-state file or current `main`.

## Mandatory implementation order

**CANONICAL LEDGER -> CURRENT PUBLIC STATE -> STARGATE LORE -> CURRENT REPO -> ACTIVE CONTRACTS -> VANILLA/OPTIONAL-MOD MECHANICS -> FEATURE MAP -> IMPLEMENT -> VERIFY -> RECONCILE -> UPDATE HANDOFF**

Do not code from memory or a stale assistant summary.

## Stargate-first rule

WNG is a Stargate mod. Before every implementation/addition/rebuild/correction, establish:
- what the feature actually is in Stargate;
- what it actually does, including limitations/scale/ownership;
- what Vardath's current decision is in the ledger/current conversation;
- what current public WNG already implements;
- what native RimWorld/Odyssey/Biotech already provides;
- what any optional Stargate integration owns;
- and only then the best faithful RimWorld implementation.

If it has become generic sci-fi rather than recognisably Stargate, redesign before coding.

## Critical state rules

- **Current public `main` is implementation state.** Old next-step/checkpoint prose can be stale.
- `next`, `unfinished`, `reconcile`, `correct`, `refine`, or `rebuild` never means delete a required existing feature.
- **Al'kesh is required and currently implemented; do not remove it.**
- **Ha'tak is implemented as an Odyssey-native gravship family**, including real Death Gliders, landed hostile carrier site and true player orbital bombardment.
- Hostile Ha'tak takeoff/retreat/pursuit remains blocked by Odyssey's player-oriented singleton; do not fake it with proxy deletion/replacement.
- **Human-form nanite physiology is implemented** using native food behavior as Nanite Reserve, with same-tick biological Malnutrition removal, reserve-funded repair/fabrication and EMP disruption.
- **The exact Replicator Queen / first Asuran recovery layer is implemented.** One exact age-13 female nanite-humanoid Queen is physically held in a real cryptosleep casket, recruited only on real vault release, and targeted by an all-or-nothing four-operative nonlethal recovery team using a physical native Asuran Jumper.
- Queen capture is committed only at the real leaving-skyfaller map-exit boundary when that exact pawn is still inside that exact transit container.
- Ordinary Asurans do not possess the Queen's sovereign authority.
- Block Replicators keep their separate stored-matter economy; human-form Nanite Reserve does not replace it.
- Do not invent a Goa'uld uranium/chemfuel fallback or any other unspecified substitute.
- Supplied ONAC/RimGate/Stargates source identities recorded in the ledger/contracts are authoritative for optional integrations.
- Use **Wraith Grav Engine**, not obsolete Wraith Gravcore.
- Ordinary Wraith Drain Life, strategic faction hunger, Mature-Hive feeding ecology and Mature-Hive retaliation are separate systems.
- CatCraft owns Stargate network/dial/iris/receive mechanics; WNG integrates around them rather than replacing them.
- No replacement/generated art unless Vardath explicitly asks.

## Current live public snapshot

Read `CURRENT_PUBLIC_STATE.md` and then verify against GitHub. At this update the mod HEAD is:

**`442800f3bd84de018c47403ec50663252a60b7c5` — `docs: record hardened Queen recovery contract`**

The canonical ledger's `4af4f60...` SHA is an original reconstruction checkpoint, not the current implementation head.

The genuine next implementation slice is **Replicator Queen sovereign authority over the real block-Replicator hierarchy**. It must be exact-Queen control state, not a passive stat aura/outbreak modifier and not a generic Asuran xenotype ability. Existing hierarchy, split/recombine, adaptations, block stored matter, EMP and containment remain real mechanics under sovereignty.

## Handoff maintenance

Before ending any meaningful work batch, update `CURRENT_PUBLIC_STATE.md` with:
- exact new public HEAD;
- what actually changed;
- implemented / unfinished-dependency / changed-by-Vardath / live-test-needed status;
- any newly superseded decision;
- the next genuinely unfinished slice derived from current `main`.

This update is part of completing the work. The objective is that Vardath can say **“refresh memory and continue”** and the next GPT can read the actual handoff and continue without interrogation or reconstruction.
